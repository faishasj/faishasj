from __future__ import annotations

from typing import List, Tuple

from PIL import Image, ImageDraw

from .palettes import (
    IDX_BACKGROUND,
    IDX_DEAD,
    IDX_OUTLINE,
    IDX_SEED_BASE,
    IDX_SEED_MAX,
    flat_palette,
)


def render_gif(
    frames: list,
    contribution_grid: List[List[int]],
    seed_offset: Tuple[int, int],
    config: dict,
    colors: list,
    output_path: str,
    terminated_early: bool,
) -> None:
    """
    Render an animated GIF for one theme.

    frames               — list of world state grids (each a list[list[bool]])
    contribution_grid    — original 7×53 intensity grid (values 0–4), never changes
    seed_offset          — (offset_row, offset_col) of the seed region in the world
    config               — merged config dict
    colors               — 8-entry list of (R, G, B) from palettes.LIGHT_COLORS/DARK_COLORS
    output_path          — destination file path
    terminated_early     — True when the simulation cycled before max_generations
    """
    cell_size: int = config["cell_size"]
    gap: int = config["gap"]
    pitch: int = cell_size + gap
    world_rows: int = len(frames[0])
    world_cols: int = len(frames[0][0])
    img_w: int = world_cols * pitch
    img_h: int = world_rows * pitch

    pal_flat = flat_palette(colors)

    images: list = []
    durations: list = []

    max_generations: int = config["max_generations"]

    for i, frame in enumerate(frames):
        img = _render_frame(
            frame,
            contribution_grid,
            seed_offset,
            pal_flat,
            cell_size,
            pitch,
            img_w,
            img_h,
        )
        images.append(img)

        if i == 0:
            durations.append(config["seed_hold_ms"])
        elif i == len(frames) - 1 and terminated_early:
            remaining_generations = max(0, max_generations - len(frames))
            terminal_duration = (
                config["terminal_hold_ms"]
                + remaining_generations * config["frame_ms"]
            )
            durations.append(terminal_duration)
        else:
            durations.append(config["frame_ms"])

    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        loop=0,
        duration=durations,
        transparency=IDX_BACKGROUND,
        optimize=False,
    )


def _render_frame(
    world: list,
    contribution_grid: List[List[int]],
    seed_offset: Tuple[int, int],
    pal_flat: list,
    cell_size: int,
    pitch: int,
    img_w: int,
    img_h: int,
) -> Image.Image:
    img = Image.new("P", (img_w, img_h), IDX_BACKGROUND)
    img.putpalette(pal_flat)
    draw = ImageDraw.Draw(img)

    # Scale GitHub's 2 px radius on 10 px cells to our cell size.
    corner_radius = max(1, round(cell_size * 2 / 10))

    offset_r, offset_c = seed_offset
    seed_rows = len(contribution_grid)
    seed_cols = len(contribution_grid[0])
    world_rows = len(world)
    world_cols = len(world[0])

    for r in range(world_rows):
        for c in range(world_cols):
            x = c * pitch
            y = r * pitch
            cell_rect = [x, y, x + cell_size - 1, y + cell_size - 1]

            in_seed = (
                offset_r <= r < offset_r + seed_rows
                and offset_c <= c < offset_c + seed_cols
            )

            if in_seed:
                level = contribution_grid[r - offset_r][c - offset_c]
                if world[r][c]:
                    if level > 0:
                        color_idx = IDX_SEED_BASE + level
                    else:
                        # Born via Conway inside seed region with no original
                        # contribution: inherit lightest adjacent alive color.
                        color_idx = _lightest_neighbor_color(
                            world, contribution_grid, seed_offset,
                            r, c, world_rows, world_cols,
                        )
                else:
                    color_idx = IDX_DEAD
            elif world[r][c]:
                # Outer alive cell: inherit lightest adjacent contribution color.
                color_idx = _lightest_neighbor_color(
                    world, contribution_grid, seed_offset,
                    r, c, world_rows, world_cols,
                )
            else:
                color_idx = IDX_DEAD

            draw.rounded_rectangle(cell_rect, radius=corner_radius, fill=color_idx)

    # Persistent outline around the seed region — sits in the 1-px gap.
    ox0 = offset_c * pitch - 1
    oy0 = offset_r * pitch - 1
    ox1 = (offset_c + seed_cols - 1) * pitch + cell_size
    oy1 = (offset_r + seed_rows - 1) * pitch + cell_size
    draw.rectangle([ox0, oy0, ox1, oy1], outline=IDX_OUTLINE, width=1)

    return img


def _lightest_neighbor_color(
    world: list,
    contribution_grid: List[List[int]],
    seed_offset: Tuple[int, int],
    r: int,
    c: int,
    world_rows: int,
    world_cols: int,
) -> int:
    """
    Return the palette index for a newly born / outer alive cell.

    Scans the 8 immediate alive neighbours for cells that carry a contribution
    intensity (seed region, level > 0) and returns the lightest (lowest level)
    among them — so that freshly born cells fade gracefully away from the seed.
    Falls back to IDX_OUTER_ALIVE when no contribution-coloured neighbour exists.
    """
    offset_r, offset_c = seed_offset
    seed_rows = len(contribution_grid)
    seed_cols = len(contribution_grid[0])

    lightest: int | None = None
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if not (0 <= nr < world_rows and 0 <= nc < world_cols):
                continue
            if not world[nr][nc]:
                continue
            n_in_seed = (
                offset_r <= nr < offset_r + seed_rows
                and offset_c <= nc < offset_c + seed_cols
            )
            if n_in_seed:
                n_level = contribution_grid[nr - offset_r][nc - offset_c]
                if n_level > 0 and (lightest is None or n_level < lightest):
                    lightest = n_level

    return IDX_SEED_BASE + lightest if lightest is not None else IDX_SEED_MAX
