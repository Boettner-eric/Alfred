# Obsidian

An Alfred workflow for today's daily note tasks and the Reminder plugin's open reminders.

## Setup

- run `make install` to link the workflow into Alfred
- in the workflow configuration, set
  - **Vault**: the vault folder
  - **Daily folder**: the daily notes folder relative to the vault, e.g. `Daily`
  - **Daily format**: the daily note filename as a strftime format, e.g. `%Y-%m-%d` for `2026-01-31.md`
  - **Tasks heading**: the heading the tasks sit under, e.g. `Tasks`
- install the [Reminder plugin](https://github.com/uphy/obsidian-reminder) in the vault

## Usage

- `dl` lists the tasks in today's daily note, enter checks or unchecks the selected task
- `rm` lists open reminders across the vault, soonest first, enter opens the note in Obsidian
- typing after either keyword filters the results
- run `./daily.py`, `./daily.py --toggle N` or `./reminders.py` to see the raw output, with the configuration passed as environment variables, e.g. `vault=~/Notes daily_folder=Daily ./daily.py`

Reminders are read from the plugin's `data.json`, which it only updates while Obsidian is running.
