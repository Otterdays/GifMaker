"""Constants for Gif-Maker."""

# UI Constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
MIN_WIDTH = 900
MIN_HEIGHT = 600
PREVIEW_MAX_SIZE = (350, 250)
MIN_REGION_SIZE = 100

# Color Scheme — Google Material light theme
COLOR_BG_PRIMARY = "#ffffff"  # window / card surface
COLOR_BG_SECONDARY = "#f8f9fa"  # app background, tab + status strips
COLOR_ACCENT_RED = "#d93025"
COLOR_ACCENT_GREEN = "#188038"
COLOR_ACCENT_BLUE = "#1a73e8"
COLOR_ACCENT_PURPLE = "#9334e6"
COLOR_ACCENT_ORANGE = "#e8710a"
COLOR_ACCENT_YELLOW = "#f9ab00"
COLOR_TEXT_WHITE = "#ffffff"  # foreground on filled accent buttons
COLOR_TEXT_LIGHT = "#5f6368"
COLOR_TEXT_LIGHTBLUE = "#1a73e8"
COLOR_BROWSE = "#5f6368"

# Extended UI palette — Material surfaces, borders & text tones
COLOR_HEADER_BG = "#ffffff"  # app bar
COLOR_BG_INPUT = "#ffffff"  # outlined text-field surface
COLOR_SURFACE = "#f1f3f4"  # filled field / inactive tab surface
COLOR_BORDER = "#dadce0"  # hairline dividers & field outlines
COLOR_TEXT_PRIMARY = "#202124"  # primary body text
COLOR_TEXT_SECONDARY = "#5f6368"  # secondary text / labels
COLOR_TEXT_MUTED = "#80868b"  # hints + disabled foreground

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
WINDOW_HIDE_DELAY = 0.5
WINDOW_HIDE_DELAY_MS = 500  # same delay for root.after (ms)
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
