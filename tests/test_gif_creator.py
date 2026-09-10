"""Unit tests for GIF create_gif atomic write and empty-input guard."""

from pathlib import Path
from typing import List, Tuple

import pytest
from PIL import Image

from gif_maker.core.gif_creator import EncodeCancelled, create_gif


def _rgb(
    color: Tuple[int, int, int] = (255, 0, 0), size: Tuple[int, int] = (16, 16)
) -> Image.Image:
    return Image.new("RGB", size, color)


class TestCreateGif:
    def test_empty_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="No screenshots"):
            create_gif(
                [],
                str(tmp_path / "out.gif"),
                "High (80%)",
                "Normal (5 FPS)",
                lambda m: None,
            )

    def test_atomic_write_creates_valid_gif(self, tmp_path: Path) -> None:
        out = tmp_path / "demo.gif"
        frames = [_rgb((255, 0, 0)), _rgb((0, 255, 0))]
        logs: List[str] = []
        create_gif(
            frames,
            str(out),
            "Low (60%)",
            "Normal (5 FPS)",
            logs.append,
        )
        assert out.is_file()
        assert out.stat().st_size > 0
        leftovers = [p for p in tmp_path.iterdir() if p.suffix == ".gif" and p != out]
        assert leftovers == []
        with Image.open(out) as img:
            assert img.format == "GIF"
            assert getattr(img, "n_frames", 1) >= 1

    def test_overwrite_replaces_existing(self, tmp_path: Path) -> None:
        out = tmp_path / "demo.gif"
        out.write_bytes(b"not-a-gif")
        create_gif(
            [_rgb()],
            str(out),
            "Medium (70%)",
            "Fast (8 FPS)",
            lambda m: None,
        )
        assert out.stat().st_size > 10
        with Image.open(out) as img:
            assert img.format == "GIF"

    def test_appends_gif_extension(self, tmp_path: Path) -> None:
        base = tmp_path / "clip"
        create_gif(
            [_rgb()],
            str(base),
            "Low (60%)",
            "Slow (3 FPS)",
            lambda m: None,
        )
        assert (tmp_path / "clip.gif").is_file()

    def test_cancel_mid_encode_raises(self, tmp_path: Path) -> None:
        out = tmp_path / "cancel.gif"
        frames = [_rgb(size=(32, 32)) for _ in range(8)]
        calls = {"n": 0}

        def cancel_after_two() -> bool:
            calls["n"] += 1
            return calls["n"] > 2

        with pytest.raises(EncodeCancelled):
            create_gif(
                frames,
                str(out),
                "MAX (100%)",
                "Normal (5 FPS)",
                lambda _m: None,
                cancel_check=cancel_after_two,
            )
        assert not out.exists()

    def test_cancel_check_none_still_works(self, tmp_path: Path) -> None:
        out = tmp_path / "ok.gif"
        create_gif(
            [_rgb()],
            str(out),
            "Medium (85%)",
            "Normal (5 FPS)",
            lambda _m: None,
            cancel_check=None,
        )
        assert out.is_file()
