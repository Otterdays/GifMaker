"""Unit tests for settings persistence helpers."""

from pathlib import Path

from gif_maker.utils.settings_store import (
    DEFAULT_SETTINGS,
    load_settings,
    sanitize_settings,
    save_settings,
)


class TestSanitizeSettings:
    def test_defaults_on_empty(self) -> None:
        assert sanitize_settings({})["count"] == DEFAULT_SETTINGS["count"]

    def test_keeps_valid_region(self) -> None:
        out = sanitize_settings({"region": [10, 20, 300, 200]})
        assert out["region"] == [10, 20, 300, 200]

    def test_drops_bad_region(self) -> None:
        assert sanitize_settings({"region": [1, 2]})["region"] is None
        assert sanitize_settings({"region": [0, 0, -1, 10]})["region"] is None

    def test_quality_legacy_max(self) -> None:
        assert sanitize_settings({"quality": "MAX"})["quality"] == "MAX (100%)"

    def test_rejects_unknown_quality(self) -> None:
        assert sanitize_settings({"quality": "Ultra"})["quality"] == DEFAULT_SETTINGS[
            "quality"
        ]


class TestLoadSaveRoundTrip:
    def test_round_trip(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.json"
        data = {
            "region": [5, 5, 400, 300],
            "count": "15",
            "capture_fps": "8 FPS",
            "playback_feel": "Match recording (1×)",
            "output": "clip.gif",
            "quality": "High (80%)",
            "speed": "Fast (8 FPS)",
        }
        save_settings(data, path)
        loaded = load_settings(path)
        assert loaded["region"] == [5, 5, 400, 300]
        assert loaded["count"] == "15"
        assert loaded["quality"] == "High (80%)"
        assert loaded["capture_fps"] == "8 FPS"
        assert loaded["playback_feel"].startswith("Match")
        assert abs(float(loaded["interval"]) - 0.125) < 1e-6

    def test_legacy_interval_maps_capture(self) -> None:
        out = sanitize_settings({"interval": "0.5"})
        assert out["capture_fps"] == "2 FPS"

    def test_missing_file_defaults(self, tmp_path: Path) -> None:
        loaded = load_settings(tmp_path / "nope.json")
        assert loaded["output"] == "demo.gif"

    def test_corrupt_file_defaults(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("{not-json", encoding="utf-8")
        loaded = load_settings(path)
        assert loaded["speed"] == DEFAULT_SETTINGS["speed"]
