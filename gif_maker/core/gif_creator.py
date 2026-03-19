"""GIF encoding and export logic."""

import os
from typing import Callable, List

from PIL import Image, ImageFilter

from gif_maker.core.quality_engine import (
    get_quality_prefix,
    parse_quality_params,
    parse_speed_frame_duration,
)


def create_gif(
    screenshots: List[Image.Image],
    output_path: str,
    quality_label: str,
    speed_label: str,
    log_callback: Callable[[str], None],
) -> None:
    """Create animated GIF from screenshots.

    Args:
        screenshots: List of PIL images to encode.
        output_path: Output file path (will add .gif if missing).
        quality_label: UI quality selection string.
        speed_label: UI speed selection string.
        log_callback: Thread-safe logging function.
    """
    if not output_path.endswith(".gif"):
        output_path += ".gif"

    frame_duration = parse_speed_frame_duration(speed_label)
    quality_params = parse_quality_params(quality_label)
    quality = quality_params["quality"]
    method = quality_params["method"]
    palette = quality_params["palette"]
    dither = quality_params["dither"]
    quality_prefix = get_quality_prefix(quality_label)

    log_callback(f"Creating GIF with {quality_label} quality settings...")
    log_callback(f"Playback speed: {speed_label} ({frame_duration}ms per frame)")

    processed_screenshots = []
    for screenshot in screenshots:
        if screenshot.mode != "RGB":
            screenshot = screenshot.convert("RGB")
        if quality_params.get("quality") == 80:
            screenshot = screenshot.filter(ImageFilter.MedianFilter(size=3))
        processed_screenshots.append(screenshot)

    if quality_prefix == "MAX":
        log_callback("MAX quality processing - this may take a moment...")
        quantized_images = []
        total_frames = len(processed_screenshots)
        for i, img in enumerate(processed_screenshots):
            try:
                sharpened = img.filter(
                    ImageFilter.UnsharpMask(radius=0.8, percent=120, threshold=2)
                )
                quantized = sharpened.quantize(
                    colors=256, method=Image.MEDIANCUT, kmeans=2
                )
                quantized = quantized.convert("RGB")
                quantized_images.append(quantized)
                progress_interval = max(1, total_frames // 10)
                if (i + 1) % progress_interval == 0 or i == total_frames - 1:
                    progress = ((i + 1) / total_frames) * 100
                    log_callback(
                        f"Processing frame {i+1}/{total_frames} ({progress:.1f}%)"
                    )
            except Exception as e:
                log_callback(
                    f"Advanced processing failed for frame {i+1}, using basic: {e}"
                )
                basic_quantized = img.quantize(colors=256, method=Image.MEDIANCUT)
                quantized_images.append(basic_quantized.convert("RGB"))

        quantized_images[0].save(
            output_path,
            save_all=True,
            append_images=quantized_images[1:],
            duration=frame_duration,
            loop=0,
            optimize=False,
            quality=quality,
            dither=1,
        )
    elif quality_prefix == "High":
        quantized_images = []
        for img in processed_screenshots:
            quantized = img.quantize(colors=256, method=Image.MEDIANCUT)
            quantized = quantized.convert("RGB")
            quantized_images.append(quantized)
        quantized_images[0].save(
            output_path,
            save_all=True,
            append_images=quantized_images[1:],
            duration=frame_duration,
            loop=0,
            optimize=False,
            dither=1,
        )
    else:
        processed_screenshots[0].save(
            output_path,
            save_all=True,
            append_images=processed_screenshots[1:],
            duration=frame_duration,
            loop=0,
            optimize=True,
            quality=quality,
            method=method,
            palette=palette,
            dither=dither,
        )

    log_callback(f"GIF created successfully: {output_path}")
    log_callback(f"File size: {os.path.getsize(output_path)} bytes")
