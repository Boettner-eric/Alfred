#!/bin/zsh

# Alfred Workflow Manager
# Scans ~/Library/Application Support/Alfred/Alfred.alfredpreferences/workflows
# and extracts workflow names from info.plist files

ALFRED_WORKFLOWS_DIR="$HOME/Library/Application Support/Alfred/Alfred.alfredpreferences/workflows"

extract_workflow_name() {
    local plist_file="$1"
    local workflow_dir="$2"
    
    local name=$(plutil -extract name raw "$plist_file" 2>/dev/null)
    if [[ $? -eq 0 && -n "$name" && ! "$name" =~ "Could not extract value" ]]; then
        echo "$name"
        return 0
    else
        echo "Failed to extract name from $plist_file"
        return 1
    fi
}

extract_description() {
    local plist_file="$1"
    
    local category=$(plutil -extract category raw "$plist_file" 2>/dev/null)
    local description=$(plutil -extract description raw "$plist_file" 2>/dev/null)
    if [[ $? -eq 0 && -n "$description" && ! "$description" =~ "Could not extract value" ]]; then
        echo "$description"
    elif [[ $? -eq 0 && -n "$category" && ! "$category" =~ "Could not extract value" ]]; then
        echo "$category"
    else
        echo "No description or category"
    fi
}

extract_website_url() {
    local plist_file="$1"
    
    local website_url=$(plutil -extract webaddress raw "$plist_file" 2>/dev/null)
    if [[ $? -eq 0 && -n "$website_url" && ! "$website_url" =~ "Could not extract value" ]]; then
        echo "$website_url"
    else
        echo "No website URL"
    fi
}

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
            local name=$(extract_workflow_name "$info_plist" "$workflow_dir" 2>/dev/null)
            local description=$(extract_description "$info_plist" 2>/dev/null)
            local website_url=$(extract_website_url "$info_plist" 2>/dev/null)
        
            local item="{\"id\": \"$id\", \"title\": \"$name\", \"subtitle\": \"$description\", \"path\": \"$workflow_dir\", \"website_url\": \"$website_url\"}"
            
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