def set_battery_level($battery_level):
  if $battery_level == null then
    "N/A"
  else
    ($battery_level | gsub("%"; "") | tonumber) as $battery_int |
    if $battery_int > 90 then
      $battery_level + " 􀛨"
    elif $battery_int > 75 then
      $battery_level + " 􀺸"
    elif $battery_int > 50 then
      $battery_level + " 􀺶"
    elif $battery_int > 20 then
      $battery_level + " 􀛩"
    else $battery_level + " 􀛪" end
  end;

def describe_device($key; $device; $is_connected):
  if $is_connected then
    if $key | contains("AirPods Pro") then
      "Airpods Pro - L: " + set_battery_level($device.device_batteryLevelLeft) + ", R: " + set_battery_level($device.device_batteryLevelRight)
    elif $key | contains("Airpods") then
      "Airpods - L: " + set_battery_level($device.device_batteryLevelLeft) + ", R: " + set_battery_level($device.device_batteryLevelRight)
    else $device.device_minorType + " - " + set_battery_level($battery_data[$key]) end
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
  elif $device.device_minorType == "Speaker" then
    {path: "icons/speaker.png"}
  else {path: "icons/blue.png"}
  end;

def format_device($device; $is_connected):
  {
    title: .key,
    uid: ("bluetooth_connector_" + .value.device_address),
    icon: choose_icon(.value),
    subtitle: describe_device(.key; .value; $is_connected),
    arg: [(if $is_connected then "disconnect" else "connect" end), (.value.device_address | gsub(":"; "-")), .key]   
  };

{
  items: ([
    ((.SPBluetoothDataType[0].device_connected[]? // []) | 
    to_entries[] | 
    select(.value | type == "object" and .device_address != null) |
    format_device(.value; true))
  ] + [
    ((.SPBluetoothDataType[0].device_not_connected[]? // []) | 
    to_entries[] | 
    select(.value | type == "object" and .device_address != null) |
    format_device(.value; false))
  ])
}
