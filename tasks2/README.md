# Task Manager CLI (prototype_pkms.py)

A small, single-file command-line task manager implemented in `prototype_pkms.py`.
It stores tasks as JSON and supports adding, listing, searching tasks, and linking tasks together.

## Features

- Add tasks with optional notes, due date, and tags
- **Auto-generated short 8-character task IDs** for easy linking and reference
- **Custom task IDs** via `--id` flag (must be unique)
- List tasks (optionally filtered by tag)
- Search by keyword in title or notes
- **Search tasks by tags** with AND/OR logic
- **List all tags** with counts
- **Link tasks together** and view linked relationships
- Show individual task details with linked tasks
- Human-friendly `created_at` format (YYYY-MM-DD HH:MM:SS UTC)
- Default JSON data file: `tasks.json` next to `prototype_pkms.py` (override with `--data`)

## Requirements

- Python 3.8 or newer
- Works cross-platform; examples below use PowerShell on Windows

## Quick start

From the repository root (where `prototype_pkms.py` lives):

### Add a task (auto-generated short ID)

```powershell
python prototype_pkms.py add "Buy milk" --notes "2 litres" --due "2025-11-11" --tag home --tag shopping
```

This creates a task with an auto-generated 8-character ID like `a1b2c3d4`.

### Add a task with custom ID

```powershell
python prototype_pkms.py add "Buy milk" --id groceries --notes "2 litres"
python prototype_pkms.py add "Study" --id study-math
```

You can also mark a task as important when adding it with --important:

```powershell
python prototype_pkms.py add "Pay taxes" --important
```

Custom IDs must be unique; attempting to reuse an ID will fail with an error.

### List tasks

```powershell
python prototype_pkms.py list
python prototype_pkms.py list --tag shopping
```

You can also sort tasks with the `--sort-by` option:

```powershell
# Sort by due date (ascending, tasks without due dates go to end)
python prototype_pkms.py list --sort-by due

# Sort by creation date (descending/newest first)
python prototype_pkms.py list --sort-by created --reverse

# Sort by title alphabetically
python prototype_pkms.py list --sort-by title

# Sort by task ID
python prototype_pkms.py list --sort-by id --reverse

# Combine sorting with tag filtering
python prototype_pkms.py list --tag shopping --sort-by due
```

The `--sort-by` option accepts: `due`, `created`, `title`, or `id` (default is `created`).
The `--reverse` flag reverses the sort order (descending instead of ascending).

### Search tasks

```powershell
python prototype_pkms.py search milk
```

### Show a task

```powershell
python prototype_pkms.py show a1b2c3d4
python prototype_pkms.py show groceries
```

Shows full task details including linked tasks.

### Link tasks

```powershell
python prototype_pkms.py link a1b2c3d4 xyz1mnop
python prototype_pkms.py link study-math study-physics
```

Links the target task to the source task. When you list or show the source task, linked tasks are displayed with view commands.

### List all tags

```powershell
python prototype_pkms.py tags
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
python prototype_pkms.py important
```

You can also mark or unmark a specific task as important by ID:

```powershell
# mark by id
python prototype_pkms.py mark-important <task-id>

# unmark by id
python prototype_pkms.py unmark-important <task-id>
```

When a task is displayed and marked important the listing will include the label `Important:` printed in yellow (ANSI). On terminals that do not support ANSI colors you will still see the word "Important:" but without color.

### Search by tags

```powershell
# Find tasks with ANY of the tags (default)
python prototype_pkms.py search-tags home work

# Find tasks with ALL of the tags
python prototype_pkms.py search-tags home urgent --all
```

### Use a custom data file

```powershell
python prototype_pkms.py --data C:\path\to\my_tasks.json add "Call Alice"
python prototype_pkms.py --data C:\path\to\my_tasks.json list
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
  "important": true
}
```

- `id`: Auto-generated 8-character hex ID or custom user-defined string (must be unique)
- `title`: Task title
- `notes`: Optional notes
- `created_at`: Human-friendly timestamp (YYYY-MM-DD HH:MM:SS UTC)
- `due`: Optional due date
- `tags`: List of optional tags
- `links`: List of IDs of linked tasks

If the data file is missing it will be created automatically. If the file is corrupted (invalid JSON), the program will attempt to back it up to a `*.bak` file and continue with an empty task list.

## Running tests

Unit tests are provided under the `tests/` directory. Run them with:

```powershell
python -m unittest discover -v
```

Or run the specific test module from the repo root:

```powershell
python -m unittest tasks2.tests.test_prototype_pkms -v
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

If you see import errors like `Import "prototype_pkms" could not be resolved`, make sure you run the command from the repository root so Python can import the module alongside `prototype_pkms.py`.

## Development notes

- Task IDs: By default, short 8-character hex IDs are auto-generated. Users can also provide custom IDs via `--id` (must be unique).
- Timestamps: Created times are stored in human-friendly format (YYYY-MM-DD HH:MM:SS UTC) for easy readability.
- Tags: Tasks support multiple tags. Use `tags` to list all tags, and `search-tags` to find tasks by tag(s) with AND/OR logic.
- Linking: Tasks can be linked to create relationships. When displaying a task, linked tasks are shown with commands to view them.
- The program exposes core functions (`add_task`, `list_tasks`, `search_tasks`, `search_tasks_by_tags`, `list_all_tags`, `add_link`, `show_task`) so it can be imported and used programmatically.
- Important flag: Tasks can be marked important (`important` field). Use `--important` when adding or the `mark-important` / `unmark-important` commands to toggle. Important tasks are highlighted when displayed.
- Sorting: The `list` command supports sorting by due date, creation time, title, or task ID with optional reverse order. When sorting by due date, tasks without a due date are placed at the end.
 - The program exposes core functions (`add_task`, `list_tasks`, `search_tasks`, `search_tasks_by_tags`, `list_all_tags`, `add_link`, `show_task`, `sort_tasks`) so it can be imported and used programmatically.
- Future enhancements could include: removing tasks, marking tasks as completed, JSON schema validation, task relationships beyond simple links, and interactive mode features.

## License / attribution

This is a small example created for a classroom project. Feel free to reuse and adapt.

