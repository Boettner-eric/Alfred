def calculate_rerun($cache_time_minutes):
  ((now | . / 60) - $cache_time_minutes) as $diff_minutes
  | if $diff_minutes < 5 then {} else {"rerun": 1} end;

def parse_cache_time($cache_time_str):
  ($cache_time_str | strptime("%d/%m/%Y, %H:%M:%S") | mktime) / 60;

def process_meetings:
  parse_cache_time(.variables.cache_time) as $cache_minutes
  | . + calculate_rerun($cache_minutes);

process_meetings