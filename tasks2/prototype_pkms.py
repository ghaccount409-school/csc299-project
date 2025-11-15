"""
Simple task manager CLI stored in `prototype_pkms.py` (per user request).

Commands:
  add    - add a task
  list   - list tasks
  search - search tasks by keyword
  tags   - list all tags
  search-tags - search by tags
  show   - show a task
  link   - link tasks

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
    links: List[str] = field(default_factory=list)
    important: bool = False


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


def generate_short_id() -> str:
    """Generate a short 8-char task ID."""
    return uuid.uuid4().hex[:8]


def task_id_exists(task_id: str, path: Optional[str] = None) -> bool:
    """Check if a task ID already exists."""
    tasks = load_tasks(path)
    return any(t.id == task_id for t in tasks)


def add_task(title: str, notes: Optional[str] = None, due: Optional[str] = None, tags: Optional[List[str]] = None, custom_id: Optional[str] = None, important: bool = False, path: Optional[str] = None) -> Optional[Task]:
    tasks = load_tasks(path)
    
    # Determine task ID
    if custom_id:
        if task_id_exists(custom_id, path):
            print(f"Task ID '{custom_id}' already exists. Please choose a different ID.", file=sys.stderr)
            return None
        task_id = custom_id
    else:
        task_id = generate_short_id()
    # Use a human-friendly date/time string
    created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    new = Task(
        id=task_id,
        title=title,
        notes=notes,
        created_at=created_at,
        due=due,
        tags=tags or [],
        links=[],
        important=important,
    )
    tasks.append(new)
    save_tasks(tasks, path)
    return new


def find_task(task_id: str, tasks: List[Task]) -> Optional[Task]:
    for t in tasks:
        if t.id == task_id:
            return t
    return None


def add_link(source_id: str, target_id: str, path: Optional[str] = None) -> bool:
    """Link target task to source task. Returns True on success, False if either task missing."""
    tasks = load_tasks(path)
    src = find_task(source_id, tasks)
    tgt = find_task(target_id, tasks)
    if src is None or tgt is None:
        return False
    if target_id not in src.links:
        src.links.append(target_id)
        save_tasks(tasks, path)
    return True


def show_task(task_id: str, path: Optional[str] = None) -> Optional[Task]:
    tasks = load_tasks(path)
    t = find_task(task_id, tasks)
    if t is None:
        print(f"Task {task_id} not found.")
        return None
    # print single task in same format as pretty_print
    if getattr(t, 'important', False):
        prefix = "\033[93mImportant:\033[0m "
    else:
        prefix = ""
    print(f"- {prefix}[{t.id}] {t.title}")
    if t.notes:
        print(f"    Notes: {t.notes}")
    if t.due:
        print(f"    Due: {t.due}")
    if t.tags:
        print(f"    Tags: {', '.join(t.tags)}")
    print(f"    Created: {t.created_at}")
    if t.links:
        print("    Linked tasks:")
        for lid in t.links:
            print(f"      - [{lid}] view: python prototype_pkms.py show {lid}")
    return t


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


def search_tasks_by_tags(tags: List[str], path: Optional[str] = None, match_all: bool = False) -> List[Task]:
    """Search for tasks by one or more tags.
    
    Args:
        tags: List of tags to search for
        path: Path to data file
        match_all: If True, task must have ALL tags. If False, task must have ANY tag.
    """
    tasks = load_tasks(path)
    if match_all:
        # Task must have all specified tags
        found = [t for t in tasks if all(tag in (t.tags or []) for tag in tags)]
    else:
        # Task must have at least one specified tag
        found = [t for t in tasks if any(tag in (t.tags or []) for tag in tags)]
    return found


def list_all_tags(path: Optional[str] = None) -> dict:
    """List all tags and their counts across all tasks."""
    tasks = load_tasks(path)
    tag_counts = {}
    for task in tasks:
        for tag in (task.tags or []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    return dict(sorted(tag_counts.items()))


def list_important_tasks(path: Optional[str] = None) -> List[Task]:
    """Return tasks marked as important."""
    tasks = load_tasks(path)
    return [t for t in tasks if getattr(t, 'important', False)]


def mark_important(task_id: str, path: Optional[str] = None) -> bool:
    """Mark a task as important. Returns True if changed, False if not found."""
    tasks = load_tasks(path)
    t = find_task(task_id, tasks)
    if t is None:
        return False
    if not getattr(t, 'important', False):
        t.important = True
        save_tasks(tasks, path)
    return True


def unmark_important(task_id: str, path: Optional[str] = None) -> bool:
    """Unmark a task as important. Returns True if changed, False if not found."""
    tasks = load_tasks(path)
    t = find_task(task_id, tasks)
    if t is None:
        return False
    if getattr(t, 'important', False):
        t.important = False
        save_tasks(tasks, path)
    return True


def pretty_print(tasks: List[Task]) -> None:
    if not tasks:
        print("No tasks.")
        return
    for t in tasks:
        if getattr(t, 'important', False):
            prefix = "\033[93mImportant:\033[0m "
        else:
            prefix = ""
        print(f"- {prefix}[{t.id}] {t.title}")
        if t.notes:
            print(f"    Notes: {t.notes}")
        if t.due:
            print(f"    Due: {t.due}")
        if t.tags:
            print(f"    Tags: {', '.join(t.tags)}")
        if t.links:
            print("    Linked tasks:")
            for lid in t.links:
                print(f"      - [{lid}] view: python prototype_pkms.py show {lid}")
        print(f"    Created: {t.created_at}")


def build_parser() -> argparse.ArgumentParser:
    # Use the actual script filename as the program name in help/usage
    parser = argparse.ArgumentParser(prog=Path(__file__).name, description="Simple JSON-backed task manager (stored in prototype_pkms.py)")
    parser.add_argument("--data", help="Path to JSON data file (defaults to tasks.json next to script)")
    sub = parser.add_subparsers(dest="cmd")

    p_add = sub.add_parser("add", help="Add a new task")
    p_add.add_argument("title", help="Title of the task")
    p_add.add_argument("--notes", help="Optional notes for the task")
    p_add.add_argument("--due", help="Optional due date (string)")
    p_add.add_argument("--tag", action="append", help="Tag (repeatable)")
    p_add.add_argument("--id", dest="custom_id", help="Optional custom task ID (must be unique). If omitted, a short ID is generated.")
    p_add.add_argument("--important", action="store_true", help="Mark task as important")

    p_list = sub.add_parser("list", help="List tasks")
    p_list.add_argument("--tag", help="Filter by tag")

    p_search = sub.add_parser("search", help="Search tasks by keyword in title or notes")
    p_search.add_argument("query", help="Search query string")

    p_show = sub.add_parser("show", help="Show a single task by id")
    p_show.add_argument("task_id", help="ID of the task to show")

    p_link = sub.add_parser("link", help="Link one task to another")
    p_link.add_argument("source_id", help="ID of the task to add link to (source)")
    p_link.add_argument("target_id", help="ID of the task to link (target)")

    p_tags = sub.add_parser("tags", help="List all tags and their counts")

    p_search_tags = sub.add_parser("search-tags", help="Search tasks by one or more tags")
    p_search_tags.add_argument("tag", nargs="+", help="Tag(s) to search for")
    p_search_tags.add_argument("--all", action="store_true", help="Match tasks with ALL specified tags (default: ANY)")

    p_important = sub.add_parser("important", help="List tasks marked as important")

    p_mark = sub.add_parser("mark-important", help="Mark a task as important")
    p_mark.add_argument("task_id", help="ID of task to mark important")

    p_unmark = sub.add_parser("unmark-important", help="Unmark a task as important")
    p_unmark.add_argument("task_id", help="ID of task to unmark as important")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd is None:
        parser.print_help()
        return 1

    data_path = args.data

    if args.cmd == "add":
        t = add_task(args.title, notes=args.notes, due=args.due, tags=args.tag, custom_id=args.custom_id, important=getattr(args, 'important', False), path=data_path)
        if t is None:
            return 2
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

    if args.cmd == "show":
        show_task(args.task_id, path=data_path)
        return 0

    if args.cmd == "link":
        ok = add_link(args.source_id, args.target_id, path=data_path)
        if ok:
            print(f"Linked {args.target_id} -> {args.source_id}")
            return 0
        else:
            print("One or both task IDs not found.")
            return 2

    if args.cmd == "tags":
        tag_counts = list_all_tags(path=data_path)
        if not tag_counts:
            print("No tags found.")
            return 0
        print("Tags:")
        for tag, count in tag_counts.items():
            print(f"  {tag}: {count} task(s)")
        return 0

    if args.cmd == "search-tags":
        match_all = args.all
        tasks = search_tasks_by_tags(args.tag, path=data_path, match_all=match_all)
        if tasks:
            mode = "all" if match_all else "any"
            print(f"Found {len(tasks)} task(s) with {mode} of: {', '.join(args.tag)}")
            pretty_print(tasks)
        else:
            print(f"No tasks found with {('all' if match_all else 'any')} of: {', '.join(args.tag)}")
        return 0

    if args.cmd == "important":
        tasks = list_important_tasks(path=data_path)
        pretty_print(tasks)
        return 0

    if args.cmd == "mark-important":
        ok = mark_important(args.task_id, path=data_path)
        if ok:
            print(f"Marked {args.task_id} as important")
            return 0
        else:
            print(f"Task {args.task_id} not found")
            return 2

    if args.cmd == "unmark-important":
        ok = unmark_important(args.task_id, path=data_path)
        if ok:
            print(f"Unmarked {args.task_id} as important")
            return 0
        else:
            print(f"Task {args.task_id} not found")
            return 2

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())