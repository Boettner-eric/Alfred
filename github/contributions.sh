export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# GraphQL DateTime needs the offset as -07:00, date gives -0700
iso_date() { date "$@" | sed -E 's/(..)$/:\1/'; }

# Query a full year so contribution levels are bucketed like the profile page
fetch_contributions() {
	GH_PAGER=cat gh api graphql \
		-f from="$(iso_date -v-1y -v+1d +%FT00:00:00%z)" \
		-f to="$(iso_date +%FT23:59:59%z)" \
		-f query='query($from:DateTime!,$to:DateTime!){viewer{login contributionsCollection(from:$from,to:$to){contributionCalendar{totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}}}}' \
		| jq -e 'select(.data.viewer) | {data, cache_time: now}' \
		> tmp.contributions.json && mv tmp.contributions.json contributions.json
}

if test -f "contributions.json"; then
	jq -f contributions.jq contributions.json

	# Same stale-while-refreshing claim as alfred.sh
	if [ "$(jq -r '
		(now - .cache_time > 300)
		and ((.refresh_started | type) != "number" or (now - .refresh_started > 60))
	' contributions.json)" = "true" ]; then
		jq '.refresh_started = now' contributions.json > tmp.contributions.json && mv tmp.contributions.json contributions.json
		(fetch_contributions) > /dev/null 2>&1 &
		disown
	fi
else
	fetch_contributions 2> /dev/null
	jq -f contributions.jq contributions.json 2> /dev/null || jq -n -f contributions.jq
fi
