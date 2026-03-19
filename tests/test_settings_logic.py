"""Unit tests for GifMaker settings validation, size estimation, and quality/speed mapping."""

import pytest
from PIL import Image

from gif_maker import (
    FRAME_DURATION_FAST,
    FRAME_DURATION_NORMAL,
    FRAME_DURATION_SLOW,
    FRAME_DURATION_VERY_FAST,
    estimate_gif_size_logic,
    parse_quality_params,
    parse_speed_frame_duration,
    validate_settings_logic,
)


class TestParseSpeedFrameDuration:
    """Tests for parse_speed_frame_duration."""

    def test_slow(self) -> None:
        assert parse_speed_frame_duration("Slow (3 FPS)") == FRAME_DURATION_SLOW

    def test_normal(self) -> None:
        assert parse_speed_frame_duration("Normal (5 FPS)") == FRAME_DURATION_NORMAL

    def test_fast(self) -> None:
        assert parse_speed_frame_duration("Fast (8 FPS)") == FRAME_DURATION_FAST

    def test_very_fast(self) -> None:
        assert parse_speed_frame_duration("Very Fast (10 FPS)") == FRAME_DURATION_VERY_FAST

    def test_unknown_defaults_to_normal(self) -> None:
        assert parse_speed_frame_duration("Unknown") == FRAME_DURATION_NORMAL

    def test_empty_defaults_to_normal(self) -> None:
        assert parse_speed_frame_duration("") == FRAME_DURATION_NORMAL


class TestParseQualityParams:
    """Tests for parse_quality_params."""

    def test_max(self) -> None:
        p = parse_quality_params("MAX (100%)")
        assert p["quality"] == 100
        assert p["use_advanced_quantization"] is True

    def test_high(self) -> None:
        p = parse_quality_params("High (80%)")
        assert p["quality"] == 80
        assert p["palette"] == 2
        assert p["dither"] == 1

    def test_medium(self) -> None:
        p = parse_quality_params("Medium (85%)")
        assert p["quality"] == 85
        assert p["palette"] == 1

    def test_low(self) -> None:
        p = parse_quality_params("Low (75%)")
        assert p["quality"] == 75
        assert p["dither"] == 0

    def test_unknown_defaults_to_medium(self) -> None:
        p = parse_quality_params("Unknown")
        assert p["quality"] == 85


class TestValidateSettingsLogic:
    """Tests for validate_settings_logic."""

    def test_valid(self) -> None:
        ok, err = validate_settings_logic(10, 0.5, (0, 0, 800, 600))
        assert ok is True
        assert err is None

    def test_count_too_low(self) -> None:
        ok, err = validate_settings_logic(0, 0.5, (0, 0, 100, 100))
        assert ok is False
        assert "Screenshot count" in (err or "")

    def test_count_too_high(self) -> None:
        ok, err = validate_settings_logic(1001, 0.5, (0, 0, 100, 100))
        assert ok is False
        assert "Screenshot count" in (err or "")

    def test_interval_too_low(self) -> None:
        ok, err = validate_settings_logic(10, 0.05, (0, 0, 100, 100))
        assert ok is False
        assert "Interval" in (err or "")

    def test_interval_too_high(self) -> None:
        ok, err = validate_settings_logic(10, 61.0, (0, 0, 100, 100))
        assert ok is False
        assert "Interval" in (err or "")

    def test_no_region(self) -> None:
        ok, err = validate_settings_logic(10, 0.5, None)
        assert ok is False
        assert "region" in (err or "").lower()


class TestEstimateGifSizeLogic:
    """Tests for estimate_gif_size_logic."""

    def test_no_screenshots(self) -> None:
        assert estimate_gif_size_logic([], "Medium (85%)") == "No screenshots"

    def test_with_images_returns_mb_format(self) -> None:
        img = Image.new("RGB", (100, 100), color="red")
        result = estimate_gif_size_logic([img], "Medium (85%)")
        assert result.startswith("~")
        assert "MB" in result

    def test_quality_affects_estimate(self) -> None:
        img = Image.new("RGB", (200, 200), color="blue")
        images = [img] * 5
        low = estimate_gif_size_logic(images, "Low (75%)")
        high = estimate_gif_size_logic(images, "MAX (100%)")
        assert low != high
        low_val = float(low.replace("~", "").replace(" MB", ""))
        high_val = float(high.replace("~", "").replace(" MB", ""))
        assert high_val > low_val
