import json
import os
import tempfile
import unittest

import campusnotes


class NotesAppTest(unittest.TestCase):
    def setUp(self):
        self.fd, self.path = tempfile.mkstemp(suffix=".json")
        os.close(self.fd)
        os.unlink(self.path)  # start empty
        self.app = campusnotes.NotesApp(path=self.path)

    def tearDown(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_add_and_list(self):
        self.app.add("Git", "version control")
        self.assertEqual(len(self.app.list_all()), 1)

    def test_search_is_case_insensitive(self):
        self.app.add("git hooks", "run before commit")
        hits = self.app.search("GIT")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["title"], "git hooks")

    def test_delete(self):
        self.app.add("temp", "x")
        self.assertTrue(self.app.delete("temp"))
        self.assertFalse(self.app.delete("temp"))

    def test_add_rejects_empty_title(self):
        with self.assertRaises(ValueError):
            self.app.add("   ")

    def test_persistence(self):
        self.app.add("notes", "persist me")
        reloaded = campusnotes.NotesApp(path=self.path)
        self.assertIn("notes", reloaded.notes)

    def test_export_markdown(self):
        self.app.add("Git", "version control basics")
        out = os.path.join(os.path.dirname(self.path), "export.md")
        count = self.app.export_markdown(out)
        self.assertEqual(count, 1)
        with open(out, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("## Git", text)
        self.assertIn("version control basics", text)

    def test_corrupt_file_recovers(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("{ this is not json")
        recovered = campusnotes.NotesApp(path=self.path)
        self.assertEqual(recovered.notes, {})
        self.assertTrue(os.path.exists(self.path + ".corrupt"))


    def test_add_note_with_tags(self):
        self.app.add("Python", "Study basics", tags=["programming", "exam"])
        note = self.app.notes["Python"]
        self.assertEqual(note["tags"], ["programming", "exam"])

    def test_list_unique_tags(self):
        self.app.add("Python", "Basics", tags=["exam", "programming"])
        self.app.add("Git", "Commands", tags=["exam"])
        self.assertEqual(self.app.list_tags(), ["exam", "programming"])

    def test_filter_notes_by_tag(self):
        self.app.add("Python", "Basics", tags=["programming"])
        self.app.add("Git", "Commands", tags=["tools"])
        results = self.app.by_tag("PROGRAMMING")
        self.assertEqual([note["title"] for note in results], ["Python"])

    def test_old_notes_without_tags(self):
        self.app.add("Python", "Basics")
        self.assertEqual(self.app.notes["Python"]["tags"], [])

if __name__ == "__main__":
    unittest.main()
