"""Unit tests for region geometry helpers."""

from gif_maker.core.constants import MIN_REGION_SIZE
from gif_maker.utils.region_math import (
    center_region,
    is_region_large_enough,
    selection_to_region,
)


class TestSelectionToRegion:
    def test_normal_drag(self) -> None:
        assert selection_to_region(10, 20, 110, 120) == (10, 20, 100, 100)

    def test_reverse_drag(self) -> None:
        assert selection_to_region(110, 120, 10, 20) == (10, 20, 100, 100)

    def test_zero_size(self) -> None:
        assert selection_to_region(50, 50, 50, 50) == (50, 50, 0, 0)


class TestIsRegionLargeEnough:
    def test_ok(self) -> None:
        assert is_region_large_enough((0, 0, MIN_REGION_SIZE, MIN_REGION_SIZE))

    def test_too_small(self) -> None:
        assert not is_region_large_enough((0, 0, MIN_REGION_SIZE - 1, MIN_REGION_SIZE))


class TestCenterRegion:
    def test_centers(self) -> None:
        assert center_region(1920, 1080, 1400, 900) == (260, 90, 1400, 900)

    def test_clamps_to_screen(self) -> None:
        assert center_region(800, 600, 2000, 2000) == (0, 0, 800, 600)
