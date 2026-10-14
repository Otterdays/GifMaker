"""Tests for gif_maker.core.theme module."""

from gif_maker.core.theme import (
    DARK,
    HIGH_CONTRAST,
    LIGHT,
    OLED,
    THEME_LABELS,
    THEME_REGISTRY,
    Theme,
    detect_system_theme,
    resolve_theme_choice,
)


class TestThemeDataclass:
    """Verify Theme dataclass structure."""

    def test_has_required_fields(self):
        required = [
            "name", "bg_primary", "bg_secondary", "bg_input", "surface",
            "border", "header_bg", "text_primary", "text_secondary",
            "text_muted", "text_white", "accent_blue", "accent_red",
            "accent_green", "accent_yellow", "accent_orange", "accent_purple",
        ]
        for field in required:
            assert hasattr(LIGHT, field), f"Missing field: {field}"

    def test_frozen(self):
        """Theme is immutable (frozen dataclass)."""
        try:
            LIGHT.bg_primary = "#000000"
            assert False, "Should not be mutable"
        except AttributeError:
            pass

    def test_color_map_excludes_name(self):
        cm = LIGHT.color_map()
        assert "name" not in cm
        assert cm["bg_primary"] == "#ffffff"

    def test_value_to_attr(self):
        mapping = LIGHT.value_to_attr()
        # All values should map back to attribute names
        assert mapping["#ffffff"] in ("bg_primary", "bg_input", "header_bg", "text_white")


class TestPresets:
    """Validate each theme preset."""

    def test_all_presets_in_registry(self):
        assert "light" in THEME_REGISTRY
        assert "dark" in THEME_REGISTRY
        assert "oled" in THEME_REGISTRY
        assert "high_contrast" in THEME_REGISTRY

    def test_names_match_keys(self):
        for key, theme in THEME_REGISTRY.items():
            assert theme.name == key

    def test_all_colors_are_hex(self):
        for theme in THEME_REGISTRY.values():
            for attr, value in theme.color_map().items():
                assert value.startswith("#"), (
                    f"{theme.name}.{attr} = {value!r} is not hex"
                )
                assert len(value) == 7, (
                    f"{theme.name}.{attr} = {value!r} is not 6-digit hex"
                )


class TestSystemDetection:
    """Test OS theme detection."""

    def test_returns_valid_string(self):
        result = detect_system_theme()
        assert result in ("light", "dark")


class TestResolveThemeChoice:
    """Test preference -> Theme mapping."""

    def test_light(self):
        assert resolve_theme_choice("light") is LIGHT

    def test_dark(self):
        assert resolve_theme_choice("dark") is DARK

    def test_oled(self):
        assert resolve_theme_choice("oled") is OLED

    def test_high_contrast(self):
        assert resolve_theme_choice("high_contrast") is HIGH_CONTRAST

    def test_system_returns_theme(self):
        theme = resolve_theme_choice("system")
        assert isinstance(theme, Theme)
        assert theme.name in ("light", "dark")

    def test_unknown_falls_back_to_light(self):
        assert resolve_theme_choice("nonexistent") is LIGHT


class TestThemeLabels:
    """GUI labels mapping."""

    def test_covers_registry_keys_plus_system(self):
        for key in THEME_REGISTRY:
            assert key in THEME_LABELS
        assert "system" in THEME_LABELS
