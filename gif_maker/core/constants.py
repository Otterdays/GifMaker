"""Constants for Gif-Maker.

Color tokens are sourced from the active Theme so that they reflect the
theme chosen by the user (or auto-detected from the OS).  Font, timing,
and dimension constants are theme-independent.
"""

from gif_maker.core.theme import LIGHT, Theme

# UI Constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
MIN_WIDTH = 900
MIN_HEIGHT = 600
PREVIEW_MAX_SIZE = (350, 250)
MIN_REGION_SIZE = 100

# ---------------------------------------------------------------------------
# Color Scheme — resolved from the default (LIGHT) theme.
# At runtime main_window uses its own self._theme; these names exist so that
# non-GUI code (dialogs, previews) can reference a sane default.
# ---------------------------------------------------------------------------

_active_theme: Theme = LIGHT


def set_active_theme(theme: Theme) -> None:
    """Update the module-level active theme and refresh COLOR_* names."""
    global _active_theme
    _active_theme = theme


def get_active_theme() -> Theme:
    """Return the currently active Theme."""
    return _active_theme


# Convenience: current-theme color accessors (read from _active_theme at import)
COLOR_BG_PRIMARY = _active_theme.bg_primary
COLOR_BG_SECONDARY = _active_theme.bg_secondary
COLOR_BG_INPUT = _active_theme.bg_input
COLOR_SURFACE = _active_theme.surface
COLOR_BORDER = _active_theme.border
COLOR_HEADER_BG = _active_theme.header_bg
COLOR_TEXT_PRIMARY = _active_theme.text_primary
COLOR_TEXT_SECONDARY = _active_theme.text_secondary
COLOR_TEXT_MUTED = _active_theme.text_muted
COLOR_TEXT_WHITE = _active_theme.text_white
COLOR_ACCENT_BLUE = _active_theme.accent_blue
COLOR_ACCENT_RED = _active_theme.accent_red
COLOR_ACCENT_GREEN = _active_theme.accent_green
COLOR_ACCENT_YELLOW = _active_theme.accent_yellow
COLOR_ACCENT_ORANGE = _active_theme.accent_orange
COLOR_ACCENT_PURPLE = _active_theme.accent_purple
# Aliases kept for backward compat
COLOR_TEXT_LIGHT = _active_theme.text_secondary
COLOR_TEXT_LIGHTBLUE = _active_theme.accent_blue
COLOR_BROWSE = _active_theme.text_secondary

# Font Scheme — Segoe UI reads cleanly on Windows (Material-ish)
FONT_FAMILY = "Segoe UI"
FONT_MONO = ("Consolas", 9)
FONT_TITLE = (FONT_FAMILY, 20, "bold")
FONT_VERSION = (FONT_FAMILY, 11, "bold")
FONT_SECTION = (FONT_FAMILY, 11, "bold")
FONT_LABEL = (FONT_FAMILY, 10)
FONT_INPUT = (FONT_FAMILY, 10)
FONT_BUTTON = (FONT_FAMILY, 10, "bold")
FONT_BUTTON_LARGE = (FONT_FAMILY, 11, "bold")
FONT_HINT = (FONT_FAMILY, 8)

# Timing Constants
WINDOW_HIDE_DELAY_MS = 500  # delay before capture starts after window hide
SELECTION_CLOSE_DELAY = 2000
MIN_INTERVAL = 0.1
MAX_INTERVAL = 60.0
MIN_SCREENSHOT_COUNT = 1
MAX_SCREENSHOT_COUNT = 1000

# Capture reliability — abort after this many consecutive screenshot failures
MAX_CAPTURE_FAILURES = 3

# Frame Duration Constants (milliseconds)
FRAME_DURATION_SLOW = 333  # 3 FPS
FRAME_DURATION_NORMAL = 200  # 5 FPS
FRAME_DURATION_FAST = 125  # 8 FPS
FRAME_DURATION_VERY_FAST = 100  # 10 FPS

# Editor Timeline Constants
TIMELINE_THUMB_SIZE = (72, 48)
TIMELINE_CANVAS_HEIGHT = 90
DEFAULT_FRAME_DURATION_MS = 200
