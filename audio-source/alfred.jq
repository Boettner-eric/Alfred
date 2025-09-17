# Required variables:
# $input: Name of current input device
# $output: Name of current output device
# $denylist: Array of device names to exclude
{
  items: [.[] | select(.name as $name | $denylist | index($name) | not) 
  | {
      uid: (.name + .type), 
      arg: (.type + "," + .name),
      title: (if .name | contains("AirPods") then "Airpods" else .name end), 
      subtitle: (if (.name == $input and .type == "input") or (.name == $output and .type == "output") 
          then .type + " - current" 
          else .type 
        end),
      match: (.name + " " + .type),
      icon: (if .name | contains("AirPods")
          then {path: "icons/airpods.png"}
          elif .name | contains("MacBook")
            then {path: "icons/macbook.png"}
          elif .type == "output" 
            then {path: "icons/speaker.png"}
          else {path: "icons/mic.png"}
        end),
      mods: {
        cmd: {
          valid: true,
          arg: ("output" + "," + .name),
          subtitle: ("set as output"),
        },
        alt: {
          valid: true,
          arg: ("input" + "," + .name),
          subtitle: ("set as input"),
        },
        ctrl: {
          valid: true,
          arg: .name,
          subtitle: ("copy \"" + .name + "\" to clipboard"),
        },
        shift: {
          valid: true,
          arg: .type,
          subtitle: ("mute/unmute " + .type),
        }
      },
    }
  ]
}
