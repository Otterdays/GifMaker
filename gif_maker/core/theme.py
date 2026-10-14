"""Theming engine for Gif-Maker.

Defines color palettes as frozen dataclasses and provides system theme detection.
Each Theme instance carries every color token the GUI needs so that widgets can be
recolored in one pass when the user switches themes.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Theme:
    """Immutable color palette for the application."""

    name: str
    # Surfaces
    bg_primary: str       # card / window surface
    bg_secondary: str     # app background, tab strip, status bar
    bg_input: str         # text-field surface
    surface: str          # filled-field / inactive tab
    border: str           # hairline dividers, outlines
    header_bg: str        # app bar background
    # Text
    text_primary: str
    text_secondary: str
    text_muted: str
    text_white: str       # fg on filled accent buttons
    # Accents
    accent_blue: str
    accent_red: str
    accent_green: str
    accent_yellow: str
    accent_orange: str
    accent_purple: str

    def color_map(self) -> Dict[str, str]:
        """Return attribute-name -> hex-color for all color tokens (excludes name)."""
        return {k: v for k, v in vars(self).items() if k != "name"}

    def value_to_attr(self) -> Dict[str, str]:
        """Return hex-color -> attribute-name mapping for recolor substitution."""
        mapping: Dict[str, str] = {}
        for attr, value in self.color_map().items():
            mapping[value] = attr
        return mapping


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------

LIGHT = Theme(
    name="light",
    bg_primary="#ffffff",
    bg_secondary="#f8f9fa",
    bg_input="#ffffff",
    surface="#f1f3f4",
    border="#dadce0",
    header_bg="#ffffff",
    text_primary="#202124",
    text_secondary="#5f6368",
    text_muted="#80868b",
    text_white="#ffffff",
    accent_blue="#1a73e8",
    accent_red="#d93025",
    accent_green="#188038",
    accent_yellow="#f9ab00",
    accent_orange="#e8710a",
    accent_purple="#9334e6",
)

DARK = Theme(
    name="dark",
    bg_primary="#1e1e1e",
    bg_secondary="#2d2d2d",
    bg_input="#3c3c3c",
    surface="#333333",
    border="#555555",
    header_bg="#1e1e1e",
    text_primary="#e8eaed",
    text_secondary="#9aa0a6",
    text_muted="#6e6e6e",
    text_white="#1e1e1e",
    accent_blue="#8ab4f8",
    accent_red="#f28b82",
    accent_green="#81c995",
    accent_yellow="#fdd663",
    accent_orange="#fcad70",
    accent_purple="#d2a8ff",
)

OLED = Theme(
    name="oled",
    bg_primary="#000000",
    bg_secondary="#0a0a0a",
    bg_input="#1a1a1a",
    surface="#111111",
    border="#333333",
    header_bg="#000000",
    text_primary="#e8eaed",
    text_secondary="#9aa0a6",
    text_muted="#6e6e6e",
    text_white="#000000",
    accent_blue="#8ab4f8",
    accent_red="#f28b82",
    accent_green="#81c995",
    accent_yellow="#fdd663",
    accent_orange="#fcad70",
    accent_purple="#d2a8ff",
)

HIGH_CONTRAST = Theme(
    name="high_contrast",
    bg_primary="#000000",
    bg_secondary="#000000",
    bg_input="#000000",
    surface="#1a1a1a",
    border="#ffffff",
    header_bg="#000000",
    text_primary="#ffffff",
    text_secondary="#cccccc",
    text_muted="#999999",
    text_white="#000000",
    accent_blue="#00bfff",
    accent_red="#ff6600",
    accent_green="#00ff00",
    accent_yellow="#ffff00",
    accent_orange="#ff8c00",
    accent_purple="#ff00ff",
)


# ---------------------------------------------------------------------------
# Registry and lookup
# ---------------------------------------------------------------------------

THEME_REGISTRY: Dict[str, Theme] = {
    "light": LIGHT,
    "dark": DARK,
    "oled": OLED,
    "high_contrast": HIGH_CONTRAST,
}

# Labels shown in the GUI combobox
THEME_LABELS: Dict[str, str] = {
    "system": "System",
    "light": "Light",
    "dark": "Dark",
    "oled": "OLED",
    "high_contrast": "High Contrast",
}

VALID_PREFERENCES = tuple(THEME_LABELS.keys())


def detect_system_theme() -> str:
    """Detect OS dark/light mode preference.

    Returns 'light' or 'dark'. On Windows reads the registry AppsUseLightTheme key.
    On other platforms defaults to 'light'.
    """
    if sys.platform == "win32":
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return "light" if value == 1 else "dark"
        except (OSError, FileNotFoundError):
            return "light"
    return "light"


def resolve_theme_choice(preference: str) -> Theme:
    """Map a user preference string to a concrete Theme instance.

    Args:
        preference: One of 'system', 'light', 'dark', 'oled', 'high_contrast'.

    Returns:
        The matching Theme object.
    """
    if preference == "system":
        detected = detect_system_theme()
        return THEME_REGISTRY.get(detected, LIGHT)
    return THEME_REGISTRY.get(preference, LIGHT)
