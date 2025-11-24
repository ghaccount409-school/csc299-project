"""
final_project: A JSON-backed task manager CLI with comprehensive task management features.

This module provides a complete task management system with support for:
- Creating, listing, searching, and deleting tasks
- Task linking and hierarchical subtasks
- Tag-based organization and filtering
- Task importance flagging
- Flexible sorting and filtering options
- Persistent JSON-based storage
- AI-powered task summarization (OpenAI integration)
- Personal Knowledge Management (PKM) system with note documents

Commands:
  Task Management:
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
  
  AI Features:
    ai-chat          - Interactive AI chat for task description summarization
    ai-summarize     - Summarize existing task(s) using AI (with optional update)
  
  Personal Knowledge Management (PKM):
    note-create      - Create a new note document
    note-list        - List all notes (with optional tag filtering)
    note-search      - Search notes by keyword in title or content
    note-show        - Display full note details with content
    note-edit        - Edit an existing note's title, content, or tags
    note-delete      - Delete a note
    note-link-note   - Link one note to another note
    note-link-task   - Link a note to a task
    note-export      - Export a note to markdown file
    note-export-all  - Export all notes to markdown files with index

PKM Features:
  - Markdown support in note content
  - Link notes together for knowledge graphs
  - Link notes to tasks for context
  - Tag-based organization
  - Full-text search across all notes
  - Export to markdown files for viewing/sharing
  - Separate storage from tasks (notes.json)

AI Features:
  - Interactive chat mode: Get AI-powered summaries for task descriptions
  - Summarize existing tasks: Process stored tasks through AI for concise summaries
  - Optional update mode: Add AI summaries directly to task notes
  - Type 'quit' in ai-chat to return to main menu

Data Storage:
  Default data file: tasks.json next to this script
  Default notes file: notes.json next to this script
  Use --data FLAG to specify a custom data file path
  Use --notes-data FLAG to specify a custom notes file path
  Data is stored in JSON format with automatic backup of corrupted files

Requirements:
  - OpenAI API key (OPENAI_API_KEY environment variable) for AI features
  - openai Python package for AI features (optional for basic task management)
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
DEFAULT_NOTES_FILENAME = "notes.json"


@dataclass
class Note:
    """Represents a note document in the PKM system.
    
    Attributes:
        id (str): Unique identifier for the note (8-char hex string or custom).
        title (str): The note's title.
        content (str): The note's content/body (supports markdown).
        created_at (str): Timestamp when note was created 
            (UTC format: YYYY-MM-DD HH:MM:SS UTC).
        updated_at (str): Timestamp when note was last updated.
        tags (List[str]): Tag strings for categorization.
        linked_notes (List[str]): Note IDs that this note links to.
        linked_tasks (List[str]): Task IDs that this note references.
    """
    id: str
    title: str
    content: str
    created_at: str
    updated_at: str
    tags: List[str] = field(default_factory=list)
    linked_notes: List[str] = field(default_factory=list)
    linked_tasks: List[str] = field(default_factory=list)


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
            print(f"      - [{lid}] view: python -m final_project show {lid}")
    
    # Display subtask count and view command if there are any
    if getattr(t, 'subtasks', None):
        subtask_count = len(t.subtasks)
        print(f"    {yellow}Subtasks:{reset} {subtask_count} subtask(s)")
        if subtask_count > 0:
            print(
                f"      To view subtasks: "
                f"python -m final_project show-subtasks {t.id}"
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


# =============================================================================
# Personal Knowledge Management (PKM) Functions
# =============================================================================

def notes_file_path(path: Optional[str] = None) -> Path:
    """Get the path to the notes data file.
    
    Args:
        path: Optional custom path to notes file. If not provided, defaults to notes.json
              in the same directory as this script.
    
    Returns:
        Path object pointing to the notes file location.
    """
    if path:
        return Path(path)
    return Path(__file__).parent.joinpath(DEFAULT_NOTES_FILENAME)


def load_notes(path: Optional[str] = None) -> List[Note]:
    """Load all notes from the data file.
    
    Args:
        path (Optional[str]): Custom path to notes file.
    
    Returns:
        List[Note]: List of all notes.
    """
    fpath = notes_file_path(path)
    if not fpath.exists():
        return []
    
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Note(**item) for item in data]
    except (json.JSONDecodeError, TypeError) as e:
        print(f"WARNING: Corrupted notes file. Backing up to {fpath}.bak", file=sys.stderr)
        fpath.rename(fpath.with_suffix(".json.bak"))
        return []


def save_notes(notes: List[Note], path: Optional[str] = None) -> None:
    """Save notes to the data file.
    
    Args:
        notes (List[Note]): List of notes to save.
        path (Optional[str]): Custom path to notes file.
    """
    fpath = notes_file_path(path)
    fpath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump([asdict(n) for n in notes], f, indent=2, ensure_ascii=False)


def note_id_exists(note_id: str, path: Optional[str] = None) -> bool:
    """Check if a note ID already exists.
    
    Args:
        note_id (str): The note ID to check.
        path (Optional[str]): Custom path to notes file.
    
    Returns:
        bool: True if ID exists, False otherwise.
    """
    notes = load_notes(path)
    return any(n.id == note_id for n in notes)


def create_note(title: str, content: str = "", tags: Optional[List[str]] = None,
                custom_id: Optional[str] = None, path: Optional[str] = None) -> Optional[Note]:
    """Create a new note.
    
    Args:
        title (str): Note title.
        content (str): Note content (markdown supported).
        tags (Optional[List[str]]): List of tags.
        custom_id (Optional[str]): Custom note ID.
        path (Optional[str]): Custom path to notes file.
    
    Returns:
        Optional[Note]: Created note or None if ID conflict.
    """
    if custom_id and note_id_exists(custom_id, path):
        print(f"ERROR: Note ID '{custom_id}' already exists.", file=sys.stderr)
        return None
    
    note_id = custom_id if custom_id else generate_short_id()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    note = Note(
        id=note_id,
        title=title,
        content=content,
        created_at=now,
        updated_at=now,
        tags=tags or [],
        linked_notes=[],
        linked_tasks=[]
    )
    
    notes = load_notes(path)
    notes.append(note)
    save_notes(notes, path)
    
    return note


def list_notes(path: Optional[str] = None, tag: Optional[str] = None) -> List[Note]:
    """List all notes, optionally filtered by tag.
    
    Args:
        path (Optional[str]): Custom path to notes file.
        tag (Optional[str]): Filter by tag.
    
    Returns:
        List[Note]: List of notes.
    """
    notes = load_notes(path)
    
    if tag:
        notes = [n for n in notes if tag in n.tags]
    
    return notes


def search_notes(query: str, path: Optional[str] = None) -> List[Note]:
    """Search notes by keyword in title or content.
    
    Args:
        query (str): Search query.
        path (Optional[str]): Custom path to notes file.
    
    Returns:
        List[Note]: Matching notes.
    """
    notes = load_notes(path)
    query_lower = query.lower()
    
    return [n for n in notes if query_lower in n.title.lower() or 
            query_lower in n.content.lower()]


def show_note(note_id: str, path: Optional[str] = None) -> None:
    """Display a note's full details.
    
    Args:
        note_id (str): Note ID to display.
        path (Optional[str]): Custom path to notes file.
    """
    notes = load_notes(path)
    note = next((n for n in notes if n.id == note_id), None)
    
    if not note:
        print(f"Note {note_id} not found.")
        return
    
    print(f"\n{'='*70}")
    print(f"Note: {note.title}")
    print(f"ID: {note.id}")
    print(f"Created: {note.created_at}")
    print(f"Updated: {note.updated_at}")
    
    if note.tags:
        print(f"Tags: {', '.join(note.tags)}")
    
    if note.linked_notes:
        print(f"Linked Notes: {', '.join(note.linked_notes)}")
    
    if note.linked_tasks:
        print(f"Linked Tasks: {', '.join(note.linked_tasks)}")
    
    print(f"\n{'-'*70}")
    print(note.content)
    print(f"{'='*70}\n")


def edit_note(note_id: str, title: Optional[str] = None, content: Optional[str] = None,
              tags: Optional[List[str]] = None, path: Optional[str] = None) -> bool:
    """Edit an existing note.
    
    Args:
        note_id (str): Note ID to edit.
        title (Optional[str]): New title.
        content (Optional[str]): New content.
        tags (Optional[List[str]]): New tags.
        path (Optional[str]): Custom path to notes file.
    
    Returns:
        bool: True if updated, False if note not found.
    """
    notes = load_notes(path)
    note = next((n for n in notes if n.id == note_id), None)
    
    if not note:
        return False
    
    if title is not None:
        note.title = title
    if content is not None:
        note.content = content
    if tags is not None:
        note.tags = tags
    
    note.updated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    save_notes(notes, path)
    
    return True


def link_note_to_note(source_id: str, target_id: str, path: Optional[str] = None) -> bool:
    """Link one note to another.
    
    Args:
        source_id (str): Source note ID.
        target_id (str): Target note ID to link to.
        path (Optional[str]): Custom path to notes file.
    
    Returns:
        bool: True if linked, False if either note not found.
    """
    notes = load_notes(path)
    source = next((n for n in notes if n.id == source_id), None)
    target = next((n for n in notes if n.id == target_id), None)
    
    if not source or not target:
        return False
    
    if target_id not in source.linked_notes:
        source.linked_notes.append(target_id)
        source.updated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        save_notes(notes, path)
    
    return True


def link_note_to_task(note_id: str, task_id: str, notes_path: Optional[str] = None,
                      tasks_path: Optional[str] = None) -> bool:
    """Link a note to a task.
    
    Args:
        note_id (str): Note ID.
        task_id (str): Task ID to link to.
        notes_path (Optional[str]): Custom path to notes file.
        tasks_path (Optional[str]): Custom path to tasks file.
    
    Returns:
        bool: True if linked, False if note or task not found.
    """
    notes = load_notes(notes_path)
    note = next((n for n in notes if n.id == note_id), None)
    
    if not note:
        return False
    
    # Verify task exists
    if not task_id_exists(task_id, tasks_path):
        return False
    
    if task_id not in note.linked_tasks:
        note.linked_tasks.append(task_id)
        note.updated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        save_notes(notes, notes_path)
    
    return True


def delete_note(note_id: str, path: Optional[str] = None) -> bool:
    """Delete a note.
    
    Args:
        note_id (str): Note ID to delete.
        path (Optional[str]): Custom path to notes file.
    
    Returns:
        bool: True if deleted, False if not found.
    """
    notes = load_notes(path)
    original_count = len(notes)
    notes = [n for n in notes if n.id != note_id]
    
    if len(notes) < original_count:
        save_notes(notes, path)
        
        # Remove references from other notes
        for note in notes:
            if note_id in note.linked_notes:
                note.linked_notes.remove(note_id)
        
        save_notes(notes, path)
        return True
    
    return False


def pretty_print_notes(notes: List[Note]) -> None:
    """Print notes in a readable format.
    
    Args:
        notes (List[Note]): List of notes to print.
    """
    if not notes:
        print("No notes found.")
        return
    
    for note in notes:
        tags_str = f" [{', '.join(note.tags)}]" if note.tags else ""
        links_str = ""
        if note.linked_notes:
            links_str += f" →{len(note.linked_notes)} notes"
        if note.linked_tasks:
            links_str += f" →{len(note.linked_tasks)} tasks"
        
        preview = note.content[:80] + "..." if len(note.content) > 80 else note.content
        preview = preview.replace("\n", " ")
        
        print(f"{note.id} | {note.title}{tags_str}{links_str}")
        if preview:
            print(f"  {preview}")


def export_note_to_markdown(note_id: str, output_path: Optional[str] = None,
                            notes_path: Optional[str] = None) -> bool:
    """Export a note to a markdown file.
    
    Args:
        note_id (str): Note ID to export.
        output_path (Optional[str]): Output file path. If None, uses note title as filename.
        notes_path (Optional[str]): Custom path to notes file.
    
    Returns:
        bool: True if exported successfully, False if note not found.
    """
    notes = load_notes(notes_path)
    note = next((n for n in notes if n.id == note_id), None)
    
    if not note:
        return False
    
    # Generate output path if not provided
    if output_path is None:
        # Sanitize title for filename
        safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in note.title)
        safe_title = safe_title.replace(' ', '_')
        output_path = f"{safe_title}.md"
    
    # Build markdown content
    md_content = f"# {note.title}\n\n"
    
    # Add metadata
    md_content += f"**ID:** {note.id}  \n"
    md_content += f"**Created:** {note.created_at}  \n"
    md_content += f"**Updated:** {note.updated_at}  \n"
    
    if note.tags:
        md_content += f"**Tags:** {', '.join(f'`{tag}`' for tag in note.tags)}  \n"
    
    md_content += "\n"
    
    # Add links section if there are any
    if note.linked_notes or note.linked_tasks:
        md_content += "## Links\n\n"
        
        if note.linked_notes:
            md_content += "**Linked Notes:**\n"
            for linked_id in note.linked_notes:
                linked_note = next((n for n in notes if n.id == linked_id), None)
                if linked_note:
                    md_content += f"- [{linked_note.title}](#{linked_id}) (`{linked_id}`)\n"
                else:
                    md_content += f"- `{linked_id}` (not found)\n"
            md_content += "\n"
        
        if note.linked_tasks:
            md_content += "**Linked Tasks:**\n"
            for task_id in note.linked_tasks:
                md_content += f"- Task `{task_id}`\n"
            md_content += "\n"
    
    # Add main content
    md_content += "## Content\n\n"
    md_content += note.content
    
    # Add separator
    md_content += "\n\n---\n"
    md_content += f"*Generated from note {note.id} on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*\n"
    
    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    return True


def export_all_notes_to_markdown(output_dir: str = "notes_export",
                                 notes_path: Optional[str] = None) -> int:
    """Export all notes to markdown files in a directory.
    
    Args:
        output_dir (str): Directory to export notes to.
        notes_path (Optional[str]): Custom path to notes file.
    
    Returns:
        int: Number of notes exported.
    """
    notes = load_notes(notes_path)
    
    if not notes:
        return 0
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create an index file
    index_content = "# Notes Index\n\n"
    index_content += f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
    index_content += f"Total notes: {len(notes)}\n\n"
    
    # Group by tags
    tags_dict = {}
    for note in notes:
        for tag in note.tags:
            if tag not in tags_dict:
                tags_dict[tag] = []
            tags_dict[tag].append(note)
    
    if tags_dict:
        index_content += "## Notes by Tag\n\n"
        for tag in sorted(tags_dict.keys()):
            index_content += f"### {tag}\n\n"
            for note in tags_dict[tag]:
                safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in note.title)
                safe_title = safe_title.replace(' ', '_')
                index_content += f"- [{note.title}]({safe_title}.md) (`{note.id}`)\n"
            index_content += "\n"
    
    index_content += "## All Notes\n\n"
    
    # Export each note
    count = 0
    for note in notes:
        safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in note.title)
        safe_title = safe_title.replace(' ', '_')
        file_path = output_path / f"{safe_title}.md"
        
        if export_note_to_markdown(note.id, str(file_path), notes_path):
            count += 1
            index_content += f"- [{note.title}]({safe_title}.md) - {note.created_at}\n"
            if note.tags:
                index_content += f"  - Tags: {', '.join(f'`{tag}`' for tag in note.tags)}\n"
    
    # Write index file
    with open(output_path / "INDEX.md", 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    return count


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
                print(f"      - [{lid}] view: python -m final_project show {lid}")
        
        # Display subtask count and command if present
        if getattr(t, 'subtasks', None):
            subtask_count = len(t.subtasks)
            if subtask_count > 0:
                print(
                    f"    {yellow}Subtasks:{reset} {subtask_count} subtask(s) - "
                    f"run: python -m final_project show-subtasks {t.id}"
                )
        
        print(f"    Created: {t.created_at}")


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser for the CLI.
    
    Configures all available commands and their arguments, including:
    Task Management:
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
    AI Features:
      - ai-chat: Interactive AI chat for summarization
      - ai-summarize: Summarize existing tasks with AI
    PKM (Personal Knowledge Management):
      - note-create: Create new note documents
      - note-list: List all notes
      - note-search: Search notes by keyword
      - note-show: Display full note details
      - note-edit: Edit note title, content, or tags
      - note-delete: Delete a note
      - note-link-note: Link notes together
      - note-link-task: Link notes to tasks
    
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

    p_ai_summarize = sub.add_parser("ai-summarize", help="Summarize existing task(s) using AI (requires openai package)")
    p_ai_summarize.add_argument("task_id", nargs="?", help="ID of specific task to summarize (optional, summarizes all if omitted)")
    p_ai_summarize.add_argument("--update", action="store_true", help="Update task notes with AI summary")

    # PKM (Personal Knowledge Management) Commands
    p_note_create = sub.add_parser("note-create", help="Create a new note")
    p_note_create.add_argument("title", help="Note title")
    p_note_create.add_argument("--content", help="Note content (markdown supported)")
    p_note_create.add_argument("--tag", action="append", help="Add a tag (can use multiple times)")
    p_note_create.add_argument("--id", dest="custom_id", help="Custom note ID")
    p_note_create.add_argument("--notes-data", help="Path to notes JSON file")

    p_note_list = sub.add_parser("note-list", help="List all notes")
    p_note_list.add_argument("--tag", help="Filter by tag")
    p_note_list.add_argument("--notes-data", help="Path to notes JSON file")

    p_note_search = sub.add_parser("note-search", help="Search notes by keyword")
    p_note_search.add_argument("query", help="Search query (searches title and content)")
    p_note_search.add_argument("--notes-data", help="Path to notes JSON file")

    p_note_show = sub.add_parser("note-show", help="Show full note details")
    p_note_show.add_argument("note_id", help="ID of note to display")
    p_note_show.add_argument("--notes-data", help="Path to notes JSON file")

    p_note_edit = sub.add_parser("note-edit", help="Edit an existing note")
    p_note_edit.add_argument("note_id", help="ID of note to edit")
    p_note_edit.add_argument("--title", help="New title")
    p_note_edit.add_argument("--content", help="New content")
    p_note_edit.add_argument("--tag", action="append", help="Set tags (replaces existing)")
    p_note_edit.add_argument("--notes-data", help="Path to notes JSON file")

    p_note_delete = sub.add_parser("note-delete", help="Delete a note")
    p_note_delete.add_argument("note_id", help="ID of note to delete")
    p_note_delete.add_argument("--notes-data", help="Path to notes JSON file")

    p_note_link_note = sub.add_parser("note-link-note", help="Link one note to another")
    p_note_link_note.add_argument("source_id", help="Source note ID")
    p_note_link_note.add_argument("target_id", help="Target note ID to link to")
    p_note_link_note.add_argument("--notes-data", help="Path to notes JSON file")

    p_note_link_task = sub.add_parser("note-link-task", help="Link a note to a task")
    p_note_link_task.add_argument("note_id", help="Note ID")
    p_note_link_task.add_argument("task_id", help="Task ID to link to")
    p_note_link_task.add_argument("--notes-data", help="Path to notes JSON file")
    p_note_link_task.add_argument("--data", dest="tasks_data", help="Path to tasks JSON file")

    p_note_export = sub.add_parser("note-export", help="Export a note to markdown file")
    p_note_export.add_argument("note_id", help="ID of note to export")
    p_note_export.add_argument("--output", help="Output file path (default: <note_title>.md)")
    p_note_export.add_argument("--notes-data", help="Path to notes JSON file")

    p_notes_export_all = sub.add_parser("note-export-all", help="Export all notes to markdown files")
    p_notes_export_all.add_argument("--output-dir", default="notes_export", help="Output directory (default: notes_export)")
    p_notes_export_all.add_argument("--notes-data", help="Path to notes JSON file")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for the final_project CLI.
    
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
        result = openai_chat_loop()
        # After exiting ai-chat, show help menu
        if result == 0:
            print("\n\033[94m" + "="*70 + "\033[0m")
            parser.print_help()
        return result

    if args.cmd == "ai-summarize":
        # Summarize existing task(s) with AI
        return ai_summarize_tasks(
            task_id=args.task_id,
            update=args.update,
            path=data_path
        )

    # PKM (Personal Knowledge Management) Commands
    if args.cmd == "note-create":
        notes_path = getattr(args, 'notes_data', None)
        note = create_note(
            title=args.title,
            content=args.content or "",
            tags=args.tag or [],
            custom_id=args.custom_id,
            path=notes_path
        )
        if note is None:
            return 2
        print(f"Created note {note.id}")
        return 0

    if args.cmd == "note-list":
        notes_path = getattr(args, 'notes_data', None)
        notes = list_notes(path=notes_path, tag=args.tag)
        pretty_print_notes(notes)
        return 0

    if args.cmd == "note-search":
        notes_path = getattr(args, 'notes_data', None)
        notes = search_notes(args.query, path=notes_path)
        pretty_print_notes(notes)
        return 0

    if args.cmd == "note-show":
        notes_path = getattr(args, 'notes_data', None)
        show_note(args.note_id, path=notes_path)
        return 0

    if args.cmd == "note-edit":
        notes_path = getattr(args, 'notes_data', None)
        ok = edit_note(
            note_id=args.note_id,
            title=args.title,
            content=args.content,
            tags=args.tag,
            path=notes_path
        )
        if ok:
            print(f"Updated note {args.note_id}")
            return 0
        else:
            print(f"Note {args.note_id} not found")
            return 2

    if args.cmd == "note-delete":
        notes_path = getattr(args, 'notes_data', None)
        ok = delete_note(args.note_id, path=notes_path)
        if ok:
            print(f"Deleted note {args.note_id}")
            return 0
        else:
            print(f"Note {args.note_id} not found")
            return 2

    if args.cmd == "note-link-note":
        notes_path = getattr(args, 'notes_data', None)
        ok = link_note_to_note(args.source_id, args.target_id, path=notes_path)
        if ok:
            print(f"Linked note {args.target_id} -> {args.source_id}")
            return 0
        else:
            print("One or both note IDs not found")
            return 2

    if args.cmd == "note-link-task":
        notes_path = getattr(args, 'notes_data', None)
        tasks_path = getattr(args, 'tasks_data', None)
        ok = link_note_to_task(args.note_id, args.task_id, notes_path, tasks_path)
        if ok:
            print(f"Linked task {args.task_id} to note {args.note_id}")
            return 0
        else:
            print("Note or task not found")
            return 2

    if args.cmd == "note-export":
        notes_path = getattr(args, 'notes_data', None)
        output_path = getattr(args, 'output', None)
        ok = export_note_to_markdown(args.note_id, output_path, notes_path)
        if ok:
            if output_path:
                print(f"Exported note {args.note_id} to {output_path}")
            else:
                print(f"Exported note {args.note_id} to markdown file")
            return 0
        else:
            print(f"Note {args.note_id} not found")
            return 2

    if args.cmd == "note-export-all":
        notes_path = getattr(args, 'notes_data', None)
        output_dir = args.output_dir
        count = export_all_notes_to_markdown(output_dir, notes_path)
        print(f"Exported {count} note(s) to {output_dir}/")
        print(f"Index file created at {output_dir}/INDEX.md")
        return 0

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


def _get_ai_summary(text: str, client) -> Optional[str]:
    """Get AI summary for a given text using OpenAI.
    
    Args:
        text (str): Text to summarize.
        client: OpenAI client instance.
    
    Returns:
        Optional[str]: Summary text or None if error occurs.
    """
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": DEVELOPER_ROLE},
                {
                    "role": "user",
                    "content": f"Summarize this task as a short phrase: {text}"
                }
            ],
            max_completion_tokens=50,
            timeout=30.0,
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error getting AI summary: {type(e).__name__}: {e}", file=sys.stderr)
        return None


def ai_summarize_tasks(
    task_id: Optional[str] = None,
    update: bool = False,
    path: Optional[str] = None
) -> int:
    """Summarize existing task(s) using OpenAI.
    
    Args:
        task_id (Optional[str]): ID of specific task to summarize. If None,
            summarizes all tasks.
        update (bool): If True, update task notes with the AI summary.
        path (Optional[str]): Path to data file.
    
    Returns:
        int: Exit code (0 for success, 1 for error).
    """
    # Import OpenAI only when this function is called
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
    
    # Load tasks
    tasks = load_tasks(path)
    
    if not tasks:
        print("No tasks found.")
        return 0
    
    # Filter to specific task if requested
    if task_id:
        task = find_task(task_id, tasks)
        if not task:
            print(f"Task {task_id} not found.")
            return 2
        tasks_to_summarize = [task]
    else:
        tasks_to_summarize = tasks
    
    # Summarize each task
    updated_count = 0
    for task in tasks_to_summarize:
        # Create description from task title and notes
        if task.notes:
            description = f"{task.title}. {task.notes}"
        else:
            description = task.title
        
        print(f"\nTask [{task.id}]: {task.title}")
        print(f"Original: {description}")
        print("Generating summary...", end=" ", flush=True)
        
        summary = _get_ai_summary(description, client)
        
        if summary:
            print(f"\nSummary: {summary}")
            
            if update:
                # Update task notes with summary (append to existing notes)
                if task.notes:
                    task.notes = f"{task.notes}\n\nAI Summary: {summary}"
                else:
                    task.notes = f"AI Summary: {summary}"
                updated_count += 1
        else:
            print("Failed to generate summary.")
    
    # Save updated tasks if requested
    if update and updated_count > 0:
        save_tasks(tasks, path)
        print(f"\n✓ Updated {updated_count} task(s) with AI summaries.")
    
    return 0


def openai_chat_loop() -> int:
    """Interactive AI chat loop for task description summarization.
    
    Prompts user for task descriptions and uses GPT-4o-mini to generate
    concise summaries. User can type 'quit' to return to the main menu,
    which displays the command help page.
    
    Returns:
        int: Exit code (0 for success/quit, 1 for error)
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
            print("Returning to main menu...")
            return 0
        
        if not task_description:
            print("Please enter a task description.")
            continue

        print("Processing... (this may take a few seconds)")
        sys.stdout.flush()
        
        try:
            # Call OpenAI API to summarize the user's task description
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