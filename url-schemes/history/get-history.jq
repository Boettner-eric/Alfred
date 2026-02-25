# Usage: jq --slurpfile urls urls.json -f history/get-history.jq history/history.json
# Merges history/history.json entries with their parent in urls.json (object keyed by scheme id).
# History entries that don't match any urls.json scheme/path are shown as raw URL items.

def path_and_query:
  (split("?") | .[0]) as $path_only
  | (split("?") | if length > 1 then .[1:] | join("?") else "" end) as $query_raw
  | { path: $path_only, query: $query_raw };

def query_to_params:
  if . == "" then {}
  else split("&") | map(select(length > 0) | split("=") | {(.[0]): (.[1:] | join("=") // "")}) | add
  end;

def fallback_item($url; $count):
  {
    count: $count,
    item: {
      title: $url,
      subtitle: ("open " + $url + " · used " + ($count | tostring) + " time" + (if $count == 1 then "" else "s" end)),
      arg: $url,
      variables: { "params": "{}", "background": false }
    }
  };

def entry_scheme: .name.scheme // .scheme;
def entry_paths: .paths // .name.paths;
def entry_icon: .name.icon // .icon;

($urls[0] // {}) as $url_list
| . as $history
| ($history | keys) as $url_keys
| [
    $url_keys[]
    | . as $url
    | $history[$url] as $count
    | (
        [$url_list | to_entries[]
          | .value as $entry
          | ($entry | entry_scheme) as $scheme
          | select($url | startswith($scheme))
          | .key as $scheme_id
          | ($url | ltrimstr($scheme) | path_and_query) as $parsed
          | ($entry | entry_paths)[$parsed.path] as $path_obj
          | select($path_obj != null)
          | ($parsed.query | query_to_params) as $actual_params
          | ($scheme + $parsed.path + (if $actual_params | length > 0 then "?" + ($actual_params | to_entries | map("\(.key)=\(.value)") | join("&")) else "" end)) as $arg
          | {
              count: $count,
              item: {
                title: ($scheme_id + " - " + ($path_obj.description // $parsed.path)),
                subtitle: ("open " + $arg + " · used " + ($count | tostring) + " time" + (if $count == 1 then "" else "s" end)),
                arg: $arg,
                variables: {
                  "params": ($actual_params | tostring),
                  "background": ($path_obj.background // false)
                },
                icon: { type: "fileicon", path: ($entry | entry_icon) }
              }
            }
        ] as $matched
        | if ($matched | length) > 0 then $matched[] else fallback_item($url; $count) end
    )
  ]
| sort_by(-.count)
| { items: [.[].item] }
| (if .items | length == 0 then { items: [{ title: "No History", subtitle: "Try the urls command" }] } else . end)
