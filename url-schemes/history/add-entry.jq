# Usage: jq --arg url "https://example.com" -f add-entry.jq history.json
.[$url] = (.[$url] // 0) + 1
