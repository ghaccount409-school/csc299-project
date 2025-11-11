import unittest
import tempfile
import os

from prototype_pkms import add_task, list_tasks, search_tasks


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


if __name__ == "__main__":
    unittest.main()
