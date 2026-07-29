export PYTHONPATH="$(pwd)/site-packages:$PYTHONPATH"

if test -f "meetings.json"; then
	jq -f meetings.jq meetings.json
	if [ "$(jq -r '(.variables.cache_time | type) as $t | if $t == "number" then (now - .variables.cache_time > 300) else true end' meetings.json)" = "true" ]; then
		python3 meetings.py > /dev/null 2>&1 &
	fi
else
	python3 meetings.py
	jq -f meetings.jq meetings.json
fi