# Required variables:
# $input: Name of current input device
# $output: Name of current output device
# $denylist: Array of device names to exclude
{
  items: [.[] | select(.name as $name | $denylist | index($name) | not) 
  | {
      uid: (.name + .type), 
      title: (if .name | contains("AirPods") then "Airpods" else .name end), 
      icon: (if .name | contains("AirPods")
          then {path: "icons/airpods.png"}
          elif .name | contains("MacBook")
            then {path: "icons/macbook.png"}
          elif .type == "output" 
            then {path: "icons/speaker.png"}
          else {path: "icons/mic.png"}
        end),
      subtitle: (if (.name == $input and .type == "input") or (.name == $output and .type == "output") 
          then .type + "- current" 
          else .type 
        end),
      arg: (.type + "," + .name),
      mods: {
        ctrl: {
          valid: true,
          arg: .name,
          subtitle: ("copy \"" + .name + "\" to clipboard"),
        },
         alt: {
          valid: true,
          arg: .name,
          subtitle: ("set as input"),
        },
         cmd: {
          valid: true,
          arg: .name,
          subtitle: ("set as output"),
        },
      },
    }
  ]
}
