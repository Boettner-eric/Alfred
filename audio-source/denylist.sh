#!/usr/bin/env bash
# Hide a device from the list for one type by adding it to that type's denylist.
# Usage: ./denylist.sh "output,Device Name"

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

type=${1%%,*}
name=${1#*,}
key=${type}_denylist

# Alfred hands user configuration to scripts as env vars. Older configs wrap the
# array in single quotes; it is written back as plain JSON either way.
list=$(jq -nc --arg current "$(printenv "$key")" --arg name "$name" '
	$current | ltrimstr("'"'"'") | rtrimstr("'"'"'") | (fromjson? // [])
	| (if type == "array" then . else [] end)
	| if index([$name]) then . else . + [$name] end')

# set configuration writes prefs.plist and updates Alfred's in-memory copy, so
# the next run sees the new list without a workflow reload.
osascript - "$key" "$list" "$alfred_workflow_bundleid" <<'EOF'
on run argv
	tell application id "com.runningwithcrayons.Alfred" to set configuration (item 1 of argv) to value (item 2 of argv) in workflow (item 3 of argv)
end run
EOF

printf 'Hid %s from %ss' "$name" "$type"
