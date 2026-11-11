#!/usr/bin/env bash
# List every tmux pane as Alfred items, or focus one.
#   ./alfred.sh          Alfred script filter feed; each item's arg is a pane id
#   ./alfred.sh %8       point tmux at pane %8 and bring Ghostty forward

# Alfred runs scripts with a bare login PATH, so name the usual suspects.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
# Without a UTF-8 locale tmux prints tabs and non-ASCII names as "_".
export LANG=${LANG:-en_US.UTF-8}

focus() {
	local pane=$1 client
	# With several Ghostty windows attached, the one used last is the best guess
	# for the window that is about to be raised.
	client=$(tmux list-clients -F '#{client_activity} #{client_name}' 2>/dev/null |
		sort -rn | head -1 | cut -d' ' -f2-)
	if [ -n "$client" ]; then
		# A pane target makes its session, window and pane all current.
		tmux switch-client -c "$client" -t "$pane"
		open -a Ghostty
	else
		open -na Ghostty --args -e tmux attach-session -t "$pane"
	fi
}

# The pinned name, the only field that can be empty, goes last: read collapses
# runs of tabs, which would shift every field after an empty one in the middle.
# It mirrors @window-label in ~/.tmux.conf: only a window renamed by hand
# (automatic-rename off, non-empty) keeps its own name.
# @cc-state is the Claude state cc-state.sh keeps on the pane; "-" stands in
# for none so that field is never empty.
panes() {
	local tab=$'\t'
	tmux list-panes -a -F "#{pane_id}$tab#{session_name}:#{window_index}.#{pane_index}$tab#{window_panes}$tab#{E:@pane-dir}$tab#{pane_tty}$tab#{pane_current_path}$tab#{?#{@cc-state},#{@cc-state},-}$tab#{?#{&&:#{!=:#{automatic-rename},1},#{!=:#W,}},#W,}" 2>/dev/null |
		while IFS=$tab read -r id target count dir tty path state pinned; do
			# window-name.sh is what fills the status bar's labels, so the names
			# here match the tabs. It is handed no window id, which keeps it from
			# clearing stale attention colours as a side effect.
			name=${pinned:-$(~/.config/tmux/window-name.sh "$tty")}
			printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$id" "$target" "$count" "$dir" "${name# }" "$path" "$state"
		done
}

if [ -n "$1" ]; then
	focus "$1"
	exit
fi

# State icons are the Claude Code robot (Simple Icons' claudecode.svg) in the
# status bar colours, with shell.png for panes without a Claude state; the
# words are the cc-sidebar labels.
panes | jq -R -n '
{busy: "working", wait: "needs you", done: "done"} as $labels
| [inputs | select(length > 0) | split("\t") | .[6] as $key | {key: $key, label: $labels[$key]} as $state | {
	# the pane index only earns its place when a window is split
	title: (.[3] + (if .[4] == "" then "" else " · " + .[4] end)
		+ (if .[2] == "1" then "" else "  [pane " + (.[1] | split(".") | last) + "]" end)),
	subtitle: ((if $state.label then $state.label + " · " else "" end) + .[1] + "  " + .[5]),
	arg: .[0],
	text: {copy: .[5]},
	match: ([.[3], .[4], .[1], (.[5] | split("/") | join(" ")), ($state.label // "")] | join(" ")),
	icon: {path: ("icons/" + (if $state.label then $state.key else "shell" end) + ".png")}
}] | if length == 0
	then {items: [{title: "No tmux panes", subtitle: "tmux server is not running", valid: false}]}
	else {items: .} end'
