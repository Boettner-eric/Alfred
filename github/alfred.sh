if test -f "repos.json"; then
    jq -f alfred.jq repos.json
    if [ $(jq -r 'now - (.cache_time | tonumber) > 300' repos.json) = "true" ]; then
        curl -s --user "$1:$2" https://api.github.com/user/repos?per_page=100 | jq ". | {items: ., cache_time: now}" > repos.json &
    fi
else
    curl -s --user "$1:$2" https://api.github.com/user/repos?per_page=100 | jq ". | {items: ., cache_time: now}" > repos.json
    jq -f alfred.jq repos.json
fi