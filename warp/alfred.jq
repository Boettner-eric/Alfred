#!/usr/bin/env jq
# Input is tab separated rows of: name, path, git remote url (url may be empty).
[inputs | select(length > 0)] |
map(split("\t")
| {
    uid: .[0],
    arg: .[1],
    title: .[0], 
    subtitle:  .[1],
    match: ((.[1] | split("/") | join(" ")) + " " + .[0]),
    icon: {type: "fileicon", path: .[1]}, 
    mods: {
        cmd: {
          subtitle: ("open in " + ($editor | split("/") | last | rtrimstr(".app"))),
          icon: {type: "fileicon", path: $editor},
        },
         alt: {
          subtitle: ("open in " + ($terminal | split("/") | last | rtrimstr(".app"))),
          icon: {type: "fileicon", path: $terminal},
        },
        ctrl: {
          subtitle: "reveal in finder",
          icon: {type: "fileicon", path: "/System/Library/CoreServices/Finder.app"}
        },
        shift: (if .[2] == "" then {
            valid: false,
            subtitle: "not a git repository",
            icon: {type: "fileicon", path: .[1]}
          } else
            # everything between the host and the repo name, so nested
            # gitlab groups read as "group/subgroup"
            ((.[2] | split("/") | .[3:-1] | join("/")) as $org | {
              arg: .[2],
              subtitle: (if $org == "" then .[2] else .[2] + " \u00b7 " + $org end),
              icon: {path: "icons/github.png"}
            })
          end),
        "cmd+alt": {
          subtitle: "open in terminal and editor",
          icon: {type: "fileicon", path: $editor},
        }
      }
}) | {items: .}
