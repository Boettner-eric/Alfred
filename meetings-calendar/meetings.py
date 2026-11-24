from __future__ import print_function
import argparse
from datetime import datetime as dt, timedelta, timezone as tz
from re import findall
from dateutil.parser import parse
from time_format import time_till
import time
import os.path
import signal
import subprocess
import webbrowser
from json import loads, dump

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug", help="print api result to a file", action="store_true")
parser.add_argument("-a", "--auth", help="sign in a new user with 'new', or reauthorize the user saved in TOKEN_PATH", metavar="new|TOKEN_PATH")
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
        r"<?https://teams\.microsoft\.com/l/meetup-join/[a-zA-Z0-9\-\._~:/?#\[\]@!$&'()*+,;=%]+>?": "./icons/teams.png",
        r"<?https://teams\.microsoft\.com/[a-zA-Z0-9\-\._~:/?#\[\]@!$&'()*+,;=%]+>?": "./icons/teams.png",
        r"(?i).*Microsoft Teams.*": "./icons/teams.png",
        r"(?i).*Flight.*": "./icons/flight.png",
        r"<?https://[a-zA-Z0-9\-\._~:/?#\[\]@!$&'()*+,;=%]+>?": "./icons/website.png",
    }

TIME_FORMAT = "%a %B %-d %-I:%M"
ENCODE_FORMAT = "%Y-%m-%dT%H:%M:%S"

def register_user(login_hint=None):
    """
    Run the browser sign in flow. login_hint preselects the account to reauthorize.
    """
    if not os.path.exists("credentials.json"):
        exit("credentials.json not found, please follow the instructions in the README to create it")

    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    # prompt=consent makes google send a refresh token even for an account that already granted access
    options = {"prompt": "consent"}
    if login_hint:
        options["login_hint"] = login_hint
    # python's default macOS opener goes through osascript, which silently fails when alfred runs the script
    webbrowser.register("macos-open", None, webbrowser.GenericBrowser(["/usr/bin/open", "%s"]))
    creds = flow.run_local_server(
        port=0,
        timeout_seconds=300,
        browser="macos-open",
        authorization_prompt_message="Sign in at: {url}",
        **options,
    )

    if not creds.refresh_token:
        print("Warning: No refresh token received during registration")

    return creds


def token_paths():
    """
    Token files saved by login, skipping anything else in the folder like .DS_Store
    """
    if not os.path.exists("tokens"):
        return []
    return sorted(os.path.join("tokens", name) for name in os.listdir("tokens") if name.endswith(".json"))


def token_account(token_path):
    """
    The account email saved in a token file, or None if it can't be read
    """
    try:
        with open(token_path) as token:
            return loads(token.read()).get("account")
    except (OSError, ValueError):
        return None


def account_email(creds):
    """
    The email of the google account the credentials belong to
    """
    return build("oauth2", "v2", credentials=creds).userinfo().get().execute().get("email")


def save_token(creds, email, token_path):
    """
    Save credentials with the account email and return them reloaded so they carry the account
    """
    token_data = loads(creds.to_json())
    if not token_data.get("refresh_token"):
        print("Warning: No refresh token in new credentials")
    token_data["account"] = email

    os.makedirs("tokens", exist_ok=True)
    with open(token_path, "w") as token:
        dump(token_data, token, indent=2)
    print(f"Successfully saved new token for {email} to {token_path}")
    return Credentials.from_authorized_user_info(token_data, SCOPES)


AUTH_PID = "auth.pid"


def replace_previous_auth():
    """
    A sign in waits up to 5 minutes for the browser, so stop an earlier one that is still
    waiting instead of leaving it to hang alongside this one
    """
    try:
        with open(AUTH_PID) as f:
            pid = int(f.read())
        command = subprocess.run(["ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True).stdout
        # the pid may have been reused by another process since the file was written
        if "meetings.py" in command and "--auth" in command:
            os.kill(pid, signal.SIGTERM)
    except (OSError, ValueError):
        pass
    with open(AUTH_PID, "w") as f:
        f.write(str(os.getpid()))


def authorize(target):
    """
    Sign in a new user ("new") or reauthorize the user saved in the target token file
    """
    replace_previous_auth()
    # exit normally when a newer sign in stops this one so the finally below cleans up the pid file
    signal.signal(signal.SIGTERM, lambda *_: exit(1))
    try:
        authorize_account(target)
    finally:
        try:
            with open(AUTH_PID) as f:
                if int(f.read()) == os.getpid():
                    os.remove(AUTH_PID)
        except (OSError, ValueError):
            pass


def authorize_account(target):
    account = None if target == "new" else token_account(target)
    creds = register_user(login_hint=account)
    email = account_email(creds)

    if account and email != account:
        # a different account was picked in the browser, so add it rather than overwrite this one
        print(f"Signed in as {email} instead of {account}, keeping {target}")
        target = "new"
    if target == "new":
        # signing in to an account that is already registered replaces its token instead of adding a duplicate
        existing = next((path for path in token_paths() if token_account(path) == email), None)
        target = existing or os.path.join("tokens", f"{email}.json")

    save_token(creds, email, target)


def login_users():
    """
    Login all users from token files, skipping any that need to sign in again
    """
    return [creds for creds in map(login, token_paths()) if creds]


def mark_needs_reauth(token_path):
    """
    Flag a token whose refresh failed so the users list (mcu) shows it needs reauthorizing
    """
    try:
        with open(token_path) as token:
            token_data = loads(token.read())
        token_data["needs_reauth"] = True
        with open(token_path, "w") as token:
            dump(token_data, token, indent=2)
    except (OSError, ValueError) as e:
        print(f"Error marking {token_path} for reauth: {e}")


def login(token_path):
    """
    Login a user from a token file, refreshing its access token. This runs in the background,
    so it never opens a browser: an account that can't refresh is skipped and flagged to be
    reauthorized from mcu.
    """
    try:
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    except Exception as e:
        print(f"Error loading credentials from {token_path}: {e}")
        return None

    if creds.valid:
        return creds

    try:
        creds.refresh(Request())
    except Exception as e:
        print(f"Error refreshing credentials from {token_path}: {e}")
        mark_needs_reauth(token_path)
        return None

    return save_token(creds, creds.account or account_email(creds), token_path)


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
                event["email"] = credentials.account
                events.append(event)

        if not events:
            return []
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
            return (matches[0].strip('<>').strip(), icon)

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
    for event in events or []:
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
                    "uid": f"meeting-{event['id']}-{event['email']}",
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
    output_data = {
        "variables": {
            "cache_time": dt.now(tz.utc).timestamp()
        },
        "items": meetings
    }
    tmp_path = "meetings.json.tmp"
    with open(tmp_path, "w") as outfile:
        dump(output_data, outfile, indent=4)
    os.replace(tmp_path, "meetings.json")


if __name__ == "__main__":
    if args.auth:
        authorize(args.auth)
    else:
        events = fetch_events()
        meetings = format_meetings(events)
        write_to_json(meetings)

        if args.debug and events != None:
            with open("debug_cal.json", "w") as outfile:
                dump({"items": events}, outfile, indent=4)
