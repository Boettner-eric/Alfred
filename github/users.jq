($avatars | split("\n")) as $avatars
| {
  items: [.items | sort_by(.name // .login | ascii_downcase) | .[] |
    (.name // .login) as $name
    | ($name | split(" ")[0]) as $first
    | ("https://github.com/pulls?q=is%3Aopen+is%3Apr+" + (.orgs | map("org%3A" + .) | join("+")) + "+") as $search
    | {
      uid: "pr \(.login)",
      title: $name,
      subtitle: "Get \($first)'s open pull requests",
      match: "\($name) \(.login)",
      text: {copy: .login},
      icon: (if (.login + ".png" | IN($avatars[])) then {path: "avatars/\(.login).png"} else {path: "icon.png"} end),
      arg: "\($search)author%3A\(.login)",
      mods: {
        cmd: {
          valid: true,
          arg: "https://github.com/\(.login)",
          subtitle: "View \($first)'s profile",
        },
        ctrl: {
          valid: true,
          arg: "\($search)assignee%3A\(.login)",
          subtitle: "Get pull requests that \($first) is assigned to",
        },
        alt: {
          valid: true,
          arg: "\($search)review-requested%3A\(.login)",
          subtitle: "Get pull requests that \($first) is reviewing",
        }
      }
    }
  ]
}
