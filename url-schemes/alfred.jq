# Consumes urls.json (object keyed by scheme id). Each value: { name: { app, scheme, icon }, paths: { "path-slug": { description, background, params } } }.
# params: { "k": { type, example } }.

def flatten_params:
  if . == null or length == 0 then ""
  else "?" + (. | to_entries | map("\(.key)=\(.value.example // .value | if type == "string" then . else tostring end | @uri)") | join("&"))
  end;

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
  | .key as $path_slug
  | .value as $path_obj
  | {
      title: ($scheme_id + " - " + ($path_obj.description // $path_slug)),
      subtitle: ("open " + $meta.scheme + $path_slug),
      arg: (($meta | del(.paths) | . + {"path": $path_slug}) | tostring),
      variables: {
        "params": ($path_obj.params // {} | tostring),
        "background": ($path_obj.background // false),
        "copy": ($meta.scheme + $path_slug + (($path_obj.params // {}) | flatten_params))
      },
      icon: { type: "fileicon", path: $meta.icon }
    }
] | { items: . }
