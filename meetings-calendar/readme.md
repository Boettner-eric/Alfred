# Meetings Calendar

Jump to slack huddles, zoom rooms and google meets directly from alfred. 

<img src="../screenshots/meetings-calendar.png" width="600">


# Setup
- setup your google calendar api access via this [guide](https://developers.google.com/workspace/calendar/api/quickstart/python#set-up-environment)
- save your generated `credentials.json` to this folder
- `make install` to create alfred symlink
- `pip3 install -r requirements.txt` to install python requirements
- `mcr NAME` in alfred to register each google account


# Mods
- `⌘` -> show meeting url
- `⌥` -> open event in calendar
- `⌃` -> show start and end times


# Run
- `alfred://runtrigger/boettner.eric.meetings_calendar/calendar`


# How it runs
- `meetings.jq` reads cached `meetings.json` and recomputes relative subtitles from *now* (so countdown text stays live)
- if the cache is older than 5 minutes, Alfred `rerun`s every second and `alfred.sh` starts a background `meetings.py`
- `cache_time` is a Unix epoch so Python and jq agree on freshness

File cache + live jq is intentional here — Alfred’s native cache would freeze those relative times for the TTL.