"""Argparse CLI for the reporead package (RepoReady internal dev build)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, report_json, report_text
from .models import EXIT_USAGE, Report, decide_exit_code
from .rules import run_checks
from .scanner import ScannerError, resolve_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reporead",
        description=(
            "Offline, read-only repository readiness checks "
            "(RepoReady internal dev build)."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"reporead {__version__}"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser(
        "check", help="check a repository directory (read-only)"
    )
    check.add_argument(
        "path",
        nargs="?",
        default=".",
        help="repository root to check (default: current directory)",
    )
    check.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )
    check.add_argument(
        "--strict",
        action="store_true",
        help="treat warnings as check failures (exit code 1)",
    )
    check.add_argument(
        "--output",
        metavar="PATH",
        type=Path,
        default=None,
        help=(
            "write the report to PATH instead of stdout; "
            "missing parent directories are not created"
        ),
    )
    return parser


def _write_stdout(text: str) -> None:
    stream = sys.stdout
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    stream.write(text)


def _run_check(args: argparse.Namespace) -> int:
    try:
        root = resolve_root(args.path)
    except ScannerError as exc:
        print(f"reporead: error: {exc}", file=sys.stderr)
        return EXIT_USAGE

    findings, evaluated = run_checks(root)
    report = Report(root=str(root), findings=findings, evaluated_rule_count=evaluated)
    rendered = (
        report_text.render_text(report)
        if args.format == "text"
        else report_json.render_json(report)
    )

    if args.output is not None:
        try:
            args.output.write_text(rendered, encoding="utf-8", newline="\n")
        except OSError as exc:
            print(
                f"reporead: error: cannot write report to "
                f"'{args.output}': {exc.strerror or exc}",
                file=sys.stderr,
            )
            return EXIT_USAGE
    else:
        _write_stdout(rendered)
    return decide_exit_code(report, strict=args.strict)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return _run_check(args)
