# Architecture Decision Records — Veritas

> **Draft for review.** This file documents the *why* behind key engineering
> decisions in Veritas, grounded in the actual engine code. It was drafted
> with AI assistance as study material. Before using any of it to explain the
> project (e.g. in an interview), the author intends to review and rewrite
> each answer in their own words — the goal is to genuinely own each decision,
> not to recite generated text.
>
> All references point at `ps-deobfuscator/ps_deobfuscator/engine.py`.

---

## 1. Why cap automatic recursion at 8 layers?

`MAX_DECODE_LAYERS = 8` bounds the loop in `recursive_decode()`. The reasoning
is threefold:

- **Real-world depth.** Stacked obfuscation in the wild (Base64 → GZIP → XOR →
  Base64 → UTF-16LE, etc.) rarely exceeds a handful of layers. 8 comfortably
  covers observed malware while staying well short of pathological input.
- **A stop condition that isn't only the score.** The loop already stops early
  when the heuristic score stops improving and no further encoding is
  detected; the layer cap is a hard backstop so a crafted input can't spin the
  decoder indefinitely.
- **Static-analysis safety.** Combined with `MAX_PAYLOAD_CHARS = 1_000_000` and
  bounded decompression, the fixed layer count keeps a single decode's work
  predictable — important for a tool meant to stay responsive while triaging
  hostile input.

## 2. How does the heuristic scoring work, and why that combination?

`score_text(s) = keyword_score(s) + printable_ratio(s) * PRINTABLE_RATIO_WEIGHT`
(`PRINTABLE_RATIO_WEIGHT = 50`). Two signals are deliberately combined:

- **`printable_ratio`** — the fraction of printable characters. This is the
  "does this look like text at all?" signal. A correct decode of an encoded
  blob almost always raises the printable ratio; a wrong decode usually lowers
  it (produces binary garbage). Weighting it by 50 lets readability dominate
  the baseline score.
- **`keyword_score`** — counts suspicious PowerShell / networking tokens (`IEX`,
  `Invoke-`, `DownloadString`, `http`, `127.0.0.1`, …). Two candidate decodes
  can both look like text; the one that reveals attacker-relevant content is
  the one the analyst wants surfaced first.

Neither signal alone is enough: printable-ratio alone can't choose between two
readable interpretations, and keyword-count alone is fooled by coincidental
substrings in garbage. Their sum biases the decoder toward *readable text that
also looks malicious* — exactly the triage goal.

## 3. Why the "readable → unreadable only if the score improves" guard?

This guard exists because of a **real reported bug**. The payload was Base64
for the sentence *"Base64 esta decodificando corretamente"*. Decoded once, it
was already correct plaintext — but with spaces stripped, the sentence is pure
`[A-Za-z0-9]`, so `can_apply_more_encoding()` thought it *still looked like
Base64*. The engine decoded the readable text again into binary garbage, then
even ran XOR on the garbage, and reported that as the result.

The fix (in `recursive_decode()`): never replace readable text with an
unreadable blob unless the score strictly improves —

```python
if new_score <= prev_score and is_readable_utf8(current) and not is_readable_utf8(step.text):
    break
```

`is_readable_utf8` uses `READABLE_PRINTABLE_THRESHOLD = 0.55`. The lesson: a
string matching an encoding's *alphabet* is not proof it *is* that encoding, so
the decoder must weigh the outcome, not just the shape of the input. A
regression test locks the reported case in place.

## 4. Why is the decoder deliberately lenient with malformed Base64 padding?

Malformed Base64 padding (missing or extra `=`) is a **known evasion trick**:
attackers use it precisely so naïve decoders that strictly validate padding
bail out and miss the payload. So `normalize_base64_string()` repairs padding
before decoding, and the engine decodes the content instead of rejecting it.

Leniency without silence, though: `input_anomalies()` detects invalid/excess
padding, invalid length and NUL bytes and returns human-readable notes that the
GUI shows as an amber banner. The analyst is *informed* that the input was
malformed and repaired — they get both the decoded content and the caveat,
rather than a hard failure that hides the payload.

## 5. Why is the strict engine/GUI separation a design decision, not an accident?

`ps_deobfuscator/engine.py` imports nothing from PySide6 or any GUI module. The
GUI, the CLI and the test suite are all *consumers* of the same
`decode_payload()` / `decode_with_ops()` API. This was chosen on purpose:

- **Testability.** The entire decode/IOC logic is exercised by fast unit tests
  with no Qt, no display, no event loop — which is also what lets CI run the
  full suite headless across Python 3.10–3.13.
- **Reuse across front-ends.** The same engine powers the desktop GUI and the
  Rich CLI without duplication; a future integration (API, batch pipeline)
  would reuse it too.
- **Independent evolution.** The "Veritas Blue" re-theme and the whole UI
  modernization touched zero engine code; conversely, new decoders (Ascii85,
  JWT, char-codes) and the manual pipeline landed without touching the GUI.
  The seam is what makes each side safe to change in isolation.
