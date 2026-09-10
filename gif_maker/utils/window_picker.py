"""List OS windows and map them to capture regions.

[TRACE: DOCS/SCRATCHPAD.md] P2#13 — pygetwindow (already via pyautogui).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

from gif_maker.core.constants import MIN_REGION_SIZE


@dataclass(frozen=True)
class WindowInfo:
    """Capturable window metadata."""

    title: str
    left: int
    top: int
    width: int
    height: int

    def as_region(self) -> Tuple[int, int, int, int]:
        return (self.left, self.top, self.width, self.height)


def is_capturable_window(
    title: str,
    width: int,
    height: int,
    *,
    is_minimized: bool = False,
    exclude_substrings: Optional[Sequence[str]] = None,
    min_size: int = MIN_REGION_SIZE,
) -> bool:
    """True when window looks usable as a capture region."""
    if is_minimized:
        return False
    if not title or not str(title).strip():
        return False
    if width < min_size or height < min_size:
        return False
    lowered = title.lower()
    for part in exclude_substrings or ():
        if part.lower() in lowered:
            return False
    return True


def filter_windows(
    windows: Iterable[WindowInfo],
    *,
    exclude_substrings: Optional[Sequence[str]] = None,
) -> List[WindowInfo]:
    """Filter a list of WindowInfo with capturable rules."""
    out: List[WindowInfo] = []
    for win in windows:
        if is_capturable_window(
            win.title,
            win.width,
            win.height,
            exclude_substrings=exclude_substrings,
        ):
            out.append(win)
    return out


def list_capturable_windows(
    *,
    exclude_substrings: Optional[Sequence[str]] = None,
) -> List[WindowInfo]:
    """Enumerate visible OS windows via pygetwindow."""
    import pygetwindow as gw  # local import — keeps import light for tests

    excludes = list(exclude_substrings or ("Gif-Maker",))
    results: List[WindowInfo] = []
    try:
        raw = gw.getAllWindows()
    except Exception:
        return results

    for win in raw:
        try:
            title = getattr(win, "title", "") or ""
            left = int(getattr(win, "left", 0) or 0)
            top = int(getattr(win, "top", 0) or 0)
            width = int(getattr(win, "width", 0) or 0)
            height = int(getattr(win, "height", 0) or 0)
            minimized = bool(getattr(win, "isMinimized", False))
        except (TypeError, ValueError):
            continue
        if not is_capturable_window(
            title,
            width,
            height,
            is_minimized=minimized,
            exclude_substrings=excludes,
        ):
            continue
        results.append(
            WindowInfo(title=title.strip(), left=left, top=top, width=width, height=height)
        )
    # Stable-ish order: largest first (easier to pick main apps)
    results.sort(key=lambda w: w.width * w.height, reverse=True)
    return results
