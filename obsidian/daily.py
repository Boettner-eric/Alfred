#!/usr/bin/env python3
"""Alfred script filter: list the tasks under "# Tasks" in today's Obsidian daily note.

Usage: daily.py [query]      list tasks as Alfred JSON
       daily.py --toggle N   check or uncheck task N (1-based, note order)
"""
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import NamedTuple, Optional

VAULT = os.environ.get("vault", "")
DAILY_DIR = Path(VAULT).expanduser() / os.environ.get("daily_folder", "")
DAILY_FORMAT = os.environ.get("daily_format") or "%Y-%m-%d"
SECTION = (os.environ.get("tasks_heading") or "Tasks").lower()
MISSING_VAULT = "Set the vault in the workflow configuration"
# leading zero-width space stops Alfred trimming; two 18pt spaces match two 12pt spaces plus a thin space
TITLE_INDENT, SUBTITLE_INDENT = "  ", "   "
ANCHOR = "​"
TASK_RE = re.compile(r"^(\s*)[-*] \[(.)\] (.+)$")


def note_path(day):
    return DAILY_DIR / f"{day.strftime(DAILY_FORMAT)}.md"


class Task(NamedTuple):
    index: int  # 1-based, note order
    line_number: int
    text: str
    done: bool
    parent: Optional[str]
    depth: int


def read_tasks(lines):
    tasks, in_section, ancestors = [], False, []
    for line_number, line in enumerate(lines):
        heading = re.match(r"^#+\s+(.*)$", line)
        if heading:
            in_section = heading.group(1).strip().lower() == SECTION
            ancestors = []
            continue
        match = TASK_RE.match(line) if in_section else None
        if match:
            indent, check, text = len(match.group(1).expandtabs(4)), match.group(2), match.group(3).strip()
            while ancestors and ancestors[-1][0] >= indent:
                ancestors.pop()
            parent = ancestors[-1][1] if ancestors else None
            tasks.append(Task(len(tasks) + 1, line_number, text, check != " ", parent, len(ancestors)))
            ancestors.append((indent, text))
    return tasks


def toggle_task(path, index):
    lines = path.read_text().splitlines(keepends=True)
    task = next((t for t in read_tasks(lines) if t.index == index), None)
    if task is None:
        sys.exit(f"No task {index} in {path.name}")
    lines[task.line_number] = re.sub(r"\[.\]", "[ ]" if task.done else "[x]", lines[task.line_number], count=1)
    path.write_text("".join(lines))
    print(f"{'unchecked' if task.done else 'checked'}: {task.text}")


def list_tasks(path, query):
    if not path.exists():
        return [{"title": "No daily note for today", "subtitle": str(path), "valid": False}]

    # no uid, so Alfred keeps note order instead of ranking by usage
    items = [
        {
            "title": ANCHOR + TITLE_INDENT * t.depth + t.text,
            "icon": {"path": f"icons/{'checked' if t.done else 'unchecked'}.png"},
            "subtitle": ANCHOR + SUBTITLE_INDENT * t.depth + (f"subtask - {t.parent}" if t.parent else "task"),
            "arg": str(t.index),
            "quicklookurl": str(path),
        }
        for t in read_tasks(path.read_text().splitlines())
        if query in t.text.lower()
    ]
    return items or [{"title": "No tasks", "subtitle": path.name, "valid": False}]


def main():
    toggle = sys.argv[1:2] == ["--toggle"]
    if not VAULT:
        if toggle:
            sys.exit(MISSING_VAULT)
        json.dump({"items": [{"title": MISSING_VAULT, "valid": False}]}, sys.stdout)
        return

    path = note_path(date.today())
    if toggle:
        if len(sys.argv) != 3 or not sys.argv[2].isdigit():
            sys.exit("Usage: daily.py --toggle N")
        toggle_task(path, int(sys.argv[2]))
        return

    query = " ".join(sys.argv[1:]).strip().lower()
    json.dump({"items": list_tasks(path, query)}, sys.stdout)


if __name__ == "__main__":
    main()
