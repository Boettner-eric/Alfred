#!/usr/bin/python3
import os
import argparse
import json
import requests as rq
from os.path import exists
from time_format import time_ago
from dotenv import load_dotenv
from datetime import datetime as dt, timezone as tz

dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".env.local"))

load_dotenv(dotenv_path)

parser = argparse.ArgumentParser()
parser.add_argument("-r", "--repos", help="cache repos", action="store_true")
parser.add_argument("-m", "--merge", help="cache merge requests", action="store_true")
parser.add_argument("-u", "--users", help="cache current users", action="store_true")
parser.add_argument("-a", "--all", help="cache users and repos", action="store_true")
args = parser.parse_args()


def get_users():
    users = []
    gitlab_url = os.getenv("GITLAB_URL") + "/api/v4/users?per_page=100"
    headers = {
        "content-type": "application/json",
        "PRIVATE-TOKEN": os.environ["GITLAB_TOKEN"],
    }

    res = rq.get(url=gitlab_url, headers=headers)
    for user in res.json():
        if user["state"] == "active" and "bot" not in user["username"]:
            if not exists(f'users/{user["username"]}.png'):
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
                    "cookie": os.environ["GITLAB_COOKIE"],
                }
                img_data = rq.get(url=user["avatar_url"], headers=headers).content
                with open(f'users/{user["username"]}.png', "wb") as handler:
                    handler.write(img_data)
            first_name = user["name"].split(" ")[0]
            users.append(
                {
                    "arg": f'author_username={user["username"]}',
                    "subtitle": f"Get {first_name}'s active pull requests",
                    "icon": {"path": f'users/{user["username"]}.png'},
                    "uid": f'pr {user["username"]}',
                    "title": user["name"],
                    "mods": {
                        "cmd": {
                            "valid": True,
                            "arg": f'{user["username"]}',
                            "subtitle": f"View {first_name}'s profile",
                        },
                        "ctrl": {
                            "valid": True,
                            "arg": f'assignee_username={user["username"]}',
                            "subtitle": f"Get pull requests that {first_name} is assigned to",
                        },
                        "alt": {
                            "valid": True,
                            "arg": f'reviewer_username={user["username"]}',
                            "subtitle": f"Get pull requests that {first_name} is reviewing",
                        },
                    },
                },
            )
    with open("pr.json", "w") as outfile:
        json.dump({"items": users}, outfile, indent=4)


def get_repos():
    users = []
    gitlab_url = os.getenv("GITLAB_URL") + "/api/v4/projects?per_page=25&order_by=updated_at"
    
    headers = {
        "content-type": "application/json",
        "PRIVATE-TOKEN": os.getenv("GITLAB_TOKEN"),
    }

    res = rq.get(url=gitlab_url, headers=headers)
    if res.json() == {"message": "401 Unauthorized"}:
        return
    for repo in res.json():
        # this cookie hack is needed to get the repo images as gitlab broke the image API for some reason
        # if you need to figure out how to get the cookie for this then it's probably a bad idea
        # HINT: _gitlab_session cookie
        if (
            repo["archived"] == False
            and repo["empty_repo"] == False
            and not "archive" in repo["http_url_to_repo"]
        ):
            if (
                not exists(f'repos/{repo["path"]}.png')
                and repo["avatar_url"] != None
            ):
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
                    "cookie": os.environ["GITLAB_COOKIE"],
                }
                img_data = rq.get(url=repo["avatar_url"], headers=headers)
                with open(f'repos/{repo["path"]}.png', "wb") as handler:
                    handler.write(img_data.content)
            users.append(
                {
                    "arg": repo["web_url"],
                    "subtitle": (
                        repo["description"]
                        if repo["description"] != "" and repo["description"] != None
                        else "No description"
                    ),
                    "icon": {
                        "path": (
                            f'repos/{repo["path"]}.png'
                            if exists(f'repos/{repo["path"]}.png')
                            else "repos/default.png"
                        )
                    },
                    "uid": f'repo {repo["name"]}',
                    "title": repo["name"],
                    "mods": {
                        "cmd": {
                            "valid": True,
                            "arg": f"{repo['web_url']}/-/merge_requests",
                            "subtitle": f"Merge Requests: {repo['web_url']}/-/merge_requests",
                        },
                        "alt": {
                            "valid": True,
                            "arg": f"{repo['readme_url']}",
                            "subtitle": f"Readme: {repo['readme_url']}",
                        },
                        "ctrl": {
                            "valid": True,
                            "arg": f"{repo['http_url_to_repo']}",
                            "subtitle": f"Clone: {repo['http_url_to_repo']}",
                        },
                    },
                },
            )
    with open("repo.json", "w") as outfile:
        json.dump({"items": users}, outfile, indent=4)


def get_mrs():
    merge_requests = []
    gitlab_url = os.getenv("GITLAB_URL") + "/api/v4/merge_requests?state=opened&scope=all&order_by=created_at"
    headers = {
        "content-type": "application/json",
        "PRIVATE-TOKEN": os.getenv("GITLAB_TOKEN"),
    }

    res = rq.get(url=gitlab_url, headers=headers)
    if res.json() == {"message": "401 Unauthorized"}:
        return     
           
    for merge in res.json():
        if merge["state"] != "closed":
            [org, rest] = merge["references"]["full"].split("/")
            [repo_name, merge_id] = rest.split("!")
            merge_requests.append(
                {
                    "match": f"mr {org} {repo_name} {merge_id} {merge['title']} {merge['author']['name']}",
                    "arg": merge["web_url"],
                    "subtitle": f"{merge['references']['full']} · created {time_ago(merge['created_at'])} by {merge['author']['name']}",
                    "icon": {
                        "path": (
                            f'users/{merge["author"]["username"]}.png'
                            if exists(f'users/{merge["author"]["username"]}.png')
                            else "repos/default.png"
                        )
                    },
                    "title": merge["title"],
                    "mods": {
                        "shift": {
                            "valid": True,
                            "arg": f"{merge["web_url"]}/-/pipelines",
                            "subtitle": f"Pipelines: {merge['web_url']}/-/pipelines",
                        },
                        "cmd": {
                            "valid": True,
                            "arg": f"{merge['source_branch']}",
                            "subtitle": f"{merge['source_branch']}",
                        },
                        "alt": {
                            "valid": True,
                            "arg": f"{linear_url(merge['source_branch'])}",
                            "subtitle": f"linear:{linear_url(merge['source_branch'])}",
                        },
                        "ctrl": {
                            "valid": True,
                            "arg": f"{merge['web_url']}",
                            "subtitle": f'assignees: {", ".join(name["name"] for name in merge["assignees"])} | reviewers: {", ".join(name["name"] for name in merge["reviewers"])}',
                        },
                    },
                },
            )
    with open("merge.json", "w") as outfile:
        json.dump({"variables": {"cache_time": dt.now(tz.utc).timestamp()}, "items": merge_requests}, outfile, indent=2)

def linear_url(url):
    sections = url.split("-")
    return (f"//workspace/issue/{'-'.join(sections[:2]).upper()}/{'-'.join(sections[2:])}")


if __name__ == "__main__":
    if args.repos:
        get_repos()
    if args.users:
        get_users()
    if args.merge:
        get_mrs()
    if args.all:
        get_repos()
        get_users()
        print("Repos and Users updated")
