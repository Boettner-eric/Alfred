#!/usr/bin/env python3

import requests
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

def download_favicon(url):
    """Download favicon for a website"""
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

# TODO: modify existing bookmark with variations and mods
#  "mods": {
#    "cmd": {
#        "valid": True,
#        "icon": {
#            "path": icon_path
#        },
#        "arg": url,
#        "subtitle": url
#    },
#    "alt": {
#        "valid": True,
#        "arg": url,
#        "subtitle": "Open",
#        "icon": {
#            "path": icon_path
#        }
#    },
#    "ctrl": {
#        "valid": True,
#        "arg": url,
#        "subtitle": title,
#        "icon": {
#            "path": icon_path
#        }
#    }
# }

def add_bookmark(title, url):
    """Add a new bookmark to common.json."""
    uid = f"cm {title.lower()}"
    
    icon_path = download_favicon(url)
    
    new_bookmark = {
        "arg": url,
        "subtitle": url,
        "icon": {
            "path": icon_path
        },
        "uid": uid,
        "title": title
    }
    
    with open('common.json', 'r+') as f:
        data = json.load(f)
        f.seek(0)
        data['items'].append(new_bookmark)
        json.dump(data, f, indent=2)
        f.truncate()
    
    print(f"Successfully added {title} to bookmarks!")

def main():
    parser = argparse.ArgumentParser(description='Add a new bookmark to Alfred workflow')
    parser.add_argument('title', help='Title for the bookmark')
    parser.add_argument('url', help='URL of the website to bookmark')
    args = parser.parse_args()
    
    # Validate URL
    if not re.match(r'https?://', args.url):
        args.url = 'https://' + args.url
    
    add_bookmark(args.title, args.url)

if __name__ == '__main__':
    main() 