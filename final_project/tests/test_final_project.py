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
	assert f"python prototype_pkms.py show {b.id}" in out

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

