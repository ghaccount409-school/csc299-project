import tempfile
import os
import json
from datetime import datetime
import sys
import pytest
import io
import contextlib
import re

# Add final_project src directory to path to import from __init__.py
THIS_DIR = os.path.dirname(__file__)
FINAL_PROJECT_SRC = os.path.abspath(os.path.join(THIS_DIR, "..", "src"))
if FINAL_PROJECT_SRC not in sys.path:
	sys.path.insert(0, FINAL_PROJECT_SRC)

from final_project import (
    add_task,
    list_tasks,
    search_tasks,
    load_tasks,
    add_link,
    show_task,
    pretty_print,
    generate_short_id,
    task_id_exists,
    search_tasks_by_tags,
    list_all_tags,
    list_important_tasks,
    mark_important,
    unmark_important,
    sort_tasks,
    add_subtask,
    show_subtasks,
    delete_task,
    ai_summarize_tasks,
    _get_ai_summary,
    openai_chat_loop,
    # PKM functions
    create_note,
    list_notes,
    search_notes,
    show_note,
    edit_note,
    delete_note,
    link_note_to_note,
    link_note_to_task,
    load_notes,
    save_notes,
    note_id_exists,
    pretty_print_notes,
    export_note_to_markdown,
    export_all_notes_to_markdown,
)


@pytest.fixture
def datafile():
	"""Create a temporary data file for testing."""
	tmpdir = tempfile.TemporaryDirectory()
	datafile_path = os.path.join(tmpdir.name, "tasks.json")
	yield datafile_path
	tmpdir.cleanup()

def test_add_and_list_and_search(datafile):
	"""Test basic task creation, listing, and searching."""
	t = add_task("Buy milk", notes="2 litres", due="tomorrow", tags=["home"], path=datafile)
	assert t.id
	tasks = list_tasks(path=datafile)
	assert len(tasks) == 1
	assert tasks[0].title == "Buy milk"
	found = search_tasks("milk", path=datafile)
	assert len(found) == 1
	assert found[0].id == t.id

def test_search_no_match(datafile):
	"""Test that searching for non-existent terms returns empty list."""
	add_task("A task", notes="nothing", path=datafile)
	found = search_tasks("zzz", path=datafile)
	assert found == []

def test_tag_filtering_and_multiple_tasks(datafile):
	"""Test filtering tasks by tags with multiple tasks."""
	a = add_task("Task A", tags=["x", "shared"], path=datafile)
	b = add_task("Task B", tags=["y"], path=datafile)
	c = add_task("Task C", tags=["shared"], path=datafile)

	all_tasks = list_tasks(path=datafile)
	assert len(all_tasks) == 3

	shared = list_tasks(path=datafile, tag="shared")
	assert {t.id for t in shared} == {a.id, c.id}

def test_persistence_and_file_contents(datafile):
	"""Test that tasks are persisted to JSON file correctly."""
	add_task("Persist 1", path=datafile)
	add_task("Persist 2", path=datafile)

	# Ensure data file exists and contains 2 items
	with open(datafile, 'r', encoding='utf-8') as f:
		raw = json.load(f)
	assert len(raw) == 2

def test_empty_list_when_no_file(datafile):
	"""Test that listing tasks returns empty list when no file exists."""
	# no file created yet
	tasks = list_tasks(path=datafile)
	assert tasks == []

def test_corrupted_json_is_backed_up_and_returns_empty(datafile):
	"""Test that corrupted JSON files are backed up and empty list is returned."""
	# create a corrupted file
	with open(datafile, 'w', encoding='utf-8') as f:
		f.write("not a json")

	# calling list_tasks should detect corruption, move file to backup, and return []
	tasks = list_tasks(path=datafile)
	assert tasks == []

	# original should have been moved to a .bak path (with_suffix('.bak'))
	bak_path = os.path.splitext(datafile)[0] + ".bak"
	assert os.path.exists(bak_path)
	# original datafile should no longer exist (it was moved)
	assert not os.path.exists(datafile)

def test_created_at_human_friendly_format(datafile):
	"""Test that created_at timestamp is in human-friendly UTC format."""
	t = add_task("Time check", path=datafile)
	tasks = list_tasks(path=datafile)
	assert len(tasks) == 1
	created = tasks[0].created_at
	# Should match 'YYYY-MM-DD HH:MM:SS UTC'
	assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC$", created)

def test_linking_and_show(datafile):
	"""Test task linking and pretty_print output for linked tasks."""
	a = add_task("Parent Task", path=datafile)
	b = add_task("Child Task", path=datafile)
	ok = add_link(a.id, b.id, path=datafile)
	assert ok

	tasks = list_tasks(path=datafile)
	buf = io.StringIO()
	with contextlib.redirect_stdout(buf):
		pretty_print(tasks)
	out = buf.getvalue()

	# linked tasks and the view command should appear in the listing for the parent
	assert "Linked tasks:" in out
	assert b.id in out
	assert f"python -m final_project show {b.id}" in out

def test_short_id_generation(datafile):
	"""Test that short IDs are 8-character hex strings."""
	# Short IDs should be 8 characters and hex
	t = add_task("Test short ID", path=datafile)
	assert len(t.id) == 8
	assert re.match(r'^[0-9a-f]{8}$', t.id)

def test_multiple_short_ids_are_unique(datafile):
	"""Test that multiple generated IDs are unique."""
	t1 = add_task("Task 1", path=datafile)
	t2 = add_task("Task 2", path=datafile)
	t3 = add_task("Task 3", path=datafile)
	ids = {t1.id, t2.id, t3.id}
	assert len(ids) == 3

def test_custom_id_creation(datafile):
	"""Test creating a task with a custom ID."""
	t = add_task("Custom task", custom_id="my-task", path=datafile)
	assert t.id == "my-task"
	tasks = list_tasks(path=datafile)
	assert len(tasks) == 1
	assert tasks[0].id == "my-task"

def test_duplicate_custom_id_rejected(datafile):
	"""Test that duplicate custom IDs are rejected."""
	add_task("First task", custom_id="dup-id", path=datafile)
	# Try to add second task with same ID
	t2 = add_task("Second task", custom_id="dup-id", path=datafile)
	assert t2 is None
	# Only first task should exist
	tasks = list_tasks(path=datafile)
	assert len(tasks) == 1

def test_task_id_exists_checker(datafile):
	"""Test the task_id_exists helper function."""
	add_task("Existing", custom_id="exists", path=datafile)
	assert task_id_exists("exists", path=datafile)
	assert not task_id_exists("nonexistent", path=datafile)

def test_search_tasks_by_tags_any(datafile):
	"""Test searching tasks with ANY of the specified tags."""
	# Create tasks with different tag combinations
	add_task("Task 1", tags=["home", "urgent"], path=datafile)
	add_task("Task 2", tags=["work"], path=datafile)
	add_task("Task 3", tags=["home", "shopping"], path=datafile)
    
	# Search for tasks with "home" OR "work"
	found = search_tasks_by_tags(["home", "work"], path=datafile, match_all=False)
	assert len(found) == 3

def test_search_tasks_by_tags_all(datafile):
	"""Test searching tasks with ALL of the specified tags."""
	# Create tasks with different tag combinations
	add_task("Task 1", tags=["home", "urgent"], path=datafile)
	add_task("Task 2", tags=["work"], path=datafile)
	add_task("Task 3", tags=["home", "urgent", "shopping"], path=datafile)
    
	# Search for tasks with "home" AND "urgent"
	found = search_tasks_by_tags(["home", "urgent"], path=datafile, match_all=True)
	assert len(found) == 2

def test_list_all_tags(datafile):
	"""Test listing all tags with counts, sorted alphabetically."""
	add_task("Task 1", tags=["home", "urgent"], path=datafile)
	add_task("Task 2", tags=["work", "urgent"], path=datafile)
	add_task("Task 3", tags=["home", "shopping"], path=datafile)
    
	tag_counts = list_all_tags(path=datafile)
	assert tag_counts["home"] == 2
	assert tag_counts["urgent"] == 2
	assert tag_counts["work"] == 1
	assert tag_counts["shopping"] == 1
	# Verify tags are sorted alphabetically
	assert list(tag_counts.keys()) == sorted(tag_counts.keys())

def test_mark_important_and_list(datafile):
	"""Test marking tasks as important and listing important tasks."""
	t = add_task("Very important", important=True, path=datafile)
	assert t.important

	important = list_important_tasks(path=datafile)
	assert len(important) == 1
	assert important[0].id == t.id

	# pretty_print should include the label 'Important' when printing
	tasks = list_tasks(path=datafile)
	buf = io.StringIO()
	with contextlib.redirect_stdout(buf):
		pretty_print(tasks)
	out = buf.getvalue()
	assert "Important" in out

def test_mark_and_unmark_commands(datafile):
	"""Test mark_important and unmark_important functions."""
	# Create a non-important task
	t = add_task("Not yet important", path=datafile)
	assert not getattr(t, 'important', False)

	# Mark it important using helper
	ok = mark_important(t.id, path=datafile)
	assert ok
	tasks = list_important_tasks(path=datafile)
	assert len(tasks) == 1
	assert tasks[0].id == t.id

	# Unmark it
	ok2 = unmark_important(t.id, path=datafile)
	assert ok2
	tasks_after = list_important_tasks(path=datafile)
	assert len(tasks_after) == 0

def test_sort_by_title(datafile):
	"""Test sorting tasks by title in ascending and descending order."""
	add_task("Zebra", path=datafile)
	add_task("Apple", path=datafile)
	add_task("Mango", path=datafile)
    
	tasks = list_tasks(path=datafile)
	sorted_asc = sort_tasks(tasks, sort_by="title", reverse=False)
	sorted_desc = sort_tasks(tasks, sort_by="title", reverse=True)
    
	# Check ascending order
	assert sorted_asc[0].title == "Apple"
	assert sorted_asc[1].title == "Mango"
	assert sorted_asc[2].title == "Zebra"
    
	# Check descending order
	assert sorted_desc[0].title == "Zebra"
	assert sorted_desc[1].title == "Mango"
	assert sorted_desc[2].title == "Apple"

def test_sort_by_id(datafile):
	"""Test sorting tasks by ID."""
	t1 = add_task("Task 1", path=datafile)
	t2 = add_task("Task 2", path=datafile)
	t3 = add_task("Task 3", path=datafile)
    
	tasks = list_tasks(path=datafile)
	sorted_asc = sort_tasks(tasks, sort_by="id", reverse=False)
	sorted_desc = sort_tasks(tasks, sort_by="id", reverse=True)
    
	# Ascending should preserve or sort by hex value
	assert len(sorted_asc) == 3
	assert len(sorted_desc) == 3
	# Just verify it returns sorted list
	assert sorted_asc[0].id == sorted(tasks, key=lambda t: t.id)[0].id

def test_sort_by_created(datafile):
	"""Test sorting tasks by creation timestamp."""
	import time
	t1 = add_task("First", path=datafile)
	time.sleep(1.1)  # Sleep 1.1 seconds to ensure different second-level timestamps
	t2 = add_task("Second", path=datafile)
    
	tasks = list_tasks(path=datafile)
	sorted_asc = sort_tasks(tasks, sort_by="created", reverse=False)
	sorted_desc = sort_tasks(tasks, sort_by="created", reverse=True)
    
	# Ascending: oldest first
	assert sorted_asc[0].title == "First"
	assert sorted_asc[1].title == "Second"
    
	# Descending: newest first
	assert sorted_desc[0].title == "Second"
	assert sorted_desc[1].title == "First"

def test_sort_by_due(datafile):
	"""Test sorting tasks by due date with null handling."""
	add_task("No due", path=datafile)
	add_task("Due early", due="2025-11-10", path=datafile)
	add_task("Due late", due="2025-11-20", path=datafile)
    
	tasks = list_tasks(path=datafile)
	sorted_asc = sort_tasks(tasks, sort_by="due", reverse=False)
    
	# Without due date should be at end
	assert sorted_asc[0].due is not None
	assert sorted_asc[1].due is not None
	assert sorted_asc[2].due is None

def test_add_subtask(datafile):
	"""Test linking an existing task as a subtask to a parent."""
	parent = add_task("Parent task", path=datafile)
	existing = add_task("Existing task", path=datafile)
    
	# Link existing task as subtask
	subtask = add_subtask(parent.id, existing.id, path=datafile)
    
	# Verify existing task was linked
	assert subtask is not None
	assert subtask.id == existing.id
    
	# Verify parent has subtask reference
	updated_parent = show_task(parent.id, path=datafile)
	assert existing.id in updated_parent.subtasks

def test_add_multiple_subtasks(datafile):
	"""Test adding multiple subtasks to a single parent task."""
	parent = add_task("Parent task", path=datafile)
	sub1 = add_task("Subtask 1", path=datafile)
	sub2 = add_task("Subtask 2", path=datafile)
	sub3 = add_task("Subtask 3", path=datafile)
    
	# Link all as subtasks
	add_subtask(parent.id, sub1.id, path=datafile)
	add_subtask(parent.id, sub2.id, path=datafile)
	add_subtask(parent.id, sub3.id, path=datafile)
    
	# Verify all subtasks are linked to parent
	tasks = load_tasks(path=datafile)
	parent_updated = [t for t in tasks if t.id == parent.id][0]
	assert len(parent_updated.subtasks) == 3
	assert sub1.id in parent_updated.subtasks
	assert sub2.id in parent_updated.subtasks
	assert sub3.id in parent_updated.subtasks

def test_add_subtask_to_nonexistent_parent(datafile):
	"""Test that adding a subtask to a nonexistent parent returns None."""
	existing = add_task("Existing", path=datafile)
	result = add_subtask("nonexistent", existing.id, path=datafile)
	assert result is None

def test_add_subtask_nonexistent_subtask(datafile):
	"""Test that adding a nonexistent task as a subtask returns None."""
	parent = add_task("Parent", path=datafile)
	result = add_subtask(parent.id, "nonexistent-task", path=datafile)
	assert result is None

def test_show_subtasks(datafile):
	"""Test displaying all subtasks for a parent task."""
	parent = add_task("Parent", path=datafile)
	sub1 = add_task("Subtask 1", path=datafile)
	sub2 = add_task("Subtask 2", path=datafile)
    
	# Link both as subtasks
	add_subtask(parent.id, sub1.id, path=datafile)
	add_subtask(parent.id, sub2.id, path=datafile)
    
	# show_subtasks should return the subtasks
	subtasks = show_subtasks(parent.id, path=datafile)
	assert len(subtasks) == 2
	ids = {s.id for s in subtasks}
	assert ids == {sub1.id, sub2.id}

def test_show_subtasks_empty(datafile):
	"""Test that showing subtasks for a parent with no subtasks returns empty list."""
	parent = add_task("Parent with no subtasks", path=datafile)
    
	# show_subtasks on empty parent should return empty list
	subtasks = show_subtasks(parent.id, path=datafile)
	assert len(subtasks) == 0

def test_link_same_subtask_twice(datafile):
	"""Test that linking the same subtask twice only adds it once."""
	parent = add_task("Parent", path=datafile)
	existing = add_task("Existing", path=datafile)
    
	# Link it twice
	add_subtask(parent.id, existing.id, path=datafile)
	add_subtask(parent.id, existing.id, path=datafile)
    
	# Should only appear once in subtasks list
	tasks = load_tasks(path=datafile)
	parent_updated = [t for t in tasks if t.id == parent.id][0]
	count = parent_updated.subtasks.count(existing.id)
	assert count == 1

def test_delete_task_simple(datafile):
	"""Delete a simple task without subtasks."""
	task = add_task("Delete me", path=datafile)
	tasks = list_tasks(path=datafile)
	assert len(tasks) == 1
    
	# Delete the task
	result = delete_task(task.id, path=datafile, delete_subtasks=False)
	assert result
    
	# Verify it's gone
	tasks = list_tasks(path=datafile)
	assert len(tasks) == 0

def test_delete_task_not_found(datafile):
	"""Try to delete a task that doesn't exist."""
	result = delete_task("nonexistent-id", path=datafile)
	assert not result

def test_delete_task_with_subtasks_yes(datafile):
	"""Delete a task and its subtasks (delete_subtasks=True)."""
	parent = add_task("Parent to delete", path=datafile)
	sub1 = add_task("Subtask 1", path=datafile)
	sub2 = add_task("Subtask 2", path=datafile)
	extra = add_task("Unrelated task", path=datafile)
    
	# Link subtasks
	add_subtask(parent.id, sub1.id, path=datafile)
	add_subtask(parent.id, sub2.id, path=datafile)
    
	# Verify initial state
	tasks = list_tasks(path=datafile)
	assert len(tasks) == 4
    
	# Delete parent with subtasks
	result = delete_task(parent.id, path=datafile, delete_subtasks=True)
	assert result
    
	# Verify parent and subtasks are gone, extra remains
	tasks = list_tasks(path=datafile)
	assert len(tasks) == 1
	assert tasks[0].id == extra.id

def test_delete_task_with_subtasks_no(datafile):
	"""Test deleting a task while orphaning its subtasks (delete_subtasks=False)."""
	parent = add_task("Parent to delete", path=datafile)
	sub1 = add_task("Subtask 1", path=datafile)
	sub2 = add_task("Subtask 2", path=datafile)
    
	# Link subtasks
	add_subtask(parent.id, sub1.id, path=datafile)
	add_subtask(parent.id, sub2.id, path=datafile)
    
	# Verify initial state
	tasks = list_tasks(path=datafile)
	assert len(tasks) == 3
    
	# Delete parent but keep subtasks
	result = delete_task(parent.id, path=datafile, delete_subtasks=False)
	assert result
    
	# Verify parent is gone but subtasks remain
	tasks = list_tasks(path=datafile)
	assert len(tasks) == 2
	ids = {t.id for t in tasks}
	assert ids == {sub1.id, sub2.id}


# =============================================================================
# AI Summarization Tests
# =============================================================================

def test_ai_summarize_tasks_no_openai_package(datafile, monkeypatch):
	"""Test ai_summarize_tasks when openai package is not available."""
	# Mock the import to raise ImportError
	import builtins
	real_import = builtins.__import__
	
	def mock_import(name, *args, **kwargs):
		if name == "openai":
			raise ImportError("No module named 'openai'")
		return real_import(name, *args, **kwargs)
	
	monkeypatch.setattr(builtins, "__import__", mock_import)
	
	# Add a task
	add_task("Test task", path=datafile)
	
	# Try to summarize without openai package
	result = ai_summarize_tasks(path=datafile)
	assert result == 1  # Should return error code


def test_ai_summarize_tasks_no_api_key(datafile, monkeypatch):
	"""Test ai_summarize_tasks when OPENAI_API_KEY is not set."""
	# Remove API key from environment
	monkeypatch.delenv("OPENAI_API_KEY", raising=False)
	
	# Add a task
	add_task("Test task", path=datafile)
	
	# Try to summarize without API key
	result = ai_summarize_tasks(path=datafile)
	assert result == 1  # Should return error code


def test_ai_summarize_tasks_no_tasks(datafile, monkeypatch):
	"""Test ai_summarize_tasks when there are no tasks."""
	# Set a fake API key
	monkeypatch.setenv("OPENAI_API_KEY", "fake-key-for-testing")
	
	# Try to summarize with no tasks
	result = ai_summarize_tasks(path=datafile)
	assert result == 0  # Should return success (nothing to do)


def test_ai_summarize_tasks_task_not_found(datafile, monkeypatch):
	"""Test ai_summarize_tasks with non-existent task ID."""
	# Set a fake API key
	monkeypatch.setenv("OPENAI_API_KEY", "fake-key-for-testing")
	
	# Add a task
	add_task("Test task", path=datafile)
	
	# Try to summarize non-existent task
	result = ai_summarize_tasks(task_id="nonexistent", path=datafile)
	assert result == 2  # Should return error code


def test_ai_summarize_tasks_with_mock_client(datafile, monkeypatch):
	"""Test ai_summarize_tasks with mocked OpenAI client."""
	# Set a fake API key
	monkeypatch.setenv("OPENAI_API_KEY", "fake-key-for-testing")
	
	# Create mock OpenAI client and response
	class MockCompletion:
		def __init__(self):
			self.choices = [type('obj', (object,), {'message': type('obj', (object,), {'content': 'Test summary'})()})]
	
	class MockChatCompletions:
		def create(self, **kwargs):
			return MockCompletion()
	
	class MockChat:
		def __init__(self):
			self.completions = MockChatCompletions()
	
	class MockOpenAI:
		def __init__(self, **kwargs):
			self.chat = MockChat()
	
	# Mock the OpenAI import
	import sys
	import types
	mock_openai = types.ModuleType('openai')
	mock_openai.OpenAI = MockOpenAI
	sys.modules['openai'] = mock_openai
	
	# Add tasks
	task1 = add_task("Task 1", notes="This is a detailed description", path=datafile)
	task2 = add_task("Task 2", path=datafile)
	
	# Test summarizing all tasks (no update)
	result = ai_summarize_tasks(path=datafile, update=False)
	assert result == 0
	
	# Verify tasks were not updated
	tasks = load_tasks(path=datafile)
	task1_updated = [t for t in tasks if t.id == task1.id][0]
	assert "AI Summary" not in (task1_updated.notes or "")
	
	# Clean up
	del sys.modules['openai']


def test_ai_summarize_tasks_with_update(datafile, monkeypatch):
	"""Test ai_summarize_tasks with --update flag."""
	# Set a fake API key
	monkeypatch.setenv("OPENAI_API_KEY", "fake-key-for-testing")
	
	# Create mock OpenAI client
	class MockCompletion:
		def __init__(self):
			self.choices = [type('obj', (object,), {'message': type('obj', (object,), {'content': 'Concise task summary'})()})]
	
	class MockChatCompletions:
		def create(self, **kwargs):
			return MockCompletion()
	
	class MockChat:
		def __init__(self):
			self.completions = MockChatCompletions()
	
	class MockOpenAI:
		def __init__(self, **kwargs):
			self.chat = MockChat()
	
	# Mock the OpenAI import
	import sys
	import types
	mock_openai = types.ModuleType('openai')
	mock_openai.OpenAI = MockOpenAI
	sys.modules['openai'] = mock_openai
	
	# Add task with notes
	task = add_task("Long task title", notes="Detailed description here", path=datafile)
	
	# Summarize with update flag
	result = ai_summarize_tasks(task_id=task.id, update=True, path=datafile)
	assert result == 0
	
	# Verify task was updated with AI summary
	tasks = load_tasks(path=datafile)
	updated_task = [t for t in tasks if t.id == task.id][0]
	assert "AI Summary: Concise task summary" in updated_task.notes
	
	# Clean up
	del sys.modules['openai']


def test_ai_summarize_specific_task(datafile, monkeypatch):
	"""Test ai_summarize_tasks for a specific task ID."""
	# Set a fake API key
	monkeypatch.setenv("OPENAI_API_KEY", "fake-key-for-testing")
	
	# Create mock OpenAI client
	class MockCompletion:
		def __init__(self):
			self.choices = [type('obj', (object,), {'message': type('obj', (object,), {'content': 'Specific task summary'})()})]
	
	class MockChatCompletions:
		def create(self, **kwargs):
			return MockCompletion()
	
	class MockChat:
		def __init__(self):
			self.completions = MockChatCompletions()
	
	class MockOpenAI:
		def __init__(self, **kwargs):
			self.chat = MockChat()
	
	# Mock the OpenAI import
	import sys
	import types
	mock_openai = types.ModuleType('openai')
	mock_openai.OpenAI = MockOpenAI
	sys.modules['openai'] = mock_openai
	
	# Add multiple tasks
	task1 = add_task("Task 1", path=datafile)
	task2 = add_task("Task 2", path=datafile)
	task3 = add_task("Task 3", path=datafile)
	
	# Summarize only task2 with update
	result = ai_summarize_tasks(task_id=task2.id, update=True, path=datafile)
	assert result == 0
	
	# Verify only task2 was updated
	tasks = load_tasks(path=datafile)
	task1_updated = [t for t in tasks if t.id == task1.id][0]
	task2_updated = [t for t in tasks if t.id == task2.id][0]
	task3_updated = [t for t in tasks if t.id == task3.id][0]
	
	assert "AI Summary" not in (task1_updated.notes or "")
	assert "AI Summary: Specific task summary" in task2_updated.notes
	assert "AI Summary" not in (task3_updated.notes or "")
	
	# Clean up
	del sys.modules['openai']


def test_get_ai_summary_helper_with_mock(monkeypatch):
	"""Test _get_ai_summary helper function with mocked client."""
	# Create mock client
	class MockCompletion:
		def __init__(self):
			self.choices = [type('obj', (object,), {'message': type('obj', (object,), {'content': 'Helper summary'})()})]
	
	class MockChatCompletions:
		def create(self, **kwargs):
			return MockCompletion()
	
	class MockChat:
		def __init__(self):
			self.completions = MockChatCompletions()
	
	class MockClient:
		def __init__(self):
			self.chat = MockChat()
	
	client = MockClient()
	
	# Test the helper function
	summary = _get_ai_summary("Test task description", client)
	assert summary == "Helper summary"


def test_get_ai_summary_error_handling(monkeypatch):
	"""Test _get_ai_summary error handling."""
	# Create mock client that raises exception
	class MockChatCompletions:
		def create(self, **kwargs):
			raise Exception("API Error")
	
	class MockChat:
		def __init__(self):
			self.completions = MockChatCompletions()
	
	class MockClient:
		def __init__(self):
			self.chat = MockChat()
	
	client = MockClient()
	
	# Test error handling
	summary = _get_ai_summary("Test task", client)
	assert summary is None  # Should return None on error


def test_openai_chat_loop_quit(monkeypatch):
	"""Test that openai_chat_loop returns 0 when user types 'quit'."""
	# Set a fake API key
	monkeypatch.setenv("OPENAI_API_KEY", "fake-key-for-testing")
	
	# Mock the OpenAI client
	class MockCompletion:
		def __init__(self):
			self.choices = [type('obj', (object,), {'message': type('obj', (object,), {'content': 'Test summary'})()})]
	
	class MockChatCompletions:
		def create(self, **kwargs):
			return MockCompletion()
	
	class MockChat:
		def __init__(self):
			self.completions = MockChatCompletions()
	
	class MockOpenAI:
		def __init__(self, **kwargs):
			self.chat = MockChat()
	
	# Mock the OpenAI import
	import sys
	import types
	mock_openai = types.ModuleType('openai')
	mock_openai.OpenAI = MockOpenAI
	sys.modules['openai'] = mock_openai
	
	# Mock input to simulate user typing 'quit'
	monkeypatch.setattr('builtins.input', lambda _: 'quit')
	
	# Test that openai_chat_loop returns 0 when user quits
	result = openai_chat_loop()
	assert result == 0
	
	# Clean up
	del sys.modules['openai']


def test_openai_chat_loop_no_openai_package(monkeypatch):
	"""Test openai_chat_loop when openai package is not available."""
	# Mock the import to raise ImportError
	import builtins
	real_import = builtins.__import__
	
	def mock_import(name, *args, **kwargs):
		if name == "openai":
			raise ImportError("No module named 'openai'")
		return real_import(name, *args, **kwargs)
	
	monkeypatch.setattr(builtins, "__import__", mock_import)
	
	# Try to run without openai package
	result = openai_chat_loop()
	assert result == 1  # Should return error code


def test_openai_chat_loop_no_api_key(monkeypatch):
	"""Test openai_chat_loop when OPENAI_API_KEY is not set."""
	# Remove API key from environment
	monkeypatch.delenv("OPENAI_API_KEY", raising=False)
	
	# Mock OpenAI to be available
	import sys
	import types
	mock_openai = types.ModuleType('openai')
	mock_openai.OpenAI = lambda **kwargs: None
	sys.modules['openai'] = mock_openai
	
	# Try to run without API key
	result = openai_chat_loop()
	assert result == 1  # Should return error code
	
	# Clean up
	del sys.modules['openai']


def test_openai_chat_loop_eof(monkeypatch):
	"""Test openai_chat_loop handles EOF gracefully."""
	# Set a fake API key
	monkeypatch.setenv("OPENAI_API_KEY", "fake-key-for-testing")
	
	# Mock OpenAI client
	class MockOpenAI:
		def __init__(self, **kwargs):
			self.chat = None
	
	import sys
	import types
	mock_openai = types.ModuleType('openai')
	mock_openai.OpenAI = MockOpenAI
	sys.modules['openai'] = mock_openai
	
	# Mock input to raise EOFError
	def mock_input(_):
		raise EOFError()
	monkeypatch.setattr('builtins.input', mock_input)
	
	# Test that openai_chat_loop handles EOF and returns 0
	result = openai_chat_loop()
	assert result == 0
	
	# Clean up
	del sys.modules['openai']


def test_openai_chat_loop_empty_input(monkeypatch):
	"""Test openai_chat_loop handles empty input correctly."""
	# Set a fake API key
	monkeypatch.setenv("OPENAI_API_KEY", "fake-key-for-testing")
	
	# Mock OpenAI client
	class MockCompletion:
		def __init__(self):
			self.choices = [type('obj', (object,), {'message': type('obj', (object,), {'content': 'Summary'})()})]
	
	class MockChatCompletions:
		def create(self, **kwargs):
			return MockCompletion()
	
	class MockChat:
		def __init__(self):
			self.completions = MockChatCompletions()
	
	class MockOpenAI:
		def __init__(self, **kwargs):
			self.chat = MockChat()
	
	import sys
	import types
	mock_openai = types.ModuleType('openai')
	mock_openai.OpenAI = MockOpenAI
	sys.modules['openai'] = mock_openai
	
	# Mock input to return empty string, then 'quit'
	input_values = iter(['', 'quit'])
	monkeypatch.setattr('builtins.input', lambda _: next(input_values))
	
	# Test that it prompts again after empty input, then quits
	result = openai_chat_loop()
	assert result == 0
	
	# Clean up
	del sys.modules['openai']


# =============================================================================
# PKM (Personal Knowledge Management) Tests
# =============================================================================

@pytest.fixture
def notesfile():
	"""Create a temporary notes data file for testing."""
	tmpdir = tempfile.TemporaryDirectory()
	notesfile_path = os.path.join(tmpdir.name, "notes.json")
	yield notesfile_path
	tmpdir.cleanup()


def test_create_and_list_notes(notesfile):
	"""Test basic note creation and listing."""
	note1 = create_note("My First Note", content="This is the content", path=notesfile)
	assert note1 is not None
	assert note1.title == "My First Note"
	assert note1.content == "This is the content"
	assert note1.id
	
	note2 = create_note("Second Note", content="More content", tags=["test"], path=notesfile)
	assert note2 is not None
	
	notes = list_notes(path=notesfile)
	assert len(notes) == 2
	assert any(n.title == "My First Note" for n in notes)
	assert any(n.title == "Second Note" for n in notes)


def test_create_note_with_custom_id(notesfile):
	"""Test creating a note with custom ID."""
	note = create_note("Custom ID Note", content="Content", custom_id="custom123", path=notesfile)
	assert note is not None
	assert note.id == "custom123"
	
	# Try to create another note with same ID
	duplicate = create_note("Duplicate", custom_id="custom123", path=notesfile)
	assert duplicate is None


def test_note_timestamps(notesfile):
	"""Test that notes have proper timestamps."""
	note = create_note("Timestamped Note", content="Content", path=notesfile)
	assert note.created_at
	assert note.updated_at
	assert note.created_at == note.updated_at


def test_search_notes(notesfile):
	"""Test searching notes by keyword."""
	create_note("Python Tutorial", content="Learn Python programming", path=notesfile)
	create_note("JavaScript Guide", content="Web development with JS", path=notesfile)
	create_note("Python Advanced", content="Advanced Python concepts", path=notesfile)
	
	# Search in title
	results = search_notes("Python", path=notesfile)
	assert len(results) == 2
	
	# Search in content
	results = search_notes("Web", path=notesfile)
	assert len(results) == 1
	assert results[0].title == "JavaScript Guide"
	
	# Case insensitive search
	results = search_notes("python", path=notesfile)
	assert len(results) == 2


def test_list_notes_with_tag_filter(notesfile):
	"""Test filtering notes by tag."""
	create_note("Work Note", tags=["work", "important"], path=notesfile)
	create_note("Personal Note", tags=["personal"], path=notesfile)
	create_note("Another Work Note", tags=["work"], path=notesfile)
	
	# Filter by work tag
	work_notes = list_notes(tag="work", path=notesfile)
	assert len(work_notes) == 2
	
	# Filter by personal tag
	personal_notes = list_notes(tag="personal", path=notesfile)
	assert len(personal_notes) == 1
	
	# Filter by non-existent tag
	no_notes = list_notes(tag="nonexistent", path=notesfile)
	assert len(no_notes) == 0


def test_edit_note(notesfile):
	"""Test editing note title, content, and tags."""
	import time
	
	note = create_note("Original Title", content="Original content", tags=["old"], path=notesfile)
	original_created_at = note.created_at
	original_updated_at = note.updated_at
	
	# Sleep briefly to ensure timestamp difference
	time.sleep(0.01)
	
	# Edit title
	ok = edit_note(note.id, title="New Title", path=notesfile)
	assert ok is True
	
	updated_notes = load_notes(path=notesfile)
	updated = next(n for n in updated_notes if n.id == note.id)
	assert updated.title == "New Title"
	assert updated.content == "Original content"  # Content unchanged
	assert updated.created_at == original_created_at  # Created time unchanged
	# Just verify updated_at exists and is a valid timestamp
	assert updated.updated_at
	
	# Edit content
	time.sleep(0.01)
	ok = edit_note(note.id, content="New content", path=notesfile)
	assert ok is True
	
	updated_notes = load_notes(path=notesfile)
	updated = next(n for n in updated_notes if n.id == note.id)
	assert updated.content == "New content"
	
	# Edit tags
	time.sleep(0.01)
	ok = edit_note(note.id, tags=["new", "updated"], path=notesfile)
	assert ok is True
	
	updated_notes = load_notes(path=notesfile)
	updated = next(n for n in updated_notes if n.id == note.id)
	assert updated.tags == ["new", "updated"]


def test_edit_nonexistent_note(notesfile):
	"""Test editing a note that doesn't exist."""
	ok = edit_note("nonexistent", title="New Title", path=notesfile)
	assert ok is False


def test_delete_note(notesfile):
	"""Test deleting a note."""
	note1 = create_note("Note 1", path=notesfile)
	note2 = create_note("Note 2", path=notesfile)
	
	notes = list_notes(path=notesfile)
	assert len(notes) == 2
	
	# Delete first note
	ok = delete_note(note1.id, path=notesfile)
	assert ok is True
	
	notes = list_notes(path=notesfile)
	assert len(notes) == 1
	assert notes[0].id == note2.id
	
	# Try to delete non-existent note
	ok = delete_note("nonexistent", path=notesfile)
	assert ok is False


def test_link_note_to_note(notesfile):
	"""Test linking notes together."""
	note1 = create_note("Note 1", path=notesfile)
	note2 = create_note("Note 2", path=notesfile)
	note3 = create_note("Note 3", path=notesfile)
	
	# Link note1 to note2
	ok = link_note_to_note(note1.id, note2.id, path=notesfile)
	assert ok is True
	
	notes = load_notes(path=notesfile)
	note1_updated = next(n for n in notes if n.id == note1.id)
	assert note2.id in note1_updated.linked_notes
	
	# Link note1 to note3
	ok = link_note_to_note(note1.id, note3.id, path=notesfile)
	assert ok is True
	
	notes = load_notes(path=notesfile)
	note1_updated = next(n for n in notes if n.id == note1.id)
	assert note2.id in note1_updated.linked_notes
	assert note3.id in note1_updated.linked_notes
	assert len(note1_updated.linked_notes) == 2


def test_link_note_to_note_prevents_duplicates(notesfile):
	"""Test that linking the same note twice doesn't create duplicates."""
	note1 = create_note("Note 1", path=notesfile)
	note2 = create_note("Note 2", path=notesfile)
	
	# Link twice
	link_note_to_note(note1.id, note2.id, path=notesfile)
	link_note_to_note(note1.id, note2.id, path=notesfile)
	
	notes = load_notes(path=notesfile)
	note1_updated = next(n for n in notes if n.id == note1.id)
	assert note1_updated.linked_notes.count(note2.id) == 1


def test_link_note_to_note_nonexistent(notesfile):
	"""Test linking to non-existent notes."""
	note1 = create_note("Note 1", path=notesfile)
	
	# Try to link to non-existent target
	ok = link_note_to_note(note1.id, "nonexistent", path=notesfile)
	assert ok is False
	
	# Try to link from non-existent source
	ok = link_note_to_note("nonexistent", note1.id, path=notesfile)
	assert ok is False


def test_link_note_to_task(notesfile, datafile):
	"""Test linking notes to tasks."""
	# Create a task
	task = add_task("Test Task", path=datafile)
	
	# Create a note
	note = create_note("Note about task", path=notesfile)
	
	# Link note to task
	ok = link_note_to_task(note.id, task.id, notes_path=notesfile, tasks_path=datafile)
	assert ok is True
	
	notes = load_notes(path=notesfile)
	note_updated = next(n for n in notes if n.id == note.id)
	assert task.id in note_updated.linked_tasks


def test_link_note_to_nonexistent_task(notesfile, datafile):
	"""Test linking note to non-existent task."""
	note = create_note("Note", path=notesfile)
	
	ok = link_note_to_task(note.id, "nonexistent_task", notes_path=notesfile, tasks_path=datafile)
	assert ok is False


def test_link_nonexistent_note_to_task(notesfile, datafile):
	"""Test linking non-existent note to task."""
	task = add_task("Test Task", path=datafile)
	
	ok = link_note_to_task("nonexistent_note", task.id, notes_path=notesfile, tasks_path=datafile)
	assert ok is False


def test_delete_note_removes_references(notesfile):
	"""Test that deleting a note removes references from other notes."""
	note1 = create_note("Note 1", path=notesfile)
	note2 = create_note("Note 2", path=notesfile)
	note3 = create_note("Note 3", path=notesfile)
	
	# Link note2 and note3 to note1
	link_note_to_note(note2.id, note1.id, path=notesfile)
	link_note_to_note(note3.id, note1.id, path=notesfile)
	
	# Verify links exist
	notes = load_notes(path=notesfile)
	note2_before = next(n for n in notes if n.id == note2.id)
	note3_before = next(n for n in notes if n.id == note3.id)
	assert note1.id in note2_before.linked_notes
	assert note1.id in note3_before.linked_notes
	
	# Delete note1
	delete_note(note1.id, path=notesfile)
	
	# Verify references are removed
	notes = load_notes(path=notesfile)
	note2_after = next(n for n in notes if n.id == note2.id)
	note3_after = next(n for n in notes if n.id == note3.id)
	assert note1.id not in note2_after.linked_notes
	assert note1.id not in note3_after.linked_notes


def test_note_id_exists(notesfile):
	"""Test checking if note ID exists."""
	note = create_note("Test Note", custom_id="test123", path=notesfile)
	
	assert note_id_exists("test123", path=notesfile) is True
	assert note_id_exists("nonexistent", path=notesfile) is False


def test_load_notes_empty_file(notesfile):
	"""Test loading notes when file doesn't exist."""
	notes = load_notes(path=notesfile)
	assert notes == []


def test_load_notes_corrupted_file(notesfile):
	"""Test loading notes with corrupted JSON."""
	# Create corrupted file
	with open(notesfile, 'w') as f:
		f.write("corrupted json data {")
	
	# Should handle corruption gracefully
	notes = load_notes(path=notesfile)
	assert notes == []
	
	# Verify backup was created
	backup_path = notesfile + ".bak"
	assert os.path.exists(backup_path)


def test_save_and_load_notes(notesfile):
	"""Test saving and loading notes."""
	from final_project import Note
	from datetime import datetime
	
	now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
	notes = [
		Note(id="1", title="Note 1", content="Content 1", created_at=now, updated_at=now, tags=["tag1"], linked_notes=[], linked_tasks=[]),
		Note(id="2", title="Note 2", content="Content 2", created_at=now, updated_at=now, tags=["tag2"], linked_notes=["1"], linked_tasks=[])
	]
	
	save_notes(notes, path=notesfile)
	
	loaded = load_notes(path=notesfile)
	assert len(loaded) == 2
	assert loaded[0].id == "1"
	assert loaded[0].title == "Note 1"
	assert loaded[1].id == "2"
	assert loaded[1].linked_notes == ["1"]


def test_pretty_print_notes(notesfile, capsys):
	"""Test pretty printing notes."""
	note1 = create_note("Short Note", content="Brief", tags=["test"], path=notesfile)
	note2 = create_note("Long Note", content="A" * 100, path=notesfile)
	note3 = create_note("Linked Note", path=notesfile)
	
	# Link note3 to note1
	link_note_to_note(note3.id, note1.id, path=notesfile)
	
	notes = list_notes(path=notesfile)
	pretty_print_notes(notes)
	
	captured = capsys.readouterr()
	assert "Short Note" in captured.out
	assert "Long Note" in captured.out
	assert "[test]" in captured.out  # Tags shown
	assert "..." in captured.out  # Long content truncated


def test_pretty_print_notes_empty(notesfile, capsys):
	"""Test pretty printing empty notes list."""
	pretty_print_notes([])
	
	captured = capsys.readouterr()
	assert "No notes found" in captured.out


def test_note_with_markdown_content(notesfile):
	"""Test notes with markdown content."""
	markdown_content = """# Heading

## Subheading

- List item 1
- List item 2

**Bold text** and *italic text*

```python
print('code block')
```
"""
	note = create_note("Markdown Note", content=markdown_content, path=notesfile)
	assert note is not None
	
	notes = load_notes(path=notesfile)
	loaded = next(n for n in notes if n.id == note.id)
	assert loaded.content == markdown_content


def test_note_multiple_links(notesfile, datafile):
	"""Test note with multiple linked notes and tasks."""
	task1 = add_task("Task 1", path=datafile)
	task2 = add_task("Task 2", path=datafile)
	
	note1 = create_note("Main Note", path=notesfile)
	note2 = create_note("Related Note 1", path=notesfile)
	note3 = create_note("Related Note 2", path=notesfile)
	
	# Link to multiple notes
	link_note_to_note(note1.id, note2.id, path=notesfile)
	link_note_to_note(note1.id, note3.id, path=notesfile)
	
	# Link to multiple tasks
	link_note_to_task(note1.id, task1.id, notes_path=notesfile, tasks_path=datafile)
	link_note_to_task(note1.id, task2.id, notes_path=notesfile, tasks_path=datafile)
	
	notes = load_notes(path=notesfile)
	main_note = next(n for n in notes if n.id == note1.id)
	
	assert len(main_note.linked_notes) == 2
	assert note2.id in main_note.linked_notes
	assert note3.id in main_note.linked_notes
	
	assert len(main_note.linked_tasks) == 2
	assert task1.id in main_note.linked_tasks
	assert task2.id in main_note.linked_tasks


# =============================================================================
# Markdown Export Tests
# =============================================================================

def test_export_note_to_markdown(notesfile):
	"""Test exporting a single note to markdown file."""
	note = create_note("Test Note", content="This is the content", tags=["test"], path=notesfile)
	
	with tempfile.TemporaryDirectory() as tmpdir:
		output_path = os.path.join(tmpdir, "test_note.md")
		ok = export_note_to_markdown(note.id, output_path, notes_path=notesfile)
		assert ok is True
		
		# Verify file was created
		assert os.path.exists(output_path)
		
		# Read and verify content
		with open(output_path, 'r', encoding='utf-8') as f:
			content = f.read()
		
		assert "# Test Note" in content
		assert note.id in content
		assert "This is the content" in content
		assert "`test`" in content


def test_export_note_to_markdown_auto_filename(notesfile):
	"""Test exporting note with auto-generated filename."""
	note = create_note("My Test Note", content="Content", path=notesfile)
	
	with tempfile.TemporaryDirectory() as tmpdir:
		# Change to temp directory for auto filename
		import os
		old_cwd = os.getcwd()
		try:
			os.chdir(tmpdir)
			ok = export_note_to_markdown(note.id, notes_path=notesfile)
			assert ok is True
			
			# Check that file was created with sanitized name
			expected_file = "My_Test_Note.md"
			assert os.path.exists(expected_file)
		finally:
			os.chdir(old_cwd)


def test_export_note_with_links(notesfile):
	"""Test exporting note with linked notes."""
	note1 = create_note("Main Note", content="Main content", path=notesfile)
	note2 = create_note("Linked Note", content="Linked content", path=notesfile)
	
	link_note_to_note(note1.id, note2.id, path=notesfile)
	
	with tempfile.TemporaryDirectory() as tmpdir:
		output_path = os.path.join(tmpdir, "main.md")
		ok = export_note_to_markdown(note1.id, output_path, notes_path=notesfile)
		assert ok is True
		
		with open(output_path, 'r', encoding='utf-8') as f:
			content = f.read()
		
		assert "## Links" in content
		assert "**Linked Notes:**" in content
		assert "Linked Note" in content
		assert note2.id in content


def test_export_note_with_task_links(notesfile, datafile):
	"""Test exporting note with linked tasks."""
	task = add_task("Test Task", path=datafile)
	note = create_note("Note with Task", content="Content", path=notesfile)
	
	link_note_to_task(note.id, task.id, notes_path=notesfile, tasks_path=datafile)
	
	with tempfile.TemporaryDirectory() as tmpdir:
		output_path = os.path.join(tmpdir, "note.md")
		ok = export_note_to_markdown(note.id, output_path, notes_path=notesfile)
		assert ok is True
		
		with open(output_path, 'r', encoding='utf-8') as f:
			content = f.read()
		
		assert "**Linked Tasks:**" in content
		assert task.id in content


def test_export_nonexistent_note(notesfile):
	"""Test exporting a note that doesn't exist."""
	with tempfile.TemporaryDirectory() as tmpdir:
		output_path = os.path.join(tmpdir, "test.md")
		ok = export_note_to_markdown("nonexistent", output_path, notes_path=notesfile)
		assert ok is False
		assert not os.path.exists(output_path)


def test_export_note_with_markdown_content(notesfile):
	"""Test that markdown content is preserved in export."""
	markdown_content = """# Heading

## Subheading

- List item 1
- List item 2

**Bold** and *italic*

```python
print('code')
```
"""
	note = create_note("Markdown Note", content=markdown_content, path=notesfile)
	
	with tempfile.TemporaryDirectory() as tmpdir:
		output_path = os.path.join(tmpdir, "markdown.md")
		ok = export_note_to_markdown(note.id, output_path, notes_path=notesfile)
		assert ok is True
		
		with open(output_path, 'r', encoding='utf-8') as f:
			content = f.read()
		
		# Verify markdown is preserved
		assert "## Subheading" in content
		assert "- List item 1" in content
		assert "**Bold**" in content
		assert "```python" in content


def test_export_all_notes_to_markdown(notesfile):
	"""Test exporting all notes to a directory."""
	note1 = create_note("First Note", content="Content 1", tags=["tag1"], path=notesfile)
	note2 = create_note("Second Note", content="Content 2", tags=["tag1", "tag2"], path=notesfile)
	note3 = create_note("Third Note", content="Content 3", tags=["tag2"], path=notesfile)
	
	with tempfile.TemporaryDirectory() as tmpdir:
		output_dir = os.path.join(tmpdir, "notes_export")
		count = export_all_notes_to_markdown(output_dir, notes_path=notesfile)
		
		assert count == 3
		assert os.path.exists(output_dir)
		
		# Verify individual note files were created
		assert os.path.exists(os.path.join(output_dir, "First_Note.md"))
		assert os.path.exists(os.path.join(output_dir, "Second_Note.md"))
		assert os.path.exists(os.path.join(output_dir, "Third_Note.md"))
		
		# Verify index file was created
		index_path = os.path.join(output_dir, "INDEX.md")
		assert os.path.exists(index_path)
		
		# Read and verify index content
		with open(index_path, 'r', encoding='utf-8') as f:
			index_content = f.read()
		
		assert "# Notes Index" in index_content
		assert "Total notes: 3" in index_content
		assert "First Note" in index_content
		assert "Second Note" in index_content
		assert "Third Note" in index_content


def test_export_all_notes_index_by_tags(notesfile):
	"""Test that index file groups notes by tags."""
	create_note("Python Note", tags=["python", "programming"], path=notesfile)
	create_note("JavaScript Note", tags=["javascript", "programming"], path=notesfile)
	create_note("CSS Note", tags=["css", "design"], path=notesfile)
	
	with tempfile.TemporaryDirectory() as tmpdir:
		output_dir = os.path.join(tmpdir, "export")
		export_all_notes_to_markdown(output_dir, notes_path=notesfile)
		
		index_path = os.path.join(output_dir, "INDEX.md")
		with open(index_path, 'r', encoding='utf-8') as f:
			index_content = f.read()
		
		assert "## Notes by Tag" in index_content
		assert "### python" in index_content or "### css" in index_content
		assert "### programming" in index_content or "### design" in index_content


def test_export_all_notes_empty(notesfile):
	"""Test exporting when there are no notes."""
	with tempfile.TemporaryDirectory() as tmpdir:
		output_dir = os.path.join(tmpdir, "empty_export")
		count = export_all_notes_to_markdown(output_dir, notes_path=notesfile)
		
		assert count == 0
		# Directory is not created when there are no notes
		assert not os.path.exists(output_dir)


def test_export_all_notes_with_links(notesfile):
	"""Test exporting notes that have links between them."""
	note1 = create_note("Parent Note", content="Main", path=notesfile)
	note2 = create_note("Child Note 1", content="Child 1", path=notesfile)
	note3 = create_note("Child Note 2", content="Child 2", path=notesfile)
	
	link_note_to_note(note1.id, note2.id, path=notesfile)
	link_note_to_note(note1.id, note3.id, path=notesfile)
	
	with tempfile.TemporaryDirectory() as tmpdir:
		output_dir = os.path.join(tmpdir, "linked_export")
		count = export_all_notes_to_markdown(output_dir, notes_path=notesfile)
		
		assert count == 3
		
		# Verify parent note has links in its markdown
		parent_file = os.path.join(output_dir, "Parent_Note.md")
		with open(parent_file, 'r', encoding='utf-8') as f:
			content = f.read()
		
		assert "Child Note 1" in content
		assert "Child Note 2" in content
		assert note2.id in content
		assert note3.id in content


def test_export_note_special_characters_in_title(notesfile):
	"""Test exporting note with special characters in title."""
	note = create_note("Note: With/Special*Characters?", content="Content", path=notesfile)
	
	with tempfile.TemporaryDirectory() as tmpdir:
		output_dir = os.path.join(tmpdir, "export")
		export_all_notes_to_markdown(output_dir, notes_path=notesfile)
		
		# Should sanitize filename
		files = os.listdir(output_dir)
		md_files = [f for f in files if f.endswith('.md') and f != 'INDEX.md']
		assert len(md_files) == 1
		# Verify file can be opened
		assert os.path.exists(os.path.join(output_dir, md_files[0]))


def test_export_note_creates_subdirectories(notesfile):
	"""Test that export creates necessary subdirectories."""
	note = create_note("Test", content="Content", path=notesfile)
	
	with tempfile.TemporaryDirectory() as tmpdir:
		output_path = os.path.join(tmpdir, "nested", "dir", "note.md")
		ok = export_note_to_markdown(note.id, output_path, notes_path=notesfile)
		assert ok is True
		assert os.path.exists(output_path)


def test_export_note_metadata_fields(notesfile):
	"""Test that all metadata fields are included in export."""
	note = create_note("Meta Test", content="Content", tags=["tag1", "tag2"], path=notesfile)
	
	with tempfile.TemporaryDirectory() as tmpdir:
		output_path = os.path.join(tmpdir, "meta.md")
		export_note_to_markdown(note.id, output_path, notes_path=notesfile)
		
		with open(output_path, 'r', encoding='utf-8') as f:
			content = f.read()
		
		assert "**ID:**" in content
		assert "**Created:**" in content
		assert "**Updated:**" in content
		assert "**Tags:**" in content
		assert "`tag1`" in content
		assert "`tag2`" in content
		assert note.id in content
		assert note.created_at in content

