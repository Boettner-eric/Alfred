if test -f "merge.json"; then
	jq -f alfred.jq merge.json
    if [ $(jq -r 'now - (.variables.cache_time | tonumber) > 300' merge.json) = "true" ]; then
        ./.venv/bin/python3 gitlab.py -m > /dev/null &
    fi
else
    ./.venv/bin/python3 gitlab.py -m
    jq -f alfred.jq merge.json
fi