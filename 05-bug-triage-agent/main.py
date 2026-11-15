#!/usr/bin/env python3
"""Bug Triage Agent — CLI (Project 5 of 5).

Usage:
    python main.py "Payment succeeds but order remains pending."
    python main.py --file sample_bugs.txt
    python main.py            # interactive mode

Each bug report is triaged (category, priority, team, summary,
matched keywords, scores) and printed as indented JSON.
"""

from __future__ import annotations

import argparse
import json
import sys

from agent import bug_agent


def print_result(bug: str) -> None:
    """Triage one bug report and print the JSON result."""
    result = bug_agent(bug)
    print(json.dumps(result, indent=2))


def interactive() -> None:
    """Prompt for bug reports until the user quits."""
    print("Bug Triage Agent — interactive mode")
    print("Type a bug report and press Enter.")
    print("Type 'quit', 'exit' or just press Enter on an empty line to stop.\n")
    while True:
        try:
            bug = input("Bug report> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if not bug or bug.lower() in {"quit", "exit"}:
            print("Goodbye.")
            break
        print_result(bug)
        print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bug Triage Agent: classify a bug, set its priority, "
                    "and route it to the right team."
    )
    parser.add_argument(
        "bug", nargs="?", default=None,
        help='A bug report, e.g. "Payment succeeds but order remains pending."',
    )
    parser.add_argument(
        "--file", "-f", default=None, metavar="PATH",
        help="File with one bug report per line; triage every line.",
    )
    args = parser.parse_args(argv)

    if args.file:
        try:
            with open(args.file, encoding="utf-8") as f:
                bugs = [line.strip() for line in f if line.strip()]
        except OSError as exc:
            print(f"Error: could not read {args.file}: {exc}", file=sys.stderr)
            return 1
        if not bugs:
            print(f"No bug reports found in {args.file}.", file=sys.stderr)
            return 1
        for bug in bugs:
            print(f"# {bug}")
            print_result(bug)
            print()
        return 0

    if args.bug:
        print_result(args.bug)
        return 0

    interactive()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
