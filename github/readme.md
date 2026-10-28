# Github
Get a user's repos

This is still in progress and might have breaking changes

`gh` lists every repo you can access (personal, org, and collaborator), repos you were recently active in first, then by last push, with the owner shown in the subtitle when it isn't you

`gh-icons` downloads avatars for those owners so their repos show the owner's avatar. Already-downloaded avatars are skipped; delete `avatars/` to refresh them

`cgh` shows your contributions for today and the previous 5 days, colored like your profile's contribution graph, plus your total for the last year

# Setup
- install the [GitHub CLI](https://cli.github.com) and run `gh auth login`
- `make install` to create alfred symlink
