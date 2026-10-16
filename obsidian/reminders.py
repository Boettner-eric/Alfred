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


def plural(count, unit):
    return f"{count} {unit}" if count == 1 else f"{count} {unit}s"


def relative(day, today):
    days = (day - today).days
    if days == 0:
        return "today"
    if abs(days) == 1:
        return "tomorrow" if days > 0 else "yesterday"
    span = abs(days)
    if span < 14:
        amount = plural(span, "day")
    elif span < 56:
        amount = plural(span // 7, "week")
    elif span < 365:
        amount = plural(round(span / 30), "month")
    else:
        amount = plural(round(span / 365), "year")
    return f"in {amount}" if days > 0 else f"{amount} ago"


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

    # no uid, so Alfred keeps date order instead of ranking by usage
    items = []
    for when, has_time, title, path in rows:
        stamp = when.strftime("%a %b %-d, %Y" + (" %H:%M" if has_time else ""))
        overdue = "overdue · " if when < now else ""
        items.append({
            "title": title,
            "subtitle": f"{overdue}{stamp} · {path.stem} - {relative(when.date(), now.date())}",
            "arg": f"obsidian://open?vault={quote(VAULT.name)}&file={quote(str(path.relative_to(VAULT)))}",
            "quicklookurl": str(path),
        })

    json.dump({"items": items or [{"title": "No open reminders", "valid": False}]}, sys.stdout)


if __name__ == "__main__":
    main()
