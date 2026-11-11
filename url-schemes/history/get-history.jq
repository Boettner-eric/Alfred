# Usage: jq --slurpfile urls urls.json -f history/get-history.jq history/history.json
# Merges history/history.json entries with their parent in urls.json (object keyed by scheme id).
# History entries that don't match any urls.json scheme/path are shown as raw URL items.
# Entries that are the same url written differently (see canonical_url) collapse into one item:
# counts add up and the most-used spelling is the one opened.
# When several saved entries share a path, the one with the most defaults present in the url wins.
include "url" {search: "./"};

def path_and_query:
  (split("?") | .[0]) as $path_only
  | (split("?") | if length > 1 then .[1:] | join("?") else "" end) as $query_raw
  | { path: $path_only, query: $query_raw };

def query_to_params: query_pairs | map({(.[0]): .[1]}) | add // {};

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
| [to_entries[] | {url: .key, count: .value, canonical: (.key | canonical_url)}]
| group_by(.canonical)
| [
    .[]
    | (max_by(.count) | .url) as $url
    | (map(.count) | add) as $count
    | .[0].canonical as $canonical
    | (
        [$url_list | to_entries[]
          | .value as $entry
          | ($entry | entry_scheme) as $scheme
          | select($url | startswith($scheme))
          | .key as $scheme_id
          | ($url | ltrimstr($scheme) | path_and_query) as $parsed
          | ($parsed.query | query_to_params) as $actual_params
          | ([($entry | entry_paths) | to_entries[]
              | select((.value.path // .key) == $parsed.path)
              | .value
              | select(.defaults // {} | to_entries | all(. as $d | ($actual_params[$d.key] | if . == null then null else decode end) == ($d.value | decode)))]
            | max_by(.defaults // {} | length)) as $path_obj
          | select($path_obj != null)
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
        # removal takes a stored key and drops every spelling of it (remove-entry.jq)
        | .item += {uid: $canonical, mods: {cmd: {arg: $url, subtitle: "remove from history"}}}
    )
  ]
| sort_by(-.count)
# rerun picks up removals while Alfred stays open; uids keep the selection in place
| { items: [.[].item], rerun: 0.1, skipknowledge: true }
| (if .items | length == 0 then { items: [{ title: "No History", subtitle: "Try the urls command" }] } else . end)
