"""GUI shell tests: tabbed layout, hover cards, scroll pages, location sync.

These construct the real window (no mainloop) so layout regressions —
clipped panels, missing tabs, dead hover cards — fail loudly in CI.
Skipped automatically when no display is available.
"""

import os
import time
from types import SimpleNamespace

import pytest
import tkinter as tk

from gif_maker.gui.main_window import GIFMaker


@pytest.fixture(scope="module")
def app():
    """Build one GIFMaker window for the whole module, then destroy it."""
    try:
        root = tk.Tk()
    except tk.TclError as exc:  # headless CI
        pytest.skip(f"no display available: {exc}")
    instance = GIFMaker(root)
    root.update()
    yield instance
    try:
        root.destroy()
    except tk.TclError:
        pass


class TestShell:
    def test_four_tabs_present(self, app) -> None:
        texts = [app.notebook.tab(t, "text").strip() for t in app.notebook.tabs()]
        assert texts == ["Capture", "Settings", "Preview", "Activity"]

    def test_menu_bar_attached(self, app) -> None:
        assert app.root.cget("menu")

    def test_status_strip_widgets(self, app) -> None:
        assert app.count_display.winfo_exists()
        assert app.progress.winfo_exists()


class TestScrollPages:
    @pytest.mark.parametrize("tab_index", [0, 1, 2])
    def test_page_has_scroll_canvas(self, app, tab_index) -> None:
        page = app.notebook.nametowidget(app.notebook.tabs()[tab_index])
        # page -> scroll container -> canvas
        containers = page.winfo_children()
        assert containers, f"tab {tab_index} has no scroll container"
        assert any(
            isinstance(grand, tk.Canvas) for grand in containers[0].winfo_children()
        ), f"tab {tab_index} missing scroll canvas"

    def test_wheel_over_child_widget_scrolls(self, app) -> None:
        """Wheel inside the card interior (over a deep child) must route+scroll.

        Regression guard: Enter/Leave-based wheel arming disarmed scrolling
        whenever the pointer sat on a child widget (labels/entries/combos).
        Deterministic by stubbing yview_scroll (no window-manager/overflow
        dependence): asserts routing and the proportional delta math.
        """
        app.notebook.select(app.notebook.tabs()[1])  # Settings must be mapped
        app.root.update_idletasks()
        app.root.update()
        try:
            page = app.notebook.nametowidget(app.notebook.tabs()[1])
            container = page.winfo_children()[0]
            canvas = next(
                c for c in container.winfo_children() if isinstance(c, tk.Canvas)
            )
            # A deep child inside the card: label -> row frame -> inner -> card.
            widget = app.output_dir_label
            cx = widget.winfo_rootx() + widget.winfo_width() // 2
            cy = widget.winfo_rooty() + widget.winfo_height() // 2

            calls = []
            real_scroll = canvas.yview_scroll
            canvas.yview_scroll = lambda n, u: calls.append(n)
            try:
                # Mouse notch (120) == 24px; two trackpad halves accumulate.
                assert (
                    app._on_mousewheel(
                        SimpleNamespace(delta=-120, x_root=cx, y_root=cy)
                    )
                    == "break"
                )
                assert (
                    app._on_mousewheel(SimpleNamespace(delta=-60, x_root=cx, y_root=cy))
                    == "break"
                )
                assert (
                    app._on_mousewheel(SimpleNamespace(delta=-60, x_root=cx, y_root=cy))
                    == "break"
                )
                # Opposite direction yields negative steps.
                assert (
                    app._on_mousewheel(SimpleNamespace(delta=120, x_root=cx, y_root=cy))
                    == "break"
                )
            finally:
                canvas.yview_scroll = real_scroll
            assert calls == [24, 12, 12, -24], calls

            # Pointer outside any scroll page must not scroll (no 'break').
            strip = app.count_display
            assert (
                app._on_mousewheel(
                    SimpleNamespace(
                        delta=-120,
                        x_root=strip.winfo_rootx() + 5,
                        y_root=strip.winfo_rooty() + 5,
                    )
                )
                is None
            )
        finally:
            app.notebook.select(app.notebook.tabs()[0])
            app.root.update()


class TestTabTooltips:
    def test_content_covers_every_tab(self, app) -> None:
        assert len(app._tab_tooltips) == len(app.notebook.tabs())
        for title, tech, consumer in app._tab_tooltips.values():
            assert title and tech and consumer

    def test_titles_match_tab_labels(self, app) -> None:
        labels = [app.notebook.tab(t, "text").strip() for t in app.notebook.tabs()]
        assert [app._tab_tooltips[i][0] for i in range(len(labels))] == labels

    def test_show_then_hide_lifecycle(self, app) -> None:
        app._show_tab_tooltip(0, 120, 120)
        assert app._tab_tooltip is not None
        assert app._tab_tooltip.winfo_exists()
        app._hide_tab_tooltip()
        assert app._tab_tooltip is None

    def test_hide_is_idempotent(self, app) -> None:
        app._hide_tab_tooltip()
        app._hide_tab_tooltip()
        assert app._tab_tooltip is None

    def test_index_at_outside_strip_is_none(self, app) -> None:
        assert app._tab_index_at(-100, -100) is None

    def test_hover_chain_shows_then_hides(self, app) -> None:
        """Real-coordinate Motion over the strip shows the card; body hides it.

        Regression guard for the bbox()-returns-zeros Tk bug: the hover chain
        must resolve tabs via notebook.index('@x,y'), not bbox.
        """
        nb = app.notebook
        # Ensure the tab strip is laid out so index("@x,y") resolves.
        app.root.update_idletasks()
        app.root.update()
        rx, ry = nb.winfo_rootx(), nb.winfo_rooty()
        try:
            app.root.event_generate(
                "<Motion>", rootx=rx + 200, rooty=ry + 8, x=200, y=8
            )
            for _ in range(20):  # let the 250ms dwell fire
                app.root.update()
                time.sleep(0.05)
            assert app._tab_tooltip is not None, "hover card did not appear"
            assert app._tab_tooltip_index == 1

            app.root.event_generate(
                "<Motion>", rootx=rx + 200, rooty=ry + 200, x=200, y=200
            )
            app.root.update()
            assert app._tab_tooltip is None, "hover card did not dismiss"
        finally:
            app._hide_tab_tooltip()


class TestOutputLocation:
    def test_folder_label_tracks_path(self, app) -> None:
        app.output_var.set(os.path.join("somedir", "out.gif"))
        app.root.update()
        assert app.output_dir_label.cget("text") == os.path.abspath("somedir")

    def test_folder_label_handles_empty(self, app) -> None:
        app.output_var.set("")
        app.root.update()
        assert app.output_dir_label.cget("text") == "(no output set)"
        app.output_var.set("demo.gif")  # restore default for other tests
        app.root.update()


class TestShortcutGuard:
    def test_not_focused_initially(self, app) -> None:
        # Focus sits on the root window, not a text widget.
        assert app._is_text_entry_focused() is False
