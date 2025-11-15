import unittest
import tempfile
import os
import json
from datetime import datetime
import sys

# Ensure the tasks2 directory is on sys.path so tests can import prototype_pkms
TEST_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if TEST_ROOT not in sys.path:
    sys.path.insert(0, TEST_ROOT)

from prototype_pkms import add_task, list_tasks, search_tasks, load_tasks, add_link, show_task, pretty_print, generate_short_id, task_id_exists, search_tasks_by_tags, list_all_tags, list_important_tasks, mark_important, unmark_important, sort_tasks, add_subtask, show_subtasks
import io
import contextlib
import re


class TestTaskCLI(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.datafile = os.path.join(self.tmpdir.name, "tasks.json")

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_add_and_list_and_search(self):
        t = add_task("Buy milk", notes="2 litres", due="tomorrow", tags=["home"], path=self.datafile)
        self.assertTrue(t.id)
        tasks = list_tasks(path=self.datafile)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].title, "Buy milk")
        found = search_tasks("milk", path=self.datafile)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].id, t.id)

    def test_search_no_match(self):
        add_task("A task", notes="nothing", path=self.datafile)
        found = search_tasks("zzz", path=self.datafile)
        self.assertEqual(found, [])

    def test_tag_filtering_and_multiple_tasks(self):
        a = add_task("Task A", tags=["x", "shared"], path=self.datafile)
        b = add_task("Task B", tags=["y"], path=self.datafile)
        c = add_task("Task C", tags=["shared"], path=self.datafile)

        all_tasks = list_tasks(path=self.datafile)
        self.assertEqual(len(all_tasks), 3)

        shared = list_tasks(path=self.datafile, tag="shared")
        self.assertEqual({t.id for t in shared}, {a.id, c.id})

    def test_persistence_and_file_contents(self):
        add_task("Persist 1", path=self.datafile)
        add_task("Persist 2", path=self.datafile)

        # Ensure data file exists and contains 2 items
        with open(self.datafile, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        self.assertEqual(len(raw), 2)

    def test_empty_list_when_no_file(self):
        # no file created yet
        tasks = list_tasks(path=self.datafile)
        self.assertEqual(tasks, [])

    def test_corrupted_json_is_backed_up_and_returns_empty(self):
        # create a corrupted file
        with open(self.datafile, 'w', encoding='utf-8') as f:
            f.write("not a json")

        # calling list_tasks should detect corruption, move file to backup, and return []
        tasks = list_tasks(path=self.datafile)
        self.assertEqual(tasks, [])

        # original should have been moved to a .bak path (with_suffix('.bak'))
        bak_path = os.path.splitext(self.datafile)[0] + ".bak"
        self.assertTrue(os.path.exists(bak_path))
        # original datafile should no longer exist (it was moved)
        self.assertFalse(os.path.exists(self.datafile))

    def test_created_at_human_friendly_format(self):
        t = add_task("Time check", path=self.datafile)
        tasks = list_tasks(path=self.datafile)
        self.assertEqual(len(tasks), 1)
        created = tasks[0].created_at
        # Should match 'YYYY-MM-DD HH:MM:SS UTC'
        import re
        self.assertRegex(created, r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC$")

    def test_linking_and_show(self):
        a = add_task("Parent Task", path=self.datafile)
        b = add_task("Child Task", path=self.datafile)
        ok = add_link(a.id, b.id, path=self.datafile)
        self.assertTrue(ok)

        tasks = list_tasks(path=self.datafile)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            pretty_print(tasks)
        out = buf.getvalue()

        # linked tasks and the view command should appear in the listing for the parent
        self.assertIn("Linked tasks:", out)
        self.assertIn(b.id, out)
        self.assertIn(f"python prototype_pkms.py show {b.id}", out)

    def test_short_id_generation(self):
        # Short IDs should be 8 characters and hex
        t = add_task("Test short ID", path=self.datafile)
        self.assertEqual(len(t.id), 8)
        self.assertTrue(re.match(r'^[0-9a-f]{8}$', t.id))

    def test_multiple_short_ids_are_unique(self):
        t1 = add_task("Task 1", path=self.datafile)
        t2 = add_task("Task 2", path=self.datafile)
        t3 = add_task("Task 3", path=self.datafile)
        ids = {t1.id, t2.id, t3.id}
        self.assertEqual(len(ids), 3)

    def test_custom_id_creation(self):
        t = add_task("Custom task", custom_id="my-task", path=self.datafile)
        self.assertEqual(t.id, "my-task")
        tasks = list_tasks(path=self.datafile)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].id, "my-task")

    def test_duplicate_custom_id_rejected(self):
        add_task("First task", custom_id="dup-id", path=self.datafile)
        # Try to add second task with same ID
        t2 = add_task("Second task", custom_id="dup-id", path=self.datafile)
        self.assertIsNone(t2)
        # Only first task should exist
        tasks = list_tasks(path=self.datafile)
        self.assertEqual(len(tasks), 1)

    def test_task_id_exists_checker(self):
        add_task("Existing", custom_id="exists", path=self.datafile)
        self.assertTrue(task_id_exists("exists", path=self.datafile))
        self.assertFalse(task_id_exists("nonexistent", path=self.datafile))

    def test_search_tasks_by_tags_any(self):
        # Create tasks with different tag combinations
        add_task("Task 1", tags=["home", "urgent"], path=self.datafile)
        add_task("Task 2", tags=["work"], path=self.datafile)
        add_task("Task 3", tags=["home", "shopping"], path=self.datafile)
        
        # Search for tasks with "home" OR "work"
        found = search_tasks_by_tags(["home", "work"], path=self.datafile, match_all=False)
        self.assertEqual(len(found), 3)

    def test_search_tasks_by_tags_all(self):
        # Create tasks with different tag combinations
        add_task("Task 1", tags=["home", "urgent"], path=self.datafile)
        add_task("Task 2", tags=["work"], path=self.datafile)
        add_task("Task 3", tags=["home", "urgent", "shopping"], path=self.datafile)
        
        # Search for tasks with "home" AND "urgent"
        found = search_tasks_by_tags(["home", "urgent"], path=self.datafile, match_all=True)
        self.assertEqual(len(found), 2)

    def test_list_all_tags(self):
        add_task("Task 1", tags=["home", "urgent"], path=self.datafile)
        add_task("Task 2", tags=["work", "urgent"], path=self.datafile)
        add_task("Task 3", tags=["home", "shopping"], path=self.datafile)
        
        tag_counts = list_all_tags(path=self.datafile)
        self.assertEqual(tag_counts["home"], 2)
        self.assertEqual(tag_counts["urgent"], 2)
        self.assertEqual(tag_counts["work"], 1)
        self.assertEqual(tag_counts["shopping"], 1)
        # Verify tags are sorted alphabetically
        self.assertEqual(list(tag_counts.keys()), sorted(tag_counts.keys()))

    def test_mark_important_and_list(self):
        t = add_task("Very important", important=True, path=self.datafile)
        self.assertTrue(t.important)

        important = list_important_tasks(path=self.datafile)
        self.assertEqual(len(important), 1)
        self.assertEqual(important[0].id, t.id)

        # pretty_print should include the label 'Important' when printing
        tasks = list_tasks(path=self.datafile)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            pretty_print(tasks)
        out = buf.getvalue()
        self.assertIn("Important", out)

    def test_mark_and_unmark_commands(self):
        # Create a non-important task
        t = add_task("Not yet important", path=self.datafile)
        self.assertFalse(getattr(t, 'important', False))

        # Mark it important using helper
        ok = mark_important(t.id, path=self.datafile)
        self.assertTrue(ok)
        tasks = list_important_tasks(path=self.datafile)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].id, t.id)

        # Unmark it
        ok2 = unmark_important(t.id, path=self.datafile)
        self.assertTrue(ok2)
        tasks_after = list_important_tasks(path=self.datafile)
        self.assertEqual(len(tasks_after), 0)

    def test_sort_by_title(self):
        add_task("Zebra", path=self.datafile)
        add_task("Apple", path=self.datafile)
        add_task("Mango", path=self.datafile)
        
        tasks = list_tasks(path=self.datafile)
        sorted_asc = sort_tasks(tasks, sort_by="title", reverse=False)
        sorted_desc = sort_tasks(tasks, sort_by="title", reverse=True)
        
        # Check ascending order
        self.assertEqual(sorted_asc[0].title, "Apple")
        self.assertEqual(sorted_asc[1].title, "Mango")
        self.assertEqual(sorted_asc[2].title, "Zebra")
        
        # Check descending order
        self.assertEqual(sorted_desc[0].title, "Zebra")
        self.assertEqual(sorted_desc[1].title, "Mango")
        self.assertEqual(sorted_desc[2].title, "Apple")

    def test_sort_by_id(self):
        t1 = add_task("Task 1", path=self.datafile)
        t2 = add_task("Task 2", path=self.datafile)
        t3 = add_task("Task 3", path=self.datafile)
        
        tasks = list_tasks(path=self.datafile)
        sorted_asc = sort_tasks(tasks, sort_by="id", reverse=False)
        sorted_desc = sort_tasks(tasks, sort_by="id", reverse=True)
        
        # Ascending should preserve or sort by hex value
        self.assertEqual(len(sorted_asc), 3)
        self.assertEqual(len(sorted_desc), 3)
        # Just verify it returns sorted list
        self.assertEqual(sorted_asc[0].id, sorted(tasks, key=lambda t: t.id)[0].id)

    def test_sort_by_created(self):
        import time
        t1 = add_task("First", path=self.datafile)
        time.sleep(1.1)  # Sleep 1.1 seconds to ensure different second-level timestamps
        t2 = add_task("Second", path=self.datafile)
        
        tasks = list_tasks(path=self.datafile)
        sorted_asc = sort_tasks(tasks, sort_by="created", reverse=False)
        sorted_desc = sort_tasks(tasks, sort_by="created", reverse=True)
        
        # Ascending: oldest first
        self.assertEqual(sorted_asc[0].title, "First")
        self.assertEqual(sorted_asc[1].title, "Second")
        
        # Descending: newest first
        self.assertEqual(sorted_desc[0].title, "Second")
        self.assertEqual(sorted_desc[1].title, "First")

    def test_sort_by_due(self):
        add_task("No due", path=self.datafile)
        add_task("Due early", due="2025-11-10", path=self.datafile)
        add_task("Due late", due="2025-11-20", path=self.datafile)
        
        tasks = list_tasks(path=self.datafile)
        sorted_asc = sort_tasks(tasks, sort_by="due", reverse=False)
        
        # Without due date should be at end
        self.assertIsNotNone(sorted_asc[0].due)
        self.assertIsNotNone(sorted_asc[1].due)
        self.assertIsNone(sorted_asc[2].due)

    def test_add_subtask(self):
        parent = add_task("Parent task", path=self.datafile)
        existing = add_task("Existing task", path=self.datafile)
        
        # Link existing task as subtask
        subtask = add_subtask(parent.id, existing.id, path=self.datafile)
        
        # Verify existing task was linked
        self.assertIsNotNone(subtask)
        self.assertEqual(subtask.id, existing.id)
        
        # Verify parent has subtask reference
        updated_parent = show_task(parent.id, path=self.datafile)
        self.assertIn(existing.id, updated_parent.subtasks)

    def test_add_multiple_subtasks(self):
        parent = add_task("Parent task", path=self.datafile)
        sub1 = add_task("Subtask 1", path=self.datafile)
        sub2 = add_task("Subtask 2", path=self.datafile)
        sub3 = add_task("Subtask 3", path=self.datafile)
        
        # Link all as subtasks
        add_subtask(parent.id, sub1.id, path=self.datafile)
        add_subtask(parent.id, sub2.id, path=self.datafile)
        add_subtask(parent.id, sub3.id, path=self.datafile)
        
        # Verify all subtasks are linked to parent
        tasks = load_tasks(path=self.datafile)
        parent_updated = [t for t in tasks if t.id == parent.id][0]
        self.assertEqual(len(parent_updated.subtasks), 3)
        self.assertIn(sub1.id, parent_updated.subtasks)
        self.assertIn(sub2.id, parent_updated.subtasks)
        self.assertIn(sub3.id, parent_updated.subtasks)

    def test_add_subtask_to_nonexistent_parent(self):
        existing = add_task("Existing", path=self.datafile)
        result = add_subtask("nonexistent", existing.id, path=self.datafile)
        self.assertIsNone(result)

    def test_add_subtask_nonexistent_subtask(self):
        parent = add_task("Parent", path=self.datafile)
        result = add_subtask(parent.id, "nonexistent-task", path=self.datafile)
        self.assertIsNone(result)

    def test_show_subtasks(self):
        parent = add_task("Parent", path=self.datafile)
        sub1 = add_task("Subtask 1", path=self.datafile)
        sub2 = add_task("Subtask 2", path=self.datafile)
        
        # Link both as subtasks
        add_subtask(parent.id, sub1.id, path=self.datafile)
        add_subtask(parent.id, sub2.id, path=self.datafile)
        
        # show_subtasks should return the subtasks
        subtasks = show_subtasks(parent.id, path=self.datafile)
        self.assertEqual(len(subtasks), 2)
        ids = {s.id for s in subtasks}
        self.assertEqual(ids, {sub1.id, sub2.id})

    def test_show_subtasks_empty(self):
        parent = add_task("Parent with no subtasks", path=self.datafile)
        
        # show_subtasks on empty parent should return empty list
        subtasks = show_subtasks(parent.id, path=self.datafile)
        self.assertEqual(len(subtasks), 0)

    def test_link_same_subtask_twice(self):
        parent = add_task("Parent", path=self.datafile)
        existing = add_task("Existing", path=self.datafile)
        
        # Link it twice
        add_subtask(parent.id, existing.id, path=self.datafile)
        add_subtask(parent.id, existing.id, path=self.datafile)
        
        # Should only appear once in subtasks list
        tasks = load_tasks(path=self.datafile)
        parent_updated = [t for t in tasks if t.id == parent.id][0]
        count = parent_updated.subtasks.count(existing.id)
        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()

