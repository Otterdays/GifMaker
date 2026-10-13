"""Tests for app logging setup and GUI color helpers."""

import logging

from gif_maker.gui.main_window import GIFMaker
from gif_maker.utils.app_logging import get_logger


def test_get_logger_is_idempotent():
    first = get_logger()
    second = get_logger()
    assert first is second
    # Calling repeatedly must not stack duplicate handlers.
    handler_count = len(first.handlers)
    get_logger()
    assert len(first.handlers) == handler_count


def test_get_logger_returns_logger_instance():
    assert isinstance(get_logger(), logging.Logger)


def test_shade_darkens_hex_color():
    # Darkening a known red should reduce each channel proportionally.
    assert GIFMaker._shade("#e74c3c", -16) == "#c23f32"


def test_shade_lightens_hex_color():
    assert GIFMaker._shade("#000000", 100) == "#000000"  # black stays black
    assert GIFMaker._shade("#ffffff", 10) == "#ffffff"  # clamped at white


def test_shade_passes_through_non_hex():
    # Named colors (e.g. "white") are returned unchanged.
    assert GIFMaker._shade("white", -16) == "white"
