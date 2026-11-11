# Shared by the history scripts: include "url" {search: "./"};

def decode: try @urid catch .;

# [[key, value], ...] from a raw query string, values left as written
def query_pairs:
  split("&") | map(select(length > 0) | split("=") | [.[0], (.[1:] | join("="))]);

# { scheme, path, query } with the query left raw
def split_url:
  (split("://")) as $parts
  | (if ($parts | length) >= 2 then $parts[1:] | join("://") else . end) as $rest
  | { scheme: (if ($parts | length) >= 2 then $parts[0] + "://" else "" end),
      path: ($rest | split("?") | .[0]),
      query: ($rest | split("?") | .[1:] | join("?")) };

# One string per logical url, so history entries that differ only in
# percent-encoding, param order, scheme case or a trailing / or ? collapse
# together. A key match, not a url to open.
def canonical_url:
  split_url as $u
  | ($u.query | query_pairs | map(map(decode)) | sort_by(.[0]) | map("\(.[0])=\(.[1])") | join("&")) as $query
  | ($u.scheme | ascii_downcase) + ($u.path | decode | rtrimstr("/"))
    + (if $query == "" then "" else "?" + $query end);
