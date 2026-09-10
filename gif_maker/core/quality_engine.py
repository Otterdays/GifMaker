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

# Simple capture rate → interval (seconds between screenshots)
CAPTURE_FPS_BY_LABEL = {
    "2 FPS": 2.0,
    "5 FPS": 5.0,
    "8 FPS": 8.0,
    "10 FPS": 10.0,
}

# Playback feel relative to capture timing (1× = realtime)
PLAYBACK_FEEL_MATCH = "Match recording (1×)"
PLAYBACK_FEEL_FASTER = "Faster (~1.5×)"
PLAYBACK_FEEL_SLOWER = "Slower (~0.75×)"
PLAYBACK_FEEL_SLOWMO = "Slow-mo (0.5×)"
PLAYBACK_FEEL_DEMO = "Demo polish (fixed 5 FPS)"

PLAYBACK_FEEL_LABELS = (
    PLAYBACK_FEEL_MATCH,
    PLAYBACK_FEEL_FASTER,
    PLAYBACK_FEEL_SLOWER,
    PLAYBACK_FEEL_SLOWMO,
    PLAYBACK_FEEL_DEMO,
)


def _label_prefix(label: str, prefixes: List[str]) -> Optional[str]:
    """Return the first matching prefix for the given label."""
    for p in prefixes:
        if label.startswith(p):
            return p
    return None


def parse_capture_fps(capture_label: str) -> float:
    """Parse capture FPS combo → FPS float (default 5)."""
    text = (capture_label or "").strip()
    for label, fps in CAPTURE_FPS_BY_LABEL.items():
        if text == label or text.startswith(label):
            return fps
    try:
        return float(text.split()[0])
    except (TypeError, ValueError, IndexError):
        return 5.0


def fps_to_interval(fps: float) -> float:
    """Convert capture FPS to sleep interval seconds."""
    fps = max(0.1, float(fps))
    return 1.0 / fps


def interval_to_nearest_capture_label(interval: float) -> str:
    """Map a raw interval back to nearest capture-FPS combo label."""
    if interval <= 0:
        return "5 FPS"
    target_fps = 1.0 / interval
    best_label = "5 FPS"
    best_diff = float("inf")
    for label, fps in CAPTURE_FPS_BY_LABEL.items():
        diff = abs(fps - target_fps)
        if diff < best_diff:
            best_diff = diff
            best_label = label
    return best_label


def resolve_frame_duration_ms(feel_label: str, interval_sec: float) -> int:
    """GIF frame duration (ms) from playback feel + capture interval.

    Match recording (1×) → duration equals capture spacing (true realtime).
    """
    base_ms = max(20, int(round(float(interval_sec) * 1000)))
    feel = (feel_label or PLAYBACK_FEEL_MATCH).strip()

    if feel.startswith("Match"):
        return base_ms
    if feel.startswith("Faster"):
        return max(20, int(round(base_ms / 1.5)))
    if feel.startswith("Slower"):
        return int(round(base_ms / 0.75))
    if feel.startswith("Slow-mo"):
        return int(round(base_ms / 0.5))
    if feel.startswith("Demo"):
        return FRAME_DURATION_NORMAL
    return base_ms


def describe_timing(capture_label: str, feel_label: str) -> str:
    """Short human summary for UI tip line."""
    fps = parse_capture_fps(capture_label)
    interval = fps_to_interval(fps)
    duration = resolve_frame_duration_ms(feel_label, interval)
    play_fps = 1000.0 / duration
    return (
        f"Capture {fps:.0f} FPS -> GIF ~{play_fps:.1f} FPS "
        f"({duration}ms/frame)"
    )


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
            f"Screenshot count must be between {MIN_SCREENSHOT_COUNT} and "
            f"{MAX_SCREENSHOT_COUNT}"
        )
    if interval < MIN_INTERVAL or interval > MAX_INTERVAL:
        return (
            False,
            f"Interval must be between {MIN_INTERVAL} and {MAX_INTERVAL} seconds",
        )
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
