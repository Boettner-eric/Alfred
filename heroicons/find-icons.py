#!/usr/bin/env python3
import sys
import json
import os
from pathlib import Path

def fuzzy_score(query, icon):
    """
    Calculate fuzzy match score based on sequential character matches.

    Returns percentage (0-100) of query characters found in order in the icon name.

    Example:
        fuzzy_score("usr", "user") -> 75 (3/4 chars match)
        fuzzy_score("usr", "cursor") -> 100 (all chars found in order)
    """
    if not query:
        return 0

    matches = 0
    query_pos = 0
    query_len = len(query)

    for char in icon:
        if query_pos < query_len and char == query[query_pos]:
            matches += 1
            query_pos += 1

    return (matches * 100) // query_len


def calculate_score(query, icon_name):
    """
    Calculate relevance score for an icon name given a query.

    Scoring hierarchy:
    1. Exact match: 1000 points (highest priority)
    2. Starts with query: 500 - length
    3. Contains query: 200 - length
    4. Fuzzy match: 0-100 based on sequential character matches
    """
    q_lower = query.lower()
    i_lower = icon_name.lower()

    if i_lower == q_lower:
        return 1000

    if i_lower.startswith(q_lower):
        return 500 - len(icon_name)

    if q_lower in i_lower:
        return 200 - len(icon_name)

    return fuzzy_score(q_lower, i_lower)


def title_case_icon_name(icon_name):
    return " ".join(word.capitalize() for word in icon_name.split("-"))


def main():
    """
    Search heroicons for a given term
    """
    if len(sys.argv) < 2:
        print('{"items":[]}')
        return

    query = sys.argv[1]

    script_dir = Path(__file__).parent / "heroicons" / "optimized"
    icon_dir = script_dir / "24" / "outline"
    solid_icon_dir = script_dir / "24" / "solid"
    solid_micro_icon_dir = script_dir / "16" / "solid"
    solid_mini_icon_dir = script_dir / "20" / "solid"

    if not icon_dir.exists():
        default_items = [
            {
                "title": "Download heroicons",
                "subtitle": "clone heroicons git repo",
                "arg": "download",
                "icon": {"path": "arrow-down-on-square.svg"}
            }
        ]

        print(json.dumps({"items": default_items}, ensure_ascii=False))
        return

    results = []
    icons = [f.stem for f in Path(str(icon_dir)).glob("*.svg")]

    for icon_name in icons:
        score = calculate_score(query, icon_name)

        if score > 0:
            results.append((score, icon_name))

    results.sort(reverse=True, key=lambda x: x[0])
    results = results[:10]

    items = []
    for score, icon_name in results:
        display_name = title_case_icon_name(icon_name)

        items.append({
            "title": display_name,
            "subtitle": f"hero-{icon_name}",
            "arg": f"hero-{icon_name}",
            "icon": {"path": str(icon_dir / f"{icon_name}.svg")},
            "mods": {
                "cmd": {
                    "icon": {"path": str(solid_icon_dir / f"{icon_name}.svg")},
                    "arg": f"hero-{icon_name}-solid",
                    "subtitle": f"hero-{icon_name}-solid"
                },
                "alt": {
                    "icon": {"path": str(solid_mini_icon_dir / f"{icon_name}.svg")},
                    "arg": f"hero-{icon_name}-solid",
                    "subtitle": f"hero-{icon_name}-solid (mini)"
                },
                "ctrl": {
                    "icon": {"path": str(solid_micro_icon_dir / f"{icon_name}.svg")},
                    "arg": f"hero-{icon_name}-solid",
                    "subtitle": f"hero-{icon_name}-solid (micro)"
                }
            }
        })

    print(json.dumps({"items": items}, ensure_ascii=False))


if __name__ == "__main__":
    main()
