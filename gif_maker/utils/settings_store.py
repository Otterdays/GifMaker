"""Persist last region + recording settings between sessions.

[TRACE: DOCS/SCRATCHPAD.md] P2#11 — isolated from GUI so other agents can keep editing main_window.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from gif_maker.core.quality_engine import (
    PLAYBACK_FEEL_LABELS,
    PLAYBACK_FEEL_MATCH,
    fps_to_interval,
    interval_to_nearest_capture_label,
    parse_capture_fps,
)

# Defaults match GUI StringVar initial values (simple timing controls).
DEFAULT_SETTINGS: Dict[str, Any] = {
    "region": None,
    "count": "10",
    "interval": "0.2",
    "output": "demo.gif",
    "quality": "High (80%)",
    "speed": "Normal (5 FPS)",
    "capture_fps": "5 FPS",
    "playback_feel": PLAYBACK_FEEL_MATCH,
}

ALLOWED_QUALITY = {
    "MAX (100%)",
    "High (80%)",
    "Medium (85%)",
    "Low (75%)",
}
ALLOWED_SPEED = {
    "Slow (3 FPS)",
    "Normal (5 FPS)",
    "Fast (8 FPS)",
    "Very Fast (10 FPS)",
}
ALLOWED_CAPTURE = set(f"{n} FPS" for n in (2, 5, 8, 10))


def default_settings_path() -> Path:
    """User-local settings file (no new deps)."""
    return Path.home() / ".gifmaker" / "settings.json"


def _normalize_region(value: Any) -> Optional[Tuple[int, int, int, int]]:
    if value is None:
        return None
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return None
    try:
        x, y, w, h = (int(v) for v in value)
    except (TypeError, ValueError):
        return None
    if w <= 0 or h <= 0:
        return None
    return (x, y, w, h)


def sanitize_settings(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Merge raw dict with defaults; drop invalid fields."""
    out = dict(DEFAULT_SETTINGS)
    if not isinstance(raw, dict):
        return out

    region = _normalize_region(raw.get("region"))
    out["region"] = list(region) if region else None

    for key in ("count", "output"):
        val = raw.get(key)
        if val is not None and str(val).strip():
            out[key] = str(val).strip()

    quality = raw.get("quality")
    if quality in ALLOWED_QUALITY:
        out["quality"] = quality
    elif isinstance(quality, str) and quality.startswith("MAX"):
        out["quality"] = "MAX (100%)"

    speed = raw.get("speed")
    if speed in ALLOWED_SPEED:
        out["speed"] = speed

    capture = raw.get("capture_fps")
    if capture in ALLOWED_CAPTURE:
        out["capture_fps"] = capture
    elif raw.get("interval") is not None:
        try:
            out["capture_fps"] = interval_to_nearest_capture_label(
                float(raw.get("interval"))
            )
        except (TypeError, ValueError):
            pass

    feel = raw.get("playback_feel")
    if feel in PLAYBACK_FEEL_LABELS:
        out["playback_feel"] = feel

    # Keep interval derived from capture FPS (source of truth)
    fps = parse_capture_fps(out["capture_fps"])
    out["interval"] = f"{fps_to_interval(fps):.4g}"

    return out


def load_settings(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load settings JSON; missing/corrupt file → defaults."""
    target = path or default_settings_path()
    try:
        with open(target, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError, TypeError):
        return dict(DEFAULT_SETTINGS)
    return sanitize_settings(data)


def save_settings(data: Dict[str, Any], path: Optional[Path] = None) -> None:
    """Write sanitized settings atomically (temp + replace)."""
    target = path or default_settings_path()
    clean = sanitize_settings(data)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = None, None
    try:
        import tempfile

        fd, temp_name = tempfile.mkstemp(
            suffix=".json", dir=str(target.parent), text=True
        )
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fd = None
            json.dump(clean, fh, indent=2)
            fh.write("\n")
        os.replace(temp_name, target)
        temp_name = None
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        if temp_name is not None:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
