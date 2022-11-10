import json
import os
import re
import requests
import sys

DEPLOY_STATUS = os.environ.get("DEPLOY_STATUS", "")
GITHUB_ACTOR = os.environ.get("GITHUB_ACTOR", "")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "")
GITHUB_RUN_ID = os.environ.get("GITHUB_RUN_ID", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
MESSAGE_TEMPLATE = os.environ.get("MESSAGE_TEMPLATE", "")
PROJECT_NAME = os.environ.get("PROJECT_NAME", "")
PROJECT_TYPE = os.environ.get("PROJECT_TYPE", "")
TARGET_NAME = os.environ.get("TARGET_NAME", "")
TARGET_URL = os.environ.get("TARGET_URL", "")

github = requests.Session()
github.headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
}

github_url = f"https://github.com/{GITHUB_REPOSITORY}"

action_status = dict(
    failure=":cross:",
    pending=":buffering:",
    skipped="🚀",
    success="🚀",
).get(DEPLOY_STATUS or "pending")
action_url = f"{github_url}/actions/runs/{GITHUB_RUN_ID}"

image_html_re = re.compile(r'<img.*?alt="(.*?)".*?src="(.*?)".*?>')
image_md_re = re.compile(r"!\[(.*?)\]\((.*?)\)")

release_re = re.compile(
    r"""
    ^\#+\s
    \[(?P<version>.*?)\]\((?P<compare_url>.*?)\)\s
    \((?P<date>.*?)\)$
    """,
    re.VERBOSE,
)


def build_message():
    user = github.get(f"https://api.github.com/users/{GITHUB_ACTOR}").json()

    actor = user["name"]
    actor_link = f"[{actor}]({user['html_url']})"
    project = f"{PROJECT_NAME} {release['version']}".strip()
    project_link = f"[{project}]({release['compare_url']})"
    run_link = f"[{action_status}]({action_url})"
    target = TARGET_NAME
    target_link = f"[{target}]({TARGET_URL})"
    verb = "released" if PROJECT_TYPE == "package" else "deployed"

    if MESSAGE_TEMPLATE == "images":
        images = get_images(release)

        if not images:
            return

        return {
            "text": f"🚀 {actor} {verb} {project} to {target}",
            "blocks": [
                {
                    "type": "image",
                    "title": {
                        "type": "plain_text",
                        "text": text,
                    },
                    "image_url": url,
                    "alt_text": text,
                }
                for text, url in images
            ],
        }

    return {
        "username": user["name"],
        "icon_url": user["avatar_url"],
        "text": f"🚀 {actor} {verb} {project} to {target}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": truncate_message(
                        transform_markdown(
                            f"{run_link} {actor_link} {verb} {project_link} to {target_link}\n{release['notes']}"
                        ),
                    ),
                },
            }
        ],
        "unfurl_links": False,
        "unfurl_media": False,
    }


def find_images(text):
    return image_html_re.findall(text) + image_md_re.findall(text)


def get_images(release):
    images = []

    response = github.get(
        f"https://api.github.com/repos/{GITHUB_REPOSITORY}/pulls",
        params=dict(
            per_page=100,
            state="closed",
        ),
    )

    pulls = {pull["number"]: pull for pull in response.json()}

    for pull in release["pulls"]:
        pull = pulls.get(pull)

        if not pull:
            continue

        images.extend(
            [
                (f"{pull['title']} #{pull['number']}: {text}".strip(": "), url)
                for text, url in find_images(pull["body"] or "")
                if "badge" not in url
            ]
        )

    return images


def get_release():
    heading = None
    notes = []

    with open("CHANGELOG.md", "r") as f:
        lines = f.readlines()
        heading = lines[4]
        for line in lines[6:]:
            if line.strip():
                notes.append(line.strip())
                continue
            break

    release = release_re.match(heading).groupdict()

    pulls = list(
        map(int, re.findall(rf"{re.escape(github_url)}/pull/([0-9]+)", "".join(notes)))
    )

    notes = "\n".join(notes)

    return dict(**release, notes=notes, pulls=pulls)


def transform_markdown(text):
    """Transform markdown into Slack mrkdwn"""
    text = text.replace("\r\n", "\n")
    # preserve **markdown bold**
    text = text.replace("**", "\\*\\*")
    # convert images and links into slack links
    text = re.sub(r"!?\[([^\[\]]*?)\]\(([^\(\)]*?)\)", r"<\2|\1>", text)
    # convert lists into bullets
    text = re.sub(
        r"(?<=^) *[·•●\-\*➤]+\s*(.*)",
        r" *•*  \1",
        text,
        flags=re.MULTILINE,
    )
    # convert headings into bold
    text = re.sub(
        r"(?<=^)\n*[#=_]+ *(.*?) *[#=_]* *\n*$",
        r"\n*\1*\n",
        text,
        flags=re.MULTILINE,
    )
    # convert indentation into code blocks
    text = re.sub(r"((?:\n {4}.*)+)", r"\n```\1\n```", text)
    text = re.sub(r"^ {4}", r"", text, flags=re.MULTILINE)
    # restore **markdown bold** as *slack bold*
    text = text.replace("\\*\\*", "*")
    # single space after periods otherwise sentences can wrap weird
    text = re.sub(r"\. {2,}", ". ", text)
    return text


def truncate_message(message, max_length=3000):
    message_lines = message.split("\n")
    extra_lines = []

    heading_anchor = f"{release['version']}-{release['date']}".replace(".", "")
    changelog_url = f"{github_url}/blob/master/CHANGELOG.md#{heading_anchor}"
    more_line = ""

    while len("\n".join(message_lines)) > max_length - len(more_line):
        extra_lines.append(message_lines.pop())
        more_line = transform_markdown(f"+ [{len(extra_lines)} more]({changelog_url})")

    if more_line:
        message_lines.append(more_line)

    return "\n".join(message_lines)


if __name__ == "__main__":
    release = get_release()
    message = build_message()

    if message:
        print(json.dumps(message))
