# Veritas — Master Plan for v1.0 ("complete app")

> **English** · [Português](pt-BR/MASTER_PLAN_V1.md)
>
> This is the detailed master prompt guiding Veritas from a well-built
> prototype (v0.6.0) to a complete portfolio product (v1.0). Each phase is
> independent, versioned, with green tests + layout check + screenshot before
> committing. No rewriting what already works — the engine, the tests and the
> GUI are the foundation; we build on top.

## Context for the executing AI

Veritas is a desktop deobfuscator (Python 3.10+ / PySide6) for defensive
payload analysis (SOC / IR / Blue Team). The engine is 100% decoupled from the
interface (`ps_deobfuscator/engine.py` imports nothing from the GUI). Dual
goal: a real tool **and** a LinkedIn portfolio showcase. Non-negotiable
principles: static analysis (never execute a payload), reliability before
features (every wrong decode becomes a regression test), engine separate from
interface, everything in English in the UI.

## Diagnosis (from 2026 research + code audit)

Strengths: real engine/GUI/CLI separation; modern `pyproject.toml`; 32 tests;
working windowed PyInstaller packaging. Gaps found:

1. Work not published to GitHub (8 commits ahead of origin).
2. No CI, no linter, no type-checker.
3. Dead code (`gui/main.py`).
4. As a "deobfuscator", missing formats common in real malware and the
   **manual/guided** mode (only the automatic heuristic existed).
5. No screenshots/demo in the README.

## Phases

### Phase 1 — Quality and publishing (credibility foundation) — v0.7.0
- [x] Remove dead code (`gui/main.py`).
- [x] `ruff` (lint + import sort) configured and clean.
- [x] `mypy` on the `ps_deobfuscator` package (pure logic) with no errors.
- [x] GitHub Actions: Python matrix, runs ruff + mypy + tests on every push.
- [x] Push the repository (owner action — publishes public identity).
- [ ] Rendered screenshots in the README + a "why" narrative (Blue Team workflow).

### Phase 2 — Format coverage ("deobfuscator" identity) — v0.7.0
Add decoders common in real malware, each with conservative detection (low
false-positive) and tests:
- [x] **Ascii85 / Base85** (Adobe `<~…~>` and raw).
- [x] **HTML entities** (`&#65;`, `&#x41;`) — web/HTA obfuscation.
- [x] **JWT** — decodes header+payload as JSON (high visual value, low false-positive).
- [x] **Char-code arrays** — `String.fromCharCode(...)` (JS) and `[char[]](...)` (PowerShell).
- [ ] Plain decimal/octal and VBScript `Chr()+concat` (later phase; higher false-positive risk).

### Phase 3 — Manual/guided decoding (the biggest differentiator) — v0.8.0 ✅
Fixes the "the heuristic picked wrong" class of bug at the root:
- [x] New engine API: `apply_operation(text, op)` (applies ONE transformation
  unconditionally) and `decode_with_ops(text, [ops])` (manual pipeline),
  without depending on the score. Reuses the existing decoders.
- [x] GUI: "Manual Pipeline" page where the analyst chains operations
  (dropdown: URL, Hex, Base64 UTF-8/UTF-16LE, Base32, Ascii85, HTML entity,
  Unicode escapes, ROT13, XOR key, reverse, remove whitespace) and sees the
  result layer by layer — inspired by CyberChef's "recipe", but lean.
- [ ] Export the recipe / byte-level steps (GZIP in the recipe) — later phase.

### Phase 4 — Blue Team integration / deliverables — v0.9.0
- **STIX 2.1** and **MISP** export of the IOCs (de-facto standard for sharing).
- **Batch** mode surfaced in the GUI (already in the CLI): drop several files,
  decode them all, export a consolidated report.
- IOC "defanging"/"refanging" (`hxxp://`, `1.2.3[.]4`) — an IR convention.

### Phase 5 — Product and distribution — v1.0.0
- Bundle the **Inter** font (OFL) to lock the intended look on any machine.
- Windows installer (Inno Setup) with a Start Menu shortcut.
- Window memory already done (v0.5.0); revisit high-DPI scaling.
- Final README with a demo GIF, CI badges, architecture section.

## Execution rules (for any session)
1. One phase at a time; never break existing tests.
2. Every reported incorrect decode → regression fixture before the fix.
3. Format detection always conservative; the scoring + the
   "readable→unreadable only if the score improves" guard (v0.3.1) protect
   against false positives.
4. Always verify: `unittest` + `scripts/check_gui_layout.py` + screenshot.
5. Version (`app_info.py` + `pyproject.toml`), update `CHANGELOG.md`,
   descriptive commit.
