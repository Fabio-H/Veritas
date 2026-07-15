# Veritas — Project Brief

> **English** · [Português](pt-BR/PROJECT_BRIEF.md)
>
> This document is the project's "master prompt": what we are building, why,
> and how we decide what is in scope. Future development sessions (human + AI)
> should start from here.

## Goal

Build **Veritas**: a desktop deobfuscator for malicious payloads (Base64, Hex,
URL encoding, GZIP/zlib, XOR and stacked layers) with automatic IOC
extraction, aimed at the real workflow of **SOC, Incident Response and Blue
Team**.

The project has two simultaneous goals:

1. **A real tool** — the analyst pastes a suspicious blob, Veritas reveals the
   text behind it and lists the indicators (IPs, URLs, domains, hashes,
   suspicious PowerShell commands). 100% static analysis: nothing is executed.
2. **A portfolio showcase (LinkedIn)** — code, UI and documentation with
   product-level quality: professional visuals, automated tests, versioned
   releases and a README with a visual demo.

## Decision principles

- **Reliability before features.** Every payload that decodes incorrectly
  becomes a test case under `ps-deobfuscator/samples/triage/` and only leaves
  it once the engine gets it right. The test suite never regresses.
- **Engine separate from interface.** `ps_deobfuscator/engine.py` imports
  nothing from the GUI; the GUI (PySide6) and the CLI are consumers of the
  engine.
- **Safety by default.** Payloads are never executed; size and decompression
  limits protect against bombs; exports carry version metadata.
- **Current scope: Windows desktop.** No web version in this repository.
  Scaling (new formats, integrations, i18n) comes only after the house is in
  order.

## Current state and priorities

| # | Priority | Status |
|---|----------|--------|
| 1 | Reproducible environment (Python + deps + green tests) | ✅ |
| 2 | History committed and repository organized | ✅ |
| 3 | Test payload library (`samples/`) to reproduce decode errors | ✅ |
| 4 | UI redesign: professional dark theme, responsive layout, product feel | ✅ |
| 5 | Fix Base64 payloads that decode incorrectly (1st case fixed in v0.3.1; new cases → `samples/triage/`) | ✅ |
| 6 | CI (GitHub Actions) + automated release `.zip` | ✅ |
| 7 | Screenshots / GIF in the README | ⏳ |

## GitHub "About" text (max 100 characters)

`Payload deobfuscator for Blue Team: recursive decoding & IOC extraction, desktop app.`

## How to reproduce a decode error

1. Save the problematic payload as a `.txt` under
   `ps-deobfuscator/samples/triage/` (one payload per file).
2. Run `python scripts/run_samples.py` — the script prints the full decode
   chain of each sample.
3. Describe what the expected output was; the case becomes a test fixture and
   the fix lands in the engine.
