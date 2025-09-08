# jq script to add a new scene to scenes.json
# Usage: jq --arg id "$id" --arg title "$title" --arg icon "$icon" --arg input "$input" --arg output "$output" -f scenes/add-scene.jq scenes/scenes.json > scenes/scenes.json.tmp && mv scenes/scenes.json.tmp scenes/scenes.json

. as $existing_scenes |
({"id": $id, "title": (if $title == "" then ($input + " → " + $output) else $title end), "icon": $icon, "input": $input, "output": $output}) as $new_scene |
if ($existing_scenes | map(select(.id == $new_scene.id)) | length) > 0 then
  $existing_scenes | map(if .id == $new_scene.id then $new_scene else . end)
else
  $existing_scenes + [$new_scene]
end