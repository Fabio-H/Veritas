"""Backward-compatible launcher (setuptools console_scripts)."""

from __future__ import annotations


def run_app() -> None:
    from main_gui import main

    main()
