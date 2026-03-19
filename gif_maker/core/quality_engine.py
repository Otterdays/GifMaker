"""Quality and speed mapping, validation, and size estimation."""

from typing import List, Optional, Tuple

from PIL import Image

from gif_maker.core.constants import (
    FRAME_DURATION_FAST,
    FRAME_DURATION_NORMAL,
    FRAME_DURATION_SLOW,
    FRAME_DURATION_VERY_FAST,
    MAX_SCREENSHOT_COUNT,
    MAX_INTERVAL,
    MIN_INTERVAL,
    MIN_SCREENSHOT_COUNT,
)

QUALITY_BY_LABEL_PREFIX = {
    "MAX": {
        "quality": 100,
        "method": 0,
        "palette": 2,
        "dither": 1,
        "use_advanced_quantization": True,
        "needs_unsharp": True,
    },
    "High": {
        "quality": 80,
        "method": 0,
        "palette": 2,
        "dither": 1,
        "use_advanced_quantization": False,
        "needs_unsharp": False,
    },
    "Medium": {
        "quality": 85,
        "method": 0,
        "palette": 1,
        "dither": 1,
        "use_advanced_quantization": False,
        "needs_unsharp": False,
    },
    "Low": {
        "quality": 75,
        "method": 0,
        "palette": 0,
        "dither": 0,
        "use_advanced_quantization": False,
        "needs_unsharp": False,
    },
}

SPEED_BY_LABEL_PREFIX = {
    "Slow": FRAME_DURATION_SLOW,
    "Normal": FRAME_DURATION_NORMAL,
    "Fast": FRAME_DURATION_FAST,
    "Very Fast": FRAME_DURATION_VERY_FAST,
}


def _label_prefix(label: str, prefixes: List[str]) -> Optional[str]:
    """Return the first matching prefix for the given label."""
    for p in prefixes:
        if label.startswith(p):
            return p
    return None


def parse_speed_frame_duration(speed_label: str) -> int:
    """Convert UI playback speed selection into frame duration ms."""
    prefix = _label_prefix(speed_label, list(SPEED_BY_LABEL_PREFIX.keys()))
    return SPEED_BY_LABEL_PREFIX.get(prefix or "Normal", FRAME_DURATION_NORMAL)


def parse_quality_params(quality_label: str) -> dict:
    """Convert UI quality selection into GIF creation parameters."""
    prefixes = list(QUALITY_BY_LABEL_PREFIX.keys())
    prefix = _label_prefix(quality_label, prefixes)
    return QUALITY_BY_LABEL_PREFIX.get(
        prefix or "Medium", QUALITY_BY_LABEL_PREFIX["Medium"]
    )


def validate_settings_logic(
    count: int,
    interval: float,
    region: Optional[Tuple[int, int, int, int]],
) -> Tuple[bool, Optional[str]]:
    """Pure validation logic for recording settings (no UI).

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is None.
    """
    if count < MIN_SCREENSHOT_COUNT or count > MAX_SCREENSHOT_COUNT:
        return False, (
            f"Screenshot count must be between {MIN_SCREENSHOT_COUNT} and {MAX_SCREENSHOT_COUNT}"
        )
    if interval < MIN_INTERVAL or interval > MAX_INTERVAL:
        return False, f"Interval must be between {MIN_INTERVAL} and {MAX_INTERVAL} seconds"
    if not region:
        return False, "Please select a region first"
    return True, None


def estimate_gif_size_logic(
    images: List[Image.Image],
    quality_label: str,
) -> str:
    """Pure logic for GIF size estimation (no UI).

    Returns:
        Estimated file size as a formatted string.
    """
    if not images:
        return "No screenshots"
    try:
        avg_size = sum(len(img.tobytes()) for img in images) / len(images)
        prefix = _label_prefix(quality_label, list(QUALITY_BY_LABEL_PREFIX.keys()))
        quality_factor = {
            "MAX": 1.0,
            "High": 0.8,
            "Medium": 0.6,
            "Low": 0.4,
        }.get(prefix or "Medium", 0.6)
        estimated = avg_size * len(images) * quality_factor
        return f"~{estimated / 1024 / 1024:.1f} MB"
    except Exception:
        return "Unable to estimate"


def get_quality_prefix(quality_label: str) -> Optional[str]:
    """Return the quality prefix for a label (used by GIF creator)."""
    return _label_prefix(quality_label, list(QUALITY_BY_LABEL_PREFIX.keys()))
