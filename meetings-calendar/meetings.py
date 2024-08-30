from __future__ import print_function
import argparse
from datetime import datetime as dt
from re import findall
from dateutil.parser import parse
from time_format import time_till

import os.path
from json import load, dump, dumps

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

parser = argparse.ArgumentParser()
parser.add_argument(
    "-d", "--debug", help="print api result to a file", action="store_true")
parser.add_argument(
    "-a", "--alfred", help="for alfred command parsing", action="store_true")
args = parser.parse_args()
# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

timeFormat = '%a %B %-d %-I:%M'


def get_events():
    """
    Get the upcoming events from the Google Calendar API.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file(
            'token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    try:
        service = build('calendar', 'v3', credentials=creds)
        # Call the Calendar API
        now = dt.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=40, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            return
        return events

    except HttpError as error:
        print('An error occurred: %s' % error)


# google calendar puts urls all over calendar events so this function hopefully checks for all of them
def parseMeetingUrl(url):
    zoomUrl = findall(
        r'http[s]?://(?:[a-zA-Z0-9-]+\.)?zoom\.us/j(?:[a-zA-Z0-9$-_@.&+!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', url)
    googleUrl = findall(
        r'https://meet\.google\.com\/(?:[a-z]|[0-9]|[-])+', url)
    slackUrl = findall(
        r'https://app.slack.com/huddle/[a-zA-Z0-9]*/[a-zA-Z0-9]*', url)

    if len(zoomUrl) > 0:
        return (zoomUrl[0], "./icons/zoom.png")
    elif len(googleUrl) > 0:
        return (googleUrl[0], "./icons/meet.png")
    elif len(slackUrl) > 0:
        return (slackUrl[0], "./icons/slack.png")
    else:
        return ('not a meeting', "./icons/cal.png")


def generate(events):
    meetings = []
    for event in events:
        stime = parse(event['start'].get(
            'dateTime', event['start'].get('date')))
        start = dt.strftime(stime, format=timeFormat)
        endTime = parse(event['end'].get('dateTime', event['end'].get('date')))
        end = dt.strftime(endTime, format=timeFormat)

        try:
            parseUrl = event['conferenceData']['entryPoints'][0]['uri'] if 'conferenceData' in event else ''
            (url, urlImg) = parseMeetingUrl(parseUrl + " " + event.get('location', '') + " " +
                                            event.get('description', ''))
        except KeyError:
            (url, urlImg) = ('error with link', '')

        if (event["eventType"]) != "outOfOffice":
            subtitle = f'{time_till(stime, endTime)}'

            meetings.append({
                "arg": url,
                "subtitle": subtitle,
                "icon": {
                    "path": urlImg
                },
                "title": event['summary'],
                "mods": {
                    "alt": {
                        "valid": True,
                        "icon": {
                            "path": "./icons/cal.png"
                        },
                        "arg": event['htmlLink'],
                        "subtitle": "go to calendar"
                    },
                    "cmd": {
                        "valid": True,
                        "arg": url,
                        "subtitle": url
                    },
                    "ctrl": {
                        "valid": True,
                        "arg": url,
                        "subtitle": f'{start} - {end}',
                    },
                }
            })
    # cache events in json
    with open("meetings.json", "w") as outfile:
        dump({"rerun": 1, "items": meetings,
              "test": "key"}, outfile, indent=4)


def alfred(meetings):
    print(dumps({"rerun": 0, "items": meetings}, indent=4))


if __name__ == '__main__':
    if args.alfred:
        with open("meetings.json") as f:
            data = load(f)
            alfred(data["items"])
        events = get_events()
        generate(events)
    else:
        events = get_events()
        generate(events)
    if args.debug:
        with open("debug_cal.json", "w") as outfile:
            dump({"items": events}, outfile, indent=4)
