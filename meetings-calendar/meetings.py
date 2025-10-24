from __future__ import print_function
import argparse
from datetime import datetime as dt, timedelta, timezone as tz
from re import findall
from dateutil.parser import parse
from time_format import time_till
import time
import os.path
from json import loads, dump

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug", help="print api result to a file", action="store_true")
parser.add_argument("-r", "--register", help="add a new user", type=str, metavar="USERNAME")
args = parser.parse_args()

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

# google calendar puts urls all over calendar events so this function hopefully checks for all of them
MEETING_PATTERNS = {
        r"http[s]?://(?:[a-zA-Z0-9-]+\.)?zoom\.us/j(?:[a-zA-Z0-9$-_@.&+!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+": "./icons/zoom.png",
        r"https://meet\.google\.com\/(?:[a-z]|[0-9]|[-])+": "./icons/meet.png",
        r"https://app.slack.com/huddle/[a-zA-Z0-9]*/[a-zA-Z0-9]*": "./icons/slack.png",
        r"(?i).*Microsoft Teams.*": "./icons/teams.png", # TODO: make this better
        r"https://teams.microsoft.com/*": "./icons/teams.png", # TODO: make this better
        r"(?i).*Flight.*": "./icons/flight.png",
        r"https://[a-zA-Z0-9\-\._~:/?#\[\]@!$&'()*+,;=%]+": "./icons/website.png",
    }

TIME_FORMAT = "%a %B %-d %-I:%M"
ENCODE_FORMAT = "%Y-%m-%dT%H:%M:%S"

def register_user():
    """
    Register a new user and ensure refresh token is saved
    """
    if not os.path.exists("credentials.json"):
        exit("credentials.json not found, please follow the instructions in the README to create it")

    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Verify refresh token is present
    token_data = loads(creds.to_json())
    if not token_data.get('refresh_token'):
        print("Warning: No refresh token received during registration")
    
    return creds


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
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            print(f"Error loading credentials from {token_path}: {e}")
            creds = None

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing credentials: {e}")
                creds = register_user()
        else:
            print("No valid credentials found, registering new user")
            creds = register_user()

        try:
            service = build("oauth2", "v2", credentials=creds)
            user_info = service.userinfo().get().execute()
            email = user_info.get("email")

            # Update the token file with the account email and ensure refresh token is saved
            token_data = loads(creds.to_json())
            if not token_data.get('refresh_token'):
                print("Warning: No refresh token in new credentials")
            token_data["account"] = email
            with open(token_path, "w") as token:
                dump(token_data, token, indent=2)
            print(f"Successfully saved new token for {email}")
        except Exception as e:
            print(f"Error saving credentials: {e}")
            raise

    return creds


def fetch_events():
    """
    Get the upcoming events from the Google Calendar API.
    """
    try:
        events = []
        logins = login_users()
        for credentials in logins:
            service = build("calendar", "v3", credentials=credentials)
            # Call the Calendar API
            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=(dt.now(tz.utc).isoformat()),
                    timeMax=(dt.now(tz.utc) + timedelta(days=14)).isoformat(),
                    maxResults=40,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            for event in events_result.get("items", []):
                event["email"] = credentials._account
                events.append(event)

        if not events:
            return
        events.sort(key=by_datetime)

        return events
    except HttpError as error:
        print("An error occurred: %s" % error)


def by_datetime(event):
    stime = parse(event["start"].get("dateTime", event["start"].get("date")))
    return time.mktime(stime.timetuple())


def find_meeting_url(*args):
    """
    Find the meeting url in multiple event fields
    """
    for pattern, icon in MEETING_PATTERNS.items():
        matches = findall(pattern, " ".join(args))
        if matches:
            return (matches[0], icon)

    return (False, "./icons/cal.png")


def get_times(event, key):
    """
    Get the start and end times of an event
    """
    parsed_time = parse(event[key].get("dateTime", event[key].get("date")))
    formatted_time = dt.strftime(parsed_time, format=ENCODE_FORMAT)
    display_time = dt.strftime(parsed_time, format=TIME_FORMAT)
    return (formatted_time, display_time, parsed_time)


def safe_get(data, keys, default=""):
    """
    Get a value from a nested dictionary or list
    """
    for key in keys:
        if isinstance(data, list):
            try:
                data = data[key]
            except IndexError:
                data = default
            except KeyError:
                raise KeyError(f"Key {key} not found in {data}")
        elif isinstance(data, dict):
            data = data.get(key, default)
        else:
            return data
    return data


def format_meetings(events):
    """
    Format meetings from google calendar events
    """
    meetings = []
    for event in events:
        (start, display_start, stime) = get_times(event, "start")
        (end, display_end, endTime) = get_times(event, "end")
        try:
            parseUrl = safe_get(event, ["conferenceData", "entryPoints", 0, "uri"])
            (url, urlImg) = find_meeting_url(
                parseUrl,
                event.get("location", ""),
                event.get("description", ""),
                event.get("summary", "")
            )
            url = url or event["htmlLink"]
        except KeyError:
            (url, urlImg) = ("error with link", "./icons/cal.png")

        if (event["eventType"]) != "outOfOffice":
            subtitle = f"{time_till(stime, endTime)}"

            meetings.append(
                {
                    "arg": url,
                    "time": f"{start} - {end}",
                    "subtitle": subtitle,
                    "match": f"{event['summary']} {event['email']}",
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
                            "subtitle": f"{display_start} - {display_end}",
                        },
                    },
                }
            )
    return meetings


def write_to_json(meetings):
    """
    Write the meetings to a json file
    """
    with open("meetings.json", "w") as outfile:
        output_data = {
            "variables": {
                "cache_time": dt.now(tz.utc).strftime('%d/%m/%Y, %H:%M:%S')
            }, 
            "items": meetings
        }
        dump(output_data, outfile, indent=4)


if __name__ == "__main__":
    if args.register:
        login(f"tokens/{args.register}.json")
    else:
        events = fetch_events()
        meetings = format_meetings(events)
        write_to_json(meetings)

        if args.debug and events != None:
            with open("debug_cal.json", "w") as outfile:
                dump({"items": events}, outfile, indent=4)
