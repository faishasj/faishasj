from __future__ import annotations

import os
from typing import List, Optional

from .config import DEFAULT_CONFIG
from .palettes import DARK_COLORS, LIGHT_COLORS
from .renderer import render_gif
from .simulation import evolve, seed_world


def generate(
    contribution_grid: List[List[int]],
    config: Optional[dict] = None,
) -> None:
    """
    Generate light and dark Conway GIFs from a contribution grid.

    contribution_grid — 7 rows × 53 cols, values 0–4.
    config            — optional overrides for DEFAULT_CONFIG values.

    Output paths default to assets/contribution-life-{light,dark}.gif
    relative to the current working directory.
    """
    cfg = {**DEFAULT_CONFIG, **(config or {})}

    world, seed_offset = seed_world(
        contribution_grid, cfg["world_rows"], cfg["world_cols"]
    )
    frames, terminated_early = evolve(world, cfg["max_generations"])

    for theme, colors in (("light", LIGHT_COLORS), ("dark", DARK_COLORS)):
        output_path = cfg[f"output_{theme}"]
        os.makedirs(
            os.path.dirname(os.path.abspath(output_path)), exist_ok=True
        )
        render_gif(
            frames,
            contribution_grid,
            seed_offset,
            cfg,
            colors,
            output_path,
            terminated_early,
        )
