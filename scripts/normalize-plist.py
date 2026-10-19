#!/usr/bin/env python3
# Git clean filter: canonical ordering for Alfred info.plist so re-saves from Alfred don't show up as diffs.
# Usage: python3 scripts/normalize-plist.py < info.plist > normalized.plist
import plistlib
import re
import sys


def normalize(d):
    d.get("objects", []).sort(key=lambda o: o.get("uid", ""))
    for links in d.get("connections", {}).values():
        links.sort(key=lambda c: (c.get("sourceoutputuid", ""), c.get("modifiers", 0), c.get("destinationuid", "")))
    out = plistlib.dumps(d, sort_keys=True).decode()
    # Alfred writes whole reals as <real>495</real>; plistlib writes 495.0
    return re.sub(r"<real>(-?\d+)\.0</real>", r"<real>\1</real>", out)


raw = sys.stdin.buffer.read()
try:
    sys.stdout.write(normalize(plistlib.loads(raw)))
except Exception:
    sys.stdout.buffer.write(raw)
