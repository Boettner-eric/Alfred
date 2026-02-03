# when adding we can use osascript -e 'tell application "Finder" to POSIX path of ((application file id "BUNDLE_ID") as alias)'

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
