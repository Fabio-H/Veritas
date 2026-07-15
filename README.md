# Veritas

**English** · [Português (pt-BR)](README.pt-BR.md)

### Automatic payload deobfuscator for SOC, IR and Blue Team

**Veritas** reveals what is hidden inside obfuscated PowerShell commands and
encoded strings. The analyst pastes the suspicious blob; the tool identifies
the encoding layers, decodes them recursively and extracts Indicators of
Compromise (IOCs) — all locally, executing nothing and sending no data
anywhere.

The name is a play on extracting the **truth** ("veritas") of what the
attacker tried to hide.

[![Download latest release](https://img.shields.io/github/v/release/Fabio-H/Veritas?label=download&logo=github)](https://github.com/Fabio-H/Veritas/releases/latest)
[![CI](https://github.com/Fabio-H/Veritas/actions/workflows/ci.yml/badge.svg)](https://github.com/Fabio-H/Veritas/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/GUI-PySide6%20(Qt%206)-41CD52?logo=qt&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-blue)

**[⬇ Download the latest Windows build](https://github.com/Fabio-H/Veritas/releases/latest)**

<!-- TODO: screenshot / GIF of the redesigned UI here -->

---

## Why it exists

In day-to-day **SOC (Tier 2)** and **Incident Response** work it is common to
run into obfuscated PowerShell, Base64, Hex, URL encoding and other layers
stacked together in endpoint logs. Decoding this by hand is slow and
error-prone. Veritas automates triage: the decode chain is visible layer by
layer, the final text is highlighted, and the IOC table is ready for
correlation.

## Features

- **Recursive decoding** (up to 8 layers) with heuristic scoring — malicious
  PowerShell keywords + readability decide the best transformation at each
  step.
- **Supported formats:** URL encoding, Hex, Base64 (UTF-8 and UTF-16LE),
  Base32, Ascii85/Base85, GZIP, zlib/DEFLATE, ROT13, single-byte XOR
  (brute-force over all 256 keys), Unicode escapes (`\x..`, `\u....`,
  `%u....`), HTML entities (`&#65;`, `&#x41;`), JWT (header + payload),
  char-code arrays (`String.fromCharCode(...)`, `[char[]](...)`), PowerShell
  `-EncodedCommand`/`-enc`, and Base64 embedded in variable assignments
  (`$x = "..."`).
- **Manual pipeline:** when the automatic heuristic picks the wrong branch,
  build a decode recipe by hand — chain operations (Base64, Hex, XOR with a
  key, ROT13, reverse, …) and inspect the result step by step.
- **IOC extraction:** IPv4/IPv6, URLs, domains (with a heuristic that avoids
  mistaking a .NET namespace for an FQDN), emails, MD5/SHA1/SHA256 hashes and
  suspicious PowerShell tokens.
- **Persistent history:** the last 20 analyses are stored locally and
  restored on launch, byte-for-byte identical to when they were captured.
- **Export** of reports as TXT and JSON, with version and timestamp metadata.
- **CLI** (via [Rich](https://github.com/Textualize/rich)) for terminal use,
  alongside the desktop GUI.

## Safety by default

- **100% static analysis** — payloads are decoded and inspected, never
  executed.
- Inputs larger than 1,000,000 characters are rejected.
- GZIP/zlib decompression is bounded to prevent decompression bombs.
- No data ever leaves the machine.

## Installation and use

Requirements: **Python 3.10+** on Windows (Linux/macOS should work, but
testing focuses on Windows). Or just grab the packaged
[latest Windows release](https://github.com/Fabio-H/Veritas/releases/latest) —
no Python required.

```powershell
git clone https://github.com/Fabio-H/Veritas.git
cd Veritas/ps-deobfuscator
pip install -e ".[gui]"
python main_gui.py
```

CLI:

```powershell
pip install -e .
ps-deobfuscator decode --help
```

### Build the Windows executable

```powershell
cd ps-deobfuscator
pip install -e ".[gui,dev,build]"
python scripts\build_exe.py
```

Outputs: `release/ps-deobfuscator-gui/ps-deobfuscator-gui.exe` and
`release/Veritas-vX.Y.Z-windows.zip`. Pushing a `v*.*.*` tag builds this
automatically and attaches the zip to a GitHub Release (see
`.github/workflows/release.yml`).

## How to use

1. Paste the obfuscated text (log, command, string exported from a SIEM) into
   the input area — or drop a `.txt` file.
2. Click **Decode**.
3. Review the decode-chain **layers**, the highlighted **final text** and the
   **IOC** table.
4. Export as TXT/JSON or copy the IOCs as needed.

**Example** (fictional data, [RFC 5737](https://datatracker.ietf.org/doc/html/rfc5737)):

```text
Input:   cG93ZXJzaGVsbC5leGUgLWVwIGJ5cGFzcyAtYyAiVGVzdC1Db25uZWN0aW9uIC1Db21wdXRlck5hbWUgMTkyLjAuMi4xMCI=
Output:  powershell.exe -ep bypass -c "Test-Connection -ComputerName 192.0.2.10"
IOCs:    IPv4 192.0.2.10 · powershell.exe · -ep bypass
```

## Architecture

```
ps-deobfuscator/
  ps_deobfuscator/   # Decode engine + CLI (no GUI dependency)
    engine.py        #   recursive decoding, scoring, IOC extraction
    history.py       #   history persistence (atomic, versioned JSON)
  gui/               # PySide6 desktop app (themes, window, widgets)
  samples/           # Test payload library (known-good + triage)
  scripts/           # exe build, icons, run_samples, cleanup
  tests/             # unittest suite (engine, history, imports)
```

At each layer the engine evaluates every applicable decode candidate, scores
each result (suspicious keywords + printable-character ratio) and keeps the
best one until the score stops improving or the layer limit is reached. The
strict separation between the pure engine and the GUI is a deliberate design
choice — see [docs/architecture-decisions.md](docs/architecture-decisions.md).

## Tests

```powershell
cd ps-deobfuscator
python -m unittest discover -s tests
```

Payloads that decode incorrectly should be saved under
`ps-deobfuscator/samples/triage/` (one `.txt` per payload) and reproduced with
`python scripts/run_samples.py` — see [docs/PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md).

## Development process

Veritas was built with "vibe coding" — a human paired with an AI assistant.
The architecture, design and security trade-offs are my own authorship and
responsibility; the reasoning behind the key decisions is documented in
[docs/architecture-decisions.md](docs/architecture-decisions.md).

## Roadmap

| Priority | Item |
|----------|------|
| High   | STIX 2.1 / MISP export of IOCs for playbook integration |
| Medium | Batch mode surfaced in the GUI (already available in the CLI) |
| Medium | IOC defang/refang (`hxxp://`, `1.2.3[.]4`) |
| Low    | Windows installer (Inno Setup) + Start Menu shortcut |

Delivered so far: recursive engine and IOC extraction, format coverage
(Ascii85/HTML/JWT/char-codes), manual/guided decoding, "Veritas Blue" UI,
CI (ruff + mypy + tests on Python 3.10–3.13) and automated releases.

## Disclaimer

This tool is provided **"as is"**, for legitimate defensive analysis, research
and cybersecurity education. It does not replace formal incident-response
processes. **Do not execute** unknown commands or binaries on production
systems.

## License

Licensed under the **MIT License** — see [LICENSE](LICENSE).
