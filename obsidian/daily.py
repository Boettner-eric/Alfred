#!/usr/bin/env python3
"""Alfred script filter: list the tasks or habits in today's Obsidian daily note.

Usage: daily.py [query]      list yesterday's tomorrow tasks, today's tasks, then tomorrow's tasks, as Alfred JSON
       daily.py --toggle N   check or uncheck task N (1-based, note order)
       daily.py --cancel N   strike through task N, or remove the strikethrough if it has one
       daily.py --move N     move task N and its subtasks between the tasks and tomorrow headings, or from yesterday to today
       daily.py --add TEXT   add an unchecked task after the last task under the tasks heading
Set list=habits, list=tomorrow or list=yesterday to use that list instead of today's tasks.
"""
import json
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import NamedTuple, Optional
from urllib.parse import quote

VAULT = os.environ.get("vault", "")
VAULT_DIR = Path(VAULT).expanduser()
DAILY_DIR = VAULT_DIR / os.environ.get("daily_folder", "")
DAILY_FORMAT = os.environ.get("daily_format") or "%Y-%m-%d"
HEADINGS = {name: os.environ.get(f"{name}_heading") or name.title() for name in ("tasks", "habits", "tomorrow")}
# list name -> (heading, days before today of the note it is in)
LISTS = {"tasks": ("tasks", 0), "habits": ("habits", 0), "tomorrow": ("tomorrow", 0), "yesterday": ("tomorrow", 1)}
LIST = os.environ.get("list") if os.environ.get("list") in LISTS else "tasks"
MOVES = {"tasks": "tomorrow", "tomorrow": "tasks", "yesterday": "tasks"}
ADVANCED_URI = VAULT_DIR / ".obsidian/plugins/obsidian-advanced-uri"
MISSING_VAULT = "Set the vault in the workflow configuration"
# leading zero-width space stops Alfred trimming; two 18pt spaces match two 12pt spaces plus a thin space
TITLE_INDENT, SUBTITLE_INDENT = "  ", "   "
ANCHOR = "​"
TASK_RE = re.compile(r"^(\s*)[-*] \[(.)\] (.+)$")
HEADING_RE = re.compile(r"^#+\s+(.*)$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
STRIKE_RE = re.compile(r"^~~(.+)~~$")


def heading(list_name):
    return HEADINGS[LISTS[list_name][0]]


def note_path(list_name):
    day = date.today() - timedelta(days=LISTS[list_name][1])
    return DAILY_DIR / f"{day.strftime(DAILY_FORMAT)}.md"


def open_url(path, line_number):
    vault, file = quote(VAULT_DIR.name), quote(str(path.relative_to(VAULT_DIR)))
    if ADVANCED_URI.is_dir():
        return f"obsidian://adv-uri?vault={vault}&filepath={file}&line={line_number + 1}"
    return f"obsidian://open?vault={vault}&file={file}"


class Task(NamedTuple):
    index: int  # 1-based, note order
    line_number: int
    text: str
    done: bool
    parent: Optional[str]
    depth: int


def noun(list_name):
    return "habit" if list_name == "habits" else "task"


def is_heading(line, list_name):
    match = HEADING_RE.match(line)
    return bool(match) and match.group(1).strip().lower() == heading(list_name).lower()


def code_lines(lines):
    """Line numbers inside fenced code blocks, where # and - [ ] are just text."""
    code, fence = set(), None
    for i, line in enumerate(lines):
        match = FENCE_RE.match(line)
        if fence or match:
            code.add(i)
        if match:
            fence = None if fence == match.group(1) else fence or match.group(1)
    return code


def sections(lines, list_name):
    """(heading line, end) for each list_name heading, end being the next heading or the end of the note."""
    code = code_lines(lines)
    headings = [i for i, line in enumerate(lines) if i not in code and HEADING_RE.match(line)]
    return [(h, next((n for n in headings if n > h), len(lines))) for h in headings if is_heading(lines[h], list_name)]


def read_tasks(lines, list_name=LIST):
    tasks, code = [], code_lines(lines)
    for start, end in sections(lines, list_name):
        ancestors = []
        for line_number in range(start + 1, end):
            match = None if line_number in code else TASK_RE.match(lines[line_number])
            if not match:
                continue
            indent, check, text = len(match.group(1).expandtabs(4)), match.group(2), match.group(3).strip()
            while ancestors and ancestors[-1][0] >= indent:
                ancestors.pop()
            parent = ancestors[-1][1] if ancestors else None
            tasks.append(Task(len(tasks) + 1, line_number, text, check != " ", parent, len(ancestors)))
            ancestors.append((indent, text))
    return tasks


def find_task(lines, index, path):
    task = next((t for t in read_tasks(lines) if t.index == index), None)
    if task is None:
        sys.exit(f"No {noun(LIST)} {index} under {heading(LIST)} in {path.name}")
    return task


def indent_of(line):
    return len(line) - len(line.lstrip())


def block_end(lines, start):
    """Last line of the task at start: its subtasks and anything else indented under it."""
    end, base = start, indent_of(lines[start].expandtabs(4))
    while end + 1 < len(lines) and lines[end + 1].strip() and indent_of(lines[end + 1].expandtabs(4)) > base:
        end += 1
    return end


def toggle_task(index):
    path = note_path(LIST)
    lines = path.read_text().splitlines(keepends=True)
    task = find_task(lines, index, path)
    lines[task.line_number] = re.sub(r"\[.\]", "[ ]" if task.done else "[x]", lines[task.line_number], count=1)
    path.write_text("".join(lines))
    print(f"{'unchecked' if task.done else 'checked'}: {plain_text(task.text)}")


def cancel_task(index):
    path = note_path(LIST)
    lines = path.read_text().splitlines(keepends=True)
    task = find_task(lines, index, path)
    line = lines[task.line_number]
    match = TASK_RE.match(line)
    struck = STRIKE_RE.match(task.text)
    text = struck.group(1) if struck else f"~~{task.text}~~"
    lines[task.line_number] = line[: match.start(3)] + text + line[match.end(3) :]
    path.write_text("".join(lines))
    print(f"{'restored' if struck else 'cancelled'}: {struck.group(1) if struck else task.text}")


def plain_text(text):
    struck = STRIKE_RE.match(text)
    return struck.group(1) if struck else text


def icon(task):
    if STRIKE_RE.match(task.text):
        return "icons/cancelled.png"
    return f"icons/{'checked' if task.done else 'unchecked'}.png"


def move_task(index):
    if LIST not in MOVES:
        sys.exit(f"Can't move {heading(LIST).lower()}")
    target = MOVES[LIST]
    path, target_path = note_path(LIST), note_path(target)
    if not target_path.exists():
        sys.exit(f"No daily note {target_path.name}")
    lines = path.read_text().splitlines()
    task = find_task(lines, index, path)
    start, end = task.line_number, block_end(lines, task.line_number)
    prefix = lines[start][: indent_of(lines[start])]
    block = [line[len(prefix):] if line.startswith(prefix) else line.lstrip() for line in lines[start : end + 1]]
    rest = lines[:start] + lines[end + 1 :]
    dest = rest if target_path == path else target_path.read_text().splitlines()
    insert_block(dest, target, block)
    target_path.write_text("\n".join(dest) + "\n")
    if dest is not rest:
        path.write_text("\n".join(rest) + "\n")
    print(f"moved to {move_label(LIST).lower()}: {plain_text(task.text)}")


def insert_block(lines, list_name, block):
    """Insert block after the last task under list_name's heading, adding the heading at the bottom if missing.

    Only the checklist is touched: notes, other lists and code under the heading stay where they are.
    """
    found = sections(lines, list_name)
    if not found:
        while lines and not lines[-1].strip():
            lines.pop()
        lines += ["", f"# {heading(list_name)}"]
        found = [(len(lines) - 1, len(lines))]
    start, end = found[0]
    tasks = [t for t in read_tasks(lines, list_name) if start < t.line_number < end]
    if tasks:
        insert = max(block_end(lines, t.line_number) for t in tasks) + 1
    else:
        # no checklist yet: start one under the heading, kept apart from whatever follows
        insert = start + 1
        if insert < len(lines) and lines[insert].strip():
            block = block + [""]
    lines[insert:insert] = block


def add_task(text):
    if LIST == "yesterday":
        sys.exit("Can't add to yesterday")
    path = note_path(LIST)
    if not path.exists():
        sys.exit(f"No daily note {path.name}")
    lines = path.read_text().splitlines()
    insert_block(lines, LIST, [f"- [ ] {text}"])
    path.write_text("\n".join(lines) + "\n")
    print(f"added to {heading(LIST).lower()}: {text}")


def move_label(list_name):
    return "Today" if list_name == "yesterday" else heading(MOVES[list_name])


def subtitle(list_name, task):
    cancelled = "cancelled · " if STRIKE_RE.match(task.text) else ""
    parent = plain_text(task.parent) if task.parent else None
    if list_name in ("tomorrow", "yesterday"):
        label = "yesterday" if list_name == "yesterday" else heading(list_name).lower()
    else:
        label = f"sub{noun(list_name)}" if parent else noun(list_name)
    return cancelled + (f"{label} - {parent}" if parent else label)


def task_items(path, list_name, query):
    lines = path.read_text().splitlines()
    return [
        {
            "uid": f"{list_name}:{t.index}",
            "title": ANCHOR + TITLE_INDENT * t.depth + plain_text(t.text),
            "icon": {"path": icon(t)},
            "subtitle": ANCHOR + SUBTITLE_INDENT * t.depth + subtitle(list_name, t),
            "arg": str(t.index),
            "text": {"copy": plain_text(t.text)},
            "variables": {"list": list_name},
            "mods": {
                "cmd": {"arg": open_url(path, t.line_number), "subtitle": "Open in Obsidian"},
                **({"alt": {"arg": str(t.index), "subtitle": f"Move to {move_label(list_name)}", "variables": {"list": list_name}}} if list_name in MOVES else {}),
                **({"ctrl": {"arg": str(t.index), "subtitle": "Restore" if STRIKE_RE.match(t.text) else "Cancel (strike through)", "variables": {"list": list_name}}} if list_name != "habits" else {}),
            },
            "quicklookurl": str(path),
        }
        for t in read_tasks(lines, list_name)
        if query in t.text.lower()
    ]


def list_tasks(query):
    lists = ["yesterday", LIST, "tomorrow"] if LIST == "tasks" else [LIST]
    items = []
    for name in lists:
        path = note_path(name)
        if path.exists():
            items += task_items(path, name, query)
        elif name == LIST:
            items.append({"title": "No daily note for today", "subtitle": str(path), "valid": False})
            break
    return items or [{"title": f"No {LIST}", "subtitle": note_path(LIST).name, "valid": False}]


def main():
    actions = {"--toggle": toggle_task, "--cancel": cancel_task, "--move": move_task, "--add": add_task}
    action = actions.get(sys.argv[1]) if len(sys.argv) > 1 else None
    if not VAULT:
        if action:
            sys.exit(MISSING_VAULT)
        json.dump({"items": [{"title": MISSING_VAULT, "valid": False}]}, sys.stdout)
        return

    if action is add_task:
        text = " ".join(sys.argv[2:]).strip()
        if not text:
            sys.exit("Usage: daily.py --add TEXT")
        action(text)
        return
    if action:
        if len(sys.argv) != 3 or not sys.argv[2].isdigit():
            sys.exit(f"Usage: daily.py {sys.argv[1]} N")
        action(int(sys.argv[2]))
        return

    query = " ".join(sys.argv[1:]).strip().lower()
    # rerun refreshes the list after a toggle that keeps Alfred open; uids keep the selection,
    # skipknowledge keeps note order instead of ranking by usage
    json.dump({"rerun": 0.1, "skipknowledge": True, "items": list_tasks(query)}, sys.stdout)


if __name__ == "__main__":
    main()
