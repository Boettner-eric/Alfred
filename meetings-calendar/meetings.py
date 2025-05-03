from __future__ import print_function
import argparse
from datetime import datetime as dt
from re import findall
from dateutil.parser import parse
from time_format import time_till
import time
import os.path
from json import load, loads, dump, dumps

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

parser = argparse.ArgumentParser()
parser.add_argument(
    "-d", "--debug", help="print api result to a file", action="store_true"
)
parser.add_argument(
    "-a", "--alfred", help="for alfred command parsing", action="store_true"
)
parser.add_argument(
    "-r", "--register", help="add a new user", type=str, metavar="USERNAME"
)
args = parser.parse_args()

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

TIME_FORMAT = "%a %B %-d %-I:%M"


def register_user():
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    return flow.run_local_server(port=0)


def login_users():
    """
    Login all users from token files
    """
    logins = []
    if os.path.exists("tokens") and os.listdir("tokens") != []:
        for token_file in os.listdir("tokens"):
            logins.append(login(os.path.join("tokens", token_file)))
    elif os.path.exists("tokens"):
        logins.append(login("tokens/primary.json"))
    else:
        os.makedirs("tokens")
        logins.append(login("tokens/primary.json"))
    return logins


def login(token_path):
    """
    Login a user from a token file
    """
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                creds = register_user()

        else:
            creds = register_user()

        service = build("oauth2", "v2", credentials=creds)
        user_info = service.userinfo().get().execute()
        email = user_info.get("email")

        # Update the token file with the account email
        token_data = loads(creds.to_json())
        token_data["account"] = email
        with open(token_path, "w") as token:
            dump(token_data, token, indent=2)
    return creds


def get_events():
    """
    Get the upcoming events from the Google Calendar API.
    """
    try:
        events = []
        logins = login_users()
        for credentials in logins:
            service = build("calendar", "v3", credentials=credentials)
            # Call the Calendar API
            now = dt.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=now,
                    maxResults=40,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events.extend(
                map(
                    lambda x: {**x, "email": credentials._account},
                    events_result.get("items", []),
                )
            )

        if not events:
            return
        events.sort(key=by_datetime)

        return [
            event
            for event in events
            if by_datetime(event) <= time.time() + (14 * 24 * 60 * 60)
        ]

    except HttpError as error:
        print("An error occurred: %s" % error)


def by_datetime(event):
    stime = parse(event["start"].get("dateTime", event["start"].get("date")))
    return time.mktime(stime.timetuple())


# google calendar puts urls all over calendar events so this function hopefully checks for all of them
def parseMeetingUrl(url):
    MEETING_PATTERNS = {
        r"http[s]?://(?:[a-zA-Z0-9-]+\.)?zoom\.us/j(?:[a-zA-Z0-9$-_@.&+!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+": "./icons/zoom.png",
        r"https://meet\.google\.com\/(?:[a-z]|[0-9]|[-])+": "./icons/meet.png",
        r"https://app.slack.com/huddle/[a-zA-Z0-9]*/[a-zA-Z0-9]*": "./icons/slack.png",
    }

    for pattern, icon in MEETING_PATTERNS.items():
        matches = findall(pattern, url)
        if matches:
            return (matches[0], icon)

    return (False, "./icons/cal.png")


def generate(events):
    meetings = []
    for event in events:
        stime = parse(event["start"].get("dateTime", event["start"].get("date")))
        start = dt.strftime(stime, format=TIME_FORMAT)
        endTime = parse(event["end"].get("dateTime", event["end"].get("date")))
        end = dt.strftime(endTime, format=TIME_FORMAT)

        try:
            parseUrl = (
                event["conferenceData"]["entryPoints"][0]["uri"]
                if "conferenceData" in event
                else ""
            )
            (url, urlImg) = parseMeetingUrl(
                parseUrl
                + " "
                + event.get("location", "")
                + " "
                + event.get("description", "")
            )
            url = url or event["htmlLink"]
        except KeyError:
            (url, urlImg) = ("error with link", "")

        if (event["eventType"]) != "outOfOffice":
            subtitle = f"{time_till(stime, endTime)}"

            meetings.append(
                {
                    "arg": url,
                    "subtitle": subtitle,
                    "icon": {"path": urlImg},
                    "title": event["summary"],
                    "mods": {
                        "alt": {
                            "valid": True,
                            "icon": {"path": "./icons/cal.png"},
                            "arg": event["htmlLink"],
                            "subtitle": f"go to calendar {event['email']}",
                        },
                        "cmd": {"valid": True, "arg": url, "subtitle": url},
                        "ctrl": {
                            "valid": True,
                            "arg": url,
                            "subtitle": f"{start} - {end}",
                        },
                    },
                }
            )
    # cache events in json
    with open("meetings.json", "w") as outfile:
        dump({"rerun": 1, "items": meetings, "test": "key"}, outfile, indent=4)


def alfred(meetings):
    print(dumps({"rerun": 1, "items": meetings}, indent=4))


if __name__ == "__main__":
    if args.register:
        login(f"tokens/{args.register}.json")
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
