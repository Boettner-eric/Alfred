# jq script to add a new scene to scenes.json
# Usage: jq --argjson new_scene '{"icon": "icons/new.png", "input": "New Input", "output": "New Output"}' -f add-scene.jq scenes.json > scenes.json.tmp && mv scenes.json.tmp scenes.json

. as $existing_scenes |
({"title": (if $title == "" then ($input + " → " + $output) else $title end), "icon": $icon, "input": $input, "output": $output}) as $scene_with_name |
$existing_scenes + [$scene_with_name]