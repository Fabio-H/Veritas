"""
Run the decode engine over every payload in samples/ and print the chains.

Usage (from ps-deobfuscator/):
    python scripts/run_samples.py            # all samples
    python scripts/run_samples.py triage     # only samples/triage

Drop any payload that decodes wrong into samples/triage/ (one .txt per
payload) and use this script to reproduce the exact engine behavior.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ps_deobfuscator.engine import decode_payload  # noqa: E402

PREVIEW_CHARS = 160


def iter_samples(only: str | None) -> list[tuple[str, Path]]:
    base = ROOT / "samples"
    subdirs = (only,) if only else ("known-good", "triage")
    found: list[tuple[str, Path]] = []
    for sub in subdirs:
        d = base / sub
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.txt")):
            found.append((sub, f))
    return found


def main() -> int:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    samples = iter_samples(only)
    if not samples:
        print("No samples found. Add .txt payloads to samples/known-good/ or samples/triage/.")
        return 1

    for sub, path in samples:
        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            continue
        print("=" * 72)
        print(f"[{sub}] {path.name}")
        try:
            result, iocs = decode_payload(raw)
        except Exception as exc:  # surface engine crashes per-sample
            print(f"  ERROR: {type(exc).__name__}: {exc}")
            continue
        for i, layer in enumerate(result.layers, start=1):
            preview = layer.text[:PREVIEW_CHARS].replace("\n", "\\n")
            if len(layer.text) > PREVIEW_CHARS:
                preview += "..."
            print(f"  {i}. {layer.type}")
            print(f"     {preview}")
        print(f"  IOCs ({len(iocs)}):")
        for ioc in iocs:
            suffix = f" [{ioc.confianca}]" if ioc.confianca else ""
            print(f"    - {ioc.tipo}: {ioc.valor}{suffix}")
    print("=" * 72)
    print(f"{len(samples)} sample(s) processed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
