{
  items: [.[] | select(.name != "ZoomAudioDevice" and .name != "ASUS VP28U") 
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
      arg: (.type + "," + .name)
    }
  ]
}
