{
  cache: {
    seconds: 300,
    loosereload: true
  },
  items: [.items | sort_by(.pushed_at) | reverse | .[] | {
      title: .name, 
      icon: (if .fork
          then {path: "icons/fork.png"}
          elif .private
          then {path: "icons/private.png"}
          else {path: "icons/repo.png"}
        end),
      subtitle: (.description // "No description"),
      arg: .html_url,
      mods: {
        cmd: {
          valid: true,
          arg: .ssh_url,
          subtitle: ("copy repo clone \"" + .ssh_url + "\""),
        },
         alt: {
          valid: true,
          arg: (.html_url + "/issues"),
          subtitle: "open issues",
        },
         ctrl: {
          valid: true,
          arg: (.html_url + "/pulls"),
          subtitle: "open pull requests",
        },
         shift: {
          valid: true,
          arg: (.html_url + "/actions"),
          subtitle: "open github actions",
        }
      },
    }
  ]
}
