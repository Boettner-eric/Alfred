def calculate_rerun($cache_time_seconds):
  (now - $cache_time_seconds) as $diff_seconds
  | if $diff_seconds < 300 then {} else {"rerun": 1} end;

. + calculate_rerun(.variables.cache_time)
