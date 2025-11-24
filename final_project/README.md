# Task Manager CLI with Personal Knowledge Management (PKM)

A comprehensive command-line task manager and knowledge management system. The implementation can be found in:
- **Primary module**: `src/final_project/__init__.py` (full implementation)
- **Tests**: `tests/test_final_project.py` (comprehensive pytest suite)

It stores tasks and notes as JSON and supports:
- Task management: adding, listing, searching, linking, subtasks, importance marking, and deletion
- Personal Knowledge Management (PKM): create, edit, link, and export notes as markdown
- AI-powered features: task summarization and interactive chat (requires OpenAI API key)

## Features

### Task Management
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

### Personal Knowledge Management (PKM)
- **Create notes** with title, content (supports markdown), and tags
- **Edit notes** - modify title, content, or tags
- **Link notes together** to build a knowledge graph
- **Link notes to tasks** for contextual reference
- **Search notes** by keyword in title or content
- **List notes** with optional tag filtering
- **Export notes** to markdown files with metadata and links
- **Batch export all notes** with auto-generated INDEX.md grouped by tags
- Separate storage: `notes.json` (override with `--notes-data`)

### AI Features (Optional - requires OpenAI API key)
- **Interactive AI chat** for task description summarization
- **AI-powered task summarization** with optional auto-update to task notes
- Type 'quit' in ai-chat to return to main menu

## Requirements

- Python 3.8 or newer
- Works cross-platform; examples below use PowerShell on Windows
- **OpenAI API key** (optional - only for AI features): Set `OPENAI_API_KEY` environment variable
- **openai Python package** (optional - only for AI features): `pip install openai`

## Quick start

From the repository root (where the module is installed):

### Task Management Examples

#### Add a task (auto-generated short ID)

```powershell
python -m final_project add "Buy milk" --notes "2 litres" --due "2025-11-11" --tag home --tag shopping
```

This creates a task with an auto-generated 8-character ID like `a1b2c3d4`.

#### Add a task with custom ID

```powershell
python -m final_project add "Buy milk" --id groceries --notes "2 litres"
python -m final_project add "Study" --id study-math
```

You can also mark a task as important when adding it with --important:

```powershell
python -m final_project add "Pay taxes" --important
```

Custom IDs must be unique; attempting to reuse an ID will fail with an error.

#### List tasks

```powershell
python -m final_project list
python -m final_project list --tag shopping
```

You can also sort tasks with the `--sort-by` option:

```powershell
# Sort by due date (ascending, tasks without due dates always appear at the end)
python -m final_project list --sort-by due

# Sort by creation date (descending/newest first)
python -m final_project list --sort-by created --reverse

# Sort by title alphabetically
python -m final_project list --sort-by title

# Sort by task ID
python -m final_project list --sort-by id --reverse

# Combine sorting with tag filtering
python -m final_project list --tag shopping --sort-by due
```

The `--sort-by` option accepts: `due`, `created`, `title`, or `id` (default is `created`).
The `--reverse` flag reverses the sort order (descending instead of ascending).

#### Search tasks

```powershell
python -m final_project search milk
```

#### Show a task

```powershell
python -m final_project show a1b2c3d4
python -m final_project show groceries
```

Shows full task details including linked tasks.

#### Link tasks

```powershell
python -m final_project link a1b2c3d4 xyz1mnop
python -m final_project link study-math study-physics
```

Links the target task to the source task. When you list or show the source task, linked tasks are displayed with view commands.

#### List all tags

```powershell
python -m final_project tags
```

Output shows all tags with their counts:
```
Tags:
  home: 3 task(s)
  shopping: 2 task(s)
  urgent: 1 task(s)
```

#### Important tasks

You can list tasks that have been marked important with the `important` command:

```powershell
python -m final_project important
```

You can also mark or unmark a specific task as important by ID:

```powershell
# mark by id
python -m final_project mark-important <task-id>

# unmark by id
python -m final_project unmark-important <task-id>
```

When a task is displayed and marked important the listing will include the label `Important:` printed in yellow (ANSI). On terminals that do not support ANSI colors you will still see the word "Important:" but without color.

#### Subtasks

You can organize tasks hierarchically by linking existing tasks as subtasks to parent tasks:

```powershell
# Link an existing task as a subtask to a parent task
python -m final_project add-subtask <parent-id> <subtask-id>

# View all subtasks for a parent task
python -m final_project show-subtasks <parent-id>
```

When you list or show a parent task that has subtasks, you'll see a hint about how to view them. The `Subtasks:` label is displayed in orange with the count of subtasks.

Example workflow:
```powershell
# Create tasks
python -m final_project add "Plan project" --id plan-proj
python -m final_project add "Research requirements" --id research
python -m final_project add "Create proposal" --id proposal
python -m final_project add "Schedule meeting" --id schedule

# Link them as subtasks
python -m final_project add-subtask plan-proj research
python -m final_project add-subtask plan-proj proposal
python -m final_project add-subtask plan-proj schedule

# Show the parent task (will display subtask count and hint)
python -m final_project show plan-proj

# View all subtasks
python -m final_project show-subtasks plan-proj
```

Only existing tasks can be added as subtasks. Both the parent task and the subtask must already exist.

#### Delete tasks

You can delete tasks using the `delete` command:

```powershell
python -m final_project delete <task-id>
```

When deleting a task that has subtasks, you will be prompted to choose:
- **Yes** (`y`): Delete the task and all its subtasks
- **No** (`n`): Delete the task but keep the subtasks as regular (independent) tasks
- **Cancel** (`c`): Abort the deletion

Example workflow:
```powershell
# Create a parent task with subtasks
python -m final_project add "Project" --id proj
python -m final_project add "Phase 1" --id phase1
python -m final_project add "Phase 2" --id phase2
python -m final_project add-subtask proj phase1
python -m final_project add-subtask proj phase2

# Delete with prompt (if task has subtasks)
python -m final_project delete proj
# > Task 'Project' has 2 subtask(s). Delete them too? (yes/no/cancel): 

# If you answer "yes": both proj, phase1, and phase2 are deleted
# If you answer "no": proj is deleted, but phase1 and phase2 become independent tasks
```

You can also force the deletion behavior programmatically by using the delete function with `delete_subtasks=True` or `delete_subtasks=False`.

#### Search by tags

```powershell
# Find tasks with ANY of the tags (default)
python -m final_project search-tags home work

# Find tasks with ALL of the tags
python -m final_project search-tags home urgent --all
```

### Personal Knowledge Management (PKM) Examples

#### Create a note

```powershell
python -m final_project note-create "Meeting Notes" --content "Discussed project timeline" --tag work --tag meetings
```

#### List notes

```powershell
python -m final_project note-list
python -m final_project note-list --tag work
```

#### Search notes

```powershell
python -m final_project note-search timeline
```

#### Show a note

```powershell
python -m final_project note-show <note-id>
```

#### Edit a note

```powershell
# Edit title
python -m final_project note-edit <note-id> --title "Updated Meeting Notes"

# Edit content
python -m final_project note-edit <note-id> --content "New content here"

# Add/update tags
python -m final_project note-edit <note-id> --tag project --tag important
```

#### Link notes together

```powershell
python -m final_project note-link-note <source-note-id> <target-note-id>
```

#### Link note to task

```powershell
python -m final_project note-link-task <note-id> <task-id>
```

#### Export note to markdown

```powershell
# Export with auto-generated filename
python -m final_project note-export <note-id>

# Export with custom filename
python -m final_project note-export <note-id> --output my_note.md
```

#### Export all notes to markdown

```powershell
# Export to default directory (notes_export/)
python -m final_project note-export-all

# Export to custom directory
python -m final_project note-export-all --output-dir my_notes
```

This creates individual markdown files for each note plus an `INDEX.md` file with links organized by tags.

#### Delete a note

```powershell
python -m final_project note-delete <note-id>
```

### AI Features Examples (requires OpenAI API key)

#### Interactive AI chat

```powershell
python -m final_project ai-chat
```

Type task descriptions and get AI-powered summaries. Type 'quit' to return to main menu.

#### Summarize existing tasks

```powershell
# Summarize a specific task
python -m final_project ai-summarize <task-id>

# Summarize and update task notes automatically
python -m final_project ai-summarize <task-id> --update
```

### Use custom data files

```powershell
# Custom task data file
python -m final_project --data C:\path\to\my_tasks.json add "Call Alice"
python -m final_project --data C:\path\to\my_tasks.json list

# Custom notes data file
python -m final_project note-create "My Note" --notes-data C:\path\to\my_notes.json
python -m final_project note-list --notes-data C:\path\to\my_notes.json
```

## Data file format

### Tasks (tasks.json)

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

### Notes (notes.json)

Notes are stored as a JSON array where each note is an object like:

```json
{
  "id": "n1a2b3c4",
  "title": "Meeting Notes",
  "content": "# Agenda\n\n- Project timeline\n- Budget review",
  "created_at": "2025-11-15 14:23:01 UTC",
  "updated_at": "2025-11-16 10:15:30 UTC",
  "tags": ["work", "meetings"],
  "linked_notes": ["n5d6e7f8"],
  "linked_tasks": ["a1b2c3d4"]
}
```

- `id`: Auto-generated note ID with 'n' prefix
- `title`: Note title
- `content`: Note content (supports markdown)
- `created_at`: Creation timestamp (YYYY-MM-DD HH:MM:SS UTC)
- `updated_at`: Last update timestamp (YYYY-MM-DD HH:MM:SS UTC)
- `tags`: List of optional tags
- `linked_notes`: List of IDs of other linked notes
- `linked_tasks`: List of IDs of linked tasks

If the data files are missing they will be created automatically. If a file is corrupted (invalid JSON), the program will attempt to back it up to a `*.bak` file and continue with an empty list.

## Running tests

Tests are provided under the `tests/` directory using the **pytest framework** with comprehensive unit tests. Run them with:

```powershell
pytest tests/
```

Or run the specific test module:

```powershell
pytest tests/test_final_project.py -v
```

To run a specific test:

```powershell
pytest tests/test_final_project.py::test_add_and_list_and_search -v
```

Tests cover:

**Task Management:**
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

**PKM (Personal Knowledge Management):**
- Note creation with title, content, and tags
- Note listing and filtering by tags
- Note searching by keyword
- Note editing (title, content, tags)
- Note deletion
- Linking notes to other notes
- Linking notes to tasks
- Note persistence and data integrity
- Markdown export for individual notes
- Batch export of all notes with INDEX.md generation
- Export with linked notes and tasks
- Special character handling in filenames

**AI Features:**
- AI chat loop functionality (when OpenAI API is available)
- Task summarization
- Quit-to-menu behavior in ai-chat

The test suite uses pytest fixtures for managing temporary test data files, ensuring clean isolation between tests.

## Development notes

- **Module structure**: The application is organized as a Python package in `src/final_project/` with full implementation in `__init__.py`.
- **Task IDs**: By default, short 8-character hex IDs are auto-generated. Users can also provide custom IDs via `--id` (must be unique).
- **Note IDs**: Auto-generated with 'n' prefix to distinguish from task IDs.
- **Timestamps**: Created/updated times are stored in human-friendly format (YYYY-MM-DD HH:MM:SS UTC) for easy readability.
- **Tags**: Both tasks and notes support multiple tags. Use `tags` to list all task tags, and `search-tags` to find tasks by tag(s) with AND/OR logic. Notes support tag filtering in `note-list`.
- **Linking**: Tasks can be linked to other tasks. Notes can be linked to other notes or to tasks, creating a knowledge graph.
- **Subtasks**: Organize tasks hierarchically by linking existing tasks as subtasks. Both parent and subtask must be existing tasks. Parent tasks display a count of subtasks with a hint to view them. The same task can be a subtask of multiple parents.
- **Important flag**: Tasks can be marked important (`important` field). Use `--important` when adding or the `mark-important` / `unmark-important` commands to toggle. Important tasks are highlighted when displayed.
- **Sorting**: The `list` command supports sorting by due date, creation time, title, or task ID with optional reverse order. When sorting by due date, tasks without a due date (or with invalid format) are placed at the end and remain there even when using `--reverse`.
- **Deletion**: The `delete` command removes tasks. If a task has subtasks, the user is prompted to choose whether to delete the subtasks along with the parent or keep them as independent tasks. The behavior can be controlled programmatically with the `delete_subtasks` parameter. Notes can be deleted with `note-delete`.
- **Markdown Support**: Note content supports full markdown syntax including headers, lists, code blocks, bold, italic, etc.
- **Markdown Export**: Notes can be exported to `.md` files with metadata (ID, timestamps, tags) and links section showing linked notes/tasks. Batch export creates an `INDEX.md` with notes grouped by tags.
- **AI Integration**: Optional AI features use OpenAI's API (gpt-4o-mini model). The `ai-chat` command provides an interactive loop that returns to the main menu when 'quit' is typed.
- **Core functions exposed**: All task management functions (`add_task`, `list_tasks`, `search_tasks`, etc.) and PKM functions (`create_note`, `edit_note`, `link_note_to_note`, `export_note_to_markdown`, etc.) are exposed for programmatic use and testing.
- **Future enhancements**: Could include: task completion/done state, recurring tasks, JSON schema validation, priority levels, time tracking, note versioning, bi-directional linking UI, graph visualization, and interactive mode features.

## License / attribution

This is a small example created for a classroom project. Feel free to reuse and adapt.

