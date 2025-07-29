# Warp Directory Navigator

An Alfred workflow that reads your `.warprc` file and provides quick access to your warp points.

## Setup

- install `jq` via `brew install jq`
- add the `wd` plugin to zsh ([link](https://github.com/mfaerevaag/wd))
- add some directories to wd via `wd add [dir]`

## Usage

- run `jq -R -f alfred.jq ~/.warprc` to see the parsed output
- use `wd` in alfred to view warp points and typeahead to filter the results

# Mods
  - `⌘` -> open in Terminal
  - `⌥` -> open in Editor
  - `⌃` -> reveal in Finder
