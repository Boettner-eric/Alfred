# Consumes urls.json (object keyed by scheme id). Each value: { name: { app, scheme, icon }, paths: { "key": { path, description, background, params } } }.
# path falls back to the key for entries saved before keys were made unique.
# params: { "k": { type, example } }. defaults: { "k": "raw value" }, always sent verbatim.

def defaults_query: . // {} | to_entries | map("\(.key)=\(.value)") | join("&");

def flatten_params($defaults):
  ([($defaults | defaults_query)] + (. // {} | to_entries | map("\(.key)=\(.value.example // .value | if type == "string" then . else tostring end | @uri)")))
  | map(select(. != "")) | join("&")
  | if . == "" then "" else "?" + . end;

# paths may live under .paths or .name.paths (legacy)
def entry_paths: .paths // .name.paths;
def entry_meta: .name // .;

[
  to_entries[]
  | .key as $scheme_id
  | .value as $entry
  | ($entry | entry_meta) as $meta
  | ($entry | entry_paths)
  | to_entries[]
  | .value as $path_obj
  | ($path_obj.path // .key) as $path_slug
  | {
      title: ($scheme_id + " - " + ($path_obj.description // $path_slug)),
      subtitle: ("open " + $meta.scheme + $path_slug),
      arg: (($meta | del(.paths) | . + {"path": $path_slug}) | tostring),
      variables: {
        "params": ($path_obj.params // {} | tostring),
        "defaults": ($path_obj.defaults | defaults_query),
        "background": ($path_obj.background // false),
        "copy": ($meta.scheme + $path_slug + ($path_obj.params | flatten_params($path_obj.defaults)))
      },
      icon: { type: "fileicon", path: $meta.icon }
    }
] | { items: . }
