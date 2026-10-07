#!/usr/bin/env bash
# Pair every warp point with its git remote, then render the Alfred feed.
# Rows are tab separated (name, path, url) so paths keep any colons they have;
# url is empty when the directory isn't a git repo root.

# Alfred runs scripts with a bare login PATH, so name the usual suspects.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

remote_url() {
	local config=$1/.git/config key url pick=
	# Reading the config file directly costs one git call, and none for non-repos.
	[ -f "$config" ] || return
	# Prefer origin, but fall back to whatever remote the repo does have.
	while read -r key url; do
		[ "$key" = remote.origin.url ] && { pick=$url; break; }
		[ -n "$pick" ] || pick=$url
	done < <(git config -f "$config" --get-regexp '^remote\..*\.url$' 2>/dev/null)
	[ -n "$pick" ] || return
	printf '%s\n' "$pick" |
		sed -E 's#^(git\+ssh|ssh)://##; s#^[^@/]*@([^:/]+)[:/]#https://\1/#; s#\.git$##'
}

warp_points() {
	while IFS=: read -r name path; do
		[ -n "$name" ] && [ -n "$path" ] || continue
		printf '%s\t%s\t%s\n' "$name" "$path" "$(remote_url "${path/#\~/$HOME}")"
	done < ~/.warprc
}

warp_points | jq --arg editor "$editor" --arg terminal "$terminal" -R -n -f alfred.jq
