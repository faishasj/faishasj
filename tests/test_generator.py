from __future__ import annotations

import json
import os

import pytest
from PIL import Image

from generator.config import DEFAULT_CONFIG
from generator.main import generate
from generator.palettes import DARK_COLORS, LIGHT_COLORS, IDX_CAPTION_TEXT
from generator.simulation import evolve, seed_world, step

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "..", "fixtures", "contribution_fixture.json")


@pytest.fixture(scope="session")
def fixture_grid():
    with open(FIXTURE_PATH) as f:
        return json.load(f)["grid"]


@pytest.fixture
def small_config(tmp_path):
    return {
        "max_generations": 5,
        "output_light": str(tmp_path / "light.gif"),
        "output_dark": str(tmp_path / "dark.gif"),
    }


def _count_frames(path: str) -> int:
    img = Image.open(path)
    n = 1
    try:
        while True:
            img.seek(img.tell() + 1)
            n += 1
    except EOFError:
        pass
    return n


# ---------------------------------------------------------------------------
# Fixture validation
# ---------------------------------------------------------------------------

def test_fixture_is_7_rows(fixture_grid):
    assert len(fixture_grid) == 7


def test_fixture_is_53_cols(fixture_grid):
    assert all(len(row) == 53 for row in fixture_grid)


def test_fixture_levels_in_range(fixture_grid):
    assert all(0 <= v <= 4 for row in fixture_grid for v in row)


# ---------------------------------------------------------------------------
# seed_world
# ---------------------------------------------------------------------------

def test_seed_world_dimensions(fixture_grid):
    world, _ = seed_world(fixture_grid, 31, 96)
    assert len(world) == 31
    assert len(world[0]) == 96


def test_seed_world_centering(fixture_grid):
    _, (off_r, off_c) = seed_world(fixture_grid, 31, 96)
    assert off_r == (31 - 7) // 2   # 12
    assert off_c == (96 - 53) // 2  # 21


def test_nonzero_contribution_is_alive(fixture_grid):
    world, (off_r, off_c) = seed_world(fixture_grid, 31, 96)
    for r in range(7):
        for c in range(53):
            expected = fixture_grid[r][c] > 0
            assert world[off_r + r][off_c + c] == expected, \
                f"Mismatch at seed ({r},{c}): level={fixture_grid[r][c]}"


def test_outer_cells_are_dead_initially(fixture_grid):
    world, _ = seed_world(fixture_grid, 31, 96)
    assert not world[0][0]
    assert not world[30][95]
    assert not world[0][95]
    assert not world[30][0]


# ---------------------------------------------------------------------------
# step — Conway rules
# ---------------------------------------------------------------------------

def test_conway_birth_requires_three_neighbors():
    world = [[False] * 5 for _ in range(5)]
    world[1][2] = True
    world[2][1] = True
    world[2][3] = True
    # (2,2) has exactly 3 live neighbours → born
    assert step(world)[2][2]


def test_conway_survival_with_two_neighbors():
    world = [[False] * 5 for _ in range(5)]
    world[2][2] = True
    world[2][3] = True
    world[3][2] = True
    # (2,2) has 2 live neighbours → survives
    assert step(world)[2][2]


def test_conway_survival_with_three_neighbors():
    world = [[False] * 5 for _ in range(5)]
    world[2][2] = True
    world[1][1] = True
    world[1][2] = True
    world[1][3] = True
    # (2,2) has 3 live neighbours → survives
    assert step(world)[2][2]


def test_conway_death_overpopulation():
    world = [[False] * 5 for _ in range(5)]
    world[1][1] = world[1][2] = world[1][3] = True
    world[2][1] = world[2][2] = True
    # (2,2) has 4 live neighbours → dies
    assert not step(world)[2][2]


def test_conway_death_underpopulation():
    world = [[False] * 5 for _ in range(5)]
    world[2][2] = True  # lone cell, 0 neighbours → dies
    assert not step(world)[2][2]


def test_hard_border_no_wraparound():
    # Three cells in a column at the right edge form a blinker.
    # With wraparound they would affect the left edge; with hard borders they must not.
    world = [[False] * 6 for _ in range(6)]
    world[2][5] = world[3][5] = world[4][5] = True
    next_w = step(world)
    # Hard-border blinker: (3,5) survives, (3,4) is born — but nothing at col 0.
    assert not next_w[3][0]
    assert not any(next_w[r][0] for r in range(6))


# ---------------------------------------------------------------------------
# evolve
# ---------------------------------------------------------------------------

def test_evolve_deterministic(fixture_grid):
    w1, _ = seed_world(fixture_grid, 31, 96)
    w2, _ = seed_world(fixture_grid, 31, 96)
    frames1, t1 = evolve(w1, 10)
    frames2, t2 = evolve(w2, 10)
    assert t1 == t2
    assert frames1 == frames2


def test_evolve_empty_world_terminates_after_one_frame():
    world = [[False] * 10 for _ in range(10)]
    frames, terminated = evolve(world, 40)
    assert terminated
    assert len(frames) == 1  # seed frame; next step == seed → cycle detected immediately


def test_evolve_still_life_2x2_block_terminates():
    # 2×2 block is a still life.
    world = [[False] * 6 for _ in range(6)]
    world[2][2] = world[2][3] = world[3][2] = world[3][3] = True
    frames, terminated = evolve(world, 40)
    assert terminated
    # Cycle detected before appending the repeated frame → only the seed frame is kept.
    assert len(frames) == 1


def test_evolve_respects_max_generations(fixture_grid):
    world, _ = seed_world(fixture_grid, 31, 96)
    frames, _ = evolve(world, 5)
    assert len(frames) <= 5


# ---------------------------------------------------------------------------
# generate — output files
# ---------------------------------------------------------------------------

def test_generate_creates_light_gif(fixture_grid, small_config):
    generate(fixture_grid, small_config)
    assert os.path.exists(small_config["output_light"])


def test_generate_creates_dark_gif(fixture_grid, small_config):
    generate(fixture_grid, small_config)
    assert os.path.exists(small_config["output_dark"])


def test_generate_is_deterministic(fixture_grid, small_config, tmp_path):
    generate(fixture_grid, small_config)
    with open(small_config["output_light"], "rb") as f:
        run1 = f.read()

    config2 = {
        **small_config,
        "output_light": str(tmp_path / "light2.gif"),
        "output_dark": str(tmp_path / "dark2.gif"),
    }
    generate(fixture_grid, config2)
    with open(config2["output_light"], "rb") as f:
        run2 = f.read()

    assert run1 == run2


def test_gif_image_dimensions(fixture_grid, small_config):
    generate(fixture_grid, small_config)
    img = Image.open(small_config["output_light"])
    cfg = {**DEFAULT_CONFIG, **small_config}
    pitch = cfg["cell_size"] + cfg["gap"]
    assert img.size == (
        cfg["world_cols"] * pitch,
        cfg["world_rows"] * pitch + cfg["caption_height"],
    )


def test_gif_caption_band_contains_text_pixels(fixture_grid, small_config):
    generate(fixture_grid, small_config)
    img = Image.open(small_config["output_light"])
    cfg = {**DEFAULT_CONFIG, **small_config}
    pitch = cfg["cell_size"] + cfg["gap"]
    caption_band = img.crop(
        (0, cfg["world_rows"] * pitch, img.size[0], img.size[1])
    )
    assert IDX_CAPTION_TEXT in set(caption_band.getdata())


def test_gif_frame_count_equals_max_generations(fixture_grid, small_config):
    generate(fixture_grid, small_config)
    assert _count_frames(small_config["output_light"]) == small_config["max_generations"]


def test_gif_last_frame_holds_on_early_termination(tmp_path):
    # Drive render_gif directly with two visually distinct frames and
    # terminated_early=True so the last frame receives terminal_hold_ms.
    from generator.renderer import render_gif

    # Frame 0: outer world all dead.
    # Frame 1: one live seeded cell with a nonzero contribution — visually
    #          different, so Pillow keeps both frames rather than deduplicating.
    world0 = [[False] * 96 for _ in range(31)]
    world1 = [row[:] for row in world0]
    world1[12][21] = True

    contribution_grid = [[0] * 53 for _ in range(7)]
    contribution_grid[0][0] = 1
    seed_offset = (12, 21)
    cfg = {**DEFAULT_CONFIG}
    output = str(tmp_path / "test.gif")

    render_gif(
        [world0, world1],
        contribution_grid,
        seed_offset,
        cfg,
        LIGHT_COLORS,
        output,
        terminated_early=True,
    )

    img = Image.open(output)
    assert img.n_frames == 2
    img.seek(1)
    expected_duration = (
        DEFAULT_CONFIG["terminal_hold_ms"]
        + (DEFAULT_CONFIG["max_generations"] - 2) * DEFAULT_CONFIG["frame_ms"]
    )
    assert img.info["duration"] == expected_duration


def test_light_dark_same_frame_count(fixture_grid, small_config):
    generate(fixture_grid, small_config)
    assert _count_frames(small_config["output_light"]) == _count_frames(small_config["output_dark"])


def test_light_dark_differ_in_bytes(fixture_grid, small_config):
    generate(fixture_grid, small_config)
    with open(small_config["output_light"], "rb") as f:
        light = f.read()
    with open(small_config["output_dark"], "rb") as f:
        dark = f.read()
    assert light != dark


# ---------------------------------------------------------------------------
# Palettes
# ---------------------------------------------------------------------------

def test_light_palette_has_8_entries():
    assert len(LIGHT_COLORS) == 8


def test_dark_palette_has_8_entries():
    assert len(DARK_COLORS) == 8


def test_palettes_differ():
    assert LIGHT_COLORS != DARK_COLORS


def test_palette_entries_are_valid_rgb():
    for colors in (LIGHT_COLORS, DARK_COLORS):
        for r, g, b in colors:
            assert 0 <= r <= 255
            assert 0 <= g <= 255
            assert 0 <= b <= 255


# ---------------------------------------------------------------------------
# README integration
# ---------------------------------------------------------------------------

README_PATH = os.path.join(os.path.dirname(__file__), "..", "README.md")


def test_readme_references_light_asset():
    with open(README_PATH) as f:
        content = f.read()
    assert "contribution-life-light.gif" in content


def test_readme_references_dark_asset():
    with open(README_PATH) as f:
        content = f.read()
    assert "contribution-life-dark.gif" in content


def test_readme_uses_picture_element():
    with open(README_PATH) as f:
        content = f.read()
    assert "<picture>" in content
    assert "prefers-color-scheme" in content
