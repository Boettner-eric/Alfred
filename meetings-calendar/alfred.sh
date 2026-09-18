# Alfred's "Excluded Events" config, e.g. ["event name"]. Fall back to an empty
# list when it is unset or not valid JSON array so jq never fails on it.
excluded_events="${exclude:-[]}"
if ! printf '%s' "$excluded_events" | jq -e 'type == "array"' > /dev/null 2>&1; then
	excluded_events="[]"
fi

if test -f "meetings.json"; then
	jq --argjson excluded_events "$excluded_events" -f meetings.jq meetings.json
	needs_refresh="$(jq -r '
	  ((.variables.cache_time | type) as $t | if $t == "number" then (now - .variables.cache_time > 300) else true end) as $stale
	  | ((.variables.refresh_started | type) as $t | if $t == "number" then (now - .variables.refresh_started < 60) else false end) as $claimed
	  | $stale and ($claimed | not)
	' meetings.json)"
	if [ "$needs_refresh" = "true" ]; then
		tmp="meetings.json.tmp.$$"
		jq '.variables.refresh_started = now' meetings.json > "$tmp" && mv "$tmp" meetings.json
		(./.venv/bin/python3 meetings.py) > /dev/null 2>&1 &
		disown
	fi
else
	./.venv/bin/python3 meetings.py
	jq --argjson excluded_events "$excluded_events" -f meetings.jq meetings.json
fi