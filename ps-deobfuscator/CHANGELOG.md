# Changelog

All notable changes to Veritas (ps-deobfuscator) are listed here.
This project follows [Semantic Versioning](https://semver.org/).

## 0.4.0

### Added
- Input anomaly warnings: an amber banner in Quick Decode now reports
  malformed input that was decoded anyway — invalid/excess Base64
  padding (e.g. `SGVsbG8gV29ybGQh===`), invalid Base64 length and NUL
  bytes. The decoder stays deliberately lenient (malformed padding is a
  common evasion trick); the analyst is informed instead of blocked.
- Honest status line when nothing decodes: "No supported encoding
  detected | input shown as-is" instead of pretending a 1-layer decode
  completed.
- `docs/UI_MODERNIZATION_PLAN.md`: phased plan (animations, feedback,
  responsiveness, real-app behavior) approved for future sessions.

### Changed
- The GUI entry point moved from `[project.scripts]` to
  `[project.gui-scripts]`: `ps-deobfuscator-gui.exe` now opens the app
  directly with no console window. A `Veritas.lnk` shortcut (repo root
  and Desktop) launches it like a regular application.

## 0.3.1

### Fixed
- Recursive decoder no longer re-decodes readable plaintext whose
  characters happen to match the Base64/Hex alphabet (e.g.
  `"Base64 esta decodificando corretamente"` was decoded again into
  garbage and then XOR-mangled). Readable output is now only replaced
  when the heuristic score actually improves. Regression tests and a
  `samples/known-good/` payload cover the reported case.

## 0.3.0

### Changed
- Complete visual redesign: new "Veritas Dark" theme (deep blue-black
  surfaces, mint signature accent) replacing the Gruvbox palette. Filled
  primary Decode button, accent-tinted navigation states, restyled cards,
  inputs, scrollbars, table headers and accordion layers.
- Semantic highlight colors in the deobfuscated stream: URLs in cyan,
  IPs in red, suspicious PowerShell tokens in amber.
- IOC table: Type column is now color-coded by category (network IOCs
  red/cyan, hashes mint, PowerShell amber, .NET muted).

### Added
- `samples/` payload library: `known-good/` regression payloads and a
  `triage/` drop zone for misdecoded payloads, plus
  `scripts/run_samples.py` to reproduce full decode chains per sample.

## 0.2.0

### Added
- Session History panel: the last 20 decode runs are persisted to disk
  (`%APPDATA%/Veritas/history.json` on Windows, `~/.local/share/Veritas/` on
  Linux, `~/Library/Application Support/Veritas/` on macOS) and restored on
  startup. Each entry stores the original input, every decode layer, the final
  text, and all extracted IOCs.
- Sidebar `History` entry alongside `Quick Decode`. Clicking `Restore` on an
  entry re-renders it in Quick Decode without re-invoking the engine, so old
  results stay byte-identical to when they were captured.
- Per-entry `Delete` and a global `Clear history` action (with confirmation).
- `HistoryStore` with versioned JSON schema (`schema_version: 1`), atomic
  writes (`tmp` + `os.replace`), and tolerant load: corrupt files or unknown
  schema versions reset to an empty store instead of crashing.

### Changed
- Bump version to 0.2.0 (`ps_deobfuscator/app_info.py`, `pyproject.toml`).

## 0.1.0

### Added
- Initial release: PySide6 desktop app and Rich-powered CLI for recursive
  PowerShell payload deobfuscation (URL, Hex, Base64 UTF-8/UTF-16LE, GZIP,
  zlib/DEFLATE, up to 8 layers).
- IOC extraction: IPv4, IPv6, URL, Domain, .NET Library, Email, MD5, SHA1,
  SHA256, Suspicious PowerShell tokens.
- TXT and JSON export of decode reports.
