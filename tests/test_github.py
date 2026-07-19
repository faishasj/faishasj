from __future__ import annotations

import datetime as dt
from types import SimpleNamespace

import pytest

import generator.github as github


def _make_contributions_html(start_date: dt.date, days: int) -> str:
    cells = []
    for offset in range(days):
        current_date = start_date + dt.timedelta(days=offset)
        cells.append(
            f'<rect data-date="{current_date.isoformat()}" data-level="{offset % 5}"></rect>'
        )
    return "<svg>" + "".join(cells) + "</svg>"


def test_fetch_contribution_grid_parses_public_graph(monkeypatch):
    html = _make_contributions_html(dt.date(2025, 7, 20), 365)

    monkeypatch.setattr(
        github,
        "urlopen",
        lambda *args, **kwargs: SimpleNamespace(read=lambda: html.encode("utf-8")),
    )

    grid = github.fetch_contribution_grid("faishasj")

    assert len(grid) == 7
    assert all(len(row) == 53 for row in grid)
    assert grid[0][0] == 0
    assert grid[1][0] == 1
    assert grid[6][0] == 1
    assert grid[0][1] == 2


def test_resolve_username_prefers_explicit_value(monkeypatch):
    monkeypatch.setenv("GITHUB_CONTRIBUTION_USERNAME", "ignored")
    assert github.resolve_username("faishasj") == "faishasj"


def test_resolve_username_falls_back_to_env(monkeypatch):
    monkeypatch.delenv("GITHUB_CONTRIBUTION_USERNAME", raising=False)
    monkeypatch.setenv("GITHUB_REPOSITORY_OWNER", "faishasj")
    assert github.resolve_username() == "faishasj"