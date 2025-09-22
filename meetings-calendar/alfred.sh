export PYTHONPATH="$(pwd)/site-packages:$PYTHONPATH"

if test -f "meetings.json"; then
    jq -f meetings.jq meetings.json
	python3 meetings.py > /dev/null &
else
	python3 meetings.py
	jq -f meetings.jq meetings.json
fi