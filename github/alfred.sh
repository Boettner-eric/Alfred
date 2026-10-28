export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

fetch_repos() {
	login=$(GH_PAGER=cat gh api user --jq .login)
	# Newest event per repo, keyed by html_url; only covers your last 100 events
	active=$(GH_PAGER=cat gh api "users/$login/events?per_page=100" \
		--jq 'map(select(.type != "WatchEvent")) | group_by(.repo.name)
			| map({key: "https://github.com/\(.[0].repo.name)", value: (map(.created_at) | max)}) | from_entries')

	GH_PAGER=cat gh api --paginate 'user/repos?per_page=100' \
		| jq -s --arg login "$login" --argjson active "${active:-{\}}" \
			'add | [.[] | {name, owner: .owner.login, avatar: .owner.avatar_url, fork, private, description, html_url, ssh_url, pushed_at,
				active_at: $active[.html_url]}]
			| {items: ., login: $login, cache_time: now}' \
		> tmp.repos.json && mv tmp.repos.json repos.json
}

# Avatars come from the separate avatars.sh command; only show the ones on disk
render() {
	jq --arg avatars "$(ls avatars 2> /dev/null)" -f alfred.jq repos.json
}

if test -f "repos.json"; then
	render

	# Stale and not already refreshing (stuck claims older than 60s are retried).
	# Claim via refresh_started so Alfred's rerun doesn't stack overlapping curls.
	if [ "$(jq -r '
		((.cache_time | type) != "number" or (now - .cache_time > 300))
		and ((.refresh_started | type) != "number" or (now - .refresh_started > 60))
	' repos.json)" = "true" ]; then
		jq '.refresh_started = now' repos.json > tmp.repos.json && mv tmp.repos.json repos.json
		(fetch_repos) > /dev/null 2>&1 &
		disown
	fi
else
	fetch_repos
	render
fi
