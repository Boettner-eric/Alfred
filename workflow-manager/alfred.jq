#!/usr/bin/env jq
.items | map({
    uid: .title,
    arg: .id,
    title: .title,
    subtitle: .subtitle + " by " + .author,
    match: (.title + " " + .subtitle),
    icon: {path: (.path + "/icon.png")},
    mods: {
        cmd: {
            subtitle: ("open in " + ($editor | split("/") | last | rtrimstr(".app"))),
            arg: .path,
            icon: {type: "fileicon", path: $editor}
        },
        alt: {
            subtitle: ("open in " + ($terminal | split("/") | last | rtrimstr(".app"))),
            arg: .path,
            icon: {type: "fileicon", path: $terminal}
        },
        ctrl: {
            subtitle: "reveal in finder",
            arg: .path,
            icon: {type: "fileicon", path: "/System/Library/CoreServices/Finder.app"}
        },
        shift: {
            subtitle: .website_url,
            arg: .website_url,
            icon: {type: "path", path: "icons/internet.png"}
        }
    }
}) | {items: .}