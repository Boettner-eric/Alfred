# Usage: jq --arg url "https://example.com" -f history/add-entry.jq history/history.json
# Counts the url against an equivalent entry already in history (same canonical_url),
# so the same url written two ways stays one entry.
include "url" {search: "./"};

($url | canonical_url) as $canonical
| (first(keys_unsorted[] | select(canonical_url == $canonical)) // $url) as $key
| .[$key] = (.[$key] // 0) + 1
