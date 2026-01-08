#!/bin/bash

BATTERY_DATA=$(pmset -g accps | sed 's/[^[:print:]	]/?/g' | LC_ALL=C awk '
BEGIN {
    print "{"
    first = 1
}
/^ -/ {
    device = $0
    gsub(/^ -/, "", device)
    gsub(/ \(.*$/, "", device)
    
    if (match($0, /[0-9]+%/)) {
        battery = substr($0, RSTART, RLENGTH)
        gsub(/%/, "", battery)
        devices[device] = battery
    }
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