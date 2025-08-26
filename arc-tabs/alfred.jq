# Extract bookmarks from Arc
# Usage: jq -f alfred.jq "~/Library/Application Support/Arc/StorableSidebar.json"

{
  "items": (
    .sidebar.containers[1].items | 
    map(select(type == "object")) | 
    map(select(.data and .data.tab and .data.tab.savedURL)) |
    map({
      "arg": .data.tab.savedURL,
      "subtitle": .data.tab.savedURL,
      "uid": "arc_" + .id,
      "title": (.title // .data.tab.savedTitle // "Untitled")
    })
  )
}
