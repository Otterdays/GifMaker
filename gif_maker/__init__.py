"""Gif-Maker V1.0 - Professional Animated GIF Creation Tool."""

from gif_maker.gui.main_window import GIFMaker
from gif_maker.main import main

# Re-export for tests and external use
from gif_maker.core.quality_engine import (
    FRAME_DURATION_FAST,
    FRAME_DURATION_NORMAL,
    FRAME_DURATION_SLOW,
    FRAME_DURATION_VERY_FAST,
    estimate_gif_size_logic,
    parse_quality_params,
    parse_speed_frame_duration,
    validate_settings_logic,
)

__all__ = [
    "GIFMaker",
    "main",
    "validate_settings_logic",
    "estimate_gif_size_logic",
    "parse_speed_frame_duration",
    "parse_quality_params",
    "FRAME_DURATION_SLOW",
    "FRAME_DURATION_NORMAL",
    "FRAME_DURATION_FAST",
    "FRAME_DURATION_VERY_FAST",
]
