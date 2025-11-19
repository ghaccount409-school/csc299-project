# Names CLI

Small CLI app to store a list of people you've met. Designed to keep the CLI separate from storage logic.

## Requirements

- **Python 3.14 or later**
- **Package manager**: pip (or optionally uv if available)

## Setup

### 1. Clone or navigate to the project

```powershell
cd c:\Users\nigel\.local\bin\names
```

### 2. Install dependencies (optional, for testing and development)

```powershell
pip install pytest pytest-cov ruff pyright
```

Or if using uv:

```powershell
uv sync
```

### 3. Run tests (optional)

```powershell
pytest tests/
```

Or with uv:

```powershell
uv run pytest tests/
```

## Usage

Run from the project root:

### Add a name

```powershell
python .\bin\names_cli.py add "Alice"
python .\bin\names_cli.py add "Bob"
python .\bin\names_cli.py add "Charlie"
```

### List all names

```powershell
python .\bin\names_cli.py list
```

Output (alphabetically sorted, case-insensitive):
```
Alice
Bob
Charlie
```

### Display help

```powershell
python .\bin\names_cli.py --help
python .\bin\names_cli.py add --help
python .\bin\names_cli.py list --help
```

## Storage

Names are stored in `data/names.json` by default. The storage component is `src/names_storage.py` (class `NameStore`) and the CLI delegates to it.

Example `data/names.json`:
```json
[
  "Alice",
  "Bob",
  "Charlie"
]
```

## Features

- ✅ Add names via CLI
- ✅ List names alphabetically (case-insensitive)
- ✅ Persistent JSON storage
- ✅ Error handling with clear messages
- ✅ Storage limits (10,000 names max, 255 characters per name)
- ✅ Duplicate names allowed
- ✅ Separation of concerns (CLI and storage are independent)

## Design Notes

- Keep CLI thin and side-effect free except for calling the storage API.
- Storage implementation is intentionally simple (JSON list). It can be swapped without changing the CLI.
- Names are sorted alphabetically (case-insensitive) but original case is preserved.
- Last-write-wins concurrency model (no file locking).

## Documentation

- **[spec.md](spec.md)** — Complete feature specification with requirements and clarifications
- **[data-model.md](data-model.md)** — Data structure, state transitions, and validation rules
- **[contracts/cli.md](contracts/cli.md)** — CLI command reference and error codes
- **[quickstart.md](quickstart.md)** — Quick setup and usage guide
- **[research.md](research.md)** — Technology decisions and alternatives considered
- **[IMPL_PLAN.md](IMPL_PLAN.md)** — Implementation plan and constitution alignment
- **[IMPL_TASKS.md](IMPL_TASKS.md)** — Detailed task breakdown

## Testing

Run all tests:

```powershell
pytest tests/
```

Run with coverage:

```powershell
pytest --cov=src tests/
```

Run specific test:

```powershell
pytest tests/test_names_storage.py::test_add_and_list
```

## Project Structure

```
names/
├── bin/
│   └── names_cli.py          # CLI entry point
├── src/
│   └── names_storage.py      # Storage component (NameStore class)
├── tests/
│   └── test_names_storage.py # Unit tests
├── data/
│   └── names.json            # Persistent storage (auto-created)
├── contracts/
│   └── cli.md                # CLI specification
├── docs/
│   └── ADR_TEMPLATE.md       # Architecture decision record template
├── .github/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── ISSUE_TEMPLATE/
│       └── documentation_request.md
├── spec.md                   # Feature specification
├── data-model.md             # Data model documentation
├── quickstart.md             # Quick start guide
├── research.md               # Research and decisions
├── IMPL_PLAN.md              # Implementation plan
├── IMPL_TASKS.md             # Task breakdown
├── CONSTITUTION.md           # Technical constitution
├── pyproject.toml            # Project metadata
└── README.md                 # This file
```

## Contributing

All changes must follow the [Speckit Technical Constitution](CONSTITUTION.md):
- Code clarity and simplicity
- High code quality with type hints
- Comprehensive testing (unit tests required)
- User documentation kept up-to-date
- Error handling as first-class concern

See [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md) for the PR checklist.
