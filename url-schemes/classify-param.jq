# Usage:
#   jq -n --arg url "app://path?a=1&b=2" --arg index "0" --arg fixed '["a"]' -f classify-param.jq
#
# Asks whether the query param at --arg index is configurable (prompted on each run) or a default (always sent as-is).
# Item variables advance param_index, append default keys to fixed, and set classify_done after the last param.

def query_pairs:
  split("?") | .[1:] | join("?")
  | split("&") | map(select(length > 0) | split("=") | [.[0], (.[1:] | join("="))]);

($url | query_pairs) as $pairs
| ($index | tonumber? // 0) as $i
| ($fixed | fromjson? // []) as $fixed_keys
| $pairs[$i] as [$key, $raw]
| ($raw | try @urid catch $raw) as $value
| (($i + 1) >= ($pairs | length) | tostring) as $done
| ("param \($i + 1) of \($pairs | length)") as $progress
| {items: [
    {
      title: "Configurable: \($key)",
      subtitle: "Prompt for a value each time (e.g. \($value)) · \($progress)",
      arg: $url,
      variables: { param_index: ($i + 1 | tostring), fixed: ($fixed_keys | tostring), classify_done: $done }
    },
    {
      title: "Default: \($key)=\($value)",
      subtitle: "Always send this value · \($progress)",
      arg: $url,
      variables: { param_index: ($i + 1 | tostring), fixed: ($fixed_keys + [$key] | tostring), classify_done: $done }
    }
  ]}
