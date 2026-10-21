# Required variables:
# $input: Name of current input device
# $output: Name of current output device
# $denylist: JSON array of device names to exclude, regardless of type
# $input_denylist: JSON array of device names to exclude when type is input
# $output_denylist: JSON array of device names to exclude when type is output

# Older configs wrap the array in single quotes ('["a"]'); anything that isn't a JSON array counts as empty.
def device_list: ltrimstr("'") | rtrimstr("'") | (fromjson? // []) | if type == "array" then . else [] end;

($denylist | device_list) as $deny
| ($input_denylist | device_list) as $input_deny
| ($output_denylist | device_list) as $output_deny
| {
  skipknowledge: true,
  items: [.[] | select(.name as $name | .type as $type
      | ($name | IN($deny[]) | not)
      and (if $type == "input" then ($name | IN($input_deny[]) | not) else true end)
      and (if $type == "output" then ($name | IN($output_deny[]) | not) else true end))]
  | sort_by(if (.name == $input and .type == "input") or (.name == $output and .type == "output")
      then 0 else 1 end)
  | [.[]
  | {
      uid: ("io-" + .name + .type),
      arg: (.type + "," + .name),
      title: (if .name | contains("AirPods Max") then "Airpods Max"
          elif .name | contains("AirPods") then "Airpods"
          else .name end),
      subtitle: (if (.name == $input and .type == "input") or (.name == $output and .type == "output") 
          then .type + " - current" 
          else .type 
        end),
      match: (.name + " " + .type),
      text: {copy: .name},
      icon: (if .name | contains("AirPods Max")
          then {path: "icons/airpods-max.png"}
          elif .name | contains("AirPods")
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
          arg: (.type + "," + .name),
          subtitle: ("hide from " + .type + "s (add to " + .type + " denylist)"),
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
