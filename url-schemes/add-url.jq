# Usage:
#   jq --arg url "finetune://set-volumes" --arg icon "/path/to/app" --arg bundleid "com.example.App" --arg name "" -f add-url.jq urls.json
#   jq --arg url "finetune://mute?app=spotify&muted=true" ... -f add-url.jq urls.json   # params inferred from query string
#
# Required: --arg url, --arg icon, --arg bundleid, --arg name (use "" to default to app name from icon path).
# Optional: params come from URL query string (?key=val&...); types inferred: number→float?, true/false→boolean?, comma-separated→array[string]/array[float], else string.
# Optional: --arg fixed '["key", ...]' marks query params as defaults: stored verbatim and always sent, never prompted.
# Optional: --arg label "My URL" sets the description shown in the urls list (defaults to the path).
#
# Structure: urls.json is an object keyed by scheme id (e.g. "finetune"). Each value:
#   { name: { app, scheme, icon }, paths: { "key": { path, description, background, defaults: { "k": "raw value" }, params: { "k": { type, example } } } } }
#   key is the path slug, suffixed (-2, -3, ...) when that path is already saved, so re-adding a path never overwrites.

def infer_type:
  if type != "string" then "string"
  elif . == "true" or . == "false" then "boolean?"
  elif (tonumber? // false) != false then "float?"
  elif test(",") then
    (tostring | split(",") | map(select(. != ""))) as $arr
    | if ($arr | length) == 0 then "string"
      elif ($arr | map((tonumber? // "nan") != "nan") | all) then "array[float]"
      else "array[string]"
      end
  else "string"
  end;

def _params_from_pairs:
  if length == 0 then {}
  else . as $pairs
  | ($pairs[0][0]) as $k
  | ($pairs[0][1]) as $v
  | ($v | infer_type) as $ty
  | ($pairs[1:] | _params_from_pairs) as $rest
  | $rest + {($k): {"type": $ty, "example": ("e.g. " + $v)}}
  end;

def query_pairs:
  (. | tostring) as $query
  | if $query == "" then []
    else $query | split("&")
      | map(select(length > 0) | split("=") | [.[0], (.[1:] | join("=") // "")])
    end;

# Normalize: ensure we're working on an object (empty or existing)
(if type == "array" then error("urls.json is in old array format; convert to object first") else . end) as $root
| ($url | tostring | split("://")) as $parts
| if ($parts | length) >= 2 then { scheme: ($parts[0] + "://"), path_part: ($parts[1:] | join("://")) } else null end
| if . == null then error("invalid url: \($url)") else . end
| . as $parsed
| ($parsed.path_part | split("?") | .[0]) as $path_only
| ($parsed.path_part | split("?") | if length > 1 then .[1:] | join("?") else "" end) as $query_raw
| (($ARGS.named.fixed // "") | fromjson? // []) as $fixed_keys
| ($query_raw | query_pairs) as $pairs
| ($pairs | map(select(.[0] as $k | $fixed_keys | index($k) | not)) | _params_from_pairs) as $params
| ($pairs | map(select(.[0] as $k | $fixed_keys | index($k))) | map({(.[0]): .[1]}) | add // {}) as $defaults
| ($path_only | split("/")[0]) as $path_slug
| ($ARGS.named.label // "" | if . != "" then . else $path_only | gsub("^/"; "") | if . == "" then $path_slug else . end end) as $description
| ({ path: $path_slug, description: $description, background: false }
  + (if $defaults | length > 0 then { defaults: $defaults } else {} end)
  + (if $params | length > 0 then { params: $params } else {} end)) as $new_path
| ($parsed.scheme | rtrimstr("://")) as $scheme_id
| $root
| if .[$scheme_id] != null then
    (.[$scheme_id].name // .[$scheme_id]) as $existing
    | ($existing.name.paths // $existing.paths // {}) as $existing_paths
    | (first(range(1; infinite) | (if . == 1 then $path_slug else "\($path_slug)-\(.)" end) | select($existing_paths[.] == null))) as $key
    | ($existing_paths + {($key): $new_path}) as $merged_paths
    | .[$scheme_id].name = (($existing.name // $existing) | .paths = $merged_paths)
  else
    . + {($scheme_id): {
      name: {
        app: $bundleid,
        scheme: $parsed.scheme,
        icon: $icon,
        paths: {($path_slug): $new_path}
      }
    }}
  end
