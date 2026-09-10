"""Unit tests for capture FPS / playback-feel timing helpers."""

from gif_maker.core.constants import FRAME_DURATION_NORMAL
from gif_maker.core.quality_engine import (
    PLAYBACK_FEEL_DEMO,
    PLAYBACK_FEEL_FASTER,
    PLAYBACK_FEEL_MATCH,
    PLAYBACK_FEEL_SLOWMO,
    describe_timing,
    fps_to_interval,
    interval_to_nearest_capture_label,
    parse_capture_fps,
    resolve_frame_duration_ms,
)


class TestCaptureFps:
    def test_parse_labels(self) -> None:
        assert parse_capture_fps("5 FPS") == 5.0
        assert parse_capture_fps("10 FPS") == 10.0

    def test_fps_to_interval(self) -> None:
        assert abs(fps_to_interval(5) - 0.2) < 1e-9
        assert abs(fps_to_interval(2) - 0.5) < 1e-9

    def test_nearest_from_legacy_interval(self) -> None:
        assert interval_to_nearest_capture_label(0.5) == "2 FPS"
        assert interval_to_nearest_capture_label(0.2) == "5 FPS"


class TestPlaybackFeel:
    def test_match_realtime(self) -> None:
        # 5 FPS capture → 200ms frames at 1×
        assert resolve_frame_duration_ms(PLAYBACK_FEEL_MATCH, 0.2) == 200

    def test_faster_shortens_frame(self) -> None:
        assert resolve_frame_duration_ms(PLAYBACK_FEEL_FASTER, 0.2) == 133

    def test_slowmo_lengthens_frame(self) -> None:
        assert resolve_frame_duration_ms(PLAYBACK_FEEL_SLOWMO, 0.2) == 400

    def test_demo_fixed(self) -> None:
        assert resolve_frame_duration_ms(PLAYBACK_FEEL_DEMO, 0.5) == FRAME_DURATION_NORMAL

    def test_describe(self) -> None:
        text = describe_timing("5 FPS", PLAYBACK_FEEL_MATCH)
        assert "Capture 5 FPS" in text
        assert "200ms" in text
