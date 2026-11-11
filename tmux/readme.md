# tmux

An Alfred workflow that lists every tmux pane and jumps to the one you pick in Ghostty.

## Setup

- install `jq` and `tmux` via `brew install jq tmux`
- run `make install` to link the workflow into Alfred

## Usage

- run `./alfred.sh` to see the parsed output
- use `tx` in alfred to list panes and typeahead to filter by directory, command, or path
- enter switches the most recently used tmux client to that pane and brings Ghostty forward
- run `./alfred.sh %8` to jump to a pane id from the shell

Titles reuse the tab labels from `~/.tmux.conf` (`@pane-dir` and `~/.config/tmux/window-name.sh`) so they match the status bar.
