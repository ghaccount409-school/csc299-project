"""CLI front-end for the names storage.

Usage:
  python bin/names_cli.py add "Alice"
  python bin/names_cli.py list

The CLI is intentionally thin and delegates storage concerns to src/names_storage.py.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure src is importable when run from project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from names_storage import NameStore  # type: ignore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="names")
    sub = parser.add_subparsers(dest="cmd", required=True)

    add = sub.add_parser("add", help="Add a person name to the store")
    add.add_argument("name", help="Person's name (use quotes if it contains spaces)")

    sub.add_parser("list", help="List stored names")

    return parser


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)

    store = NameStore(file_path=PROJECT_ROOT / "data" / "names.json")

    if args.cmd == "add":
        store.add_name(args.name)
        print(f"Added: {args.name}")
        return 0

    if args.cmd == "list":
        names = store.list_names()
        if not names:
            print("(no names stored)")
            return 0
        for n in names:
            print(n)
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
