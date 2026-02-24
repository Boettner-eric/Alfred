# Usage:
#   jq --arg url "finetune://volume" --arg icon "/path/to/app" --arg bundleid "com.example.App" --arg name "" -f add-url.jq urls.json
#   jq --arg url "finetune://mute?app=spotify&muted=true" ... -f add-url.jq urls.json   # params inferred from query string
#
# Required: --arg url, --arg icon, --arg bundleid, --arg name (use "" to default to app name from icon path).
# Optional: params come from URL query string (?key=val&...); types inferred: number→float?, true/false→boolean?, comma-separated→array[string]/array[float], else string.

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
  | ($pairs[0][1] | infer_type) as $ty
  | ($pairs[1:] | _params_from_pairs) as $rest
  | $rest + {($k): $ty + " e.g. " + $pairs[0][1]}
  end;

def query_to_param_types:
  (. | tostring) as $query
  | if $query == "" then {}
    else $query | split("&")
      | map(select(length > 0) | split("=") | [.[0], (.[1:] | join("=") // "")])
      | _params_from_pairs
    end;

(($url | tostring | split("://")) as $parts
 | if ($parts | length) >= 2 then { scheme: ($parts[0] + "://"), path_part: ($parts[1:] | join("://")) } else null end) as $parsed
| if $parsed == null then error("invalid url: \($url)") else . end
| ($parsed.path_part | split("?") | .[0]) as $path_only
| ($parsed.path_part | split("?") | if length > 1 then .[1:] | join("?") else "" end) as $query_raw
| ($query_raw | query_to_param_types) as $params
| ($path_only | split("/")[0]) as $path_slug
| (if $params | length > 0 then { title: ($path_only | gsub("^/"; "") | if . == "" then $path_slug else . end), path: $path_only, background: false, params: $params } else { title: ($path_only | gsub("^/"; "") | if . == "" then $path_slug else . end), path: $path_only, background: false } end) as $new_path
| if any(.scheme == $parsed.scheme) then
    # todo add path checking / dedupe
    map(if .scheme == $parsed.scheme then .paths += [$new_path] else . end)
  else
    . + [{
      name: $name,
      app: $bundleid,
      scheme: $parsed.scheme,
      icon: $icon,
      paths: [$new_path]
    }]
  end
