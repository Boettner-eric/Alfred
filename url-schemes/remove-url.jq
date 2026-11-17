# Usage: jq --argjson target '{"scheme": "obsidian", "key": "adv-uri-2"}' -f remove-url.jq urls.json
# Removes one saved path, and the whole scheme once its last path is gone.
# key is the paths key, not .path, since several saved urls can share a path.

if .[$target.scheme].name.paths != null then
  del(.[$target.scheme].name.paths[$target.key])
  | if .[$target.scheme].name.paths == {} then del(.[$target.scheme]) else . end
elif .[$target.scheme].paths != null then
  del(.[$target.scheme].paths[$target.key])
  | if .[$target.scheme].paths == {} then del(.[$target.scheme]) else . end
else . end
