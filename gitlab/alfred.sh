if test -f "merge.json"; then
	jq -f alfred.jq merge.json
    if [ $(jq -r 'now - (.variables.cache_time | tonumber) > 300' merge.json) = "true" ]; then
        ~/.asdf/shims/python3 gitlab.py -m > /dev/null &
    fi
else
    ~/.asdf/shims/python3 gitlab.py -m > /dev/null &
    jq -f alfred.jq merge.json
fi