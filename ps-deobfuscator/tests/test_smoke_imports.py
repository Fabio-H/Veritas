from __future__ import annotations

import importlib
import unittest


class SmokeImportTests(unittest.TestCase):
    def test_core_modules_import(self) -> None:
        for module_name in (
            "main_gui",
            "ps_deobfuscator.cli",
            "ps_deobfuscator.engine",
            "ps_deobfuscator.app_info",
        ):
            with self.subTest(module=module_name):
                importlib.import_module(module_name)

    def test_gui_modules_import_when_pyside6_is_available(self) -> None:
        try:
            importlib.import_module("PySide6")
        except ImportError:
            self.skipTest("PySide6 is not installed")

        for module_name in ("gui.app_icon", "gui.main_window", "gui.widgets.decode_panel"):
            with self.subTest(module=module_name):
                importlib.import_module(module_name)


if __name__ == "__main__":
    unittest.main()

