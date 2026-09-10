"""Pure region geometry helpers (drag → x,y,w,h).

[TRACE: DOCS/SCRATCHPAD.md] P2#15 — testable without Tk overlay.
"""

from __future__ import annotations

from typing import Tuple

from gif_maker.core.constants import MIN_REGION_SIZE


def selection_to_region(
    x1: int, y1: int, x2: int, y2: int
) -> Tuple[int, int, int, int]:
    """Normalize drag corners to (x, y, width, height) with positive size."""
    x = min(x1, x2)
    y = min(y1, y2)
    width = abs(x2 - x1)
    height = abs(y2 - y1)
    return (x, y, width, height)


def is_region_large_enough(
    region: Tuple[int, int, int, int],
    min_size: int = MIN_REGION_SIZE,
) -> bool:
    """True when width and height meet minimum selection size."""
    _x, _y, width, height = region
    return width >= min_size and height >= min_size


def center_region(
    screen_width: int,
    screen_height: int,
    region_width: int,
    region_height: int,
) -> Tuple[int, int, int, int]:
    """Clamp and center a box on the screen (browser-size style)."""
    w = max(1, min(region_width, screen_width))
    h = max(1, min(region_height, screen_height))
    x = max(0, (screen_width - w) // 2)
    y = max(0, (screen_height - h) // 2)
    return (x, y, w, h)
