fetch_repos() {
	curl -s --user "$Username:$Token" "https://api.github.com/user/repos?per_page=100" \
		| jq '[.[] | {name, fork, private, description, html_url, ssh_url, pushed_at}]
			| {items: ., cache_time: now}' \
		> tmp.repos.json && mv tmp.repos.json repos.json
}

if test -f "repos.json"; then
	jq -f alfred.jq repos.json

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
	jq -f alfred.jq repos.json
fi
