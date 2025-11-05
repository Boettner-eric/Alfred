def calculate_rerun($cache_time_minutes):
  ((now | . / 60) - $cache_time_minutes) as $diff_minutes
  | if $diff_minutes < 5 then {} else {"rerun": 1} end;

def parse_cache_time($cache_time_str):
  ($cache_time_str | strptime("%d/%m/%Y, %H:%M:%S") | mktime) / 60;

def parse_meeting_time($time_str):
  ($time_str | split(" - ")[0] | strptime("%Y-%m-%dT%H:%M:%S") | mktime) / 60;

def parse_meeting_time_end($time_str):
  ($time_str | split(" - ")[1] | strptime("%Y-%m-%dT%H:%M:%S") | mktime) / 60;

def pad_zero($num):
  if $num < 10 then "0\($num)" else "\($num)" end;

def format_subtitle($time_str):
  ($time_str | split(" - ")) as $times
  | ($times[0] | strptime("%Y-%m-%dT%H:%M:%S")) as $start_time
  | ($times[1] | strptime("%Y-%m-%dT%H:%M:%S")) as $end_time
  | "Today from \($start_time[3] | pad_zero(.)):\($start_time[4] | pad_zero(.)) to \($end_time[3] | pad_zero(.)):\($end_time[4] | pad_zero(.))";

def calc_minute_diff($minutes):
  now
  | strflocaltime("%Y-%m-%dT%H:%M:%S%z")
  | strptime("%Y-%m-%dT%H:%M:%S%z")
  | mktime
  | . / 60 - 1
  | ($minutes - .)
  | floor;

def update_meeting_subtitle($meeting):
  $meeting.time as $time_str
  | parse_meeting_time($time_str) as $meeting_start_minutes
  | parse_meeting_time_end($time_str) as $meeting_end_minutes
  | calc_minute_diff($meeting_start_minutes) as $minutes_until
  | calc_minute_diff($meeting_end_minutes) as $minutes_left
  | if $minutes_until < 60 then
      if $minutes_until <= 0 then
        if $minutes_left <= 0 then
          empty
        elif $minutes_left == 1 then
          $meeting + {"subtitle": "about to end"}
        else
          $meeting + {"subtitle": "right now (\($minutes_left) minutes left)"}
        end
      elif $minutes_until == 1 then
        $meeting + {"subtitle": "in a minute"}
      else
        $meeting + {"subtitle": "in \($minutes_until) minutes | \(format_subtitle($time_str))"}
      end
    else
      $meeting
    end;

.variables.cache_time as $cache_time_str
| parse_cache_time($cache_time_str) as $cache_minutes
| . + calculate_rerun($cache_minutes) 
| .items |= map(update_meeting_subtitle(.))