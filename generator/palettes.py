# Palette color indices — shared by renderer and tests.
# 0: background (gap between cells)
# 1: dead / seed level 0
# 2: seed level 1
# 3: seed level 2
# 4: seed level 3
# 5: seed level 4
# 6: outline (seed region border)
# 7: caption text

IDX_BACKGROUND = 0
IDX_DEAD = 1
IDX_SEED_BASE = 1   # contribution level k → IDX_SEED_BASE + k  (0→1, 1→2, …, 4→5)
IDX_SEED_MAX = IDX_SEED_BASE + 4  # fallback for cells with no contribution-coloured neighbour
IDX_OUTLINE = 6
IDX_CAPTION_TEXT = 7

# fmt: off
LIGHT_COLORS = [
    (255, 255, 255),  # 0  background
    (235, 237, 240),  # 1  dead / seed level 0  #ebedf0
    (155, 233, 168),  # 2  seed level 1          #9be9a8
    ( 64, 196,  99),  # 3  seed level 2          #40c463
    ( 48, 161,  78),  # 4  seed level 3          #30a14e
    ( 33, 110,  57),  # 5  seed level 4          #216e39
    (209, 217, 224),  # 6  outline               #d1d9e0
    ( 33,  37,  41),  # 7  caption text          #212529
]

DARK_COLORS = [
    ( 13,  17,  23),  # 0  background            #0d1117
    ( 22,  27,  34),  # 1  dead / seed level 0   #161b22
    ( 14,  68,  41),  # 2  seed level 1          #0e4429
    (  0, 109,  50),  # 3  seed level 2          #006d32
    ( 38, 166,  65),  # 4  seed level 3          #26a641
    ( 57, 211,  83),  # 5  seed level 4          #39d353
    ( 61,  68,  77),  # 6  outline               #3d444d
    (240, 246, 252),  # 7  caption text          #f0f6fc
]
# fmt: on

PALETTES = {"light": LIGHT_COLORS, "dark": DARK_COLORS}


def flat_palette(colors):
    """Return a 768-byte flat palette list suitable for PIL putpalette."""
    flat = []
    for r, g, b in colors:
        flat.extend([r, g, b])
    flat.extend([0] * (768 - len(flat)))
    return flat
