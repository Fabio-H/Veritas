from __future__ import annotations

import json
import unittest
from pathlib import Path

from ps_deobfuscator.engine import (
    MAX_PAYLOAD_CHARS,
    PayloadTooLargeError,
    decode_payload,
    extract_iocs,
    format_txt_report,
    highlight_final,
)


FIXTURES = Path(__file__).parent / "fixtures" / "payloads.json"


class EngineDecodeTests(unittest.TestCase):
    def test_decodes_benign_fixture_payloads(self) -> None:
        cases = json.loads(FIXTURES.read_text(encoding="utf-8"))
        for case in cases:
            with self.subTest(case=case["name"]):
                result, iocs = decode_payload(case["payload"])
                layer_types = [layer.type for layer in result.layers]

                self.assertIn(case["expected"], result.final_text)
                self.assertTrue(
                    any(layer.startswith(case["layer_prefix"]) for layer in layer_types),
                    layer_types,
                )
                self.assertTrue(any(ioc.tipo == "URL" for ioc in iocs))
                self.assertTrue(any(ioc.tipo == "Suspicious PowerShell" for ioc in iocs))

    def test_extracts_iocs_without_misclassifying_dotnet_namespaces(self) -> None:
        rows = extract_iocs(
            "System.Net.WebClient downloads from http://example.com/a.ps1 and 192.0.2.10"
        )
        pairs = {(row.tipo, row.valor) for row in rows}

        self.assertIn((".NET Library", "System.Net.WebClient"), pairs)
        self.assertIn(("URL", "http://example.com/a.ps1"), pairs)
        self.assertIn(("IPv4", "192.0.2.10"), pairs)
        self.assertNotIn(("Domain", "System.Net.WebClient"), pairs)

    def test_report_contains_metadata_and_static_analysis_notice(self) -> None:
        result, iocs = decode_payload("SUVYIGh0dHA6Ly9leGFtcGxlLmNvbS9hLnBzMQ==")
        report = format_txt_report(result, iocs)

        self.assertIn("=== Veritas report ===", report)
        self.assertIn("Version:", report)
        self.assertIn("static defensive analysis", report)
        self.assertIn("=== Final text ===", report)
        self.assertIn("IEX http://example.com/a.ps1", report)

    def test_highlight_escapes_html_before_markup(self) -> None:
        highlighted = highlight_final("<script>IEX http://example.com/a.ps1</script>")

        self.assertIn("&lt;script&gt;", highlighted)
        self.assertIn('class="hl-url"', highlighted)
        self.assertIn('class="hl-ps"', highlighted)

    def test_rejects_oversized_payloads(self) -> None:
        with self.assertRaises(PayloadTooLargeError):
            decode_payload("A" * (MAX_PAYLOAD_CHARS + 1))


if __name__ == "__main__":
    unittest.main()

