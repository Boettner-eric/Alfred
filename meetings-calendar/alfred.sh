export PYTHONPATH="$(pwd)/site-packages:$PYTHONPATH"

if test -f "meetings.json"; then
	jq -f meetings.jq meetings.json
	needs_refresh="$(jq -r '
	  ((.variables.cache_time | type) as $t | if $t == "number" then (now - .variables.cache_time > 300) else true end) as $stale
	  | ((.variables.refresh_started | type) as $t | if $t == "number" then (now - .variables.refresh_started < 60) else false end) as $claimed
	  | $stale and ($claimed | not)
	' meetings.json)"
	if [ "$needs_refresh" = "true" ]; then
		tmp="meetings.json.tmp.$$"
		jq '.variables.refresh_started = now' meetings.json > "$tmp" && mv "$tmp" meetings.json
		(python3 meetings.py) > /dev/null 2>&1 &
		disown
	fi
else
	python3 meetings.py
	jq -f meetings.jq meetings.json
fi