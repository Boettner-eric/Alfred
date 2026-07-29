curl -s --user "$Username:$Token" "https://api.github.com/user/repos?per_page=100" \
    | jq '[.[] | {name, fork, private, description, html_url, ssh_url, pushed_at}] | {items: .}' \
    > tmp.repos.json && mv tmp.repos.json repos.json

jq -f alfred.jq repos.json
