import os
import re
import sys

GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "")

repo_url = f"https://github.com/{GITHUB_REPOSITORY}"

lines = []

for line in sys.stdin.readlines():
    match = re.match(rf"^- (.*) #([0-9]+)$", line)

    if match is None:
        lines.append((line.lstrip("- "), []))
        continue

    title, pr = match.groups()

    if lines and title == lines[-1][0]:
        lines[-1][1].append(pr)
        continue

    lines.append((title, [pr]))

print(
    "\n".join(
        f"- {title} {' '.join(f'[#{pr}]({repo_url}/pull/{pr})' for pr in prs)}"
        for title, prs in lines
    )
)
