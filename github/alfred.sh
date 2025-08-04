if test -f "repos.json"; then
	jq -f alfred.jq repos.json
    if [ $(jq -r .cache_time repos.json | cut -d. -f1) -gt $(($(date +%s) - 300)) ]; then
	    curl -s --user "$1:$2" https://api.github.com/user/repos | jq ". | {items: ., cache_time: now}" > repos.json &
    fi
else
	curl -s --user "$1:$2" https://api.github.com/user/repos | jq ". | {items: ., cache_time: now}" > repos.json
	jq -f alfred.jq repos.json
fi
