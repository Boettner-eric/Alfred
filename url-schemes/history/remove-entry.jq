# Usage: jq --arg url "https://example.com" -f history/remove-entry.jq history/history.json
# Removes the url and every equivalent entry, since history shows them as one item.
include "url" {search: "./"};

($url | canonical_url) as $canonical
| with_entries(select(.key | canonical_url != $canonical))
