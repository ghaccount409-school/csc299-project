"""
tasks3: A JSON-backed task manager CLI with comprehensive task management features.

This module provides a complete task management system with support for:
- Creating, listing, searching, and deleting tasks
- Task linking and hierarchical subtasks
- Tag-based organization and filtering
- Task importance flagging
- Flexible sorting and filtering options
- Persistent JSON-based storage

Commands:
  add              - Add a new task (with optional tags, due date, notes)
  list             - List all tasks (with optional tag filtering and sorting)
  search           - Search tasks by keyword in title or notes
  show             - Display details of a single task
  link             - Link one task to another (task relationships)
  tags             - List all tags and their usage counts
  search-tags      - Search tasks by one or more tags (ANY or ALL matching)
  important        - List tasks marked as important
  mark-important   - Mark a task as important
  unmark-important - Unmark a task as important
  add-subtask      - Link an existing task as a subtask to a parent task
  show-subtasks    - Display all subtasks for a given parent task
  delete           - Delete a task (with options for handling subtasks)

Data Storage:
  Default data file: tasks.json next to this script
  Use --data FLAG to specify a custom data file path
  Data is stored in JSON format with automatic backup of corrupted files
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
    """Represents a task in the task manager.
    
    Attributes:
        id: Unique identifier for the task (8-char hex string or custom)
        title: The task's title/description
        notes: Optional additional notes or details
        created_at: Timestamp when task was created (UTC format: YYYY-MM-DD HH:MM:SS UTC)
        due: Optional due date (user-specified string format, e.g., "2025-11-20")
        tags: List of tag strings for categorization and filtering
        links: List of task IDs that this task is linked to (task relationships)
        important: Boolean flag indicating if task is marked as important
        subtasks: List of task IDs that are subtasks of this parent task
    """


def data_file_path(path: Optional[str] = None) -> Path:
    """Get the path to the data file.
    
    Args:
        path: Optional custom path to data file. If not provided, defaults to tasks.json
              in the same directory as this script.
    
    Returns:
        Path object pointing to the data file location.
    """
    if path:
        return Path(path)
    return Path(__file__).parent.joinpath(DEFAULT_FILENAME)


def load_tasks(path: Optional[str] = None) -> List[Task]:
    """Load all tasks from the data file.
    
    Handles JSON parsing and corrupted file recovery. If the data file is corrupted,
    it is automatically backed up with a .bak extension and an empty list is returned.
    
    Args:
        path: Optional custom path to data file. Defaults to tasks.json next to script.
    
    Returns:
        List of Task objects loaded from the data file, or empty list if file doesn't exist
        or is corrupted.
    """
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
    """Save tasks to the data file.
    
    Creates necessary parent directories and writes tasks as formatted JSON.
    
    Args:
        tasks: List of Task objects to save
        path: Optional custom path to data file. Defaults to tasks.json next to script.
    """
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
    """Add a new task to the task manager.
    
    Args:
        title: The task title (required)
        notes: Optional notes or additional details for the task
        due: Optional due date (user-specified string format, e.g., "2025-11-20")
        tags: Optional list of tags for categorization and filtering
        custom_id: Optional custom unique identifier. If omitted, an 8-character hex ID is generated.
                   Must be unique or the task will not be added.
        important: If True, mark the task as important (default: False)
        path: Optional custom path to data file. Defaults to tasks.json next to script.
    
    Returns:
        The newly created Task object, or None if a duplicate custom_id was provided.
    """
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
    """Find a task by ID in a list of tasks.
    
    Args:
        task_id: The ID to search for
        tasks: List of Task objects to search in
    
    Returns:
        The Task object if found, None otherwise.
    """
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


def add_subtask(parent_id: str, subtask_id: str, path: Optional[str] = None) -> Optional[Task]:
    """Link an existing task as a subtask of a parent task.
    
    Both parent_id and subtask_id must exist as existing tasks.
    
    Returns the subtask on success, None if either task not found or already linked.
    """
    tasks = load_tasks(path)
    parent = find_task(parent_id, tasks)
    subtask = find_task(subtask_id, tasks)
    
    if parent is None:
        print(f"Parent task {parent_id} not found.", file=sys.stderr)
        return None
    
    if subtask is None:
        print(f"Subtask {subtask_id} not found.", file=sys.stderr)
        return None
    
    # Link the subtask to the parent if not already linked
    if subtask_id not in parent.subtasks:
        parent.subtasks.append(subtask_id)
        save_tasks(tasks, path)
    
    return subtask


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
    # Highlight only the title in green; keep ID uncolored
    green = "\033[92m"
    reset = "\033[0m"
    print(f"- {prefix}[{t.id}] {green}{t.title}{reset}")
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
    # Display subtask count if there are any
    if getattr(t, 'subtasks', None):
        subtask_count = len(t.subtasks)
        print(f"    \033[33mSubtasks:\033[0m {subtask_count} subtask(s)")
        if subtask_count > 0:
            print(f"      To view subtasks: python prototype_pkms.py show-subtasks {t.id}")
    return t


def list_tasks(path: Optional[str] = None, tag: Optional[str] = None) -> List[Task]:
    tasks = load_tasks(path)
    if tag:
        tasks = [t for t in tasks if tag in (t.tags or [])]
    return tasks


def show_subtasks(parent_id: str, path: Optional[str] = None) -> List[Task]:
    """Show all subtasks for a given parent task. Returns list of subtasks."""
    tasks = load_tasks(path)
    parent = find_task(parent_id, tasks)
    if parent is None:
        print(f"Parent task {parent_id} not found.")
        return []
    
    subtasks = [find_task(sid, tasks) for sid in getattr(parent, 'subtasks', [])]
    subtasks = [s for s in subtasks if s is not None]  # Filter out any None values
    
    if not subtasks:
        # Show title highlighted only
        green = "\033[92m"
        reset = "\033[0m"
        print(f"No subtasks for task [{parent.id}] {green}{parent.title}{reset}")
        return []

    green = "\033[92m"
    reset = "\033[0m"
    # Highlight only the parent title, not the ID
    print(f"Subtasks for [{parent.id}] {green}{parent.title}{reset}:")
    pretty_print(subtasks)
    return subtasks


def search_tasks(query: str, path: Optional[str] = None) -> List[Task]:
    """Search for tasks by keyword in title or notes.

    Args:
        query: Search string to match (case-insensitive) against title and notes.
        path: Optional path to the data file.

    Returns:
        List of matching Task objects.
    """
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


def sort_tasks(tasks: List[Task], sort_by: str = "created", reverse: bool = False) -> List[Task]:
    """Sort tasks by specified field.
    
    Args:
        tasks: List of tasks to sort
        sort_by: Field to sort by ('due', 'created', 'title', 'id'). Default: 'created'
        reverse: If True, sort in descending order
    
    Returns:
        Sorted list of tasks
    """
    def is_valid_date_format(date_str: Optional[str]) -> bool:
        """Check if date string is in YYYY-MM-DD format."""
        if date_str is None:
            return False
        try:
            from datetime import datetime as dt
            dt.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    
    if sort_by == "due":
        # Sort by due date; tasks without due date or invalid format go to end
        # First sort by valid/invalid, then by date within each group
        def due_sort_key(t):
            is_valid = is_valid_date_format(t.due)
            # Return tuple: (is_invalid, date_or_empty)
            # Invalid dates will have (True, ""), valid will have (False, "2025-11-10")
            # When reverse=False: (False, ...) < (True, ...) so valid dates come first
            # When reverse=True: we reverse the order, but we need to handle this specially
            return (not is_valid, t.due or "")
        
        sorted_tasks = sorted(tasks, key=due_sort_key)
        # If reverse is True, we need to reverse but keep invalid dates at the end
        if reverse:
            # Split into valid and invalid
            valid = [t for t in sorted_tasks if is_valid_date_format(t.due)]
            invalid = [t for t in sorted_tasks if not is_valid_date_format(t.due)]
            # Reverse valid dates, keep invalid at end
            valid.reverse()
            sorted_tasks = valid + invalid
    elif sort_by == "created":
        # Sort by created_at timestamp
        sorted_tasks = sorted(tasks, key=lambda t: t.created_at, reverse=reverse)
    elif sort_by == "title":
        # Sort by title (alphanumeric)
        sorted_tasks = sorted(tasks, key=lambda t: t.title.lower(), reverse=reverse)
    elif sort_by == "id":
        # Sort by task ID
        sorted_tasks = sorted(tasks, key=lambda t: t.id, reverse=reverse)
    else:
        # Default to created if invalid sort_by
        sorted_tasks = sorted(tasks, key=lambda t: t.created_at, reverse=reverse)
    
    return sorted_tasks


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


def delete_task(task_id: str, path: Optional[str] = None, delete_subtasks: Optional[bool] = None) -> Optional[bool]:
    """Delete a task.
    
    Args:
        task_id: ID of the task to delete
        path: Optional path to the data file
        delete_subtasks: If the task has subtasks:
            - True: delete subtasks along with the parent task
            - False: orphan subtasks (remove their parent reference, making them regular tasks)
            - None: prompt user for choice (returns None if user cancels)
    
    Returns:
        True if task was deleted successfully
        False if task not found
        None if user cancelled (when delete_subtasks=None and task has subtasks)
    """
    tasks = load_tasks(path)
    t = find_task(task_id, tasks)
    
    if t is None:
        return False
    
    # Check if task has subtasks
    subtasks = getattr(t, 'subtasks', [])
    if subtasks and delete_subtasks is None:
        # Prompt user
        while True:
            response = input(f"Task '{t.title}' has {len(subtasks)} subtask(s). Delete them too? (yes/no/cancel): ").strip().lower()
            if response in ('yes', 'y'):
                delete_subtasks = True
                break
            elif response in ('no', 'n'):
                delete_subtasks = False
                break
            elif response in ('cancel', 'c'):
                return None
            else:
                print("Please enter 'yes', 'no', or 'cancel'.")
    
    # Handle subtasks
    if delete_subtasks and subtasks:
        # Delete subtasks along with parent
        tasks = [t for t in tasks if t.id not in subtasks]
    elif not delete_subtasks and subtasks:
        # Orphan subtasks: clear their parent reference
        for subtask_id in subtasks:
            subtask = find_task(subtask_id, tasks)
            if subtask:
                # Subtasks don't have a "parent_id" field; they're referenced in parent's subtasks list
                # So just removing from parent.subtasks list orphans them (done below)
                pass
    
    # Remove the task itself
    tasks = [t for t in tasks if t.id != task_id]
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
        # Highlight only the title in green; keep ID plain
        green = "\033[92m"
        reset = "\033[0m"
        print(f"- {prefix}[{t.id}] {green}{t.title}{reset}")
        if t.notes:
            print(f"    Notes: {t.notes}")
        if t.due:
            print(f"    Due: {t.due}")
        if t.tags:
            print(f"    Tags: {', '.join(t.tags)}")
        if t.links:
            print("    Linked tasks:")
            for lid in t.links:
                # Do not color linked task IDs in the list view
                print(f"      - [{lid}] view: python prototype_pkms.py show {lid}")
        # Display subtask count if there are any
        if getattr(t, 'subtasks', None):
            subtask_count = len(t.subtasks)
            if subtask_count > 0:
                print(f"    \033[33mSubtasks:\033[0m {subtask_count} subtask(s) - run: python prototype_pkms.py show-subtasks {t.id}")
        print(f"    Created: {t.created_at}")


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser for the CLI.
    
    Configures all available commands and their arguments, including:
    - add: Create new tasks with optional metadata
    - list: List tasks with filtering and sorting options
    - search: Search by keyword
    - show: Display a single task's details
    - link: Create task relationships
    - tags: List tag usage statistics
    - search-tags: Find tasks by tag(s) with ANY/ALL matching
    - important: List flagged tasks
    - mark-important/unmark-important: Toggle importance flag
    - add-subtask/show-subtasks: Manage task hierarchies
    - delete: Remove tasks with subtask handling options
    
    Returns:
        Configured ArgumentParser instance.
    """
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
    p_list.add_argument("--sort-by", choices=["due", "created", "title", "id"], default="created", help="Sort by field (default: created)")
    p_list.add_argument("--reverse", action="store_true", help="Sort in descending order")

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

    p_add_subtask = sub.add_parser("add-subtask", help="Link an existing task as a subtask to a parent task")
    p_add_subtask.add_argument("parent_id", help="ID of the parent task")
    p_add_subtask.add_argument("subtask_id", help="ID of the existing task to link as a subtask")

    p_show_subtasks = sub.add_parser("show-subtasks", help="Show all subtasks for a parent task")
    p_show_subtasks.add_argument("parent_id", help="ID of the parent task")

    p_delete = sub.add_parser("delete", help="Delete a task")
    p_delete.add_argument("task_id", help="ID of the task to delete")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for the tasks3 CLI.
    
    Parses command-line arguments and dispatches to appropriate command handlers.
    
    Args:
        argv: Optional list of command-line arguments. If None, sys.argv is used.
    
    Returns:
        Exit code:
          0 - Command executed successfully
          1 - No command provided or user cancelled operation
          2 - Command failed (task not found, ID conflict, etc.)
    """
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
        sort_by = getattr(args, 'sort_by', 'created')
        reverse = getattr(args, 'reverse', False)
        tasks = sort_tasks(tasks, sort_by=sort_by, reverse=reverse)
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

    if args.cmd == "add-subtask":
        t = add_subtask(args.parent_id, args.subtask_id, path=data_path)
        if t is None:
            return 2
        print(f"Linked task {t.id} as subtask to parent {args.parent_id}")
        return 0

    if args.cmd == "show-subtasks":
        show_subtasks(args.parent_id, path=data_path)
        return 0

    if args.cmd == "delete":
        result = delete_task(args.task_id, path=data_path)
        if result is True:
            print(f"Deleted task {args.task_id}")
            return 0
        elif result is False:
            print(f"Task {args.task_id} not found")
            return 2
        else:  # result is None (user cancelled)
            print("Delete cancelled.")
            return 1

    parser.print_help()
    return 2

#if __name__ == "__main__":
#    raise SystemExit(main())


if __name__ == "__main__":
    main()