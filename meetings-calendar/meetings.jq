def excluded_events:
  ($ARGS.named.excluded_events // []) | map(select(type == "string") | ascii_downcase);

def is_excluded($meeting):
  ($meeting.title // "" | ascii_downcase) as $title
  | excluded_events | index($title) != null;

def calculate_rerun($cache_time_seconds):
  (now - $cache_time_seconds) as $diff_seconds
  | if $diff_seconds < 300 then {} else {"rerun": 1} end;

def pad_zero: if . < 10 then "0\(.)" else "\(.)" end;

def get_day_name:
  ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][.];

def format_time_range($time_str):
  ($time_str | split(" - ") | map(strptime("%Y-%m-%dT%H:%M:%S"))) as [$s, $e]
  | "\($s[3]):\($s[4] | pad_zero) - \($e[3]):\($e[4] | pad_zero)";

def calc_minute_diff($minutes):
  $minutes - (now | strflocaltime("%Y-%m-%dT%H:%M:%S%z") | strptime("%Y-%m-%dT%H:%M:%S%z") | mktime / 60 - 1) | floor;

def calc_day_diff($time_str):
  (($time_str | split(" - ")[0] | strptime("%Y-%m-%dT%H:%M:%S") | mktime) - 
   (now | strflocaltime("%Y-%m-%d") | strptime("%Y-%m-%d") | mktime)) / 86400 | floor;

def format_duration_phrase($mins):
  if $mins == 1 then "a minute"
  elif $mins < 60 then "\($mins) minutes"
  else
    ($mins / 60 | floor) as $h
    | ($mins % 60) as $m
    | (if $h == 1 then "1 hour" else "\($h) hours" end) as $hour_part
    | if $m == 0 then $hour_part
      elif $m == 1 then "\($hour_part) 1 minute"
      else "\($hour_part) \($m) minutes" end
  end;

def today($minutes_until; $phrase):
  if $minutes_until < 1 then "right now"
  elif $minutes_until < 1440 then "in \(format_duration_phrase($minutes_until)) | \($phrase)"
  else $phrase end;

def days_from_today($t):
  (($t | mktime) - (now | strflocaltime("%Y-%m-%d") | strptime("%Y-%m-%d") | mktime)) / 86400 | floor;

def day_label($days; $t; $next):
  if $days == 0 then "Today"
  elif $days == 1 then "Tomorrow"
  elif $next and $days >= 7 then "Next \($t[6] | get_day_name)"
  else $t[6] | get_day_name end;

# all-day events run midnight to midnight with an exclusive end, so their last day is the day before the end
def event_span($time_str):
  ($time_str | split(" - ") | map(strptime("%Y-%m-%dT%H:%M:%S"))) as [$s, $e]
  | ($s[3:6] == [0, 0, 0] and $e[3:6] == [0, 0, 0]) as $all_day
  | (if $all_day then $e | mktime - 86400 | gmtime else $e end) as $last
  | {start: $s, last: $last, all_day: $all_day, multi_day: ($s[0:3] != $last[0:3])};

def update_meeting_subtitle($meeting):
  ($meeting.time | split(" - ") | map(strptime("%Y-%m-%dT%H:%M:%S") | mktime / 60)) as [$start, $end]
  | calc_minute_diff($start) as $minutes_until
  | calc_minute_diff($end) as $minutes_left
  | calc_day_diff($meeting.time) as $days_until
  | format_time_range($meeting.time) as $time_range
  | event_span($meeting.time) as $span
  | day_label(days_from_today($span.last); $span.last; false) as $last_label
  | (if $span.all_day then "all day" else "from \($time_range)" end) as $when
  | def phrase($label): if $span.multi_day then "\($label) - \($last_label)" else "\($label) \($when)" end;
  ($meeting + {"subtitle": (
      if $minutes_until <= 0 and $minutes_left > 0 and $span.multi_day then "now | \(phrase(day_label($days_until; $span.start; false)))"
      elif $minutes_until <= 0 and $minutes_left > 0 and $span.all_day then "Today all day"
      elif $minutes_until <= 0 and $minutes_left == 1 then "now (about to end)"
      elif $minutes_until <= 0 and $minutes_left > 0 then "now (\($minutes_left) minutes left)"
      # skip meetings that are over
      elif $minutes_left <= 0 or $days_until < 0 then empty
      elif $days_until == 0 then today($minutes_until; phrase("Today"))
      elif $days_until == 1 then phrase("Tomorrow")
      elif $days_until < 14 then "in \($days_until) days | \(phrase(day_label($days_until; $span.start; true)))"
      elif $days_until < 31 then "\($days_until / 7 | floor) weeks from now"
      elif $days_until < 365 then "\($days_until / 30 | floor) months from now"
      else "\($days_until / 365 | floor) years from now" end
    )});

. + {"skipknowledge": true}
  + (if (.variables.cache_time | type) == "number"
      then calculate_rerun(.variables.cache_time)
      else {"rerun": 1} end)
| .items |= (map(select(is_excluded(.) | not)) | map(update_meeting_subtitle(.)))