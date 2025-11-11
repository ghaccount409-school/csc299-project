# Task Manager CLI (prototype_pkms.py)

A small, single-file command-line task manager implemented in `prototype_pkms.py`.
It stores tasks as JSON and supports adding, listing, and searching tasks.

## Features

- Add tasks with optional notes, due date, and tags
- List tasks (optionally filtered by tag)
- Search by keyword in title or notes
- Default JSON data file: `tasks.json` next to `prototype_pkms.py` (override with `--data`)

## Requirements

- Python 3.8 or newer
- Works cross-platform; examples below use PowerShell on Windows

## Quick start

From the repository root (where `prototype_pkms.py` lives):

Add a task:

```powershell
python prototype_pkms.py add "Buy milk" --notes "2 litres" --due "2025-11-11" --tag home --tag shopping
```

List tasks:

```powershell
python prototype_pkms.py list
python prototype_pkms.py list --tag shopping
```

Search tasks:

```powershell
python prototype_pkms.py search milk
```

Use a custom data file:

```powershell
python prototype_pkms.py --data C:\path\to\my_tasks.json add "Call Alice"
python prototype_pkms.py --data C:\path\to\my_tasks.json list
```

## Data file format

Tasks are stored as a JSON array where each task is an object like:

```json
{
  "id": "<hex>",
  "title": "Buy milk",
  "notes": "2 litres",
  "created_at": "2025-11-10T12:34:56.789Z",
  "due": "2025-11-11",
  "tags": ["home", "shopping"]
}
```

If the data file is missing it will be created automatically. If the file is corrupted (invalid JSON), the program will attempt to back it up to a `*.bak` file and continue with an empty task list.

## Running tests

Unit tests are provided under the `tests/` directory. Run them with:

```powershell
python -m unittest discover -v
```

If you see import errors like `Import "prototype_pkms" could not be resolved`, make sure you run the command from the repository root so Python can import the module alongside `prototype_pkms.py`.

## Development notes

- The program exposes functions (`add_task`, `list_tasks`, `search_tasks`) so it can be imported and tested programmatically.
- Consider adding commands for removing or marking tasks completed, and adding JSON schema validation for the data file.

## License / attribution

This is a small example created for a classroom project. Feel free to reuse and adapt.

