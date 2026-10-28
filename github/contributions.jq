def plural($n; $word): "\($n) \($word)" + (if $n == 1 then "" else "s" end);

def icon:
  {
    NONE: "none",
    FIRST_QUARTILE: "first",
    SECOND_QUARTILE: "second",
    THIRD_QUARTILE: "third",
    FOURTH_QUARTILE: "fourth"
  }[.] as $level
  | {path: "icons/contrib-\($level).png"};

# Compared to the clock, not list position, so a cache from before midnight labels correctly
def day_label:
  if . == (now | strflocaltime("%Y-%m-%d")) then "Today"
  elif . == (now - 86400 | strflocaltime("%Y-%m-%d")) then "Yesterday"
  else strptime("%Y-%m-%d") | mktime | strftime("%A")
  end;

if .data.viewer == null then
  {items: [{
    title: "Couldn't load contributions",
    subtitle: "Check that gh is installed and logged in",
    valid: false
  }]}
else
  .data.viewer.login as $login
  | .data.viewer.contributionsCollection.contributionCalendar as $calendar
  | (if now - .cache_time > 300 then {rerun: 1} else {} end)
  + {
      items: (
        [$calendar.weeks[].contributionDays[]]
        | .[-6:]
        | reverse
        | map({
            title: plural(.contributionCount; "contribution"),
            subtitle: "\(.date | day_label) · \(.date | strptime("%Y-%m-%d") | mktime | strftime("%b %-d"))",
            icon: (.contributionLevel | icon),
            arg: "https://github.com/\($login)?tab=overview&from=\(.date)&to=\(.date)"
          })
      ) + [{
        title: "\(plural($calendar.totalContributions; "contribution")) in the last year",
        subtitle: "Open profile",
        icon: {path: "icon.png"},
        arg: "https://github.com/\($login)"
      }]
    }
end
