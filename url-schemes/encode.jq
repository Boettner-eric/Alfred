# Shared url encoding: include "encode" {search: "./"};

# For text that is already url-shaped (saved defaults, examples, history urls):
# percent-encodes only what can't appear in a url, like spaces, so existing
# escapes and query syntax (& = + %20) are kept and nothing is encoded twice.
def fix_url:
  gsub("%(?![0-9A-Fa-f]{2})"; "%25")
  | gsub("(?<c>[^A-Za-z0-9._~!$&'()*+,;=:@/?%#\\[\\]-])"; .c | @uri);
