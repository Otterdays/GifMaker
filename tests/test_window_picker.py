"""Unit tests for window picker filters (no live OS dependency)."""

from gif_maker.utils.window_picker import (
    WindowInfo,
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


class TestWindowInfo:
    def test_as_region(self) -> None:
        win = WindowInfo("Good App", 10, 10, 500, 400)
        assert win.as_region() == (10, 10, 500, 400)

    def test_is_frozen(self) -> None:
        win = WindowInfo("Good App", 10, 10, 500, 400)
        try:
            win.title = "changed"  # type: ignore[misc]
        except Exception:
            pass
        else:  # pragma: no cover - frozen dataclass must raise
            raise AssertionError("WindowInfo should be frozen")
