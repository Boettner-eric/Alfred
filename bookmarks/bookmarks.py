#!/usr/bin/env python3

import requests
import argparse
import json
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse

parser = argparse.ArgumentParser(description='Manage Alfred bookmarks')
parser.add_argument('mode', help='add, edit, or delete', type=str)
parser.add_argument('parts', nargs='+', help='For add/edit: title words then URL. For delete: title words.')
args = parser.parse_args()


def download_favicon(url):
    try:
        domain = urlparse(url).netloc
        favicon_url = f"https://www.google.com/s2/favicons?sz=128&domain={domain}"
        response = requests.get(favicon_url, timeout=5)
        response.raise_for_status()
        filename = f"{domain.replace('.', '_')}.png"
        icon_path = Path('icons') / filename
        with open(icon_path, 'wb') as f:
            f.write(response.content)
        return str(icon_path)
    except Exception as e:
        print(f"Warning: Could not download favicon: {e}")
        return "./icons/default.png"


def read_json():
    with open('common.json') as f:
        return json.load(f)


def write_json(data):
    with tempfile.NamedTemporaryFile('w', dir='.', delete=False, suffix='.tmp') as f:
        json.dump(data, f, indent=2)
        tmp = f.name
    os.replace(tmp, 'common.json')


def add_bookmark(title, url):
    data = read_json()
    for item in data['items']:
        if item.get('title') == title:
            print(f"Bookmark '{title}' already exists")
            return
    data['items'].append({
        "arg": url,
        "subtitle": url,
        "icon": {"path": download_favicon(url)},
        "uid": f"cm {title.lower()}",
        "title": title
    })
    write_json(data)
    print(f"Successfully added {title}!")


def edit_bookmark(title, url):
    data = read_json()
    for i, item in enumerate(data['items']):
        if item.get('title') == title:
            data['items'][i] = {
                "arg": url,
                "subtitle": url,
                "icon": {"path": download_favicon(url)},
                "uid": f"cm {title.lower()}",
                "title": title
            }
            write_json(data)
            print(f"Successfully edited {title}!")
            return
    print(f"No bookmark found with title '{title}'")


def delete_bookmark(title):
    data = read_json()
    before = len(data['items'])
    data['items'] = [item for item in data['items'] if item.get('title') != title]
    if len(data['items']) == before:
        print(f"No bookmark found with title '{title}'")
        return
    write_json(data)
    print(f"Deleted '{title}'")


def alfred():
    if args.mode in ('add', 'edit'):
        if len(args.parts) < 2:
            print("Error: provide a title and URL")
            return
        url = args.parts[-1]
        title = ' '.join(args.parts[:-1])
        if not re.match(r'https?://', url):
            url = 'https://' + url
        if args.mode == 'add':
            add_bookmark(title, url)
        else:
            edit_bookmark(title, url)
    elif args.mode == 'delete':
        title = ' '.join(args.parts)
        delete_bookmark(title)
    else:
        print(f"Invalid mode: {args.mode}")


if __name__ == '__main__':
    alfred()
