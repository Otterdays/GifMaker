"""Image utilities for preview and thumbnails."""

from PIL import Image

from gif_maker.core.constants import PREVIEW_MAX_SIZE


def make_thumbnail(image: Image.Image) -> Image.Image:
    """Create a thumbnail for preview display."""
    resized = image.copy()
    resized.thumbnail(PREVIEW_MAX_SIZE, Image.Resampling.LANCZOS)
    return resized
