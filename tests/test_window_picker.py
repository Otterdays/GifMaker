"""Unit tests for window picker filters (no live OS dependency)."""

from gif_maker.utils.window_picker import (
    WindowInfo,
    filter_windows,
    is_capturable_window,
)


class TestIsCapturableWindow:
    def test_ok(self) -> None:
        assert is_capturable_window("Chrome", 800, 600)

    def test_empty_title(self) -> None:
        assert not is_capturable_window("", 800, 600)

    def test_too_small(self) -> None:
        assert not is_capturable_window("Tiny", 50, 50)

    def test_minimized(self) -> None:
        assert not is_capturable_window("App", 800, 600, is_minimized=True)

    def test_exclude_substring(self) -> None:
        assert not is_capturable_window(
            "Gif-Maker V1.0.7", 800, 600, exclude_substrings=("Gif-Maker",)
        )


class TestFilterWindows:
    def test_filters_and_keeps(self) -> None:
        wins = [
            WindowInfo("Good App", 10, 10, 500, 400),
            WindowInfo("", 0, 0, 500, 400),
            WindowInfo("Tiny", 0, 0, 10, 10),
            WindowInfo("Gif-Maker V1", 0, 0, 500, 400),
        ]
        out = filter_windows(wins, exclude_substrings=("Gif-Maker",))
        assert len(out) == 1
        assert out[0].title == "Good App"
        assert out[0].as_region() == (10, 10, 500, 400)
