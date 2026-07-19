DEFAULT_CONFIG = {
    # World dimensions (cols × rows). Contribution grid (53×7) is centred inside.
    "world_cols": 96,
    "world_rows": 31,
    # Maximum number of frames (including the initial seed frame).
    "max_generations": 100,
    # Cell rendering — pitch = cell_size + gap.
    "cell_size": 10,
    "gap": 3,
    # Animation timing (milliseconds per frame).
    "seed_hold_ms": 800,       # pause on the initial seed frame
    "frame_ms": 100,           # normal evolution cadence
    "terminal_hold_ms": 2000,  # pause on the final frame when terminated early
    # Output paths (relative to cwd or absolute).
    "output_light": "assets/contribution-life-light.gif",
    "output_dark": "assets/contribution-life-dark.gif",
}
