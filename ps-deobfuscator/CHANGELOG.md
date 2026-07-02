# Changelog

All notable changes to Veritas (ps-deobfuscator) are listed here.
This project follows [Semantic Versioning](https://semver.org/).

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
