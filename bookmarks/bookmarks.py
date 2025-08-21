#!/usr/bin/env python3

import requests
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

parser = argparse.ArgumentParser(description='Add a new bookmark to Alfred workflow')
parser.add_argument('mode', help='Add or Edit', type=str)
parser.add_argument('title', help='Title for the bookmark', type=str)
parser.add_argument('url', help='URL of the website to bookmark', type=str)
args = parser.parse_args()


def download_favicon(url):
    """
    Download favicon for a website
    """
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

def edit_bookmark(title, url):
    """
    Edit an existing bookmark in common.json.
    """    
    with open('common.json', 'r+') as f:
        data = json.load(f)
        f.seek(0)
        
        found = False
        for i, item in enumerate(data['items']):
            if item.get('title') == title:
                data['items'][i] = {
                    "arg": url,
                    "subtitle": url,
                    "icon": {"path": download_favicon(url)},
                    "uid": f"cm {title.lower()}",
                    "title": title
                }
                found = True
                break
        
        if not found:
            print(f"No existing bookmark found with title '{title}'")
        else: 
            print(f"Successfully edited {title}!")

        
        json.dump(data, f, indent=2)
        f.truncate()

def add_bookmark(title, url):
    """
    Add a new bookmark to common.json.
    """    
    new_bookmark = {
        "arg": url,
        "subtitle": url,
        "icon": {"path": download_favicon(url)},
        "uid": f"cm {title.lower()}",
        "title": title
    }
    
    with open('common.json', 'r+') as f:
        data = json.load(f)
        f.seek(0)
        data['items'].append(new_bookmark)
        json.dump(data, f, indent=2)
        f.truncate()
    
    print(f"Successfully added {title} to bookmarks!")

def alfred():    
    if not re.match(r'https?://', args.url):
        args.url = 'https://' + args.url
    if args.mode == 'add':
        add_bookmark(args.title, args.url)
    elif args.mode == 'edit':
        edit_bookmark(args.title, args.url)
    else:
        print(f"Invalid mode: {args.mode}")

if __name__ == '__main__':
    alfred()