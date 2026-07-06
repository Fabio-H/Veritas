"""CLI: decode | batch | interactive."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

from ps_deobfuscator.app_info import APP_NAME, APP_VERSION
from ps_deobfuscator.engine import (
    PayloadTooLargeError,
    decode_payload,
    format_txt_report,
    highlight_final,
    iocs_as_dicts,
    layers_as_dicts,
)

console = Console(stderr=True)


def _read_path(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def _collect_files(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for base in paths:
        if base.is_file():
            out.append(base)
        elif base.is_dir():
            for f in sorted(base.rglob("*")):
                if f.is_file() and f.suffix.lower() in {".txt", ".log", ".ps1", "", ".dat", ".b64"}:
                    out.append(f)
        else:
            console.print(f"[yellow]Skip missing:[/] {base}")
    return out


def cmd_decode(args: argparse.Namespace) -> int:
    if args.text is not None:
        raw = args.text
    elif args.file is not None:
        raw = _read_path(Path(args.file))
    else:
        console.print("[red]Provide --text or --file[/]")
        return 2

    try:
        result, iocs = decode_payload(raw)
    except PayloadTooLargeError as exc:
        console.print(f"[red]{exc}[/]")
        return 2

    if args.json_out:
        payload = {
            "metadata": _report_metadata(len(result.layers), len(iocs)),
            "layers": layers_as_dicts(result),
            "final_text": result.final_text,
            "final_html_highlight": highlight_final(result.final_text),
            "iocs": iocs_as_dicts(iocs),
        }
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
        else:
            print(text)
        return 0

    tree = Tree("[cyan]Decode layers[/]")
    for i, layer in enumerate(result.layers, 1):
        tree.add(f"[bold]{i}.[/] [green]{layer.type}[/] ({len(layer.text)} chars)")
    console.print(tree)
    console.print(Panel(result.final_text, title="Final text", border_style="cyan"))
    tbl = Table(title="IOCs")
    tbl.add_column("Type")
    tbl.add_column("Value", overflow="fold")
    tbl.add_column("Confidence")
    for r in iocs:
        tbl.add_row(r.tipo, r.valor, r.confianca or "-")
    console.print(tbl)

    if args.output:
        Path(args.output).write_text(format_txt_report(result, iocs), encoding="utf-8")
        console.print(f"[green]Wrote[/] {args.output}")
    return 0


def cmd_batch(args: argparse.Namespace) -> int:
    files = _collect_files([Path(p) for p in args.paths])
    if not files:
        console.print("[red]No files matched[/]")
        return 2
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in files:
        try:
            raw = _read_path(f)
        except OSError as e:
            console.print(f"[red]{f}:[/] {e}")
            continue
        try:
            result, iocs = decode_payload(raw)
        except PayloadTooLargeError as e:
            console.print(f"[yellow]Skip too large:[/] {f}: {e}")
            continue
        stem = f.name.replace("/", "_")
        if args.format in ("txt", "both"):
            (out_dir / f"{stem}.decoded.txt").write_text(
                format_txt_report(result, iocs), encoding="utf-8"
            )
        if args.format in ("json", "both"):
            payload = {
                "source": str(f),
                "metadata": _report_metadata(len(result.layers), len(iocs)),
                "layers": layers_as_dicts(result),
                "final_text": result.final_text,
                "iocs": iocs_as_dicts(iocs),
            }
            (out_dir / f"{stem}.decoded.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        console.print(f"[green]OK[/] {f}")
    return 0


def cmd_interactive(_args: argparse.Namespace) -> int:
    console.print(
        "[bold cyan]ps-deobfuscator interactive[/] - paste payload, empty line + Enter to decode, Ctrl+Z Enter (Win) or Ctrl+D (Unix) to exit."
    )
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "" and lines:
            raw = "\n".join(lines)
            lines.clear()
            try:
                result, iocs = decode_payload(raw)
            except PayloadTooLargeError as exc:
                console.print(f"[red]{exc}[/]")
                console.print("[dim]--- next payload ---[/]")
                continue
            console.print(
                Syntax(result.final_text, "powershell", theme="monokai", word_wrap=True)
            )
            tbl = Table(title="IOCs")
            tbl.add_column("Type")
            tbl.add_column("Value", overflow="fold")
            tbl.add_column("Confidence")
            for r in iocs:
                tbl.add_row(r.tipo, r.valor, r.confianca or "-")
            console.print(tbl)
            console.print("[dim]--- next payload ---[/]")
        elif line == "" and not lines:
            continue
        else:
            lines.append(line)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ps-deobfuscator",
        description="Recursive payload deobfuscator (URL / Hex / Base64 / GZIP / zlib).",
    )
    p.add_argument("--version", action="version", version=f"{APP_NAME} {APP_VERSION}")
    sub = p.add_subparsers(dest="command", required=True)

    d = sub.add_parser("decode", help="Decode a single payload from --text or --file")
    d.add_argument("--text", "-t", help="Raw payload string")
    d.add_argument("--file", "-f", help="Path to file containing payload")
    d.add_argument("--json-out", action="store_true", help="Emit JSON (layers + IOCs + HTML highlight)")
    d.add_argument("--output", "-o", help="Write report (.txt or .json per --json-out)")
    d.set_defaults(func=cmd_decode)

    b = sub.add_parser("batch", help="Decode many files or all files under folders")
    b.add_argument("paths", nargs="+", help="Files and/or directories")
    b.add_argument(
        "--output-dir",
        "-o",
        default="decoded_out",
        help="Output directory for .decoded.txt / .decoded.json",
    )
    b.add_argument(
        "--format",
        choices=("txt", "json", "both"),
        default="both",
        help="Export format",
    )
    b.set_defaults(func=cmd_batch)

    i = sub.add_parser("interactive", help="Multi-line paste REPL")
    i.set_defaults(func=cmd_interactive)

    return p


def _report_metadata(layer_count: int, ioc_count: int) -> dict[str, object]:
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "mode": "static defensive analysis",
        "layers": layer_count,
        "iocs": ioc_count,
    }


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
