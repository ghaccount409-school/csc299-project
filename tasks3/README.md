# Task Manager CLI (PKMS - Personal Knowledge Management System)

A comprehensive command-line task manager system. The implementation can be found in:
- **Primary module**: `src/tasks3/__init__.py` (full implementation)
- **Tests**: `tests/test_pycache_pkms.py` (comprehensive pytest suite)

It stores tasks as JSON and supports adding, listing, searching tasks, linking tasks together, organizing with subtasks, and more.

## Features

- Add tasks with optional notes, due date, and tags
- **Auto-generated short 8-character task IDs** for easy linking and reference
- **Custom task IDs** via `--id` flag (must be unique)
- List tasks (optionally filtered by tag)
- Search by keyword in title or notes
- **Search tasks by tags** with AND/OR logic
- **List all tags** with counts
- **Link tasks together** and view linked relationships
- **Organize tasks hierarchically with subtasks** - link existing tasks as subtasks to parent tasks
- Show individual task details with linked tasks and subtask counts
- **Mark tasks as important** with visual highlighting (yellow) - includes mark/unmark commands
- Task titles are highlighted in green in terminal listings for easier scanning
- **Delete tasks** with optional handling of subtasks (delete them or orphan them)
- **Sort tasks** by due date, creation time, title, or ID with ascending/descending options
- Human-friendly `created_at` format (YYYY-MM-DD HH:MM:SS UTC)
- Default JSON data file: `tasks.json` next to the module (override with `--data`)

## Requirements

- Python 3.8 or newer
- Works cross-platform; examples below use PowerShell on Windows

## Quick start

From the repository root (where the module is installed):

### Add a task (auto-generated short ID)

```powershell
python -m tasks3 add "Buy milk" --notes "2 litres" --due "2025-11-11" --tag home --tag shopping
```

This creates a task with an auto-generated 8-character ID like `a1b2c3d4`.

### Add a task with custom ID

```powershell
python -m tasks3 add "Buy milk" --id groceries --notes "2 litres"
python -m tasks3 add "Study" --id study-math
```

You can also mark a task as important when adding it with --important:

```powershell
python -m tasks3 add "Pay taxes" --important
```

Custom IDs must be unique; attempting to reuse an ID will fail with an error.

### List tasks

```powershell
python -m tasks3 list
python -m tasks3 list --tag shopping
```

You can also sort tasks with the `--sort-by` option:

```powershell
# Sort by due date (ascending, tasks without due dates always appear at the end)
python -m tasks3 list --sort-by due

# Sort by creation date (descending/newest first)
python -m tasks3 list --sort-by created --reverse

# Sort by title alphabetically
python -m tasks3 list --sort-by title

# Sort by task ID
python -m tasks3 list --sort-by id --reverse

# Combine sorting with tag filtering
python -m tasks3 list --tag shopping --sort-by due
```

The `--sort-by` option accepts: `due`, `created`, `title`, or `id` (default is `created`).
The `--reverse` flag reverses the sort order (descending instead of ascending).

### Search tasks

```powershell
python -m tasks3 search milk
```

### Show a task

```powershell
python -m tasks3 show a1b2c3d4
python -m tasks3 show groceries
```

Shows full task details including linked tasks.

### Link tasks

```powershell
python -m tasks3 link a1b2c3d4 xyz1mnop
python -m tasks3 link study-math study-physics
```

Links the target task to the source task. When you list or show the source task, linked tasks are displayed with view commands.

### List all tags

```powershell
python -m tasks3 tags
```

Output shows all tags with their counts:
```
Tags:
  home: 3 task(s)
  shopping: 2 task(s)
  urgent: 1 task(s)
```

### Important tasks

You can list tasks that have been marked important with the `important` command:

```powershell
python -m tasks3 important
```

You can also mark or unmark a specific task as important by ID:

```powershell
# mark by id
python -m tasks3 mark-important <task-id>

# unmark by id
python -m tasks3 unmark-important <task-id>
```

When a task is displayed and marked important the listing will include the label `Important:` printed in yellow (ANSI). On terminals that do not support ANSI colors you will still see the word "Important:" but without color.

### Subtasks

You can organize tasks hierarchically by linking existing tasks as subtasks to parent tasks:

```powershell
# Link an existing task as a subtask to a parent task
python -m tasks3 add-subtask <parent-id> <subtask-id>

# View all subtasks for a parent task
python -m tasks3 show-subtasks <parent-id>
```

When you list or show a parent task that has subtasks, you'll see a hint about how to view them. The `Subtasks:` label is displayed in orange with the count of subtasks.

Example workflow:
```powershell
# Create tasks
python -m tasks3 add "Plan project" --id plan-proj
python -m tasks3 add "Research requirements" --id research
python -m tasks3 add "Create proposal" --id proposal
python -m tasks3 add "Schedule meeting" --id schedule

# Link them as subtasks
python -m tasks3 add-subtask plan-proj research
python -m tasks3 add-subtask plan-proj proposal
python -m tasks3 add-subtask plan-proj schedule

# Show the parent task (will display subtask count and hint)
python -m tasks3 show plan-proj

# View all subtasks
python -m tasks3 show-subtasks plan-proj
```

Only existing tasks can be added as subtasks. Both the parent task and the subtask must already exist.

### Delete tasks

You can delete tasks using the `delete` command:

```powershell
python -m tasks3 delete <task-id>
```

When deleting a task that has subtasks, you will be prompted to choose:
- **Yes** (`y`): Delete the task and all its subtasks
- **No** (`n`): Delete the task but keep the subtasks as regular (independent) tasks
- **Cancel** (`c`): Abort the deletion

Example workflow:
```powershell
# Create a parent task with subtasks
python -m tasks3 add "Project" --id proj
python -m tasks3 add "Phase 1" --id phase1
python -m tasks3 add "Phase 2" --id phase2
python -m tasks3 add-subtask proj phase1
python -m tasks3 add-subtask proj phase2

# Delete with prompt (if task has subtasks)
python -m tasks3 delete proj
# > Task 'Project' has 2 subtask(s). Delete them too? (yes/no/cancel): 

# If you answer "yes": both proj, phase1, and phase2 are deleted
# If you answer "no": proj is deleted, but phase1 and phase2 become independent tasks
```

You can also force the deletion behavior programmatically by using the delete function with `delete_subtasks=True` or `delete_subtasks=False`.

### Search by tags

```powershell
# Find tasks with ANY of the tags (default)
python -m tasks3 search-tags home work

# Find tasks with ALL of the tags
python -m tasks3 search-tags home urgent --all
```

### Use a custom data file

```powershell
python -m tasks3 --data C:\path\to\my_tasks.json add "Call Alice"
python -m tasks3 --data C:\path\to\my_tasks.json list
```

## Data file format

Tasks are stored as a JSON array where each task is an object like:

```json
{
  "id": "a1b2c3d4",
  "title": "Buy milk",
  "notes": "2 litres",
  "created_at": "2025-11-15 14:23:01 UTC",
  "due": "2025-11-11",
  "tags": ["home", "shopping"],
  "links": ["xyz1mnop"],
  "important": true,
  "subtasks": ["b2c3d4e5", "c3d4e5f6"]
}
```

- `id`: Auto-generated 8-character hex ID or custom user-defined string (must be unique)
- `title`: Task title
- `notes`: Optional notes
- `created_at`: Human-friendly timestamp (YYYY-MM-DD HH:MM:SS UTC)
- `due`: Optional due date (YYYY-MM-DD format)
- `tags`: List of optional tags
- `links`: List of IDs of linked tasks
- `important`: Boolean indicating if task is marked as important
- `subtasks`: List of IDs of subtasks (children) of this task

If the data file is missing it will be created automatically. If the file is corrupted (invalid JSON), the program will attempt to back it up to a `*.bak` file and continue with an empty task list.

## Running tests

Tests are provided under the `tests/` directory using the **pytest framework** with comprehensive unit tests. Run them with:

```powershell
pytest tests/
```

Or run the specific test module:

```powershell
pytest tests/test_pycache_pkms.py -v
```

To run a specific test:

```powershell
pytest tests/test_pycache_pkms.py::test_add_and_list_and_search -v
```

Tests cover:
- Task addition, listing, and searching
- Short ID auto-generation (8-char hex format)
- Custom ID creation and uniqueness checking
- Task linking and showing linked relationships
- Data file persistence and corruption handling
- Human-friendly created timestamp format validation (YYYY-MM-DD HH:MM:SS UTC)
- Tag searching with ANY/ALL logic
- Tag listing and counting
- Important flag marking and unmarking
- Task sorting by due date, creation time, title, and ID with reverse order
- Subtask creation, listing, and parent-child relationships
- Linking existing tasks as subtasks and avoiding duplicates
- Task deletion with and without subtasks

The test suite uses pytest fixtures for managing temporary test data files, ensuring clean isolation between tests.

## Development notes

- **Module structure**: The application is organized as a Python package in `src/tasks3/` with full implementation in `__init__.py`.
- **Task IDs**: By default, short 8-character hex IDs are auto-generated. Users can also provide custom IDs via `--id` (must be unique).
- **Timestamps**: Created times are stored in human-friendly format (YYYY-MM-DD HH:MM:SS UTC) for easy readability.
- **Tags**: Tasks support multiple tags. Use `tags` to list all tags, and `search-tags` to find tasks by tag(s) with AND/OR logic.
- **Linking**: Tasks can be linked to create relationships. When displaying a task, linked tasks are shown with commands to view them.
- **Subtasks**: Organize tasks hierarchically by linking existing tasks as subtasks. Both parent and subtask must be existing tasks. Parent tasks display a count of subtasks with a hint to view them. The same task can be a subtask of multiple parents.
- **Important flag**: Tasks can be marked important (`important` field). Use `--important` when adding or the `mark-important` / `unmark-important` commands to toggle. Important tasks are highlighted when displayed.
- **Sorting**: The `list` command supports sorting by due date, creation time, title, or task ID with optional reverse order. When sorting by due date, tasks without a due date (or with invalid format) are placed at the end and remain there even when using `--reverse`.
- **Deletion**: The `delete` command removes tasks. If a task has subtasks, the user is prompted to choose whether to delete the subtasks along with the parent or keep them as independent tasks. The behavior can be controlled programmatically with the `delete_subtasks` parameter.
- **Core functions exposed**: `add_task`, `list_tasks`, `search_tasks`, `search_tasks_by_tags`, `list_all_tags`, `add_link`, `show_task`, `sort_tasks`, `add_subtask`, `show_subtasks`, `delete_task`, `mark_important`, `unmark_important` allow programmatic use and testing.
- **Future enhancements**: Could include: task completion/done state, recurring tasks, JSON schema validation, task completion tracking, priority levels, time tracking, and interactive mode features.

## License / attribution

This is a small example created for a classroom project. Feel free to reuse and adapt.

