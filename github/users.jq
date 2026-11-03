($avatars | split("\n")) as $avatars
# The pulls page ANDs repeated org: filters, so scope each user to one org:
# the configured default org if they're in it, otherwise their largest
| (reduce .items[].orgs[] as $org ({}; .[$org] += 1)) as $org_sizes
| {
  items: [.items | sort_by(.name // .login | ascii_downcase) | .[] |
    (.name // .login) as $name
    | ($name | split(" ")[0]) as $first
    | (if any(.orgs[]; . == $default_org) then $default_org else .orgs | max_by($org_sizes[.]) end) as $org
    | "https://github.com/pulls?q=is%3Aopen+is%3Apr+org%3A\($org)+" as $search
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
