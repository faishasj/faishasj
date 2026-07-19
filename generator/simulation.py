from __future__ import annotations

from typing import List, Tuple

Grid = List[List[bool]]


def seed_world(
    contribution_grid: List[List[int]],
    world_rows: int,
    world_cols: int,
) -> Tuple[Grid, Tuple[int, int]]:
    """
    Place the contribution grid centred inside a world of the given dimensions.

    Any contribution level > 0 becomes a live cell; 0 stays dead.

    Returns (world, (offset_row, offset_col)).
    """
    seed_rows = len(contribution_grid)
    seed_cols = len(contribution_grid[0])
    offset_row = (world_rows - seed_rows) // 2
    offset_col = (world_cols - seed_cols) // 2

    world: Grid = [[False] * world_cols for _ in range(world_rows)]
    for r in range(seed_rows):
        for c in range(seed_cols):
            world[offset_row + r][offset_col + c] = contribution_grid[r][c] > 0

    return world, (offset_row, offset_col)


def step(world: Grid) -> Grid:
    """Apply one generation of Conway's Game of Life with hard (dead) borders."""
    rows = len(world)
    cols = len(world[0])
    next_world: Grid = [[False] * cols for _ in range(rows)]

    for r in range(rows):
        for c in range(cols):
            n = _count_neighbors(world, r, c, rows, cols)
            alive = world[r][c]
            next_world[r][c] = (alive and n in (2, 3)) or (not alive and n == 3)

    return next_world


def _count_neighbors(world: Grid, r: int, c: int, rows: int, cols: int) -> int:
    count = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and world[nr][nc]:
                count += 1
    return count


def evolve(
    world: Grid,
    max_generations: int,
) -> Tuple[List[Grid], bool]:
    """
    Evolve the world for up to max_generations total frames (including the
    initial seed frame).

    Stops early if the next state has been seen before (still life, oscillator,
    or total extinction).

    Returns (frames, terminated_early).
    """
    frames: List[Grid] = [world]
    seen = {_hash(world)}

    for _ in range(max_generations - 1):
        next_world = step(frames[-1])
        h = _hash(next_world)
        if h in seen:
            return frames, True
        frames.append(next_world)
        seen.add(h)

    return frames, False


def _hash(world: Grid) -> tuple:
    return tuple(tuple(row) for row in world)
