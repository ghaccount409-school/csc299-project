"""
Simple task manager CLI stored in `prototype_pkms.py` (per user request).

Commands:
  add    - add a task
  list   - list tasks
  search - search tasks by keyword

Data file (default): tasks.json next to this script
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

DEFAULT_FILENAME = "tasks.json"


@dataclass
class Task:
    id: str
    title: str
    notes: Optional[str]
    created_at: str
    due: Optional[str] = None
    tags: List[str] = field(default_factory=list)


def data_file_path(path: Optional[str] = None) -> Path:
    if path:
        return Path(path)
    return Path(__file__).parent.joinpath(DEFAULT_FILENAME)


def load_tasks(path: Optional[str] = None) -> List[Task]:
    p = data_file_path(path)
    if not p.exists():
        return []
    try:
        with p.open("r", encoding="utf-8") as f:
            raw = json.load(f)
            tasks = [Task(**t) for t in raw]
            return tasks
    except (json.JSONDecodeError, TypeError) as e:
        # Corrupt file: back it up and return empty
        backup = p.with_suffix(".bak")
        try:
            p.replace(backup)
            print(f"Warning: corrupted data file moved to {backup}", file=sys.stderr)
        except Exception:
            print("Warning: corrupted data file could not be backed up", file=sys.stderr)
        return []


def save_tasks(tasks: List[Task], path: Optional[str] = None) -> None:
    p = data_file_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump([asdict(t) for t in tasks], f, ensure_ascii=False, indent=2)


def add_task(title: str, notes: Optional[str] = None, due: Optional[str] = None, tags: Optional[List[str]] = None, path: Optional[str] = None) -> Task:
    tasks = load_tasks(path)
    new = Task(
        id=uuid.uuid4().hex,
        title=title,
        notes=notes,
        created_at=datetime.utcnow().isoformat() + "Z",
        due=due,
        tags=tags or [],
    )
    tasks.append(new)
    save_tasks(tasks, path)
    return new


def list_tasks(path: Optional[str] = None, tag: Optional[str] = None) -> List[Task]:
    tasks = load_tasks(path)
    if tag:
        tasks = [t for t in tasks if tag in (t.tags or [])]
    return tasks


def search_tasks(query: str, path: Optional[str] = None) -> List[Task]:
    q = query.lower()
    tasks = load_tasks(path)
    found = [t for t in tasks if q in t.title.lower() or (t.notes and q in t.notes.lower())]
    return found


def pretty_print(tasks: List[Task]) -> None:
    if not tasks:
        print("No tasks.")
        return
    for t in tasks:
        print(f"- [{t.id}] {t.title}")
        if t.notes:
            print(f"    Notes: {t.notes}")
        if t.due:
            print(f"    Due: {t.due}")
        if t.tags:
            print(f"    Tags: {', '.join(t.tags)}")
        print(f"    Created: {t.created_at}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="taskmgr", description="Simple JSON-backed task manager (stored in prototype_pkms.py)")
    parser.add_argument("--data", help="Path to JSON data file (defaults to tasks.json next to script)")
    sub = parser.add_subparsers(dest="cmd")

    p_add = sub.add_parser("add", help="Add a new task")
    p_add.add_argument("title", help="Title of the task")
    p_add.add_argument("--notes", help="Optional notes for the task")
    p_add.add_argument("--due", help="Optional due date (string)")
    p_add.add_argument("--tag", action="append", help="Tag (repeatable)")

    p_list = sub.add_parser("list", help="List tasks")
    p_list.add_argument("--tag", help="Filter by tag")

    p_search = sub.add_parser("search", help="Search tasks by keyword in title or notes")
    p_search.add_argument("query", help="Search query string")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd is None:
        parser.print_help()
        return 1

    data_path = args.data

    if args.cmd == "add":
        t = add_task(args.title, notes=args.notes, due=args.due, tags=args.tag, path=data_path)
        print(f"Added task {t.id}")
        return 0

    if args.cmd == "list":
        tasks = list_tasks(path=data_path, tag=args.tag)
        pretty_print(tasks)
        return 0

    if args.cmd == "search":
        tasks = search_tasks(args.query, path=data_path)
        pretty_print(tasks)
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())