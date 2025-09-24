def describe_device($key; $device; $is_connected):
  if $is_connected then
    if $key | contains("AirPods Pro") then
      "Airpods Pro - L: \($device.device_batteryLevelLeft // "N/A"), R: \($device.device_batteryLevelRight // "N/A")"
    elif $key | contains("Airpods") then
      "Airpods - L: \($device.device_batteryLevelLeft // "N/A"), R: \($device.device_batteryLevelRight // "N/A")"
    else $device.device_minorType end
  else 
    if $key | contains("AirPods Pro") then
      "Airpods Pro (not connected)"
    elif $key | contains("Airpods") then
      "Airpods (not connected)"
    else $device.device_minorType + " (not connected)" end
  end;

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
      subtitle: describe_device(.key; .value; $is_connected),
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
