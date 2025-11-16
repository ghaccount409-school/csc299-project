import tempfile
import os
import json
from datetime import datetime
import sys
import pytest

# Ensure the tasks2 directory (where prototype_pkms.py lives) is on sys.path so tests can import it
THIS_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
TASKS2_DIR = os.path.join(REPO_ROOT, "tasks2")
if TASKS2_DIR not in sys.path:
	sys.path.insert(0, TASKS2_DIR)

from prototype_pkms import add_task, list_tasks, search_tasks, load_tasks, add_link, show_task, pretty_print, generate_short_id, task_id_exists, search_tasks_by_tags, list_all_tags, list_important_tasks, mark_important, unmark_important, sort_tasks, add_subtask, show_subtasks, delete_task
import io
import contextlib
import re


@pytest.fixture
def datafile():
	tmpdir = tempfile.TemporaryDirectory()
	datafile_path = os.path.join(tmpdir.name, "tasks.json")
	yield datafile_path
	tmpdir.cleanup()

def test_add_and_list_and_search(datafile):
	t = add_task("Buy milk", notes="2 litres", due="tomorrow", tags=["home"], path=datafile)
	assert t.id
	tasks = list_tasks(path=datafile)
	assert len(tasks) == 1
	assert tasks[0].title == "Buy milk"
	found = search_tasks("milk", path=datafile)
	assert len(found) == 1
	assert found[0].id == t.id

def test_search_no_match(datafile):
	add_task("A task", notes="nothing", path=datafile)
	found = search_tasks("zzz", path=datafile)
	assert found == []

def test_tag_filtering_and_multiple_tasks(datafile):
	a = add_task("Task A", tags=["x", "shared"], path=datafile)
	b = add_task("Task B", tags=["y"], path=datafile)
	c = add_task("Task C", tags=["shared"], path=datafile)

	all_tasks = list_tasks(path=datafile)
	assert len(all_tasks) == 3

	shared = list_tasks(path=datafile, tag="shared")
	assert {t.id for t in shared} == {a.id, c.id}

def test_persistence_and_file_contents(datafile):
	add_task("Persist 1", path=datafile)
	add_task("Persist 2", path=datafile)

	# Ensure data file exists and contains 2 items
	with open(datafile, 'r', encoding='utf-8') as f:
		raw = json.load(f)
	assert len(raw) == 2

def test_empty_list_when_no_file(datafile):
	# no file created yet
	tasks = list_tasks(path=datafile)
	assert tasks == []

def test_corrupted_json_is_backed_up_and_returns_empty(datafile):
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
	t = add_task("Time check", path=datafile)
	tasks = list_tasks(path=datafile)
	assert len(tasks) == 1
	created = tasks[0].created_at
	# Should match 'YYYY-MM-DD HH:MM:SS UTC'
	assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC$", created)

def test_linking_and_show(datafile):
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
	# Short IDs should be 8 characters and hex
	t = add_task("Test short ID", path=datafile)
	assert len(t.id) == 8
	assert re.match(r'^[0-9a-f]{8}$', t.id)

def test_multiple_short_ids_are_unique(datafile):
	t1 = add_task("Task 1", path=datafile)
	t2 = add_task("Task 2", path=datafile)
	t3 = add_task("Task 3", path=datafile)
	ids = {t1.id, t2.id, t3.id}
	assert len(ids) == 3

def test_custom_id_creation(datafile):
	t = add_task("Custom task", custom_id="my-task", path=datafile)
	assert t.id == "my-task"
	tasks = list_tasks(path=datafile)
	assert len(tasks) == 1
	assert tasks[0].id == "my-task"

def test_duplicate_custom_id_rejected(datafile):
	add_task("First task", custom_id="dup-id", path=datafile)
	# Try to add second task with same ID
	t2 = add_task("Second task", custom_id="dup-id", path=datafile)
	assert t2 is None
	# Only first task should exist
	tasks = list_tasks(path=datafile)
	assert len(tasks) == 1

def test_task_id_exists_checker(datafile):
	add_task("Existing", custom_id="exists", path=datafile)
	assert task_id_exists("exists", path=datafile)
	assert not task_id_exists("nonexistent", path=datafile)

def test_search_tasks_by_tags_any(datafile):
	# Create tasks with different tag combinations
	add_task("Task 1", tags=["home", "urgent"], path=datafile)
	add_task("Task 2", tags=["work"], path=datafile)
	add_task("Task 3", tags=["home", "shopping"], path=datafile)
    
	# Search for tasks with "home" OR "work"
	found = search_tasks_by_tags(["home", "work"], path=datafile, match_all=False)
	assert len(found) == 3

def test_search_tasks_by_tags_all(datafile):
	# Create tasks with different tag combinations
	add_task("Task 1", tags=["home", "urgent"], path=datafile)
	add_task("Task 2", tags=["work"], path=datafile)
	add_task("Task 3", tags=["home", "urgent", "shopping"], path=datafile)
    
	# Search for tasks with "home" AND "urgent"
	found = search_tasks_by_tags(["home", "urgent"], path=datafile, match_all=True)
	assert len(found) == 2

def test_list_all_tags(datafile):
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
	existing = add_task("Existing", path=datafile)
	result = add_subtask("nonexistent", existing.id, path=datafile)
	assert result is None

def test_add_subtask_nonexistent_subtask(datafile):
	parent = add_task("Parent", path=datafile)
	result = add_subtask(parent.id, "nonexistent-task", path=datafile)
	assert result is None

def test_show_subtasks(datafile):
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
	parent = add_task("Parent with no subtasks", path=datafile)
    
	# show_subtasks on empty parent should return empty list
	subtasks = show_subtasks(parent.id, path=datafile)
	assert len(subtasks) == 0

def test_link_same_subtask_twice(datafile):
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
	"""Delete a task but orphan its subtasks (delete_subtasks=False)."""
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

