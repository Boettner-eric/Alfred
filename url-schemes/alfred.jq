{
  items: [
    .[] | . as $entry | .paths[]
     | {
        title: ($entry.name + " - " + .title),
        subtitle: ("open " + $entry.scheme + .path), 
        arg: (($entry | del(.paths))  + {"path": .path} | tostring), 
        variables: {"params": .params | tostring, "background": .background},
        icon: {type: "fileicon", path: $entry.icon} 
        }
    ]
}
