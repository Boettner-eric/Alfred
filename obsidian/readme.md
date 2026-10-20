# Obsidian

An Alfred workflow for today's daily note tasks and habits, and the Reminder plugin's open reminders.

## Setup

- run `make install` to link the workflow into Alfred
- in the workflow configuration, set
  - **Vault**: the vault folder
  - **Daily folder**: the daily notes folder relative to the vault, e.g. `Daily`
  - **Daily format**: the daily note filename as a strftime format, e.g. `%Y-%m-%d` for `2026-01-31.md`
  - **Tasks heading**: the heading the tasks sit under, e.g. `Tasks`
  - **Habits heading**: the heading the habits sit under, e.g. `Habits`
  - **Tomorrow heading**: the heading for tomorrow's tasks, e.g. `Tomorrow`
- install the [Reminder plugin](https://github.com/uphy/obsidian-reminder) in the vault
- optionally install the [Advanced URI plugin](https://github.com/Vinzent03/obsidian-advanced-uri) so cmd + enter puts the cursor on the selected line

## Usage

- `dl` lists the tasks in today's daily note, enter checks or unchecks the selected task, cmd + enter opens the note at that line, alt + enter moves the task and its subtasks to the end of the tomorrow heading (added at the bottom of the note if missing)
- the tasks under the tomorrow heading in yesterday's daily note are listed first, alt + enter moves them to the end of today's tasks heading
- tomorrow's tasks are listed after today's, alt + enter moves them back to the tasks heading
- `hb` does the same for the habits in today's daily note, without yesterday's or tomorrow's tasks or alt + enter
- `ta <text>` adds an unchecked task to the end of today's tasks heading, cmd + enter adds it to the tomorrow heading instead
- `rm` lists open reminders across the vault, soonest first with how far away each one is, enter opens the note in Obsidian
- typing after any keyword filters the results
- run `./daily.py`, `./daily.py --toggle N`, `./daily.py --move N`, `./daily.py --add TEXT` or `./reminders.py` to see the raw output, with the configuration passed as environment variables, e.g. `vault=~/Notes daily_folder=Daily ./daily.py`, adding `list=habits` for habits, `list=tomorrow` for tomorrow's tasks or `list=yesterday` for yesterday's

Reminders are read from the plugin's `data.json`, which it only updates while Obsidian is running.
