# Final Project - Usage Examples

## Three Modes of Operation

The final_project module now supports three modes of operation:

### 1. Task Management Mode (Default)

Use the standard task management commands to create, list, search, and manage tasks:

```bash
# Add a task
python -m final_project add "Buy groceries" --notes "milk, eggs, bread" --tag shopping

# List all tasks
python -m final_project list

# Search tasks
python -m final_project search "groceries"

# Show a specific task
python -m final_project show <task-id>

# Mark task as important
python -m final_project mark-important <task-id>

# Add subtasks
python -m final_project add-subtask <parent-id> <subtask-id>

# Delete a task
python -m final_project delete <task-id>
```

For a complete list of commands:
```bash
python -m final_project --help
```

### 2. AI Chat Mode (OpenAI Integration)

Use the AI chat mode to get AI-powered task summarization:

```bash
python -m final_project ai-chat
```

This will launch an interactive chat where you can:
- Enter task descriptions
- Get AI-generated summaries using GPT-4o-mini
- Continue chatting until you type 'quit'

**Example AI Chat Session:**
```
$ python -m final_project ai-chat

Enter a task description (or 'quit' to exit):
> I need to plan a birthday party for 20 people, including booking a venue, ordering cake, sending invitations, and preparing decorations

Processing... (this may take a few seconds)

Summary:
Plan birthday party: venue, cake, invitations, decorations

Enter a task description (or 'quit' to exit):
> quit
Goodbye!
```

### 3. AI Summarize Mode (Summarize Existing Tasks)

Use the AI summarize mode to get AI summaries for tasks already stored in your JSON file:

```bash
# Summarize all tasks
python -m final_project ai-summarize

# Summarize a specific task
python -m final_project ai-summarize <task-id>

# Summarize and update task notes with the AI summary
python -m final_project ai-summarize --update
python -m final_project ai-summarize <task-id> --update
```

**Example:**
```
$ python -m final_project ai-summarize a1b2c3d4

Task [a1b2c3d4]: Organize team meeting
Original: Organize team meeting. Need to schedule a meeting with the entire development team to discuss Q4 roadmap, assign new features, and review current sprint progress
Generating summary... 
Summary: Schedule team meeting for Q4 roadmap and sprint review

$ python -m final_project ai-summarize --update

Task [a1b2c3d4]: Organize team meeting
Original: Organize team meeting. Need to schedule meeting...
Generating summary... 
Summary: Schedule team meeting for Q4 roadmap

Task [e5f6g7h8]: Buy office supplies
Original: Buy office supplies. Order pens, notebooks, sticky notes
Generating summary... 
Summary: Order office supplies: pens, notebooks, sticky notes

✓ Updated 2 task(s) with AI summaries.
```

## Requirements for AI Features

Both AI Chat and AI Summarize modes require:
- Install openai package: `pip install openai`
- Set OPENAI_API_KEY environment variable:
  - PowerShell: `$env:OPENAI_API_KEY='your-api-key-here'`
  - Bash/Linux/Mac: `export OPENAI_API_KEY='your-api-key-here'`
  - CMD: `set OPENAI_API_KEY=your-api-key-here`

## Choosing Between Modes

- **Use Task Management Mode when:** You want to organize, track, and manage tasks with full CRUD operations, tags, links, and subtasks
- **Use AI Chat Mode when:** You want to quickly generate concise task summaries from longer descriptions using AI (for new tasks)
- **Use AI Summarize Mode when:** You want to get AI summaries for tasks already saved in your JSON file, optionally updating them with the summaries
