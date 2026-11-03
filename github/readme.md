# Github
Get a user's repos

This is still in progress and might have breaking changes

`gh` lists every repo you can access (personal, org, and collaborator), repos you were recently active in first, then by last push, with the owner shown in the subtitle when it isn't you

`gh-icons` downloads avatars for those owners so their repos show the owner's avatar. Already-downloaded avatars are skipped; delete `avatars/` to refresh them

`prs` lists the members of every org you belong to with their avatars. Users are loaded on first run; run `gh-users` to reload them and download any new avatars. Pull request links are scoped to the orgs you share with that user

- default -> open pull requests the user authored
- `⌘` -> view the user's profile
- `⌃` -> open pull requests the user is assigned to
- `⌥` -> open pull requests awaiting the user's review

`cgh` shows your contributions for today and the previous 5 days, colored like your profile's contribution graph, plus your total for the last year

# Setup
- install the [GitHub CLI](https://cli.github.com) and run `gh auth login`
- `make install` to create alfred symlink
