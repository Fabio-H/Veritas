# Changelog

All notable changes to Veritas (ps-deobfuscator) are listed here.
This project follows [Semantic Versioning](https://semver.org/).

## 0.8.0 — manual / guided decoding pipeline

### Added
- **Manual Pipeline** (new sidebar page): the analyst builds a decode
  recipe by hand — pick an operation, add it as a step, reorder/remove,
  then Run — overriding the automatic heuristic. Directly answers the
  "the auto decoder picked the wrong branch" problem (e.g. XOR winning
  over the intended Base64).
- Engine manual API (pure, fully tested): `apply_operation(text, op_id,
  key=…)` applies a single transform unconditionally; `run_manual_pipeline`
  / `decode_with_ops` run an ordered recipe and record each step as a
  layer (including "(not applicable)" markers). Operations: URL, Hex,
  Base64 (UTF-8 / UTF-16LE), Base32, Ascii85, HTML entities, Unicode
  escapes, ROT13, XOR (byte key), reverse, remove whitespace.
- Output mirrors Quick Decode: pipeline layers, highlighted result stream,
  and IOC table.

### Notes
- Manual operations are text→text (no bytes-only steps like GZIP in the
  recipe yet); the automatic engine still handles compression. Byte-level
  recipe steps are a candidate for a later phase.

## 0.7.0 — format coverage + engineering quality

### Added
- New decoders in the engine, each with conservative detection and
  regression tests + known-good samples:
  - **Ascii85 / Base85** (Adobe `<~…~>` framed and raw).
  - **HTML numeric entities** (`&#65;`, `&#x41;`).
  - **JWT** — decodes header + payload into readable JSON.
  - **Char-code arrays** — JS `String.fromCharCode(...)` and PowerShell
    `[char[]](...)`.
- Continuous integration: `.github/workflows/ci.yml` runs Ruff, Mypy and
  the unit tests on Python 3.10–3.13 for every push and PR.
- `docs/MASTER_PLAN_V1.md`: phased roadmap to a v1.0 "complete app".

### Changed
- Tooling: Ruff (lint + import order) and Mypy (type-check of the pure
  `ps_deobfuscator` package) configured in `pyproject.toml`; both pass
  clean. Added to the `dev` extra.

### Fixed
- Python 3.10 compatibility: replaced `datetime.UTC` (3.11+) with
  `datetime.timezone.utc` in engine/history/CLI, honoring the declared
  `requires-python = ">=3.10"`. On 3.10 the app would previously fail at
  import.

### Removed
- Dead code: `gui/main.py` (unused since the GUI entry point moved to
  `[project.gui-scripts]` in 0.4.0).

## 0.6.0 — "Veritas Blue" theme

### Changed
- New color direction based on the Claude Design "Electric cyan on cool
  slate" mockup (VS Code / Linear adjacent): cool blue-slate surfaces
  (`#0B0E13` / `#11151C` / `#161C26`), a single electric-blue accent
  (`#4C9EFF`), replacing the mint "Veritas Dark" palette. Amber, red and
  green are kept strictly for semantic status (PowerShell tokens,
  IPs/danger, success).
- Typography now targets Apple's system look: the UI font stack tries
  SF Pro Display/Text, then Inter (closest free match), then Segoe UI;
  code/data uses SF Mono → JetBrains Mono → Cascadia → Consolas.
- Input field sits on an elevated slate surface (`#161C26`) with a
  brighter border, matching the mockup's "paste payload" panel.

### Notes
- SF Pro / Inter are not bundled (SF Pro is licensed to Apple platforms
  only). On a stock Windows install the UI renders in Segoe UI until
  Inter or SF Pro is installed; bundling Inter (OFL) is a possible
  follow-up to lock the Apple look everywhere.
- Kept our real feature set — the mockup's illustrative-only elements
  (byte-size/timing columns, STAGE column, mutex/registry IOC types,
  session naming) were intentionally not copied.

## 0.5.0 — UI modernization

### Added
- **Motion**: sidebar collapses/expands with a 200 ms eased slide;
  decode-chain layers open with an animated reveal; switching
  Quick Decode ↔ History crossfades instead of snapping.
- **Feedback**: toast confirmations ("Copied to clipboard",
  "N IOC(s) copied", "TXT/JSON report exported") — actions no longer
  happen silently.
- **Copy all IOCs** button: every indicator copied as tab-separated
  lines in one click (SOC guideline: from alert to action in seconds).
- **Window memory**: size, position and sidebar state persist across
  sessions (QSettings) — per Microsoft's desktop UX checklist.
- **Single instance**: relaunching the shortcut activates the running
  window instead of opening a second copy (QLocalServer).
- **Dark native title bar** on Windows (Qt color scheme hint): the
  window frame finally matches the dark theme.
- Stat pills reflow to a second row on narrow windows (FlowLayout).

### Changed
- IOC table Confidence column sizes to its content instead of a fixed
  150 px.

### Notes
- Card drop shadows were evaluated and intentionally skipped: Qt allows
  one graphics effect per widget (conflicts with the crossfade) and
  rasterizes the whole card on each repaint, hurting scroll performance.

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
