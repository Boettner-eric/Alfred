#!/usr/bin/env python3

import requests
import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urljoin, urlparse

parser = argparse.ArgumentParser(description='Manage Alfred bookmarks')
parser.add_argument('mode', help='add, edit, or delete', type=str)
parser.add_argument('parts', nargs='+', help='For add/edit: title words then URL. For delete: title words.')
args = parser.parse_args()

ICON_PX = 256
MAX_CANDIDATES = 8
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')


def fetch(url):
    try:
        r = requests.get(url, timeout=6, headers={'User-Agent': UA})
        r.raise_for_status()
        return r
    except Exception:
        return None


def pixel_width(path):
    """Pixel width via sips, or 0 if it isn't an image macOS can read."""
    try:
        out = subprocess.run(['sips', '-g', 'pixelWidth', str(path)],
                             capture_output=True, text=True, timeout=10).stdout
        return int(re.search(r'pixelWidth:\s*(\d+)', out).group(1))
    except Exception:
        return 0


def page_icons(url):
    """Icon URLs the page advertises, largest declared size first."""
    r = fetch(url)
    if r is None:
        return []
    html = r.text[:200000]
    found = []
    for tag in re.findall(r'<link\b[^>]*>', html, re.I):
        rel = re.search(r'rel=["\']([^"\']*)["\']', tag, re.I)
        href = re.search(r'href=["\']([^"\']+)["\']', tag, re.I)
        if not rel or not href:
            continue
        rel, href = rel.group(1).lower(), urljoin(r.url, href.group(1))
        size = re.search(r'sizes=["\'](\d+)x', tag, re.I)
        size = int(size.group(1)) if size else 0
        if rel == 'manifest':
            found += manifest_icons(href)
        elif 'icon' in rel and 'mask-icon' not in rel:
            # apple-touch-icon is 180px on most sites; plain favicons are often 32px
            found.append((size or (180 if 'apple' in rel else 0), href))
    found.sort(key=lambda pair: -pair[0])
    return [href for _, href in found]


def manifest_icons(manifest_url):
    """Icons from a web app manifest - usually the largest a site publishes."""
    r = fetch(manifest_url)
    if r is None:
        return []
    try:
        icons = r.json().get('icons', [])
    except Exception:
        return []
    out = []
    for icon in icons:
        if not icon.get('src'):
            continue
        size = re.match(r'(\d+)x', str(icon.get('sizes', '')))
        out.append((int(size.group(1)) if size else 0, urljoin(r.url, icon['src'])))
    return out


def rasterize_svg(src, dest_dir):
    """Render an SVG with Quick Look - vector art stays sharp at any size."""
    out = subprocess.run(['qlmanage', '-t', '-s', str(ICON_PX), '-o', str(dest_dir), str(src)],
                         capture_output=True, timeout=20)
    rendered = Path(dest_dir) / f'{Path(src).name}.png'
    return rendered if rendered.exists() else None


def best_icon(url, workdir):
    """Download every icon the site offers and keep the highest resolution one."""
    domain = urlparse(url).netloc
    candidates = page_icons(url) + [
        urljoin(url, '/apple-touch-icon.png'),
        urljoin(url, '/fluidicon.png'),
        f'https://www.google.com/s2/favicons?sz={ICON_PX}&domain={domain}',
        f'https://icons.duckduckgo.com/ip3/{domain}.ico',
    ]

    seen, best, best_width = set(), None, 0
    for i, candidate in enumerate(candidates):
        if candidate in seen or len(seen) >= MAX_CANDIDATES:
            continue
        seen.add(candidate)
        r = fetch(candidate)
        if r is None:
            continue
        raw = workdir / f'{i}{Path(urlparse(candidate).path).suffix or ".img"}'
        raw.write_bytes(r.content)

        if raw.suffix.lower() == '.svg' or r.headers.get('content-type', '').startswith('image/svg'):
            raw = raw.with_suffix('.svg')
            raw.write_bytes(r.content)
            rendered = rasterize_svg(raw, workdir)
            if rendered:
                return rendered  # vector beats anything rasterized
            continue

        width = pixel_width(raw)
        if width > best_width:
            best, best_width = raw, width
        if best_width >= ICON_PX:
            break
    return best


def download_favicon(url):
    try:
        icon_path = Path('icons') / f"{urlparse(url).netloc.replace('.', '_')}.png"
        with tempfile.TemporaryDirectory() as tmp:
            source = best_icon(url, Path(tmp))
            if source is None:
                raise RuntimeError('no usable icon found')
            # shrink oversized art, but never upscale - interpolation only adds blur
            resize = ['-Z', str(ICON_PX)] if pixel_width(source) > ICON_PX else []
            subprocess.run(['sips', '-s', 'format', 'png', *resize,
                            str(source), '--out', str(icon_path)],
                           capture_output=True, check=True, timeout=20)
        return str(icon_path)
    except Exception as e:
        print(f"Warning: Could not download favicon: {e}")
        return "icon.png"


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
