#!/usr/bin/env jq
[inputs | select(length > 0 and test("^\\s*$") | not)] | 
map(select(contains(":")) | split(":") 
| {
    uid: .[0],
    arg: .[1:],
    title: .[0], 
    subtitle:  .[1],
    match: ((.[1] | split("/") | join(" ")) + " " + .[0]),
    icon: {type: "fileicon", path: .[1]}, 
    mods: {
        cmd: {
          valid: true,
          subtitle: "open in " + ($editor | split("/") | last | rtrimstr(".app")),
          icon: {type: "fileicon", path: $editor},
        },
         alt: {
          valid: true,
          subtitle: "open in " + ($terminal | split("/") | last | rtrimstr(".app")),
          icon: {type: "fileicon", path: $terminal},
        },
        ctrl: {
          valid: true,
          subtitle: "reveal in finder",
          icon: {type: "fileicon", path: "/System/Library/CoreServices/Finder.app"}
        }
      }
}) | {items: .}