#!/usr/bin/env python3

import argparse
import html
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urljoin, urlparse

parser = argparse.ArgumentParser(description='Manage Alfred bookmarks')
parser.add_argument('mode', help='list, add, edit, or delete', type=str)
parser.add_argument('parts', nargs='*',
                    help='For add: title words, url, then an optional description. '
                         'For edit: the same, optionally prefixed with a modifier key. '
                         'For delete: title words.')
args = parser.parse_args()

ICON_PX = 256
MAX_CANDIDATES = 8
# shift is reserved for the copy variant every binding gets in list_items
MOD_KEYS = ('cmd', 'alt', 'ctrl', 'fn')
URL_RE = re.compile(r'^(?:https?://\S+|[\w-]+(?:\.[\w-]+)+(?:[/?#]\S*)?)$', re.I)
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')


def fetch(url):
    # imported lazily because the script filter runs list on every keystroke
    import requests
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
    html_text = r.text[:200000]
    found = []
    for tag in re.findall(r'<link\b[^>]*>', html_text, re.I):
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


def page_title(url):
    """The page's own <title>, so a binding gets a readable subtitle for free."""
    r = fetch(url)
    if r is None:
        return None
    match = re.search(r'<title[^>]*>(.*?)</title>', r.text[:200000], re.I | re.S)
    if not match:
        return None
    return re.sub(r'\s+', ' ', html.unescape(match.group(1))).strip()[:60] or None


def read_json():
    with open('common.json') as f:
        return json.load(f)


def write_json(data):
    with tempfile.NamedTemporaryFile('w', dir='.', delete=False, suffix='.tmp') as f:
        json.dump(data, f, indent=2)
        tmp = f.name
    os.replace(tmp, 'common.json')


def find_item(data, title):
    for item in data['items']:
        if item.get('title', '').lower() == title.lower():
            return item
    return None


def host(url):
    # www.site.com and site.com serve the same icon, so treat them as one host
    return re.sub(r'^www\.', '', urlparse(url).netloc)


def same_site(a, b):
    return host(a) == host(b)


def list_items():
    """Emit the saved bookmarks, giving every binding a shift variant that copies its url."""
    data = read_json()
    for item in data['items']:
        icon = item.get('icon', {})
        arg = item.get('arg', '')
        mods = item.get('mods') or {}
        filled = {'shift': copy_mod(arg, icon)}
        for key in MOD_KEYS:
            # an unbound key opens the bookmark itself, so mirror it rather than show nothing
            mod = mods.get(key) or {"valid": bool(arg), "arg": arg,
                                    "subtitle": item.get('subtitle', ''), "icon": icon}
            filled[key] = mod
            filled[f'{key}+shift'] = copy_mod(mod.get('arg', ''), mod.get('icon', icon))
        item['mods'] = {**filled, **mods}
    json.dump(data, sys.stdout)


def copy_mod(url, icon):
    return {"valid": bool(url), "arg": url, "subtitle": f"Copy {url}", "icon": icon}


def add_bookmark(title, url, subtitle):
    data = read_json()
    if find_item(data, title):
        print(f"Bookmark '{title}' already exists")
        return
    data['items'].append({
        "arg": url,
        "subtitle": subtitle or url,
        "icon": {"path": download_favicon(url)},
        "uid": f"cm {title.lower()}",
        "title": title
    })
    write_json(data)
    print(f"Successfully added {title}!")


def edit_bookmark(title, url, subtitle):
    data = read_json()
    item = find_item(data, title)
    if item is None:
        print(f"No bookmark found with title '{title}'")
        return
    if not same_site(url, item.get('arg', '')):
        item['icon'] = {"path": download_favicon(url)}
    item['arg'] = url
    item['subtitle'] = subtitle or url
    write_json(data)
    print(f"Successfully edited {item['title']}!")


def bind_mod(title, key, url, subtitle):
    """Point one modifier at a second url for an existing bookmark, or unbind it."""
    data = read_json()
    item = find_item(data, title)
    if item is None:
        print(f"No bookmark found with title '{title}'")
        return
    mods = item.setdefault('mods', {})
    if url is None:
        if mods.pop(key, None) is None:
            print(f"'{item['title']}' has no {key} binding")
            return
        print(f"Unbound {key} from {item['title']}")
    else:
        icon = item.get('icon', {})
        if not same_site(url, item.get('arg', '')):
            icon = {"path": download_favicon(url)}
        mods[key] = {
            "valid": True,
            "arg": url,
            "subtitle": subtitle or page_title(url) or url,
            "icon": icon
        }
        print(f"Bound {key} on {item['title']} to {mods[key]['subtitle']}")
    if not mods:
        del item['mods']
    write_json(data)


def delete_bookmark(title):
    data = read_json()
    item = find_item(data, title)
    if item is None:
        print(f"No bookmark found with title '{title}'")
        return
    data['items'].remove(item)
    write_json(data)
    print(f"Deleted '{item['title']}'")


def split_query(parts):
    """Title words, then the url, then an optional description of it."""
    for i, part in enumerate(parts):
        if URL_RE.match(part):
            url = part if re.match(r'https?://', part) else 'https://' + part
            return ' '.join(parts[:i]), url, ' '.join(parts[i + 1:])
    return ' '.join(parts), None, ''


def alfred():
    parts = ' '.join(args.parts).split()

    if args.mode == 'list':
        list_items()
        return
    if args.mode == 'delete':
        delete_bookmark(' '.join(parts))
        return
    if args.mode not in ('add', 'edit'):
        print(f"Invalid mode: {args.mode}")
        return

    key = None
    if args.mode == 'edit' and parts and parts[0].lower() in MOD_KEYS:
        key, parts = parts[0].lower(), parts[1:]

    title, url, subtitle = split_query(parts)
    if not title:
        print("Error: provide a bookmark title")
    elif key:
        bind_mod(title, key, url, subtitle)
    elif url is None:
        print("Error: provide a url")
    elif args.mode == 'add':
        add_bookmark(title, url, subtitle)
    else:
        edit_bookmark(title, url, subtitle)


if __name__ == '__main__':
    alfred()
