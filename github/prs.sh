export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# Chained from users.sh's shift modifier, which sets pr_login, pr_name and pr_org.
# The first run starts the search in the background and shows a loading row; Alfred
# reruns with pr_result set and the list replaces the row once the search lands.
# pr_result is a temp file for this one open, never reused.
if [ -z "$pr_result" ]; then
	tmp="${TMPDIR:-/tmp}"
	find "${tmp%/}" -maxdepth 1 -name 'alfred-prs-*' -mmin +60 -delete 2> /dev/null
	pr_result="${tmp%/}/alfred-prs-$$-$RANDOM.json"
	(
		# GraphQL search skips most of gh search prs's overhead (~1.2s vs ~1.8s)
		GH_PAGER=cat gh api graphql -f q="is:pr is:open assignee:$pr_login org:$pr_org sort:updated-desc" \
			-f query='query($q:String!){search(query:$q,type:ISSUE,first:100){nodes{...on PullRequest{number title url isDraft repository{name} author{login}}}}}' \
			--jq '.data.search.nodes' > "$pr_result.part" 2> /dev/null || echo null > "$pr_result.part"
		mv "$pr_result.part" "$pr_result"
	) > /dev/null 2>&1 &
	disown
fi

if test -f "$pr_result"; then
	jq --arg avatars "$(ls avatars 2> /dev/null)" --arg name "${pr_name:-$pr_login}" --arg org "$pr_org" \
		-f prs.jq "$pr_result"
else
	jq -n --arg file "$pr_result" --arg name "${pr_name:-$pr_login}" '{
		rerun: 0.25,
		variables: {pr_result: $file},
		items: [{title: "Loading pull requests…", subtitle: "Searching for pull requests assigned to \($name)", icon: {path: "icon.png"}, valid: false}]
	}'
fi
