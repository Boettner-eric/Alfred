#!/bin/zsh

# Alfred Workflow Manager
# Scans ~/Library/Application Support/Alfred/Alfred.alfredpreferences/workflows
# and extracts workflow names from info.plist files

ALFRED_WORKFLOWS_DIR="$HOME/Library/Application Support/Alfred/Alfred.alfredpreferences/workflows"

list_workflows() {
    local workflows_dir="${1:-$ALFRED_WORKFLOWS_DIR}"
        
    if [[ ! -d "$workflows_dir" ]]; then
        echo "Alfred workflows directory not found: $workflows_dir"
        return 1
    fi
        
    local json_items=""

    for workflow_dir in "$workflows_dir"/*; do
        if [[ ! -d "$workflow_dir" && ! -L "$workflow_dir" ]] || [[ "$workflow_dir" == "$workflows_dir" ]]; then
            continue
        fi
        
        local info_plist="$workflow_dir/info.plist"
        local id="${workflow_dir##*/}"

        if [[ -f "$info_plist" ]]; then
            local icon="icons/question.png"
            if [ -f "$workflow_dir/icon.png" ]; then
                icon="$workflow_dir/icon.png"
            fi
            local item=$(plutil -convert json -o - "$info_plist" 2>/dev/null |\
                jq -c --arg id "$id" --arg path "$workflow_dir" --arg icon $icon '{
                    id: $id,
                    path: $path,
                    icon: $icon,
                    title: (.name // "Failed to extract name"),
                    subtitle: (.description // .category // "No description or category"),
                    website_url: (.webaddress // "No website URL"),
                    author: (.createdby // "Unknown")
                }')

            if [[ -n "$json_items" ]]; then
                json_items="$json_items,$item"
            else
                json_items="$item"
            fi
        fi
    done
    echo "{\"items\": [$json_items]}" | jq "." > workflows.json
};

list_workflows