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
        id (str): Unique identifier for the task (8-char hex string or custom).
        title (str): The task's title/description.
        notes (Optional[str]): Additional notes or details.
        created_at (str): Timestamp when task was created 
            (UTC format: YYYY-MM-DD HH:MM:SS UTC).
        due (Optional[str]): Due date (user-specified string format, 
            e.g., "2025-11-20").
        tags (List[str]): Tag strings for categorization and filtering.
        links (List[str]): Task IDs that this task is linked to 
            (task relationships).
        important (bool): Flag indicating if task is marked as important.
        subtasks (List[str]): Task IDs that are subtasks of this parent task.
    """
    id: str
    title: str
    notes: Optional[str]
    created_at: str
    due: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    important: bool = False
    subtasks: List[str] = field(default_factory=list)


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
    
    Handles JSON parsing and corrupted file recovery. If the data file is 
    corrupted, it is automatically backed up with a .bak extension and an 
    empty list is returned.
    
    Args:
        path (Optional[str]): Custom path to data file. Defaults to tasks.json 
            next to script.
    
    Returns:
        List[Task]: Task objects loaded from the data file, or empty list if 
            file doesn't exist or is corrupted.
    """
    p = data_file_path(path)
    if not p.exists():
        return []
    
    try:
        with p.open("r", encoding="utf-8") as f:
            raw = json.load(f)
            # Convert raw dictionaries to Task objects
            tasks = [Task(**t) for t in raw]
            return tasks
    except (json.JSONDecodeError, TypeError) as e:
        # Corrupt file: back it up and return empty list
        backup = p.with_suffix(".bak")
        try:
            p.replace(backup)
            print(
                f"Warning: corrupted data file moved to {backup}",
                file=sys.stderr
            )
        except Exception:
            print(
                "Warning: corrupted data file could not be backed up",
                file=sys.stderr
            )
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


def add_task(
    title: str,
    notes: Optional[str] = None,
    due: Optional[str] = None,
    tags: Optional[List[str]] = None,
    custom_id: Optional[str] = None,
    important: bool = False,
    path: Optional[str] = None
) -> Optional[Task]:
    """Add a new task to the task manager.
    
    Args:
        title (str): The task title (required).
        notes (Optional[str]): Notes or additional details for the task.
        due (Optional[str]): Due date (user-specified string format, 
            e.g., "2025-11-20").
        tags (Optional[List[str]]): List of tags for categorization and filtering.
        custom_id (Optional[str]): Custom unique identifier. If omitted, an 
            8-character hex ID is generated. Must be unique or the task will 
            not be added.
        important (bool): If True, mark the task as important (default: False).
        path (Optional[str]): Custom path to data file. Defaults to tasks.json 
            next to script.
    
    Returns:
        Optional[Task]: The newly created Task object, or None if a duplicate 
            custom_id was provided.
    """
    tasks = load_tasks(path)
    
    # Determine task ID: use custom if provided and unique, else generate
    if custom_id:
        if task_id_exists(custom_id, path):
            print(
                f"Task ID '{custom_id}' already exists. "
                f"Please choose a different ID.",
                file=sys.stderr
            )
            return None
        task_id = custom_id
    else:
        task_id = generate_short_id()
    
    # Use a human-friendly date/time string in UTC
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
    """Link target task to source task.
    
    Args:
        source_id (str): ID of the task to add link to (source).
        target_id (str): ID of the task to link (target).
        path (Optional[str]): Custom path to data file.
    
    Returns:
        bool: True on success, False if either task is missing.
    """
    tasks = load_tasks(path)
    src = find_task(source_id, tasks)
    tgt = find_task(target_id, tasks)
    
    if src is None or tgt is None:
        return False
    
    # Only add link if not already present
    if target_id not in src.links:
        src.links.append(target_id)
        save_tasks(tasks, path)
    return True


def add_subtask(
    parent_id: str,
    subtask_id: str,
    path: Optional[str] = None
) -> Optional[Task]:
    """Link an existing task as a subtask of a parent task.
    
    Both parent_id and subtask_id must exist as existing tasks.
    
    Args:
        parent_id (str): ID of the parent task.
        subtask_id (str): ID of the task to link as a subtask.
        path (Optional[str]): Custom path to data file.
    
    Returns:
        Optional[Task]: The subtask on success, None if either task not found 
            or already linked.
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
    """Display details of a single task.
    
    Args:
        task_id (str): ID of the task to show.
        path (Optional[str]): Custom path to data file.
    
    Returns:
        Optional[Task]: The task if found, None otherwise.
    """
    tasks = load_tasks(path)
    t = find_task(task_id, tasks)
    
    if t is None:
        print(f"Task {task_id} not found.")
        return None
    
    # Print single task in same format as pretty_print
    # ANSI color codes for formatting
    important_yellow = "\033[93m"
    green = "\033[92m"
    yellow = "\033[33m"
    reset = "\033[0m"
    
    # Add importance prefix if flagged
    prefix = f"{important_yellow}Important:{reset} " if getattr(t, 'important', False) else ""
    
    # Display task with colored title
    print(f"- {prefix}[{t.id}] {green}{t.title}{reset}")
    
    # Display optional fields if present
    if t.notes:
        print(f"    Notes: {t.notes}")
    if t.due:
        print(f"    Due: {t.due}")
    if t.tags:
        print(f"    Tags: {', '.join(t.tags)}")
    
    print(f"    Created: {t.created_at}")
    
    # Display linked tasks with view command
    if t.links:
        print("    Linked tasks:")
        for lid in t.links:
            print(f"      - [{lid}] view: python prototype_pkms.py show {lid}")
    
    # Display subtask count and view command if there are any
    if getattr(t, 'subtasks', None):
        subtask_count = len(t.subtasks)
        print(f"    {yellow}Subtasks:{reset} {subtask_count} subtask(s)")
        if subtask_count > 0:
            print(
                f"      To view subtasks: "
                f"python prototype_pkms.py show-subtasks {t.id}"
            )
    
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


def sort_tasks(
    tasks: List[Task],
    sort_by: str = "created",
    reverse: bool = False
) -> List[Task]:
    """Sort tasks by specified field.
    
    Args:
        tasks (List[Task]): List of tasks to sort.
        sort_by (str): Field to sort by ('due', 'created', 'title', 'id'). 
            Default: 'created'.
        reverse (bool): If True, sort in descending order.
    
    Returns:
        List[Task]: Sorted list of tasks.
    """
    def is_valid_date_format(date_str: Optional[str]) -> bool:
        """Check if date string is in YYYY-MM-DD format.
        
        Args:
            date_str (Optional[str]): Date string to validate.
        
        Returns:
            bool: True if valid YYYY-MM-DD format, False otherwise.
        """
        if date_str is None:
            return False
        try:
            from datetime import datetime as dt
            dt.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    
    if sort_by == "due":
        # Sort by due date with special handling:
        # - Tasks with valid dates come first (sorted by date)
        # - Tasks with invalid/missing dates come last
        def due_sort_key(t):
            is_valid = is_valid_date_format(t.due)
            # Return tuple: (is_invalid, date_or_empty)
            # Invalid dates: (True, ""), valid dates: (False, "2025-11-10")
            # When reverse=False: (False, ...) < (True, ...) 
            # so valid dates come first
            return (not is_valid, t.due or "")
        
        sorted_tasks = sorted(tasks, key=due_sort_key)
        
        # Special handling for reverse: keep invalid dates at end
        if reverse:
            # Split tasks into valid and invalid date groups
            valid = [t for t in sorted_tasks if is_valid_date_format(t.due)]
            invalid = [t for t in sorted_tasks if not is_valid_date_format(t.due)]
            # Reverse only the valid dates, keep invalid at end
            valid.reverse()
            sorted_tasks = valid + invalid
    elif sort_by == "created":
        # Sort by created_at timestamp
        sorted_tasks = sorted(tasks, key=lambda t: t.created_at, reverse=reverse)
    elif sort_by == "title":
        # Sort by title (case-insensitive alphanumeric)
        sorted_tasks = sorted(tasks, key=lambda t: t.title.lower(), reverse=reverse)
    elif sort_by == "id":
        # Sort by task ID
        sorted_tasks = sorted(tasks, key=lambda t: t.id, reverse=reverse)
    else:
        # Default to created if invalid sort_by specified
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


def delete_task(
    task_id: str,
    path: Optional[str] = None,
    delete_subtasks: Optional[bool] = None
) -> Optional[bool]:
    """Delete a task with optional subtask handling.
    
    Args:
        task_id (str): ID of the task to delete.
        path (Optional[str]): Path to the data file.
        delete_subtasks (Optional[bool]): If the task has subtasks:
            - True: delete subtasks along with the parent task
            - False: orphan subtasks (remove parent reference, make them 
              regular tasks)
            - None: prompt user for choice (returns None if user cancels)
    
    Returns:
        Optional[bool]:
            - True if task was deleted successfully
            - False if task not found
            - None if user cancelled (when delete_subtasks=None and task has 
              subtasks)
    """
    tasks = load_tasks(path)
    t = find_task(task_id, tasks)
    
    if t is None:
        return False
    
    # Check if task has subtasks that need handling
    subtasks = getattr(t, 'subtasks', [])
    if subtasks and delete_subtasks is None:
        # Prompt user for subtask handling choice
        while True:
            response = input(
                f"Task '{t.title}' has {len(subtasks)} subtask(s). "
                f"Delete them too? (yes/no/cancel): "
            ).strip().lower()
            
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
    
    # Handle subtasks based on user choice
    if delete_subtasks and subtasks:
        # Delete subtasks along with parent task
        tasks = [t for t in tasks if t.id not in subtasks]
    elif not delete_subtasks and subtasks:
        # Orphan subtasks: they become regular tasks
        # Note: Subtasks don't have a "parent_id" field; they're only 
        # referenced in the parent's subtasks list. Removing the parent 
        # automatically orphans them.
        pass
    
    # Remove the parent task itself
    tasks = [t for t in tasks if t.id != task_id]
    save_tasks(tasks, path)
    return True


def pretty_print(tasks: List[Task]) -> None:
    """Print a formatted list of tasks with color coding.
    
    Args:
        tasks (List[Task]): Tasks to display.
    """
    if not tasks:
        print("No tasks.")
        return
    
    # ANSI color codes for formatting
    important_yellow = "\033[93m"
    green = "\033[92m"
    yellow = "\033[33m"
    reset = "\033[0m"
    
    for t in tasks:
        # Add importance prefix if task is flagged
        prefix = (
            f"{important_yellow}Important:{reset} "
            if getattr(t, 'important', False)
            else ""
        )
        
        # Display task ID and title (title in green)
        print(f"- {prefix}[{t.id}] {green}{t.title}{reset}")
        
        # Display optional fields if present
        if t.notes:
            print(f"    Notes: {t.notes}")
        if t.due:
            print(f"    Due: {t.due}")
        if t.tags:
            print(f"    Tags: {', '.join(t.tags)}")
        
        # Display linked tasks with view command
        if t.links:
            print("    Linked tasks:")
            for lid in t.links:
                print(f"      - [{lid}] view: python prototype_pkms.py show {lid}")
        
        # Display subtask count and command if present
        if getattr(t, 'subtasks', None):
            subtask_count = len(t.subtasks)
            if subtask_count > 0:
                print(
                    f"    {yellow}Subtasks:{reset} {subtask_count} subtask(s) - "
                    f"run: python prototype_pkms.py show-subtasks {t.id}"
                )
        
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
    # Use final_project as the program name in help/usage
    parser = argparse.ArgumentParser(prog="final_project", description="Simple JSON-backed task manager with AI chat support")
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

    p_ai_chat = sub.add_parser("ai-chat", help="Interactive AI chat for task summarization (requires openai package)")

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

    if args.cmd == "ai-chat":
        # Launch the AI chat interface
        return openai_chat_loop()

    parser.print_help()
    return 2

#if __name__ == "__main__":
#    raise SystemExit(main())


import os

DEVELOPER_ROLE = "You are a helpful assistant that summarizes tasks as short phrases."


def _check_api_key() -> bool:
    """Verify OPENAI_API_KEY is set; return True if present else print guidance and return False."""
    if os.getenv("OPENAI_API_KEY"):
        return True
    print("ERROR: OPENAI_API_KEY environment variable is not set!")
    print("\nSet it with one of these commands:")
    print("  Bash/Linux/Mac: export OPENAI_API_KEY='your-api-key-here'")
    print("  PowerShell: $env:OPENAI_API_KEY='your-api-key-here'")
    print("  CMD: set OPENAI_API_KEY=your-api-key-here")
    print("\nGet a key from: https://platform.openai.com/api/keys")
    sys.stdout.flush()
    return False

def openai_chat_loop() -> int:
    """Interactive AI chat loop for task description summarization.
    
    Prompts user for task descriptions and uses GPT-4o-mini to generate
    concise summaries. Continues until user types 'quit' or sends EOF.
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    # Import OpenAI only when this function is called to avoid import errors
    # when the module is imported for testing other functions
    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: openai package is not installed!")
        print("Install it with: pip install openai")
        return 1
    
    if not _check_api_key():
        return 1
    
    # Initialize OpenAI client
    client = OpenAI()
    
    while True:
        print("\nEnter a task description (or 'quit' to exit):")
        sys.stdout.flush()
        
        try:
            task_description = input("> ").strip()
        except EOFError:
            # Graceful exit if stdin closes
            print("\nEOF received. Exiting.")
            break

        if task_description.lower() == "quit":
            print("Goodbye!")
            break
        
        if not task_description:
            print("Please enter a task description.")
            continue

        print("Processing... (this may take a few seconds)")
        sys.stdout.flush()
        
        try:
            # Call OpenAI API with example context for better summarization
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": DEVELOPER_ROLE},
                    {
                        "role": "user",
                        "content": (
                            f"Summarize this task as a short phrase: "
                            f"{task_description}"
                        )
                    },
                    # Example 1: Camping trip planning
                    {
                        "role": "user",
                        "content": (
                            "Planning a successful camping trip requires careful "
                            "preparation and attention to multiple details. You must "
                            "first research and select an appropriate campsite, "
                            "considering factors like proximity to water sources, "
                            "terrain difficulty, weather forecasts, and permit "
                            "requirements. Next comes assembling essential gear "
                            "including a tent, sleeping bags rated for expected "
                            "temperatures, cooking equipment, food storage containers, "
                            "and navigation tools like maps or GPS devices. Safety "
                            "preparations involve packing a first aid kit, informing "
                            "someone of your itinerary, checking for wildlife "
                            "advisories, and understanding leave-no-trace principles "
                            "to minimize environmental impact. Finally, meal planning "
                            "should account for nutritional needs, weight constraints, "
                            "and proper food storage techniques to prevent attracting "
                            "animals while ensuring you have adequate sustenance for "
                            "the duration of your outdoor adventure."
                        )
                    },
                    # Example 2: Bicycle restoration
                    {
                        "role": "user",
                        "content": (
                            "Restoring a vintage bicycle requires patience, mechanical "
                            "skills, and attention to detail across several phases. "
                            "Begin by thoroughly cleaning the frame to assess its "
                            "condition, identifying rust spots, dents, or cracks that "
                            "need addressing. Disassemble all components systematically, "
                            "photographing each step to aid reassembly, and organize "
                            "hardware in labeled containers. The frame may need "
                            "sandblasting or chemical stripping to remove old paint, "
                            "followed by rust treatment, primer application, and fresh "
                            "paint or powder coating in your chosen color scheme. "
                            "Overhauling components involves rebuilding wheel hubs with "
                            "new bearings, replacing worn brake pads and cables, "
                            "servicing or replacing the bottom bracket and headset, and "
                            "cleaning or upgrading the drivetrain. Final assembly "
                            "requires careful adjustment of brakes, derailleurs, and "
                            "wheel alignment, followed by a test ride to ensure smooth "
                            "operation and safety before the restored bicycle is ready "
                            "for the road."
                        )
                    },
                    # Instruction for generating additional example
                    {
                        "role": "user",
                        "content": (
                            "Generate a paragraph of useful information for an "
                            "unrelated topic. Do not use em-dashes."
                        )
                    },
                    # Final summarization instruction
                    {
                        "role": "user",
                        "content": (
                            "Summarize each of the three paragraphs as individual "
                            "short phrases."
                        )
                    }
                ],
                max_completion_tokens=100,
                timeout=30.0,
            )
        except Exception as e:
            print(f"\nError calling API: {type(e).__name__}: {e}")
            sys.stdout.flush()
            continue

        # Display the AI-generated summary
        print("\nSummary:")
        try:
            summary = completion.choices[0].message.content
            print(summary)
        except (AttributeError, IndexError) as e:
            print(f"Error parsing response: {e}")
            print(completion)
        sys.stdout.flush()
    
    return 0


# Export main function for external use
__all__ = ["main"]