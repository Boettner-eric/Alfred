#!/usr/bin/python3
import requests as rq
import os
import time
import datetime
import argparse
from dotenv import load_dotenv
from os.path import exists
import json

dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".env.local"))

load_dotenv(dotenv_path)

parser = argparse.ArgumentParser()
parser.add_argument(
    "-e", "--emoji", help="specify an emoji to display", default="charmander")
parser.add_argument(
    "-s", "--status", help="specify your status message", default="I forgot something")
parser.add_argument(
    "-t", "--time", help="specify how long you want the status", default="0")
parser.add_argument(
    "-g", "--get_emoji", help="fetch emoji from slack", action="store_true")
parser.add_argument(
    "-a", "--alfred", help="return results for alfred", action="store_true")
parser.add_argument('argv', nargs='*')
args = parser.parse_args()

APPLE_EMOJI_PATH = 'node_modules/emoji-datasource-apple/img/apple/64'
GENERIC_EMOJI_PATH = 'node_modules/emoji-datasource/emoji.json'

def change_status(emoji, status, minutes):
    status = status.replace('/|/', ' ')
    my_datetime = datetime.datetime.now() + datetime.timedelta(minutes=int(minutes))
    unix_timestamp = time.mktime(my_datetime.timetuple())
    slack_url = 'https://slack.com/api/users.profile.set'
    headers = {'content-type': 'application/json',
               'Authorization': 'Bearer ' + os.environ['SLACK_TOKEN']}
    data = {
        "profile": {
            "status_text": status,
            "status_emoji": ':' + emoji + ':',
            "status_expiration": unix_timestamp
        }
    }

    res = rq.post(url=slack_url, headers=headers, json=data)

    if res.json()['ok'] == False:
        print('Error: ' + res.json()['error'])
    else:
        print('Success')


def get_custom_emoji():
    slack_url = 'https://slack.com/api/emoji.list'
    headers = {'content-type': 'application/json',
               'Authorization': 'Bearer ' + os.environ['SLACK_TOKEN']}

    res = rq.get(url=slack_url, headers=headers)

    if res.json()['ok'] == False:
        print('Error: ' + res.json()['error'])
    else:
        for emote, url in res.json()['emoji'].items():
            print(":" + emote + ': ' + url)
            if 'alias' not in url and not exists(f'emotes/{emote}.png'):
                img_data = rq.get(url).content
                with open(f'emotes/{emote}.png', 'wb') as handler:
                    handler.write(img_data)


def emoji_data_exists():
    return (exists(GENERIC_EMOJI_PATH) and 
            os.access(GENERIC_EMOJI_PATH, os.R_OK) and 
            exists(APPLE_EMOJI_PATH) and 
            os.access(APPLE_EMOJI_PATH, os.R_OK))


def find_default_emoji(emote):
    with open(GENERIC_EMOJI_PATH, 'r') as emotes:
        data = json.load(emotes)
        for i in data:
            if i['short_name'] == emote:
                return i['image']


def format_status(status):
    (emote, minutes, status) = status
    if exists(f'emotes/{emote}.png'):
        icon = f'emotes/{emote}.png'
    else:
        default_emote = find_default_emoji(emote)
        if (default_emote):
            icon = f'{APPLE_EMOJI_PATH}/{default_emote}'
        else:
            icon = f'{APPLE_EMOJI_PATH}/1F604.png'
    return {
        "arg": f'{emote} {minutes} {"/|/".join(status.split(" "))}',
        "subtitle": format_time(minutes),
        "icon": {
            "path": icon
        },
        "title": status,
        "mods": {
            "alt": {
                "valid": True,
                "subtitle": "[ emote ] [ minutes ] [ status ]"
            },
            "cmd": {
                "valid": True,
                "subtitle": "secret link"
            },
        }
    }


def format_time(minutes):
    try:
        minutes = int(minutes)
    except ValueError:
        minutes = 0

    if minutes < 60:
        return f"for {pluralize(minutes, 'minute')}"
    elif minutes < 1440:  # 24 hours * 60 minutes
        hours = minutes // 60
        remaining_minutes = minutes % 60

        if remaining_minutes == 0:
            return f"for {pluralize(hours, 'hour')}"
        else:
            return f"for {pluralize(hours, 'hour')} {pluralize(remaining_minutes, 'minute')}"
    else:
        days = minutes // 1440
        remaining_hours = (minutes % 1440) // 60
        remaining_minutes = minutes % 60
        
        if remaining_hours == 0 and remaining_minutes == 0:
            return pluralize(days, 'day')
        elif remaining_minutes == 0:
            return f"for {pluralize(days, 'day')} {pluralize(remaining_hours, 'hour')}"
        else:
            return f"for {pluralize(days, 'day')} {pluralize(remaining_hours, 'hour')} {pluralize(remaining_minutes, 'minute')}"


def pluralize(count, word):
    return f'{count} {word}{"s" if count != 1 else ""}'


def alfred(argp):
    [emote, minutes, *status] = (
        argp + ['charmander', '0', 'your status here'][len(argp):])
    
    print(json.dumps({
        "items": [format_status(status_tuple) for status_tuple in [
            (emote, minutes, ' '.join(status)),
            ('dog2', '10', 'walking the dog'),
            ('pizza', '30', 'eating lunch'),
            ('no_entry', '480', 'out of office')
        ]]
    }))


if __name__ == '__main__':
    if not emoji_data_exists():
        print("Error: Emoji data file not found or not accessible. Please run `npm install`.")
        exit(1)

    if args.get_emoji:
        get_custom_emoji()
    elif args.alfred:
        alfred(args.argv)
    else:
        change_status(args.emoji, args.status, args.time)
