"""CLI entry point — run as: python -m generator [fixture_path|username]"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .github import ContributionDataError, fetch_contribution_grid
from .main import generate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", nargs="?", help="Fixture JSON path or explicit GitHub username")
    args = parser.parse_args()

    source = args.source
    if source and Path(source).is_file():
        fixture_path = Path(source)
        with fixture_path.open() as f:
            data = json.load(f)
        contribution_grid = data["grid"]
        description = f"fixture {fixture_path}"
    else:
        contribution_grid = fetch_contribution_grid(source)
        description = f"public contributions for {source or 'repository owner'}"

    generate(contribution_grid)
    print(f"Generated assets from {description}")


if __name__ == "__main__":
    try:
        main()
    except ContributionDataError as exc:
        raise SystemExit(str(exc)) from exc

