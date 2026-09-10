"""Unit tests for thumbnail helper + create_gif quality paths."""

from pathlib import Path

from PIL import Image

from gif_maker.core.constants import PREVIEW_MAX_SIZE
from gif_maker.core.gif_creator import create_gif
from gif_maker.utils.image_utils import make_thumbnail


def _rgb(color=(0, 128, 255), size=(400, 300)) -> Image.Image:
    return Image.new("RGB", size, color)


class TestMakeThumbnail:
    def test_shrinks_large_image(self) -> None:
        thumb = make_thumbnail(_rgb(size=(800, 600)))
        assert thumb.size[0] <= PREVIEW_MAX_SIZE[0]
        assert thumb.size[1] <= PREVIEW_MAX_SIZE[1]

    def test_small_image_unchanged_or_smaller(self) -> None:
        src = _rgb(size=(50, 40))
        thumb = make_thumbnail(src)
        assert thumb.size[0] <= 50
        assert thumb.size[1] <= 40

    def test_does_not_mutate_source(self) -> None:
        src = _rgb(size=(500, 500))
        before = src.size
        make_thumbnail(src)
        assert src.size == before


class TestCreateGifQualityPaths:
    """Extra edge cases; complements tests/test_gif_creator.py (other agent)."""

    def test_single_frame(self, tmp_path: Path) -> None:
        out = tmp_path / "one.gif"
        create_gif(
            [_rgb(size=(32, 32))],
            str(out),
            "Medium (85%)",
            "Slow (3 FPS)",
            lambda _m: None,
        )
        assert out.is_file()
        with Image.open(out) as img:
            assert img.format == "GIF"
            assert getattr(img, "n_frames", 1) == 1

    def test_high_quality_path(self, tmp_path: Path) -> None:
        out = tmp_path / "high.gif"
        frames = [_rgb((255, 0, 0), (24, 24)), _rgb((0, 255, 0), (24, 24))]
        create_gif(frames, str(out), "High (80%)", "Normal (5 FPS)", lambda _m: None)
        with Image.open(out) as img:
            assert img.format == "GIF"
            assert getattr(img, "n_frames", 1) >= 2

    def test_max_quality_path(self, tmp_path: Path) -> None:
        out = tmp_path / "max.gif"
        create_gif(
            [_rgb(size=(20, 20)), _rgb((10, 10, 10), (20, 20))],
            str(out),
            "MAX (100%)",
            "Very Fast (10 FPS)",
            lambda _m: None,
        )
        assert out.stat().st_size > 0
