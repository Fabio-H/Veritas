# Payload sample library

Test payloads for the Veritas decode engine. All samples are **benign and
fictional** (RFC 5737 documentation addresses, example.com), used only to
exercise the decoder.

## Layout

| Folder | Purpose |
|--------|---------|
| `known-good/` | Payloads the engine is expected to decode correctly. Each one mirrors a regression test in `tests/`. |
| `triage/` | **Drop zone for problem payloads.** Anything that decodes wrong goes here (one payload per `.txt` file) until the engine is fixed and the case is promoted to a test fixture. |

## Workflow for a bad decode

1. Save the payload as `triage/<short-name>.txt` (raw payload only, no notes
   inside the file).
2. Run the reproduction script from `ps-deobfuscator/`:

   ```powershell
   python scripts/run_samples.py
   ```

   It prints the full decode chain and extracted IOCs for every sample.
3. Note what the output *should* have been. The case then becomes a fixture
   in `tests/fixtures/payloads.json` and the fix lands in the engine.
4. Once the engine handles it, move the file to `known-good/`.

Never put real malware or non-anonymized production payloads in this folder.
