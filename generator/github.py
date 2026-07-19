from __future__ import annotations

import datetime as dt
import os
import re
import ssl
import subprocess
from typing import List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ContributionDataError(RuntimeError):
    pass


_CONTRIBUTION_CELL_RE = re.compile(
    r'data-date="(?P<date>\d{4}-\d{2}-\d{2})"[^>]*data-level="(?P<level>[0-4])"'
)
_GITHUB_REMOTE_RE = re.compile(r"github\.com[:/](?P<owner>[^/]+)/")


def resolve_username(explicit: Optional[str] = None) -> str:
    if explicit:
        return explicit

    env_username = os.environ.get("GITHUB_CONTRIBUTION_USERNAME")
    if env_username:
        return env_username

    repo_owner = os.environ.get("GITHUB_REPOSITORY_OWNER")
    if repo_owner:
        return repo_owner

    try:
        remote = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ContributionDataError(
            "Set GITHUB_CONTRIBUTION_USERNAME or run from a GitHub profile repository."
        ) from exc

    match = _GITHUB_REMOTE_RE.search(remote)
    if not match:
        raise ContributionDataError(
            "Could not infer the GitHub username from the repository remote."
        )
    return match.group("owner")


def fetch_contribution_grid(explicit_username: Optional[str] = None) -> List[List[int]]:
    username = resolve_username(explicit_username)
    url = f"https://github.com/users/{username}/contributions"
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/537.36",
        },
    )

    try:
        response = urlopen(request, context=ssl._create_unverified_context())
        html = response.read().decode("utf-8")
    except (HTTPError, URLError, OSError) as exc:
        raise ContributionDataError(f"Failed to fetch public contribution data for {username}.") from exc

    cells = [
        (dt.date.fromisoformat(match.group("date")), int(match.group("level")))
        for match in _CONTRIBUTION_CELL_RE.finditer(html)
    ]
    if not cells:
        raise ContributionDataError(f"No contribution cells were found for {username}.")

    cells.sort(key=lambda item: item[0])
    start_date = cells[0][0]
    if start_date.weekday() != 6:
        raise ContributionDataError(
            f"Expected the contribution graph to start on a Sunday, got {start_date.isoformat()}."
        )

    grid: List[List[int]] = [[0] * 53 for _ in range(7)]
    for current_date, level in cells:
        day_offset = (current_date - start_date).days
        week_index = day_offset // 7
        weekday_index = (current_date.weekday() + 1) % 7
        if not 0 <= week_index < 53:
            raise ContributionDataError(
                f"Contribution date {current_date.isoformat()} fell outside the 53-week grid."
            )
        grid[weekday_index][week_index] = level

    return grid