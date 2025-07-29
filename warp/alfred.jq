#!/usr/bin/env jq
[inputs | select(length > 0 and test("^\\s*$") | not)] | 
map(select(contains(":")) | split(":") | {arg: .[1:] | join(":"), title: .[0], icon: {type: "fileicon", path: (.[1:] | join(":"))}, subtitle:  (.[1:] | join(":"))}) |
{items: .}