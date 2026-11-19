# Usage: jq -rn --arg url "app://path" --arg defaults "a=1&b=x%20y" --arg prompted $'k=hello world\nk2=x' -f open-url.jq
# Builds the url to open, so spaces in params don't break `open`.
#   url, defaults: already url-shaped (defaults joined with &), only fixed up (see fix_url)
#   prompted: values typed into the param prompts, one key=value per line. They are
#     plain text, so the whole value is encoded, & and = included.
# Both optional args may be empty or start with a separator.
include "encode" {search: "./"};

[ ($ARGS.named.defaults // "" | split("&")[] | select(length > 0) | fix_url),
  ($ARGS.named.prompted // "" | split("\n")[] | select(length > 0)
    | split("=") | if length == 1 then .[0] else .[0] + "=" + (.[1:] | join("=") | @uri) end)
] | join("&") as $query
| ($url | fix_url) + (if $query == "" then "" elif ($url | contains("?")) then "&" + $query else "?" + $query end)
