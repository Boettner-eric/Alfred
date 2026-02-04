def flatten_params:
  if . == null then ""
  else "?" + (. | to_entries | map("\(.key)=\(.value)") | join("&"))
  end;

{
  items: [
    .[] | . as $entry | .paths[]
     | {
        title: ($entry.name + " - " + .title),
        subtitle: ("open " + $entry.scheme + .path), 
        arg: (($entry | del(.paths))  + {"path": .path} | tostring), 
        variables: {"params": .params | tostring, "background": .background, "copy": $entry.scheme + .path + (.params | flatten_params)},
        icon: {type: "fileicon", path: $entry.icon} 
        }
    ]
}
