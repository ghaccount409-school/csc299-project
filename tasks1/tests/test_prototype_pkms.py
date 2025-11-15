import unittest
import tempfile
import os
import json
from datetime import datetime

from prototype_pkms import add_task, list_tasks, search_tasks, load_tasks, add_link, show_task, pretty_print
import io
import contextlib


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

    def test_created_at_iso_and_z_suffix(self):
        t = add_task("Time check", path=self.datafile)
        tasks = list_tasks(path=self.datafile)
        self.assertEqual(len(tasks), 1)
        created = tasks[0].created_at
        # should end with Z and be a valid ISO timestamp when trimming the Z
        self.assertTrue(created.endswith("Z"))
        # basic parse check (without timezone)
        datetime.fromisoformat(created.rstrip("Z"))

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


if __name__ == "__main__":
    unittest.main()
