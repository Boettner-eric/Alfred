def calculate_rerun($cache_time_minutes):
  if (now / 60 - $cache_time_minutes) < 5 then {} else {"rerun": 1} end;

def parse_cache_time($cache_time_str):
  ($cache_time_str | strptime("%d/%m/%Y, %H:%M:%S") | mktime) / 60;

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

def today($minutes_until; $time_range):
  if $minutes_until < 1 then "right now"
  elif $minutes_until == 1 then "in a minute | Today from \($time_range)"
  elif $minutes_until < 60 then "in \($minutes_until) minutes | Today from \($time_range)"
  elif $minutes_until < 120 then "in an hour | Today at \($time_range)"
  elif $minutes_until < 1440 then "in \($minutes_until / 60 | floor) hours | Today from \($time_range)"
  else "Today from \($time_range)" end;

def update_meeting_subtitle($meeting):
  ($meeting.time | split(" - ") | map(strptime("%Y-%m-%dT%H:%M:%S") | mktime / 60)) as [$start, $end]
  | calc_minute_diff($start) as $minutes_until
  | calc_minute_diff($end) as $minutes_left
  | calc_day_diff($meeting.time) as $days_until
  | format_time_range($meeting.time) as $time_range
  | ($meeting + {"subtitle": (
      if $minutes_until <= 0 and $minutes_left == 1 then "now (about to end)"   
      elif $minutes_until <= 0 and $minutes_left > 0 then "now (\($minutes_left) minutes left)"
      # skip meetings that are over
      elif $minutes_left <= 0 or $days_until < 0 then empty
      elif $days_until == 0 then today($minutes_until; $time_range)
      elif $days_until == 1 then "Tomorrow from \($time_range)"
      elif $days_until < 7 then "in \($days_until) days | \(($meeting.time | split(" - ")[0] | strptime("%Y-%m-%dT%H:%M:%S")[6]) | get_day_name) from \($time_range)"
      elif $days_until < 14 then "1 week from now"
      elif $days_until < 31 then "\($days_until / 7 | floor) weeks from now"
      elif $days_until < 365 then "\($days_until / 30 | floor) months from now"
      else "\($days_until / 365 | floor) years from now" end
    )});

. + calculate_rerun(parse_cache_time(.variables.cache_time)) 
| .items |= map(update_meeting_subtitle(.))