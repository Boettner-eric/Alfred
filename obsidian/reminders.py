#!/usr/bin/env python3
"""Alfred script filter: list open reminders from the Obsidian Reminder plugin's saved state."""
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

VAULT = Path(os.environ.get("vault", "")).expanduser()
DATA = VAULT / ".obsidian/plugins/obsidian-reminder-plugin/data.json"


def parse_time(raw):
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt), fmt != "%Y-%m-%d"
        except ValueError:
            pass
    return None, False


def main():
    if not os.environ.get("vault"):
        json.dump({"items": [{"title": "Set the vault in the workflow configuration", "valid": False}]}, sys.stdout)
        return
    query = " ".join(sys.argv[1:]).strip().lower()
    now = datetime.now()
    reminders = json.loads(DATA.read_text()).get("reminders", {})

    rows = []
    for file, entries in reminders.items():
        for entry in entries:
            when, has_time = parse_time(entry["time"])
            if when and query in entry["title"].lower():
                rows.append((when, has_time, entry["title"], VAULT / file))
    rows.sort(key=lambda r: r[0])

    items = []
    for when, has_time, title, path in rows:
        stamp = when.strftime("%a %b %-d, %Y" + (" %H:%M" if has_time else ""))
        overdue = "overdue · " if when < now else ""
        items.append({
            "uid": f"{path}:{title}",
            "title": title,
            "subtitle": f"{overdue}{stamp} · {path.stem}",
            "arg": f"obsidian://open?vault={quote(VAULT.name)}&file={quote(str(path.relative_to(VAULT)))}",
            "quicklookurl": str(path),
        })

    json.dump({"items": items or [{"title": "No open reminders", "valid": False}]}, sys.stdout)


if __name__ == "__main__":
    main()
