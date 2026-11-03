export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# Members of every org you belong to, merged by login with the orgs they share with you
fetch_users() {
	orgs=$(GH_PAGER=cat gh api user/orgs --jq '.[].login') || return 1
	for org in $orgs; do
		GH_PAGER=cat gh api graphql --paginate -f org="$org" \
			-f query='query($org:String!,$endCursor:String){organization(login:$org){membersWithRole(first:100,after:$endCursor){pageInfo{hasNextPage endCursor} nodes{login name avatarUrl}}}}' \
			| jq -c --arg org "$org" '.data.organization.membersWithRole.nodes[] | . + {org: $org}'
	done \
		| jq -s 'group_by(.login) | map(.[0] + {orgs: map(.org)} | del(.org)) | {items: ., cache_time: now}' \
		> tmp.users.json && mv tmp.users.json users.json
}

# Shares avatars/ with avatars.sh; existing files are kept, so delete one to refresh it
fetch_avatars() {
	mkdir -p avatars
	jq -r '.items[] | "\(.login) \(.avatarUrl)"' users.json \
		| while read -r login url; do test -f "avatars/$login.png" || printf '%s\n%s\n' "$login" "$url"; done \
		| xargs -n 2 -P 16 sh -c 'curl -sfL "$2&s=128" -o "avatars/.$1" && sips -s format png "avatars/.$1" --out "avatars/$1.png" > /dev/null; rm -f "avatars/.$1"' _
}

render() {
	jq --arg avatars "$(ls avatars 2> /dev/null)" --arg default_org "${default_org:-}" -f users.jq users.json
}

if [ "$1" = "fetch" ]; then
	before=$(ls avatars 2> /dev/null | wc -l)
	fetch_users || { printf "Couldn't load users, check that gh is logged in"; exit; }
	fetch_avatars
	after=$(ls avatars | wc -l)
	printf "Loaded %s users (%s new avatars)" "$(jq '.items | length' users.json)" "$((after - before))"
elif test -f "users.json"; then
	render
else
	fetch_users && fetch_avatars
	render 2> /dev/null || jq -n '{items: [{title: "Couldn'"'"'t load users", subtitle: "Check that gh is installed and logged in", valid: false}]}'
fi
