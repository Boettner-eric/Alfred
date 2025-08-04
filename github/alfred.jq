def calculate_rerun($cache_time_minutes):
  ((now | . / 60) - $cache_time_minutes) as $diff_minutes
  | if $diff_minutes < 5 then {} else {"rerun": 1} end;

{
  variables: {
    cache_time: now
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
          arg: .clone_url,
          subtitle: ("copy repo clone \"" + .clone_url + "\""),
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
      },
    }
  ]
} + calculate_rerun(.cache_time / 60)