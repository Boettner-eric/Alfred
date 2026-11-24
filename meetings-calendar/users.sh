#!/bin/bash
# Script filter for the calendar users keyword. The top item signs in a new google
# account, the rest reauthorize the account saved in each tokens/*.json. The arg is
# passed to `meetings.py --auth`.

tokens=()
for f in tokens/*.json; do
	[ -s "$f" ] && tokens+=("$f")
done

# stdin is /dev/null so jq doesn't wait on it when there are no token files yet
jq -n '{
  skipknowledge: true,
  items: (
    [{
      title: "Add user",
      subtitle: "sign in to another google calendar",
      arg: "new",
      match: "add new user",
      icon: {path: "./icon.png"}
    }]
    + [inputs | input_filename as $path | {
      title: (.account // $path),
      subtitle: (
        if .needs_reauth then "⚠️ sign in expired, reauthorize · \($path)"
        elif .refresh_token then "reauthorize · \($path)"
        else "⚠️ missing refresh token, reauthorize · \($path)" end
      ),
      arg: $path,
      match: "\(.account // "") \($path)",
      icon: {path: "./icons/cal.png"}
    }]
  )
}' "${tokens[@]}" < /dev/null
