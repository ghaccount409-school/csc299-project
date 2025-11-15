import unittest
import tempfile
import os
import json
from datetime import datetime

from prototype_pkms import add_task, list_tasks, search_tasks, load_tasks, add_link, show_task, pretty_print, generate_short_id, task_id_exists
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


if __name__ == "__main__":
    unittest.main()
