#!/bin/bash

BATTERY_DATA=$(pmset -g accps | awk '\
BEGIN {
    print "{"
    first = 1
}
/^ -/ {
    device = $0
    gsub(/^ -/, "", device)
    gsub(/ \(.*$/, "", device)
    
    devices[device] = match($0, /[0-9]+%/)
}
END {
    for (device in devices) {
        if (!first) print ","
        first = 0
        printf "  \"%s\": \"%s%%\"", device, devices[device]
    }
    print "\n}"
}')

system_profiler SPBluetoothDataType -json | jq --argjson battery_data "$BATTERY_DATA" -f alfred.jq