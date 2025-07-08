def calculate_rerun($cache_time_minutes):
  ((now | . / 60) - $cache_time_minutes) as $diff_minutes
  | if $diff_minutes < 5 then {} else {"rerun": 1} end;

def parse_cache_time($cache_time_str):
  ($cache_time_str | strptime("%d/%m/%Y, %H:%M:%S") | mktime) / 60;

def parse_meeting_time($time_str):
  ($time_str | split(" - ")[0] | strptime("%Y-%m-%dT%H:%M:%S") | mktime) / 60;

def update_meeting_subtitle($meeting):
  $meeting.time as $time_str
  | parse_meeting_time($time_str) as $meeting_start_minutes
  | ($meeting_start_minutes - (now | . / 60)) as $minutes_until
  | if $minutes_until >= 0 and $minutes_until < 60 then
      if $minutes_until == 0 then
        $meeting + {"subtitle": "right now"}
      elif $minutes_until == 1 then
        $meeting + {"subtitle": "in a minute"}
      else
        $meeting + {"subtitle": "in \($minutes_until) minutes"}
      end
    else
      $meeting
    end;

def process_meetings:
  .variables.cache_time as $cache_time_str
  | parse_cache_time($cache_time_str) as $cache_minutes
  | . + calculate_rerun($cache_minutes) 
  | .items |= map(update_meeting_subtitle(.));

# dynamically set the rerun time and update time_till subtitles
process_meetings