def calculate_rerun($cache_time_seconds):
  (now - $cache_time_seconds) as $diff_seconds
  # 1s to match gitlab/meetings-calendar's cadence — polling at 0.1s caused
  # the whole list to redraw every 100ms while the background refresh ran.
  | if $diff_seconds < 300 then {} else {"rerun": 1} end;

{
  items: [.items | sort_by(.pushed_at) | reverse | .[] | {
      uid: .html_url,
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
} + (if (.cache_time | type) == "number"
      then calculate_rerun(.cache_time)
      else {"rerun": 1} end)
