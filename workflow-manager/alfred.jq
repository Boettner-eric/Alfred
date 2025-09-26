#!/usr/bin/env jq
.items | map({
    uid: .title,
    arg: .arg,
    title: .title,
    subtitle: .subtitle,
    match: (.title + " " + .subtitle),
    icon: .icon,
    mods: {
        cmd: {
            subtitle: ("open in " + ($editor | split("/") | last | rtrimstr(".app"))),
            icon: {type: "fileicon", path: $editor}
        },
        alt: {
            subtitle: ("open in " + ($terminal | split("/") | last | rtrimstr(".app"))),
            icon: {type: "fileicon", path: $terminal}
        },
        ctrl: {
            subtitle: "reveal in finder",
            icon: {type: "fileicon", path: "/System/Library/CoreServices/Finder.app"}
        },
        shift: {
            subtitle: "open in terminal and editor",
            icon: {type: "fileicon", path: $editor}
        }
    }
}) | {items: .}