($avatars | split("\n")) as $avatars
| if . == null then {items: [{
    title: "Couldn't load pull requests",
    subtitle: "Check that gh is installed and logged in",
    valid: false
  }]} else {
  skipknowledge: true,
  items: (if length == 0 then [{
      title: "No open pull requests",
      subtitle: "Nothing in \($org) is assigned to \($name)",
      icon: {path: "icon.png"},
      valid: false
    }] else [.[] | (.author.login // "ghost") as $author | {
      uid: .url,
      title: .title,
      subtitle: "\(.repository.name)#\(.number) · \($author)\(if .isDraft then " · draft" else "" end)",
      match: "\(.title) \(.repository.name) \(.number) \($author)",
      icon: (if ($author + ".png" | IN($avatars[])) then {path: "avatars/\($author).png"} else {path: "icon.png"} end),
      arg: .url,
      text: {copy: .url}
    }] end)
} end
