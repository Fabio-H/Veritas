"""
Core decoding engine for ps-deobfuscator.

Mirrors the browser Veritas deobfuscator: scoring, recursive URL/Hex/Base64
(including UTF-8, UTF-16LE, GZIP), .NET vs FQDN heuristics, and IOC extraction.

Extensions beyond the original JS (requested for this CLI):
- zlib / raw DEFLATE on decoded bytes (magic 0x78 zlib header or raw inflate attempt)
- extra candidates from PowerShell FromBase64String('...') / IEX-adjacent quoted Base64
"""

from __future__ import annotations

import base64
import binascii
import codecs
import io
import gzip
import logging
import math
import re
import zlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Final, Iterable
from urllib.parse import unquote_plus

from ps_deobfuscator.app_info import APP_NAME, APP_VERSION

# ---------------------------------------------------------------------------
# Configuration (frozen copies of JS CONFIG)
# ---------------------------------------------------------------------------

SCORE_KEYWORDS: Final[tuple[str, ...]] = (
    "IEX",
    "Invoke-",
    "New-Object",
    "WebClient",
    "DownloadString",
    "-EncodedCommand",
    "Start-Process",
    "cmd.exe",
    "powershell.exe",
    "http",
    "https",
    "127.0.0.1",
)

MAX_DECODE_LAYERS: Final[int] = 8
MAX_PAYLOAD_CHARS: Final[int] = 1_000_000
MAX_DECOMPRESSED_BYTES: Final[int] = 2_000_000
MAX_XOR_INPUT_BYTES: Final[int] = 65_536
MAX_XOR_TOP_CANDIDATES: Final[int] = 8
PRINTABLE_RATIO_WEIGHT: Final[int] = 50
READABLE_PRINTABLE_THRESHOLD: Final[float] = 0.55
MIN_HEX_LENGTH: Final[int] = 8
MIN_EMBEDDED_ASSIGN_BASE64_LEN: Final[int] = 28
MIN_EMBEDDED_ASSIGN_BLOB_ENTROPY: Final[float] = 3.0
DECODE_CHAIN_PREVIEW_CHARS: Final[int] = 200

SUSPICIOUS_PS_COMMANDS: Final[tuple[str, ...]] = (
    "IEX",
    "Invoke-Expression",
    "Invoke-WebRequest",
    "DownloadString",
    "DownloadFile",
    "FromBase64String",
    "Start-Process",
    "WebClient",
)

DOTNET_NAMESPACE_PREFIXES: Final[tuple[str, ...]] = (
    "system.",
    "microsoft.",
    "newtonsoft.",
    "system.management.automation.",
    "system.security.",
    "system.net.",
    "system.io.",
    "system.text.",
    "system.runtime.",
    "system.diagnostics.",
    "system.threading.",
    "system.collections.",
)

COMMON_TLDS: Final[frozenset[str]] = frozenset(
    {
        "com",
        "net",
        "org",
        "io",
        "co",
        "uk",
        "br",
        "edu",
        "gov",
        "mil",
        "info",
        "biz",
        "tv",
        "me",
        "cc",
        "xyz",
        "ru",
        "cn",
        "de",
        "fr",
        "au",
        "jp",
        "nl",
        "eu",
        "int",
        "arpa",
        "local",
        "app",
        "dev",
        "cloud",
        "tech",
        "site",
        "online",
        "store",
        "blog",
        "ai",
        "go",
        "us",
        "ca",
        "in",
        "mx",
        "pt",
        "example",
        "test",
        "invalid",
        "localhost",
        "internal",
        "corp",
        "lan",
        "home",
        "arpa",
    }
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DecodeLayer:
    """One layer in the recursive decode chain."""

    type: str
    text: str


@dataclass(frozen=True, slots=True)
class DecodeResult:
    """Full decode output: layers + final plaintext."""

    layers: tuple[DecodeLayer, ...]
    final_text: str


@dataclass(frozen=True, slots=True)
class IocRow:
    """Single extracted IOC row (matches JS table semantics)."""

    tipo: str
    valor: str
    confianca: str = ""


@dataclass(slots=True)
class DecodeCandidate:
    """Internal: one candidate transformation at a layer."""

    type: str
    text: str
    score: float = field(compare=False)
    force_continue: bool = field(default=False, compare=False)


class PayloadTooLargeError(ValueError):
    """Raised when input exceeds the safe static-analysis limit."""


# ---------------------------------------------------------------------------
# Scoring (matches JS Scoring)
# ---------------------------------------------------------------------------


def keyword_score(s: str) -> int:
    n = 0
    for kw in SCORE_KEYWORDS:
        idx = 0
        while True:
            i = s.find(kw, idx)
            if i == -1:
                break
            n += 1
            idx = i + len(kw)
    return n


def printable_ratio(s: str) -> float:
    if not s:
        return 0.0
    printable = 0
    for c in s:
        o = ord(c)
        if o in (9, 10, 13) or 32 <= o <= 126:
            printable += 1
    return printable / len(s)


def shannon_entropy_bytes(data: bytes) -> float:
    """Shannon entropy on byte stream (0.0..8.0)."""
    if not data:
        return 0.0
    counts: dict[int, int] = {}
    for b in data:
        counts[b] = counts.get(b, 0) + 1
    total = len(data)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        entropy -= p * math.log2(p)
    return entropy


def score_text(s: str) -> float:
    return keyword_score(s) + printable_ratio(s) * PRINTABLE_RATIO_WEIGHT


def is_readable_utf8(s: str) -> bool:
    return printable_ratio(s) >= READABLE_PRINTABLE_THRESHOLD


# ---------------------------------------------------------------------------
# Domain / .NET classification (matches JS DomainNet)
# ---------------------------------------------------------------------------


def extract_hostname_from_url(url_string: str) -> str:
    from urllib.parse import urlparse

    try:
        u = urlparse(url_string)
        if u.hostname:
            return u.hostname
    except Exception:
        pass
    m = re.match(r"^https?://([^/?#\s]+)", url_string, re.I)
    if not m:
        return ""
    host = m.group(1)
    return re.sub(r":\d+$", "", host)


def looks_like_dot_net_namespace_or_class(value: str) -> bool:
    s = value.strip()
    if "." not in s or "://" in s or "/" in s or "@" in s:
        return False
    parts = s.split(".")
    if len(parts) < 2:
        return False
    lower0 = parts[0].lower()
    last_lower = parts[-1].lower()

    if (
        len(parts) == 2
        and lower0 in ("system", "microsoft", "windows")
        and last_lower in COMMON_TLDS
    ):
        return False

    low = s.lower()
    for p in DOTNET_NAMESPACE_PREFIXES:
        if low.startswith(p):
            return True

    roots_multi = frozenset(
        {
            "system",
            "microsoft",
            "windows",
            "management",
            "reflection",
            "diagnostics",
            "collections",
            "runtime",
            "threading",
            "security",
            "globalization",
            "servicemodel",
            "configuration",
            "componentmodel",
            "activities",
            "workflow",
            "presentation",
            "drawing",
            "forms",
            "serialization",
        }
    )
    if lower0 in roots_multi and len(parts) >= 3:
        return True
    if lower0 in roots_multi and len(parts) == 2 and last_lower not in COMMON_TLDS:
        return True

    if re.match(r"^(IO|UI|Xml|Linq|Data|Net|Text|Threading)\.[A-Z]", s):
        return True

    all_pascal = all(re.match(r"^[A-Z][A-Za-z0-9_]*$", seg) for seg in parts)
    if all_pascal and len(parts) >= 2 and last_lower not in COMMON_TLDS:
        return True

    return False


def network_fqdn_structure(value: str) -> bool:
    s = value.strip()
    if "://" in s or "/" in s or "@" in s:
        return False
    parts = s.split(".")
    if len(parts) < 2:
        return False

    def label_ok(lab: str) -> bool:
        return bool(re.match(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$", lab, re.I))

    if not all(label_ok(p) for p in parts):
        return False
    last = parts[-1].lower()
    if not re.match(r"^[a-z]{2,24}$", last):
        return False
    has_at_least_two_dots = len(parts) >= 3
    apex_with_known_tld = len(parts) == 2 and last in COMMON_TLDS
    if not (has_at_least_two_dots or apex_with_known_tld):
        return False
    if last in COMMON_TLDS:
        return True
    if 2 <= len(last) <= 6:
        return True
    return False


def looks_like_network_fqdn(value: str) -> bool:
    if looks_like_dot_net_namespace_or_class(value):
        return False
    return network_fqdn_structure(value)


# ---------------------------------------------------------------------------
# Utils (escape / bytes)
# ---------------------------------------------------------------------------


def escape_html(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def escape_regex(t: str) -> str:
    return re.escape(t)


def normalize_base64_string(s: str) -> str:
    t = re.sub(r"\s+", "", s).replace("-", "+").replace("_", "/")
    pad = len(t) % 4
    if pad:
        t += "=" * (4 - pad)
    return t


def normalize_base32_string(s: str) -> str:
    t = re.sub(r"\s+", "", s).upper()
    pad = len(t) % 8
    if pad:
        t += "=" * (8 - pad)
    return t


def has_url_encoding(s: str) -> bool:
    return bool(re.search(r"%[0-9A-Fa-f]{2}", s))


def looks_like_hex(s: str) -> bool:
    t = re.sub(r"\s+", "", s)
    if len(t) < MIN_HEX_LENGTH or len(t) % 2 != 0:
        return False
    return bool(re.fullmatch(r"[0-9a-fA-F]+", t))


def looks_like_base64(s: str) -> bool:
    t = normalize_base64_string(s)
    if len(t) < 8 or len(t) % 4 != 0:
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9+/]+=*", t))


def _looks_like_encoded_base64_token(norm_no_ws: str) -> bool:
    """Heuristic: ASCII letters-only strings often match Base64 alphabet but are not payloads."""
    if "=" in norm_no_ws:
        return True
    return any(ch in "+/0123456789" for ch in norm_no_ws)


def looks_like_base32(s: str) -> bool:
    t = normalize_base32_string(s)
    if len(t) < 16 or len(t) % 8 != 0:
        return False
    return bool(re.fullmatch(r"[A-Z2-7]+=*", t))


def has_escaped_unicode(s: str) -> bool:
    return bool(
        re.search(r"(\\x[0-9a-fA-F]{2})|(\\u[0-9a-fA-F]{4})|(%u[0-9a-fA-F]{4})", s)
    )


def can_apply_more_encoding(s: str) -> bool:
    return (
        has_url_encoding(s)
        or looks_like_hex(s)
        or looks_like_base64(s)
        or looks_like_base32(s)
        or has_escaped_unicode(s)
    )


_RE_B64_TOKEN_WITH_PAD = re.compile(r"\A([A-Za-z0-9+/_-]+)(=+)\Z")
_RE_B64_TOKEN = re.compile(r"\A[A-Za-z0-9+/_-]+=*\Z")


def input_anomalies(raw: str) -> tuple[str, ...]:
    """Non-fatal input irregularities worth surfacing in the UI.

    The decoder stays deliberately lenient (malformed padding is a common
    evasion trick in the wild), so anomalies are reported to the analyst
    instead of rejecting the payload.
    """
    notes: list[str] = []
    stripped = raw.strip()

    # Only judge padding when the whole input is a single Base64-like token;
    # interior whitespace means mixed content (commands, flags, prose).
    if stripped and not re.search(r"\s", stripped) and _RE_B64_TOKEN.match(stripped):
        m = _RE_B64_TOKEN_WITH_PAD.match(stripped)
        body = m.group(1) if m else stripped
        pad_found = len(m.group(2)) if m else 0
        expected = (-len(body)) % 4
        if expected == 3:
            notes.append(
                "Base64 length is invalid (one stray or missing character); "
                "the decode result may be unreliable."
            )
        elif pad_found != expected:
            notes.append(
                f"Invalid Base64 padding: found {pad_found} '=' but {expected} expected. "
                "Decoded after automatic repair (malformed padding is a common evasion trick)."
            )

    if "\x00" in raw:
        notes.append("Input contains NUL bytes; they were stripped before analysis.")

    return tuple(notes)


def strip_null_bytes(s: str) -> str:
    if "\x00" not in s:
        return s
    return s.replace("\x00", "")


def validate_payload_size(raw: str) -> None:
    """Keep GUI/CLI analysis bounded for accidental huge pastes or files."""
    if len(raw) > MAX_PAYLOAD_CHARS:
        raise PayloadTooLargeError(
            f"Input is too large ({len(raw):,} chars). "
            f"Limit is {MAX_PAYLOAD_CHARS:,} chars for safe static analysis."
        )


def try_url_decode(s: str) -> str | None:
    if not has_url_encoding(s):
        return None
    try:
        dec = unquote_plus(s.replace("+", "%20"))
    except (ValueError, UnicodeDecodeError):
        return None
    return dec if dec != s else None


def try_hex_decode(s: str) -> str | None:
    if not looks_like_hex(s):
        return None
    t = re.sub(r"\s+", "", s)
    try:
        raw = binascii.unhexlify(t)
    except binascii.Error:
        return None
    try:
        dec = raw.decode("utf-8", errors="replace")
    except UnicodeDecodeError:
        return None
    return dec if dec else None


def try_unicode_escape_decode(s: str) -> tuple[str, str] | None:
    if not has_escaped_unicode(s):
        return None
    if "%u" in s:
        try:
            s = re.sub(
                r"%u([0-9a-fA-F]{4})",
                lambda m: chr(int(m.group(1), 16)),
                s,
            )
        except ValueError:
            return None
    try:
        decoded = codecs.decode(s, "unicode_escape")
    except (ValueError, UnicodeDecodeError):
        return None
    if not decoded or decoded == s:
        return None
    return ("Unicode escape decode", decoded)


def gunzip_bytes(data: bytes) -> bytes | None:
    if len(data) < 3 or data[0:2] != b"\x1f\x8b":
        return None
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as gz:
            out = gz.read(MAX_DECOMPRESSED_BYTES + 1)
    except Exception:
        return None
    if len(out) > MAX_DECOMPRESSED_BYTES:
        return None
    return out


def _bounded_zlib_decompress(data: bytes, wbits: int) -> bytes | None:
    try:
        dec = zlib.decompressobj(wbits)
        out = dec.decompress(data, MAX_DECOMPRESSED_BYTES + 1)
        if len(out) > MAX_DECOMPRESSED_BYTES or dec.unconsumed_tail:
            return None
        out += dec.flush(MAX_DECOMPRESSED_BYTES + 1 - len(out))
    except Exception:
        return None
    if len(out) > MAX_DECOMPRESSED_BYTES:
        return None
    return out


def zlib_inflate_bytes(data: bytes) -> bytes | None:
    """Try zlib-wrapped or raw DEFLATE (extensions for CLI)."""
    if not data:
        return None
    # zlib header typical 0x78
    if len(data) >= 2 and data[0] == 0x78:
        for wbits in (zlib.MAX_WBITS, -zlib.MAX_WBITS):
            out = _bounded_zlib_decompress(data, wbits)
            if out is not None:
                return out
    # raw deflate (no header), best-effort
    return _bounded_zlib_decompress(data, -15)


def _decode_utf8_utf16le_from_bytes(data: bytes) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    out.append(("UTF-8", data.decode("utf-8", errors="replace")))
    out.append(("UTF-16LE", data.decode("utf-16-le", errors="replace")))
    return out


def _expand_compressed_variants(
    label_prefix: str, inflated: bytes
) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for enc_label, txt in _decode_utf8_utf16le_from_bytes(inflated):
        rows.append((f"{label_prefix} -> {enc_label}", txt))
    return rows


def base64_candidates(s: str) -> list[tuple[str, str]]:
    """Return list of (type_label, decoded_text) matching JS base64Candidates + extensions."""
    if not looks_like_base64(s):
        return []
    t = normalize_base64_string(s)
    try:
        raw = base64.b64decode(t)
    except Exception:
        return []

    out: list[tuple[str, str]] = []
    for enc_label, txt in _decode_utf8_utf16le_from_bytes(raw):
        out.append((f"Base64 -> {enc_label}", txt))

    gz = gunzip_bytes(raw)
    if gz is not None:
        out.extend(_expand_compressed_variants("Base64 -> GZIP", gz))
    else:
        zl = zlib_inflate_bytes(raw)
        if zl is not None and zl != raw:
            out.extend(_expand_compressed_variants("Base64 -> ZLIB/DEFLATE", zl))

    # Filter weak UTF-8 when UTF-16LE scores better (JS logic, only direct Base64)
    filtered: list[tuple[str, str]] = []
    utf16_plain = next((x for x in out if x[0] == "Base64 -> UTF-16LE"), None)
    for typ, txt in out:
        if typ == "Base64 -> UTF-8" and not is_readable_utf8(txt):
            if utf16_plain and score_text(utf16_plain[1]) >= score_text(txt):
                continue
        filtered.append((typ, txt))
    return filtered


def base32_candidates(s: str) -> list[tuple[str, str]]:
    if not looks_like_base32(s):
        return []
    t = normalize_base32_string(s)
    try:
        raw = base64.b32decode(t, casefold=True)
    except (binascii.Error, ValueError):
        return []

    out: list[tuple[str, str]] = []
    for enc_label, txt in _decode_utf8_utf16le_from_bytes(raw):
        out.append((f"Base32 -> {enc_label}", txt))
    return out


_RE_FROM_B64 = re.compile(
    r"FromBase64String\s*\(\s*['\"]([A-Za-z0-9+/=\s]+)['\"]", re.IGNORECASE
)
_RE_IEX_QUOTED_B64 = re.compile(
    r"\bIEX\b[^'\"]{0,120}?['\"]([A-Za-z0-9+/=\s]{16,})['\"]", re.IGNORECASE | re.DOTALL
)

_PS_ASSIGN_VAR_FRAGMENT = r"(?:\$[A-Za-z_][\w:]*|\$\{[^}]+\})"
_RE_PS_ASSIGN_DQ_B64 = re.compile(
    rf"""
    (?P<pre>
      {_PS_ASSIGN_VAR_FRAGMENT}
      \s*=\s*
      (?:
          #
          \s*
          [^\r\n]*
      )?
      (?:
          \s
          |
          \r?\n
      )*
    )
    "
    (?P<blob>
      [^"\r\n]+
    )
    "
    """,
    re.VERBOSE | re.MULTILINE,
)
_RE_PS_ASSIGN_SQ_B64 = re.compile(
    rf"""
    (?P<pre>
      {_PS_ASSIGN_VAR_FRAGMENT}
      \s*=\s*
      (?:
          #
          \s*
          [^\r\n]*
      )?
      (?:
          \s
          |
          \r?\n
      )*
    )
    '
    (?P<blob>
      [^\r\n']*
    )
    '
    """,
    re.VERBOSE | re.MULTILINE,
)
_RE_ENCODED_COMMAND = re.compile(
    r"""
    (?:^|[\s;|&])
    -
    (?:encodedcommand|enc)
    \s+
    (?:
        "([^"]+)"
        |
        '([^']+)'
        |
        ([A-Za-z0-9+/_=-]+)
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


def encodedcommand_candidates(s: str) -> list[tuple[str, str]]:
    """Decode PowerShell -EncodedCommand/-enc argument with automatic padding."""
    found: list[tuple[str, str]] = []
    seen_chunks: set[str] = set()

    for m in _RE_ENCODED_COMMAND.finditer(s):
        chunk = (m.group(1) or m.group(2) or m.group(3) or "").strip()
        if not chunk or chunk in seen_chunks:
            continue
        seen_chunks.add(chunk)

        normalized = normalize_base64_string(chunk)
        if not looks_like_base64(normalized):
            continue

        try:
            raw = base64.b64decode(normalized)
        except Exception:
            continue

        for enc_label, txt in _decode_utf8_utf16le_from_bytes(raw):
            if txt and txt != s:
                found.append((f"EncodedCommand -> {enc_label}", txt))
    return found


def rot13_candidate(s: str) -> str | None:
    """Apply ROT13 only when it improves score or readability."""
    transformed = s.translate(
        str.maketrans(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm",
        )
    )
    if transformed == s:
        return None

    old_score = score_text(s)
    new_score = score_text(transformed)
    if new_score > old_score:
        return transformed
    if not is_readable_utf8(s) and is_readable_utf8(transformed):
        return transformed
    return None


def _decode_text_from_xor(raw: bytes) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    out.append(("UTF-8", raw.decode("utf-8", errors="replace")))
    if len(raw) % 2 == 0:
        out.append(("UTF-16LE", raw.decode("utf-16-le", errors="replace")))
    return out


def xor_byte_candidates(s: str) -> list[tuple[str, str]]:
    """Bruteforce XOR with all 1-byte keys and keep top scoring outputs."""
    if not s:
        return []

    # Quoted `$var = "..." ` patterns are handled by Embedded PS assignment; XOR often false-positives.
    if _RE_PS_ASSIGN_DQ_B64.search(s) or _RE_PS_ASSIGN_SQ_B64.search(s):
        return []

    raw_input = s.encode("latin-1", errors="replace")
    if len(raw_input) > MAX_XOR_INPUT_BYTES:
        logger.debug("Skipping XOR brute force due to input size: %d bytes", len(raw_input))
        return []

    # Focus XOR on high-entropy or hard-to-read blobs to avoid unnecessary CPU.
    entropy = shannon_entropy_bytes(raw_input)
    if is_readable_utf8(s) and entropy < 4.0:
        return []

    baseline_score = score_text(s)
    candidates: list[tuple[str, str, float]] = []

    for key in range(256):
        xored = bytes(b ^ key for b in raw_input)
        for enc_label, txt in _decode_text_from_xor(xored):
            if not txt or txt == s:
                continue

            text_score = score_text(txt)
            improved = text_score > baseline_score
            readability_gain = not is_readable_utf8(s) and is_readable_utf8(txt)
            if not (improved or readability_gain):
                continue

            if not is_readable_utf8(txt) and text_score < baseline_score + 4:
                continue

            candidates.append((f"XOR(0x{key:02X}) -> {enc_label}", txt, text_score))

    # Deduplicate by output text, keep the highest score per unique output.
    dedup: dict[str, tuple[str, float]] = {}
    for label, txt, text_score in candidates:
        prev = dedup.get(txt)
        if prev is None or text_score > prev[1]:
            dedup[txt] = (label, text_score)

    ranked = sorted(
        ((label, txt, text_score) for txt, (label, text_score) in dedup.items()),
        key=lambda x: x[2],
        reverse=True,
    )
    return [(label, txt) for label, txt, _ in ranked[:MAX_XOR_TOP_CANDIDATES]]


def embedded_powershell_base64_candidates(s: str) -> list[tuple[str, str, bool]]:
    """Decode embedded PowerShell Base64 blobs and optional assignment substitutions."""
    found: list[tuple[str, str, bool]] = []
    seen: set[str] = set()

    def add_chunk(label: str, chunk: str) -> None:
        chunk = re.sub(r"\s+", "", chunk)
        if chunk in seen or len(chunk) < 8:
            return
        seen.add(chunk)
        if not looks_like_base64(chunk):
            return
        for typ, txt in base64_candidates(chunk):
            found.append((f"{label} -> {typ}", txt, False))

    for m in _RE_FROM_B64.finditer(s):
        add_chunk("Embedded FromBase64String", m.group(1))
    for m in _RE_IEX_QUOTED_B64.finditer(s):
        add_chunk("Embedded IEX-quoted Base64", m.group(1))

    seen_output: set[str] = set()
    for rex, use_double in (
        (_RE_PS_ASSIGN_DQ_B64, True),
        (_RE_PS_ASSIGN_SQ_B64, False),
    ):
        for m in rex.finditer(s):
            blob = m.group("blob") or ""
            norm = re.sub(r"\s+", "", blob)
            if len(norm) < MIN_EMBEDDED_ASSIGN_BASE64_LEN:
                continue
            entropy = shannon_entropy_bytes(norm.encode("latin-1", errors="replace"))
            if entropy < MIN_EMBEDDED_ASSIGN_BLOB_ENTROPY:
                continue
            if not looks_like_base64(norm):
                continue
            if not _looks_like_encoded_base64_token(norm):
                continue

            variants = base64_candidates(norm)
            if not variants:
                continue

            utf8_plain = next((txt for typ, txt in variants if typ == "Base64 -> UTF-8"), None)
            if utf8_plain is not None and is_readable_utf8(utf8_plain):
                decoded = utf8_plain
                inner_label = "Base64 -> UTF-8"
            else:
                inner_label, decoded = max(variants, key=lambda x: score_text(x[1]))
            prefix = m.group("pre") or ""

            replacement = (
                prefix + '"' + decoded.replace('"', '""') + '"'
                if use_double
                else prefix + "'" + decoded.replace("'", "''") + "'"
            )
            rebuilt = s[: m.start()] + replacement + s[m.end() :]

            if rebuilt == s:
                continue
            if rebuilt in seen_output:
                continue
            seen_output.add(rebuilt)

            label = f"Embedded PS assignment {inner_label}"
            found.append((label, rebuilt, True))

    return found


def type_rank(typ: str) -> int:
    if typ.startswith("EncodedCommand"):
        return 4
    if typ == "URL decode":
        return 3
    if typ.startswith("Embedded PS assignment"):
        return 3
    if typ.startswith("Base32"):
        return 2
    if typ == "Hex -> text":
        return 2
    if typ.startswith("Embedded"):
        return 1
    return 1


def better_candidate(a: DecodeCandidate, b: DecodeCandidate) -> int:
    if b.score != a.score:
        return 1 if b.score > a.score else -1
    br, ar = type_rank(b.type), type_rank(a.type)
    if br != ar:
        return 1 if br > ar else -1
    return 0


def pick_best_step(current: str) -> DecodeCandidate | None:
    candidates: list[DecodeCandidate] = []

    unicode_decoded = try_unicode_escape_decode(current)
    if unicode_decoded is not None:
        typ, txt = unicode_decoded
        candidates.append(DecodeCandidate(typ, txt, score_text(txt)))

    u = try_url_decode(current)
    if u is not None:
        candidates.append(DecodeCandidate("URL decode", u, score_text(u)))

    h = try_hex_decode(current)
    if h is not None:
        candidates.append(DecodeCandidate("Hex -> text", h, score_text(h)))

    for typ, txt in base64_candidates(current):
        candidates.append(DecodeCandidate(typ, txt, score_text(txt)))

    for typ, txt in base32_candidates(current):
        candidates.append(DecodeCandidate(typ, txt, score_text(txt)))

    for typ, txt in encodedcommand_candidates(current):
        candidates.append(DecodeCandidate(typ, txt, score_text(txt)))

    for typ, txt, force_cont in embedded_powershell_base64_candidates(current):
        candidates.append(
            DecodeCandidate(typ, txt, score_text(txt), force_continue=force_cont)
        )

    r13 = rot13_candidate(current)
    if r13 is not None:
        candidates.append(DecodeCandidate("ROT13", r13, score_text(r13)))

    for typ, txt in xor_byte_candidates(current):
        candidates.append(DecodeCandidate(typ, txt, score_text(txt)))

    if not candidates:
        return None

    best = candidates[0]
    for c in candidates[1:]:
        if better_candidate(best, c) > 0:
            best = c
    return best


def recursive_decode(initial: str) -> DecodeResult:
    layers: list[DecodeLayer] = [DecodeLayer("Raw input", initial)]
    current = initial
    prev_score = score_text(current)
    for _ in range(MAX_DECODE_LAYERS):
        step = pick_best_step(current)
        if step is None or step.text == current:
            break
        new_score = score_text(step.text)
        current_encoded = can_apply_more_encoding(current)
        still_encoded = can_apply_more_encoding(step.text)
        if not step.force_continue:
            # Plain readable text often matches the Base64/Hex alphabet once
            # whitespace is stripped (e.g. "Base64 esta decodificando..."),
            # which makes can_apply_more_encoding() a false positive. Never
            # trade readable output for an unreadable blob on a non-improving
            # score, regardless of how "encoded" the text still looks.
            if (
                new_score <= prev_score
                and is_readable_utf8(current)
                and not is_readable_utf8(step.text)
            ):
                break
            if new_score <= prev_score and not still_encoded and not current_encoded:
                break
        layers.append(DecodeLayer(step.type, step.text))
        current = step.text
        prev_score = new_score
    return DecodeResult(layers=tuple(layers), final_text=current)


# ---------------------------------------------------------------------------
# IOC extraction (matches JS IocExtractor)
# ---------------------------------------------------------------------------


def extract_iocs(text: str) -> tuple[IocRow, ...]:
    rows: list[IocRow] = []
    seen: set[str] = set()

    def add(tipo: str, valor: str, confianca: str = "") -> None:
        if not valor or len(valor) > 2000:
            return
        key = f"{tipo}\0{valor}\0{confianca}"
        if key in seen:
            return
        seen.add(key)
        rows.append(IocRow(tipo, valor, confianca))

    ipv4 = re.compile(
        r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
    )
    for m in ipv4.finditer(text):
        add("IPv4", m.group(0))

    ipv6 = re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}\b")
    for m in ipv6.finditer(text):
        add("IPv6", m.group(0))

    urls = re.compile(r"\bhttps?://[^\s<>\"']+", re.I)
    for m in urls.finditer(text):
        add("URL", m.group(0))
        host = extract_hostname_from_url(m.group(0))
        if host and network_fqdn_structure(host):
            if looks_like_dot_net_namespace_or_class(host):
                add("Domain", host, "low (possible .NET namespace)")
            elif looks_like_network_fqdn(host):
                add("Domain", host, "high")

    dotted = re.compile(
        r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b", re.I
    )
    for m in dotted.finditer(text):
        token = m.group(0)
        if "://" in token:
            continue
        if looks_like_dot_net_namespace_or_class(token):
            add(".NET Library", token)
            if network_fqdn_structure(token):
                add("Domain", token, "low (possible .NET namespace)")
        elif looks_like_network_fqdn(token):
            add("Domain", token, "high")

    emails = re.compile(r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b", re.I)
    for m in emails.finditer(text):
        add("Email", m.group(0))

    md5 = re.compile(r"\b[a-f0-9]{32}\b", re.I)
    for m in md5.finditer(text):
        add("MD5", m.group(0))

    sha1 = re.compile(r"\b[a-f0-9]{40}\b", re.I)
    for m in sha1.finditer(text):
        add("SHA1", m.group(0))

    sha256 = re.compile(r"\b[a-f0-9]{64}\b", re.I)
    for m in sha256.finditer(text):
        add("SHA256", m.group(0))

    for cmd in SUSPICIOUS_PS_COMMANDS:
        cre = re.compile(rf"\b{re.escape(cmd)}\b", re.I)
        for m in cre.finditer(text):
            add("Suspicious PowerShell", m.group(0))

    return tuple(rows)


# ---------------------------------------------------------------------------
# Highlighter (HTML spans, parity with JS for export / optional TUI)
# ---------------------------------------------------------------------------


def highlight_final(text: str) -> str:
    s = escape_html(text)
    s = re.sub(
        r"\bhttps?://[^\s<>\"']+",
        lambda m: f'<span class="hl-url">{m.group(0)}</span>',
        s,
        flags=re.I,
    )
    s = re.sub(
        r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b",
        lambda m: f'<span class="hl-ip">{m.group(0)}</span>',
        s,
    )
    s = re.sub(
        r"\b(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}\b",
        lambda m: f'<span class="hl-ip">{m.group(0)}</span>',
        s,
    )
    for cmd in SUSPICIOUS_PS_COMMANDS:
        pat = re.compile(re.escape(cmd), re.I)
        s = pat.sub(lambda m: f'<span class="hl-ps">{m.group(0)}</span>', s)
    return s


# ---------------------------------------------------------------------------
# High-level API
# ---------------------------------------------------------------------------


def decode_payload(raw: str) -> tuple[DecodeResult, tuple[IocRow, ...]]:
    """Run recursive decode + IOC extraction on a single string."""
    validate_payload_size(raw)
    cleaned = strip_null_bytes(raw)
    result = recursive_decode(cleaned)
    iocs = extract_iocs(result.final_text)
    return result, iocs


def layers_as_dicts(result: DecodeResult) -> list[dict[str, str]]:
    return [{"type": layer.type, "text": layer.text} for layer in result.layers]


def iocs_as_dicts(iocs: Iterable[IocRow]) -> list[dict[str, str]]:
    return [{"type": r.tipo, "value": r.valor, "confidence": r.confianca} for r in iocs]


def format_txt_report(result: DecodeResult, iocs: Iterable[IocRow]) -> str:
    ioc_rows = tuple(iocs)
    generated_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")

    decode_chain_lines = ["=== Decode chain ===\n"]
    for i, layer in enumerate(result.layers, start=1):
        preview_raw = layer.text.replace("\r\n", "\n")
        if len(preview_raw) > DECODE_CHAIN_PREVIEW_CHARS:
            preview_raw = preview_raw[:DECODE_CHAIN_PREVIEW_CHARS].rstrip() + "..."
        preview_one_line = preview_raw.replace("\n", "\\n")
        decode_chain_lines.append(f"{i}. {layer.type}\t{preview_one_line}\n")
    decode_chain_lines.append("\n")

    parts: list[str] = [
        f"=== {APP_NAME} report ===\n",
        f"Version: {APP_VERSION}\n",
        f"Generated: {generated_at}\n",
        "Mode: static defensive analysis; payloads are decoded, never executed.\n",
        f"Layers: {len(result.layers)}\n",
        f"IOCs: {len(ioc_rows)}\n\n",
        *decode_chain_lines,
        "=== Final text ===\n",
        result.final_text,
        "\n\n=== IOCs ===\n",
    ]
    for x in ioc_rows:
        suf = f" [{x.confianca}]" if x.confianca else ""
        parts.append(f"{x.tipo}: {x.valor}{suf}\n")
    return "".join(parts)
