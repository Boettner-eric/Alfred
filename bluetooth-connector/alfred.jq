def describe_device($device):
  if $device.device_minorType == "Headphones" then
    "\($device.device_minorType) - Left: \($device.device_batteryLevelLeft // "N/A"), Right: \($device.device_batteryLevelRight // "N/A")"
  else $device.device_minorType end;

def choose_icon($device):
  if $device.device_minorType == "Headphones" then
    {path: "icons/airpods.png"}
  elif $device.device_minorType == "Keyboard" then
    {path: "icons/keyboard.png"}
  elif $device.device_minorType == "Magic Trackpad" then
    {path: "icons/trackpad.png"}
  else {path: "icons/blue.png"}
  end;

def format_device($device; $is_connected):
    {
      title: .key,
      icon: choose_icon(.value),
      subtitle: describe_device(.value) + (if $is_connected then "" else " (not connected)" end),
      arg: [(if $is_connected then "disconnect" else "connect" end), (.value.device_address | gsub(":"; "-"))],
      mods: {
        cmd: {
          valid: true,
          arg: (.value.device_address | gsub(":"; "-")),
          subtitle: "mark as airpods"
        }
      }
    };

{
  items: [
    ((.SPBluetoothDataType[0].device_connected[]? // []) | 
    to_entries[] | 
    select(.value | type == "object" and .device_address != null) |
    format_device(.value; true))
  ] + [
    ((.SPBluetoothDataType[0].device_not_connected[]? // []) | 
    to_entries[] | 
    select(.value | type == "object" and .device_address != null) |
    format_device(.value; false))
  ]
}
