# Usage: jq --argjson target '{"uid": "meeting-abc-me@example.com", "end": "2026-11-19T10:30:00"}' -f hide-meeting.jq hidden.json
# hidden.json maps a meeting uid to its end time. uids hold the event id, so for a
# recurring meeting only the one occurrence is hidden. Entries that have ended are
# dropped on each write so the file doesn't grow forever.

(now | strflocaltime("%Y-%m-%dT%H:%M:%S")) as $now
| with_entries(select(.value > $now))
| .[$target.uid] = $target.end
