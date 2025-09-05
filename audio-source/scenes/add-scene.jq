# jq script to add a new scene to scenes.json
# Usage: jq --arg title "$title" --arg icon "$icon" --arg input "$input" --arg output "$output" -f scenes/add-scene.jq scenes/scenes.json > scenes/scenes.json.tmp && mv scenes/scenes.json.tmp scenes/scenes.json

. as $existing_scenes |
({"title": (if $title == "" then ($input + " → " + $output) else $title end), "icon": $icon, "input": $input, "output": $output}) as $scene_with_name |
$existing_scenes + [$scene_with_name]