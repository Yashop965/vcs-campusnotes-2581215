
"""CampusNotes - a tiny CLI notes organizer for students."""

import json
import os
import sys

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "notes.json")


class NotesApp:
    """Manages notes persisted to a JSON file."""

    def __init__(self, path=DATA_FILE):
        self.path = path
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.notes = json.load(f)
            except json.JSONDecodeError:
                backup = self.path + ".corrupt"
                os.replace(self.path, backup)
                self.notes = {}
                self._log(f"recovered corrupt notes file -> {backup}")
        else:
            self.notes = {}

        # Support notes created before tags were introduced.
        for note in self.notes.values():
            note.setdefault("tags", [])

    @staticmethod
    def _log(message):
        log_path = os.path.join(os.path.dirname(__file__), "campusnotes.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(message + "\n")

    def _save(self):
        folder = os.path.dirname(self.path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.notes, f, indent=2, sort_keys=True)

    def add(self, title, body="", tags=None):
        """Add or update a note, including its tags."""
        title = title.strip()
        if not title:
            raise ValueError("title must not be empty")

        old_note = self.notes.get(title, {})
        if tags is None:
            tags = old_note.get("tags", [])

        clean_tags = []
        seen = set()
        for tag in tags:
            tag = tag.strip()
            key = tag.casefold()
            if tag and key not in seen:
                clean_tags.append(tag)
                seen.add(key)

        self.notes[title] = {
            "title": title,
            "body": body,
            "tags": clean_tags,
        }
        self._save()
        return self.notes[title]

    def delete(self, title):
        existed = self.notes.pop(title, None) is not None
        if existed:
            self._save()
        return existed

    def list_all(self):
        return [self.notes[k] for k in sorted(self.notes)]

    def search(self, keyword):
        keyword = keyword.casefold()
        return [
            note for note in self.list_all()
            if keyword in note["title"].casefold()
            or keyword in note["body"].casefold()
        ]

    def list_tags(self):
        """Return all unique tags in alphabetical order."""
        tags = {}
        for note in self.notes.values():
            for tag in note.get("tags", []):
                tags.setdefault(tag.casefold(), tag)
        return [tags[key] for key in sorted(tags)]

    def by_tag(self, tag):
        """Return notes containing the requested tag."""
        tag = tag.strip().casefold()
        return [
            note for note in self.list_all()
            if any(t.casefold() == tag for t in note.get("tags", []))
        ]

    @staticmethod
    def word_count(note):
        return len(note.get("body", "").split())

    def export_markdown(self, path):
        lines = ["# CampusNotes export", ""]
        for note in self.list_all():
            lines.append(f"## {note['title']}\n")
            if note.get("tags"):
                lines.append("Tags: " + ", ".join(note["tags"]))
                lines.append("")
            lines.append(note["body"] or "")
            lines.append("")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return len(self.notes)


def _cmd_add(args, app):
    title = args[0]
    body_parts = []
    tags = []
    i = 1

    while i < len(args):
        if args[i] == "--tag":
            if i + 1 >= len(args):
                raise ValueError("--tag requires a tag name")
            tags.append(args[i + 1])
            i += 2
        else:
            body_parts.append(args[i])
            i += 1

    app.add(title, " ".join(body_parts), tags=tags)
    print(f'Added note "{title}"')


def _cmd_list(args, app):
    for note in app.list_all():
        print(f"- {note['title']}  ({NotesApp.word_count(note)} words)")


def _cmd_search(args, app):
    for note in app.search(args[0]):
        print(f"- {note['title']}")


def _cmd_delete(args, app):
    title = args[0]
    if app.delete(title):
        print(f'Deleted note "{title}"')
    else:
        print(f'No note titled "{title}"')


def _cmd_export(args, app):
    count = app.export_markdown(args[0])
    print(f"Exported {count} notes to {args[0]}")


def _cmd_tags(args, app):
    for tag in app.list_tags():
        print(f"- {tag}")


def _cmd_bytag(args, app):
    for note in app.by_tag(args[0]):
        print(f"- {note['title']}")


COMMANDS = {
    "add": _cmd_add,
    "list": _cmd_list,
    "search": _cmd_search,
    "delete": _cmd_delete,
    "export": _cmd_export,
    "tags": _cmd_tags,
    "bytag": _cmd_bytag,
}

USAGE = (
    "usage: campusnotes.py "
    "<add|list|search|delete|export|tags|bytag> ..."
)


def main(argv):
    if len(argv) < 2 or argv[1] not in COMMANDS:
        print(USAGE)
        return 1

    command = argv[1]

    if command == "list" or command == "tags":
        COMMANDS[command](None, NotesApp())
        return 0

    if len(argv) < 3:
        print(USAGE)
        return 1

    COMMANDS[command](argv[2:], NotesApp())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
