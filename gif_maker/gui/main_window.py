"""
Main window GUI for Gif-Maker.
"""

import os
import platform
import subprocess
import threading
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional, Tuple

import pyautogui
import time
from PIL import ImageTk

from gif_maker.core.constants import (
    COLOR_ACCENT_BLUE,
    COLOR_ACCENT_GREEN,
    COLOR_ACCENT_ORANGE,
    COLOR_ACCENT_PURPLE,
    COLOR_ACCENT_RED,
    COLOR_ACCENT_YELLOW,
    COLOR_BG_INPUT,
    COLOR_BG_PRIMARY,
    COLOR_BG_SECONDARY,
    COLOR_BORDER,
    COLOR_BROWSE,
    COLOR_HEADER_BG,
    COLOR_SURFACE,
    COLOR_TEXT_LIGHT,
    COLOR_TEXT_LIGHTBLUE,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_WHITE,
    FONT_BUTTON,
    FONT_BUTTON_LARGE,
    FONT_HINT,
    FONT_INPUT,
    FONT_LABEL,
    FONT_MONO,
    FONT_SECTION,
    FONT_TITLE,
    FONT_VERSION,
    MAX_CAPTURE_FAILURES,
    MIN_HEIGHT,
    MIN_WIDTH,
    SELECTION_CLOSE_DELAY,
    WINDOW_HEIGHT,
    WINDOW_HIDE_DELAY_MS,
    WINDOW_WIDTH,
)
from gif_maker.core.gif_creator import EncodeCancelled, create_gif
from gif_maker.core.quality_engine import (
    PLAYBACK_FEEL_LABELS,
    PLAYBACK_FEEL_MATCH,
    describe_timing,
    estimate_gif_size_logic,
    fps_to_interval,
    interval_to_nearest_capture_label,
    parse_capture_fps,
    resolve_frame_duration_ms,
    validate_settings_logic,
)
from gif_maker.utils.image_utils import make_thumbnail
from gif_maker.utils.app_logging import get_logger
from gif_maker.utils.region_math import (
    is_region_large_enough,
    selection_to_region,
)
from gif_maker.utils.settings_store import load_settings, save_settings
from gif_maker.utils.window_picker import WindowInfo, list_capturable_windows
from gif_maker.version import __version__


class GIFMaker:
    def __init__(self, root: tk.Tk) -> None:
        """Initialize the GIFMaker application.

        Args:
            root: The main tkinter root window.
        """
        self.root = root
        self.root.title(f"Gif-Maker V{__version__}")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.root.configure(bg=COLOR_BG_PRIMARY)

        # Thread safety — lock guards screenshots + busy flags
        self._lock = threading.Lock()
        self._recording_active = False
        self._encoding_active = False
        self._encode_cancel = threading.Event()
        self.recording_thread: Optional[threading.Thread] = None
        self.gif_thread: Optional[threading.Thread] = None
        self._window_picker: Optional[tk.Toplevel] = None
        self._picked_windows: List[WindowInfo] = []

        # Center the window on screen
        self.center_window()

        # Variables
        self.screenshots: List = []
        self.is_recording = False
        self.region: Optional[Tuple[int, int, int, int]] = None
        self.screenshot_count = 10
        self.interval = 0.5
        self.output_path = "demo.gif"
        self.current_preview_index = 0
        self.preview_images: List = []  # Store resized images for preview

        # Create GUI
        self.create_widgets()

        # Menu bar (File / Edit / Help)
        self._build_menu()

        # Setup keyboard shortcuts
        self.setup_keyboard_shortcuts()

        # P2#11 — restore last region/settings (after widgets exist)
        self._load_persisted_settings()

        # Safe shutdown: stop record / wait encode before destroy
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _ui(self, fn, *args, **kwargs) -> None:
        """Schedule `fn` to run on the Tk main thread."""
        self.root.after(0, lambda: fn(*args, **kwargs))

    def _safe_stop_recording_from_worker(self) -> None:
        """Stop recording from a worker thread (thread-safe wrapper)."""
        self._ui(self.stop_recording)

    def _is_busy(self) -> bool:
        """True while recording or GIF encode holds the frame list."""
        with self._lock:
            return self._recording_active or self._encoding_active

    def _snapshot_screenshots(self) -> List:
        """Copy screenshot list under lock for encode (no mutate race)."""
        with self._lock:
            return list(self.screenshots)

    def _set_mutate_controls(self, enabled: bool) -> None:
        """Enable/disable Clear + Delete while frames must stay stable."""
        state = "normal" if enabled else "disabled"
        self.clear_button.config(state=state)
        # Delete only when enabled and frames exist
        if enabled and self.screenshots:
            self.delete_button.config(state="normal")
        else:
            self.delete_button.config(state="disabled")

    def on_close(self) -> None:
        """Handle window close: stop recording, wait for encode, then destroy."""
        if self.is_recording or self._recording_active:
            if not messagebox.askyesno(
                "Recording in progress",
                "Stop recording and exit?",
            ):
                return
            self.is_recording = False
            thread = self.recording_thread
            if thread is not None and thread.is_alive():
                thread.join(timeout=3.0)

        with self._lock:
            encoding = self._encoding_active
        if encoding:
            if not messagebox.askokcancel(
                "GIF encode in progress",
                "Cancel encode and exit?\n"
                "OK cancels encode (partial file discarded), then closes.\n"
                "Cancel keeps the window open.",
            ):
                return
            self.request_encode_cancel()
            thread = self.gif_thread
            if thread is not None and thread.is_alive():
                self.root.config(cursor="watch")
                self.root.update_idletasks()
                thread.join(timeout=30.0)
                self.root.config(cursor="")
                if thread.is_alive():
                    messagebox.showwarning(
                        "Still encoding",
                        "Encode still stopping. Wait, then close again.",
                    )
                    return

        self._save_persisted_settings()
        self.root.destroy()

    def _load_persisted_settings(self) -> None:
        """Apply saved region + form fields from ~/.gifmaker/settings.json."""
        data = load_settings()
        region = data.get("region")
        if isinstance(region, list) and len(region) == 4:
            try:
                self.region = tuple(int(v) for v in region)  # type: ignore[assignment]
                x, y, w, h = self.region
                self.region_label.config(text=f"Region: {x},{y} {w}x{h}")
            except (TypeError, ValueError):
                self.region = None
        self.count_var.set(str(data.get("count", "10")))
        # Prefer new simple controls; fall back from legacy interval/speed
        capture = data.get("capture_fps")
        if capture:
            self.capture_fps_var.set(str(capture))
        else:
            try:
                interval = float(data.get("interval", "0.2"))
            except (TypeError, ValueError):
                interval = 0.2
            self.capture_fps_var.set(interval_to_nearest_capture_label(interval))

        feel = data.get("playback_feel")
        if feel in PLAYBACK_FEEL_LABELS:
            self.playback_feel_var.set(str(feel))
        else:
            self.playback_feel_var.set(PLAYBACK_FEEL_MATCH)

        self.output_var.set(str(data.get("output", "demo.gif")))
        self.quality_var.set(str(data.get("quality", "High (80%)")))
        self._sync_timing_from_simple()

    def _save_persisted_settings(self) -> None:
        """Persist current region + form fields (best-effort on exit)."""
        try:
            self._sync_timing_from_simple()
            region_list = list(self.region) if self.region else None
            save_settings(
                {
                    "region": region_list,
                    "count": self.count_var.get(),
                    "interval": self.interval_var.get(),
                    "output": self.output_var.get(),
                    "quality": self.quality_var.get(),
                    "speed": self.speed_var.get(),
                    "capture_fps": self.capture_fps_var.get(),
                    "playback_feel": self.playback_feel_var.get(),
                }
            )
        except OSError:
            pass

    def _sync_timing_from_simple(self) -> None:
        """Keep interval/speed mirrors + tip in sync with Capture rate / feel."""
        fps = parse_capture_fps(self.capture_fps_var.get())
        interval = fps_to_interval(fps)
        self.interval_var.set(f"{interval:.4g}")
        duration = resolve_frame_duration_ms(self.playback_feel_var.get(), interval)
        # Mirror nearest legacy speed label for older settings consumers
        if duration >= 300:
            self.speed_var.set("Slow (3 FPS)")
        elif duration >= 160:
            self.speed_var.set("Normal (5 FPS)")
        elif duration >= 110:
            self.speed_var.set("Fast (8 FPS)")
        else:
            self.speed_var.set("Very Fast (10 FPS)")
        if hasattr(self, "timing_hint"):
            self.timing_hint.config(
                text=describe_timing(
                    self.capture_fps_var.get(), self.playback_feel_var.get()
                )
            )

    def center_window(self) -> None:
        """Center the window using its configured size.

        Runs before widgets exist, so ``winfo_width`` can report 1 for an
        unmapped window; fall back to the geometry constants to avoid the
        window collapsing to a tiny size on launch.
        """
        self.root.update_idletasks()
        width = max(self.root.winfo_width(), WINDOW_WIDTH)
        height = max(self.root.winfo_height(), WINDOW_HEIGHT)
        x = max(0, (self.root.winfo_screenwidth() - width) // 2)
        y = max(0, (self.root.winfo_screenheight() - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    # --- Visual styling helpers (flat modern theme, no extra deps) ---------

    @staticmethod
    def _shade(hex_color: str, percent: int) -> str:
        """Return a lightened (percent>0) or darkened (percent<0) hex color.

        Falls back to the input unchanged for non-6-digit values (e.g. "white").
        """
        raw = hex_color.lstrip("#")
        if len(raw) != 6:
            return hex_color
        try:
            channels = [int(raw[i : i + 2], 16) for i in (0, 2, 4)]
        except ValueError:
            return hex_color
        out = []
        for value in channels:
            adjusted = int(value + (value * percent / 100))
            out.append(max(0, min(255, adjusted)))
        return "#{:02x}{:02x}{:02x}".format(*out)

    def _on_button_enter(self, event: "tk.Event") -> None:
        """Darken a flat button while hovered (ignored when disabled)."""
        widget = event.widget
        if str(widget.cget("state")) == "disabled":
            return
        widget._hover_base = widget.cget("bg")
        widget.config(bg=self._shade(widget.cget("bg"), -16))

    def _on_button_leave(self, event: "tk.Event") -> None:
        """Restore a flat button's background on hover-out."""
        widget = event.widget
        widget.config(bg=getattr(widget, "_hover_base", widget._base_bg))

    def _make_button(
        self,
        parent: tk.Widget,
        text: str,
        command,
        bg: str,
        *,
        font: tuple = FONT_BUTTON,
        width: Optional[int] = None,
        state: str = "normal",
    ) -> tk.Button:
        """Create a flat, hoverable accent button consistent with the theme."""
        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=COLOR_TEXT_WHITE,
            activebackground=self._shade(bg, -16),
            activeforeground=COLOR_TEXT_WHITE,
            disabledforeground=COLOR_TEXT_MUTED,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=font,
            padx=16,
            pady=8,
            cursor="hand2",
            width=width,
            state=state,
        )
        button._base_bg = bg
        button.bind("<Enter>", self._on_button_enter)
        button.bind("<Leave>", self._on_button_leave)
        return button

    def _make_entry(
        self, parent: tk.Widget, textvariable: tk.StringVar, width: int
    ) -> tk.Entry:
        """Create an outlined Material text field with a focus highlight."""
        return tk.Entry(
            parent,
            textvariable=textvariable,
            width=width,
            bg=COLOR_BG_INPUT,
            fg=COLOR_TEXT_PRIMARY,
            insertbackground=COLOR_TEXT_PRIMARY,
            relief="flat",
            font=FONT_INPUT,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            highlightcolor=COLOR_ACCENT_BLUE,
        )

    def _make_label(
        self,
        parent: tk.Widget,
        text: str,
        *,
        font: tuple = FONT_LABEL,
        fg: str = COLOR_TEXT_PRIMARY,
        bg: str = COLOR_BG_PRIMARY,
        anchor: str = "w",
        wraplength: Optional[int] = None,
    ) -> tk.Label:
        """Create a themed label bound to the current surface color."""
        return tk.Label(
            parent,
            text=text,
            font=font,
            fg=fg,
            bg=bg,
            anchor=anchor,
            wraplength=wraplength or 0,
            justify="left",
        )

    def _make_section(
        self, parent: tk.Widget, text: str
    ) -> Tuple[tk.LabelFrame, tk.Frame]:
        """Create a Material card (white surface, hairline border) + inner pad."""
        frame = tk.LabelFrame(
            parent,
            text=text,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_BG_PRIMARY,
            font=FONT_SECTION,
            relief="groove",
            bd=1,
            highlightthickness=0,
        )
        inner = tk.Frame(frame, bg=COLOR_BG_PRIMARY, padx=16, pady=12)
        inner.pack(fill="both", expand=True)
        return frame, inner

    def _configure_ttk_styles(self) -> None:
        """Apply the Google Material light theme to ttk widgets + tabs."""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=COLOR_BG_PRIMARY)
        style.configure(
            "TLabel", background=COLOR_BG_PRIMARY, foreground=COLOR_TEXT_PRIMARY
        )
        # Material tabs: light strip, white selected tab, blue selected label
        style.configure("TNotebook", background=COLOR_BG_SECONDARY, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=COLOR_BG_SECONDARY,
            foreground=COLOR_TEXT_SECONDARY,
            padding=[20, 10],
            font=FONT_BUTTON,
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", COLOR_BG_PRIMARY)],
            foreground=[("selected", COLOR_ACCENT_BLUE)],
        )
        style.configure(
            "TCombobox",
            fieldbackground=COLOR_BG_INPUT,
            background=COLOR_BG_INPUT,
            foreground=COLOR_TEXT_PRIMARY,
            arrowcolor=COLOR_TEXT_SECONDARY,
            bordercolor=COLOR_BORDER,
            lightcolor=COLOR_BORDER,
            darkcolor=COLOR_BORDER,
            arrowsize=16,
            padding=6,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", COLOR_BG_INPUT)],
            foreground=[("readonly", COLOR_TEXT_PRIMARY)],
            selectbackground=[("readonly", COLOR_BG_INPUT)],
            selectforeground=[("readonly", COLOR_TEXT_PRIMARY)],
            arrowcolor=[("disabled", COLOR_TEXT_MUTED)],
        )
        style.configure(
            "Vertical.TScrollbar",
            background=COLOR_BORDER,
            troughcolor=COLOR_BG_PRIMARY,
            bordercolor=COLOR_BG_PRIMARY,
            arrowcolor=COLOR_TEXT_SECONDARY,
        )
        style.configure(
            "Horizontal.TProgressbar",
            troughcolor=COLOR_SURFACE,
            background=COLOR_ACCENT_BLUE,
            bordercolor=COLOR_SURFACE,
            lightcolor=COLOR_ACCENT_BLUE,
            darkcolor=COLOR_ACCENT_BLUE,
            thickness=8,
        )

    def create_widgets(self) -> None:
        """Create and configure all GUI widgets."""
        self._configure_ttk_styles()

        # App bar: product name + version chip over a hairline divider
        app_bar = tk.Frame(self.root, bg=COLOR_HEADER_BG)
        app_bar.pack(fill="x")
        tk.Label(
            app_bar,
            text="🎬 Gif-Maker",
            font=FONT_TITLE,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_HEADER_BG,
        ).pack(side="left", padx=(24, 8), pady=12)
        tk.Label(
            app_bar,
            text=f"V{__version__}",
            font=FONT_VERSION,
            fg=COLOR_ACCENT_BLUE,
            bg=COLOR_HEADER_BG,
        ).pack(side="left", pady=12)
        tk.Frame(self.root, bg=COLOR_BORDER, height=1).pack(fill="x")

        # Persistent bottom status strip (visible on every tab)
        status_strip = tk.Frame(self.root, bg=COLOR_BG_SECONDARY)
        status_strip.pack(side="bottom", fill="x")
        tk.Frame(self.root, bg=COLOR_BORDER, height=1).pack(side="bottom", fill="x")

        self.count_display = self._make_label(
            status_strip,
            "Screenshots: 0",
            bg=COLOR_BG_SECONDARY,
            fg=COLOR_TEXT_SECONDARY,
            font=FONT_BUTTON,
        )
        self.count_display.pack(side="left", padx=(20, 12), pady=8)

        self.progress = ttk.Progressbar(status_strip, mode="determinate")
        self.progress.pack(side="left", fill="x", expand=True, padx=(0, 20), pady=8)

        # Tabbed workspace — each view stays short so nothing clips on small screens
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=12)

        tab_capture = tk.Frame(self.notebook, bg=COLOR_BG_PRIMARY)
        tab_settings = tk.Frame(self.notebook, bg=COLOR_BG_PRIMARY)
        tab_preview = tk.Frame(self.notebook, bg=COLOR_BG_PRIMARY)
        tab_activity = tk.Frame(self.notebook, bg=COLOR_BG_PRIMARY)
        self.notebook.add(tab_capture, text="  Capture  ")
        self.notebook.add(tab_settings, text="  Settings  ")
        self.notebook.add(tab_preview, text="  Preview  ")
        self.notebook.add(tab_activity, text="  Activity  ")

        # --- Capture tab: region selection + primary actions ---
        region_frame, region_inner = self._make_section(tab_capture, "Region Selection")
        region_frame.pack(fill="x", padx=4, pady=(4, 12))

        region_buttons = tk.Frame(region_inner, bg=COLOR_BG_PRIMARY)
        region_buttons.pack(anchor="w")
        self._make_button(
            region_buttons, "Manual Coordinates", self.select_region, COLOR_ACCENT_BLUE
        ).pack(side="left", padx=(0, 8))
        self._make_button(
            region_buttons, "Full Screen", self.select_fullscreen, COLOR_ACCENT_PURPLE
        ).pack(side="left", padx=(0, 8))
        self._make_button(
            region_buttons, "Pick Window", self.pick_window, COLOR_ACCENT_ORANGE
        ).pack(side="left")

        self.region_label = self._make_label(
            region_inner, "No region selected", fg=COLOR_TEXT_SECONDARY
        )
        self.region_label.pack(anchor="w", pady=(10, 0))

        control_frame = tk.Frame(tab_capture, bg=COLOR_BG_PRIMARY)
        control_frame.pack(fill="x", padx=4)

        self.record_button = self._make_button(
            control_frame,
            "🎬 Start Recording",
            self.toggle_recording,
            COLOR_ACCENT_RED,
            font=FONT_BUTTON_LARGE,
        )
        self.record_button.pack(side="left", padx=(0, 8))

        self.create_button = self._make_button(
            control_frame,
            "🎞️ Create GIF",
            self.create_gif,
            COLOR_ACCENT_GREEN,
            font=FONT_BUTTON_LARGE,
            state="disabled",
        )
        self.create_button.pack(side="left", padx=(0, 8))

        # Cancel encode (enabled only while GIF worker runs)
        self.cancel_encode_button = self._make_button(
            control_frame,
            "⏹️ Cancel Encode",
            self.request_encode_cancel,
            COLOR_ACCENT_ORANGE,
            font=FONT_BUTTON_LARGE,
            state="disabled",
        )
        self.cancel_encode_button.pack(side="left", padx=(0, 8))

        self.clear_button = self._make_button(
            control_frame,
            "🗑️ Clear",
            self.clear_screenshots,
            COLOR_ACCENT_YELLOW,
            font=FONT_BUTTON_LARGE,
        )
        self.clear_button.pack(side="left")

        # --- Settings tab ---
        settings_frame, settings_inner = self._make_section(
            tab_settings, "Recording Settings"
        )
        settings_frame.pack(fill="x", padx=4, pady=(4, 12))
        settings_inner.columnconfigure(1, weight=1)

        self._make_label(settings_inner, "Number of Screenshots:").grid(
            row=0, column=0, sticky="w", padx=(0, 12), pady=5
        )
        self.count_var = tk.StringVar(value="10")
        self._make_entry(settings_inner, self.count_var, 10).grid(
            row=0, column=1, sticky="w", pady=5
        )

        # Capture rate (replaces raw interval — drives recording FPS)
        self._make_label(settings_inner, "Capture rate:").grid(
            row=1, column=0, sticky="w", padx=(0, 12), pady=5
        )
        self.capture_fps_var = tk.StringVar(value="5 FPS")
        self.interval_var = tk.StringVar(value="0.2")  # kept in sync for validate/persist
        capture_combo = ttk.Combobox(
            settings_inner, textvariable=self.capture_fps_var, width=15, state="readonly"
        )
        capture_combo["values"] = ("2 FPS", "5 FPS", "8 FPS", "10 FPS")
        capture_combo.grid(row=1, column=1, sticky="w", pady=5)
        capture_combo.bind(
            "<<ComboboxSelected>>", lambda _e: self._sync_timing_from_simple()
        )

        # Output path + browse
        self._make_label(settings_inner, "Output File:").grid(
            row=2, column=0, sticky="w", padx=(0, 12), pady=5
        )
        self.output_var = tk.StringVar(value="demo.gif")
        output_row = tk.Frame(settings_inner, bg=COLOR_BG_PRIMARY)
        output_row.grid(row=2, column=1, sticky="w", pady=5)
        self._make_entry(output_row, self.output_var, 22).pack(side="left")
        self._make_button(
            output_row, "Browse", self.browse_output, COLOR_BROWSE, font=FONT_LABEL
        ).pack(side="left", padx=(8, 0))

        # Quality setting
        self._make_label(settings_inner, "Quality:").grid(
            row=3, column=0, sticky="w", padx=(0, 12), pady=5
        )
        self.quality_var = tk.StringVar(value="High (80%)")
        quality_combo = ttk.Combobox(
            settings_inner, textvariable=self.quality_var, width=18, state="readonly"
        )
        quality_combo["values"] = (
            "MAX (100%)",
            "High (80%)",
            "Medium (85%)",
            "Low (75%)",
        )
        quality_combo.grid(row=3, column=1, sticky="w", pady=5)

        self._make_label(
            settings_inner,
            "High = best everyday look | MAX = pro demos | Medium/Low = smaller files",
            font=FONT_HINT,
            fg=COLOR_TEXT_LIGHTBLUE,
            wraplength=520,
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 6))

        # Playback feel (links capture timing → GIF frame duration)
        self._make_label(settings_inner, "Playback feel:").grid(
            row=5, column=0, sticky="w", padx=(0, 12), pady=5
        )
        self.playback_feel_var = tk.StringVar(value=PLAYBACK_FEEL_MATCH)
        self.speed_var = tk.StringVar(value="Normal (5 FPS)")  # legacy persist mirror
        feel_combo = ttk.Combobox(
            settings_inner, textvariable=self.playback_feel_var, width=22, state="readonly"
        )
        feel_combo["values"] = PLAYBACK_FEEL_LABELS
        feel_combo.grid(row=5, column=1, sticky="w", pady=5)
        feel_combo.bind(
            "<<ComboboxSelected>>", lambda _e: self._sync_timing_from_simple()
        )

        self.timing_hint = self._make_label(
            settings_inner,
            describe_timing("5 FPS", PLAYBACK_FEEL_MATCH),
            font=FONT_HINT,
            fg=COLOR_TEXT_LIGHTBLUE,
            wraplength=520,
        )
        self.timing_hint.grid(row=6, column=0, columnspan=2, sticky="w", pady=(0, 2))

        self._sync_timing_from_simple()

        # --- Preview tab ---
        self.setup_preview_panel(tab_preview)

        # --- Activity tab: rolling log ---
        log_frame = tk.Frame(tab_activity, bg=COLOR_BG_PRIMARY, padx=4, pady=4)
        log_frame.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        self.status_text = tk.Text(
            log_frame,
            bg=COLOR_BG_PRIMARY,
            fg=COLOR_TEXT_PRIMARY,
            font=FONT_MONO,
            relief="flat",
            padx=10,
            pady=8,
            wrap="word",
            insertbackground=COLOR_TEXT_PRIMARY,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            yscrollcommand=scrollbar.set,
        )
        self.status_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.status_text.yview)

    def setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts for common actions."""
        self.root.bind("<space>", self._on_space_shortcut)
        self.root.bind("<Escape>", lambda e: self.cancel_if_recording())
        self.root.bind("<Control-s>", self._on_save_shortcut)
        # Ctrl+C kept free for OS copy; clear uses Ctrl+Shift+Delete
        self.root.bind("<Control-Shift-Delete>", lambda e: self.clear_screenshots())

    def _is_text_entry_focused(self) -> bool:
        """True when a text-editing widget holds focus (typing, not shortcut).

        Global shortcuts like Space must not fire while the user is typing in
        an Entry/Combobox/Text, or a stray space would toggle recording.
        """
        focused = self.root.focus_get()
        return isinstance(focused, (tk.Entry, tk.Text, ttk.Combobox))

    def _on_space_shortcut(self, event: Optional[tk.Event] = None) -> None:
        """Space: toggle recording, unless the user is typing in a field."""
        if self._is_text_entry_focused():
            return
        self.toggle_recording()

    def _on_save_shortcut(self, event: Optional[tk.Event] = None) -> None:
        """Ctrl+S: create GIF, unless the user is typing in a field."""
        if self._is_text_entry_focused():
            return
        self.create_gif()

    def show_shortcuts_dialog(self) -> None:
        """Show the keyboard-shortcut reference dialog."""
        messagebox.showinfo(
            "Keyboard Shortcuts",
            "Space — Start / Stop recording\n"
            "Escape — Cancel recording or encode\n"
            "Ctrl+S — Create GIF\n"
            "Ctrl+Shift+Delete — Clear all screenshots",
        )

    def show_about_dialog(self) -> None:
        """Show the About dialog with version and credits."""
        messagebox.showinfo(
            "About Gif-Maker",
            f"Gif-Maker V{__version__}\n\n"
            "Create high-quality animated GIFs from screen captures.\n"
            "Built with Python, tkinter and Pillow.\n\n"
            "Logs: ~/.gifmaker/logs/gifmaker.log",
        )

    def _build_menu(self) -> None:
        """Create the application menu bar (File / Edit / Help)."""
        menubar = tk.Menu(self.root, tearoff=0)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Set Output File…", command=self.browse_output)
        file_menu.add_command(
            label="Open Output Folder",
            command=lambda: self.open_file_location(self.output_var.get()),
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(
            label="Delete Current Frame", command=self.delete_current_image
        )
        edit_menu.add_command(label="Clear All Screenshots", command=self.clear_screenshots)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Keyboard Shortcuts…", command=self.show_shortcuts_dialog)
        help_menu.add_command(label="About Gif-Maker…", command=self.show_about_dialog)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def cancel_if_recording(self, event: Optional[tk.Event] = None) -> None:
        """Escape: stop recording, or cancel in-progress GIF encode."""
        if self.is_recording:
            self.stop_recording()
            return
        with self._lock:
            encoding = self._encoding_active
        if encoding:
            self.request_encode_cancel()

    def request_encode_cancel(self) -> None:
        """Signal GIF worker to stop at next cancel check."""
        with self._lock:
            encoding = self._encoding_active
        if not encoding:
            return
        self._encode_cancel.set()
        self.log("Cancel requested — stopping encode…")
        self.cancel_encode_button.config(state="disabled")

    def setup_preview_panel(self, parent: tk.Frame) -> None:
        """Setup the image preview panel.

        Args:
            parent: The parent frame to attach the preview panel to.
        """
        preview_frame, preview_inner = self._make_section(parent, "Image Preview")
        preview_frame.pack(fill="both", expand=True, padx=4, pady=(4, 4))
        preview_inner.rowconfigure(0, weight=1)
        preview_inner.columnconfigure(0, weight=1)

        # Image display fills the available vertical space
        self.preview_label = tk.Label(
            preview_inner,
            text="No images captured yet",
            bg=COLOR_BG_PRIMARY,
            fg=COLOR_TEXT_SECONDARY,
            font=FONT_LABEL,
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
        )
        self.preview_label.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        # Navigation controls
        nav_frame = tk.Frame(preview_inner, bg=COLOR_BG_PRIMARY)
        nav_frame.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        nav_frame.columnconfigure(1, weight=1)

        self.prev_button = self._make_button(
            nav_frame, "◀", self.prev_image, COLOR_ACCENT_BLUE,
            font=FONT_BUTTON, width=3, state="disabled",
        )
        self.prev_button.grid(row=0, column=0)

        self.image_counter = self._make_label(
            nav_frame, "0/0", font=FONT_BUTTON, anchor="center"
        )
        self.image_counter.grid(row=0, column=1, sticky="ew")

        self.next_button = self._make_button(
            nav_frame, "▶", self.next_image, COLOR_ACCENT_BLUE,
            font=FONT_BUTTON, width=3, state="disabled",
        )
        self.next_button.grid(row=0, column=2)

        # Image info
        self.image_info = self._make_label(
            preview_inner, "", font=FONT_HINT, fg=COLOR_TEXT_LIGHTBLUE, anchor="center"
        )
        self.image_info.grid(row=2, column=0, sticky="ew", pady=(0, 6))

        # Action buttons
        action_frame = tk.Frame(preview_inner, bg=COLOR_BG_PRIMARY)
        action_frame.grid(row=3, column=0, sticky="ew")
        action_frame.columnconfigure(0, weight=1)

        self.delete_button = self._make_button(
            action_frame, "🗑️ Delete", self.delete_current_image, COLOR_ACCENT_RED,
            font=FONT_LABEL, state="disabled",
        )
        self.delete_button.grid(row=0, column=0, sticky="w")

        self.refresh_button = self._make_button(
            action_frame, "🔄 Refresh", self.refresh_preview, COLOR_ACCENT_GREEN,
            font=FONT_LABEL,
        )
        self.refresh_button.grid(row=0, column=1, sticky="e")

    def log(self, message: str) -> None:
        """Add message to the on-screen status log and the rotating file log.

        Args:
            message: The message to log.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        # Mirror to the file log for post-mortem debugging. No root.update():
        # re-entering the event loop mid-handler is a classic Tk footgun.
        get_logger().info(message)

    def log_thread_safe(self, message: str) -> None:
        """Thread-safe logging for background operations.

        Args:
            message: The message to log.
        """

        def update_log():
            self.log(message)

        self.root.after(0, update_log)

    def _refresh_preview_thread_safe(self) -> None:
        """Refresh preview from a worker thread."""
        self._ui(self.refresh_preview)

    def _set_count_display(self, text: str) -> None:
        """Update count label safely."""
        self._ui(self.count_display.config, text=text)

    def _set_progress(self, value: float) -> None:
        """Update progress bar safely."""
        self._ui(self.progress.__setitem__, "value", value)

    def refresh_preview(self) -> None:
        """Refresh preview; append only new thumbs (O(1) per frame, not O(n²))."""
        with self._lock:
            shot_count = len(self.screenshots)
            if shot_count == 0:
                new_frames = None
            elif len(self.preview_images) < shot_count:
                # Refs only — thumbnail work happens outside the lock
                new_frames = self.screenshots[len(self.preview_images) :]
            elif len(self.preview_images) > shot_count:
                new_frames = "rebuild"
                shots_copy = list(self.screenshots)
            else:
                new_frames = []

        if shot_count == 0:
            self.preview_images.clear()
            self.preview_label.config(text="No images captured yet")
            self.image_counter.config(text="0/0")
            self.image_info.config(text="")
            self.prev_button.config(state="disabled")
            self.next_button.config(state="disabled")
            self.delete_button.config(state="disabled")
            return

        if new_frames == "rebuild":
            self.preview_images = [make_thumbnail(s) for s in shots_copy]
        elif new_frames:
            for screenshot in new_frames:
                self.preview_images.append(make_thumbnail(screenshot))
            # Show newest frame while recording appends
            self.current_preview_index = len(self.preview_images) - 1

        self.update_preview_display()

    def update_preview_display(self) -> None:
        """Update the preview display with current image."""
        if not self.screenshots or not self.preview_images:
            return

        # Ensure index is valid
        if self.current_preview_index >= len(self.screenshots):
            self.current_preview_index = len(self.screenshots) - 1
        if self.current_preview_index < 0:
            self.current_preview_index = 0

        # Display current image
        current_image = self.preview_images[self.current_preview_index]

        photo = ImageTk.PhotoImage(current_image)
        self.preview_label.config(image=photo, text="")
        self.preview_label.image = photo  # Keep a reference

        # Update counter
        self.image_counter.config(
            text=f"{self.current_preview_index + 1}/{len(self.screenshots)}"
        )

        # Update image info
        original = self.screenshots[self.current_preview_index]
        info_text = f"Size: {original.width}x{original.height}\nMode: {original.mode}"
        self.image_info.config(text=info_text)

        # Update button states
        self.prev_button.config(
            state="normal" if self.current_preview_index > 0 else "disabled"
        )
        self.next_button.config(
            state="normal"
            if self.current_preview_index < len(self.screenshots) - 1
            else "disabled"
        )
        self.delete_button.config(state="normal")

    def prev_image(self) -> None:
        """Show previous image."""
        if self.current_preview_index > 0:
            self.current_preview_index -= 1
            self.update_preview_display()

    def next_image(self) -> None:
        """Show next image."""
        if self.current_preview_index < len(self.screenshots) - 1:
            self.current_preview_index += 1
            self.update_preview_display()

    def delete_current_image(self) -> None:
        """Delete the currently displayed image (with confirmation)."""
        if self._is_busy():
            self.log("Cannot delete while recording or encoding")
            return
        if not messagebox.askyesno(
            "Delete frame",
            f"Delete frame {self.current_preview_index + 1}? This cannot be undone.",
        ):
            return
        with self._lock:
            if not self.screenshots or self.current_preview_index >= len(
                self.screenshots
            ):
                return
            # Remove the image and free memory
            img = self.screenshots[self.current_preview_index]
            if hasattr(img, "close"):
                img.close()
            del self.screenshots[self.current_preview_index]

        if self.current_preview_index < len(self.preview_images):
            preview_img = self.preview_images[self.current_preview_index]
            if hasattr(preview_img, "close"):
                preview_img.close()
            del self.preview_images[self.current_preview_index]

        # Adjust index if needed
        if self.current_preview_index >= len(self.screenshots):
            self.current_preview_index = len(self.screenshots) - 1
        if self.current_preview_index < 0:
            self.current_preview_index = 0

        # Update display
        self.count_display.config(text=f"Screenshots: {len(self.screenshots)}")
        self.log(f"Deleted image {self.current_preview_index + 1}")

        # Refresh preview
        self.refresh_preview()

    def validate_settings(self) -> Tuple[bool, Optional[str]]:
        """Validate all user settings before recording.

        Returns:
            Tuple of (is_valid, error_message). If valid, error_message is None.
        """
        try:
            count = int(self.count_var.get())
            interval = float(self.interval_var.get())
            return validate_settings_logic(count, interval, self.region)
        except ValueError as e:
            return False, f"Invalid input: {e}"

    def estimate_gif_size(self) -> str:
        """Estimate GIF file size based on current settings.

        Returns:
            Estimated file size as a formatted string.
        """
        return estimate_gif_size_logic(self.screenshots, self.quality_var.get())

    def open_file_location(self, path: str) -> None:
        """Open file location in system file manager (cross-platform).

        Args:
            path: The file path whose directory should be opened.
        """
        folder = os.path.dirname(os.path.abspath(path))
        try:
            if platform.system() == "Windows":
                os.startfile(folder)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", folder])
            else:  # Linux
                subprocess.run(["xdg-open", folder])
        except Exception as e:
            self.log(f"Could not open file location: {e}")

    def select_region(self) -> None:
        """Select region with visual feedback.

        Creates a full-screen overlay with canvas drawing for interactive
        region selection. User can click and drag to select the area
        to capture.
        """
        self.log("Starting visual region selection...")

        # Create a full-screen overlay for region selection
        self.region_overlay = tk.Toplevel()
        self.region_overlay.attributes("-fullscreen", True)
        self.region_overlay.attributes("-alpha", 0.5)  # More opaque for better contrast
        self.region_overlay.configure(bg="#1a1a1a")  # Darker background
        self.region_overlay.attributes("-topmost", True)

        # Create canvas for drawing
        self.region_canvas = tk.Canvas(
            self.region_overlay,
            highlightthickness=0,
            bg="black",
            cursor="crosshair",
        )
        self.region_canvas.pack(fill="both", expand=True)

        # Variables for selection
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.instruction_text = None

        # Bind mouse events
        self.region_canvas.bind("<Button-1>", self.start_selection)
        self.region_canvas.bind("<B1-Motion>", self.update_selection)
        self.region_canvas.bind("<ButtonRelease-1>", self.end_selection)
        # bind_all so Escape works even when canvas lacks keyboard focus
        self.region_overlay.bind_all("<Escape>", self.cancel_selection)

        # Show instructions
        self.show_selection_instructions()

        # Force focus — focus_set alone often fails on fullscreen overlays
        self.region_overlay.focus_force()
        self.region_canvas.focus_force()

    def show_selection_instructions(self) -> None:
        """Show instructions on the overlay."""
        screen_width = self.region_overlay.winfo_screenwidth()
        screen_height = self.region_overlay.winfo_screenheight()

        # Create a nice boxed instruction window
        box_width = 400
        box_height = 200
        box_x = (screen_width - box_width) // 2
        box_y = (screen_height - box_height) // 2 - 100  # Move higher to avoid overlap

        # Draw instruction box with border
        self.region_canvas.create_rectangle(
            box_x - 10,
            box_y - 10,
            box_x + box_width + 10,
            box_y + box_height + 10,
            fill="#34495e",
            outline="#aed6f1",
            width=3,
            tags="instruction_box",
        )

        # Add inner shadow effect
        self.region_canvas.create_rectangle(
            box_x - 8,
            box_y - 8,
            box_x + box_width + 8,
            box_y + box_height + 8,
            fill="",
            outline="#aed6f1",
            width=1,
            tags="instruction_box",
        )

        # Title
        self.region_canvas.create_text(
            screen_width // 2,
            box_y + 30,
            text="🎯 REGION SELECTION",
            fill="#ffffff",
            font=("Arial", 18, "bold"),
            anchor="center",
            tags="instruction_box",
        )

        # Instructions
        instruction_lines = [
            "Click and drag to select your browser window",
            "",
            "• Click at the TOP-LEFT corner of your browser",
            "• Drag to the BOTTOM-RIGHT corner",
            "• Release to confirm selection",
            "",
            "Press ESC to cancel",
        ]

        y_offset = 60
        for i, line in enumerate(instruction_lines):
            color = "#e8f4fd" if line else "#bdc3c7"
            font_size = 14 if i == 0 else 12
            font_weight = "bold" if i == 0 else "normal"

            self.region_canvas.create_text(
                screen_width // 2,
                box_y + y_offset + i * 20,
                text=line,
                fill=color,
                font=("Arial", font_size, font_weight),
                anchor="center",
                tags="instruction_box",
            )

    def start_selection(self, event: tk.Event) -> None:
        """Start region selection.

        Args:
            event: The mouse event containing click coordinates.
        """
        self.start_x = event.x
        self.start_y = event.y

        # Clear previous rectangle
        if self.rect_id:
            self.region_canvas.delete(self.rect_id)

        # Create new rectangle with better visual feedback
        self.rect_id = self.region_canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.start_x,
            self.start_y,
            outline="#e74c3c",
            width=4,
            fill="#e74c3c",
            stipple="gray12",
            tags="selection_rect",
        )

        # Bring selection elements to front
        self.region_canvas.tag_raise("selection_rect")
        self.region_canvas.tag_raise("corner_markers")

        # Add corner markers for better precision
        self.corner_markers = []
        marker_size = 8
        corners = [
            (self.start_x, self.start_y),  # Top-left
            (self.start_x, self.start_y),  # Top-right (will update)
            (self.start_x, self.start_y),  # Bottom-left (will update)
            (self.start_x, self.start_y),  # Bottom-right (will update)
        ]

        for i, (x, y) in enumerate(corners):
            marker = self.region_canvas.create_oval(
                x - marker_size // 2,
                y - marker_size // 2,
                x + marker_size // 2,
                y + marker_size // 2,
                fill="#f39c12",
                outline="#e67e22",
                width=2,
                tags="corner_markers",
            )
            self.corner_markers.append(marker)

        # Update instructions without deleting selection elements
        self.region_canvas.delete("instruction_box")
        self.show_selection_instructions()

        # Show live coordinates in a nice box
        screen_width = self.region_overlay.winfo_screenwidth()
        screen_height = self.region_overlay.winfo_screenheight()

        # Create coordinate display box in top-right corner
        coord_box_width = 200
        coord_box_height = 40
        coord_x = screen_width - coord_box_width - 20  # Top-right corner
        coord_y = 20  # Top of screen

        self.region_canvas.create_rectangle(
            coord_x - 5,
            coord_y - 5,
            coord_x + coord_box_width + 5,
            coord_y + coord_box_height + 5,
            fill="#2c3e50",
            outline="#aed6f1",
            width=2,
            tags="coord_box",
        )

        self.region_canvas.create_text(
            coord_x + coord_box_width // 2,
            coord_y + 15,
            text=f"Start: {self.start_x}, {self.start_y}",
            fill="#ffffff",
            font=("Arial", 12, "bold"),
            anchor="center",
            tags="coord_box",
        )

    def update_selection(self, event: tk.Event) -> None:
        """Update selection rectangle.

        Args:
            event: The mouse event containing current drag coordinates.
        """
        if self.rect_id:
            # Update rectangle
            self.region_canvas.coords(
                self.rect_id,
                self.start_x,
                self.start_y,
                event.x,
                event.y,
            )

            # Update corner markers
            if hasattr(self, "corner_markers") and self.corner_markers:
                # Calculate corners
                x1, y1 = self.start_x, self.start_y
                x2, y2 = event.x, event.y

                # Ensure proper corner order
                left = min(x1, x2)
                right = max(x1, x2)
                top = min(y1, y2)
                bottom = max(y1, y2)

                corners = [
                    (left, top),  # Top-left
                    (right, top),  # Top-right
                    (left, bottom),  # Bottom-left
                    (right, bottom),  # Bottom-right
                ]

                marker_size = 8
                for i, marker in enumerate(self.corner_markers):
                    if i < len(corners):
                        x, y = corners[i]
                        self.region_canvas.coords(
                            marker,
                            x - marker_size // 2,
                            y - marker_size // 2,
                            x + marker_size // 2,
                            y + marker_size // 2,
                        )

                # Bring selection elements to front
                self.region_canvas.tag_raise("selection_rect")
                self.region_canvas.tag_raise("corner_markers")

            # Update coordinates display
            self.region_canvas.delete("coords")
            width = abs(event.x - self.start_x)
            height = abs(event.y - self.start_y)

            screen_width = self.region_overlay.winfo_screenwidth()
            screen_height = self.region_overlay.winfo_screenheight()

            # Create updated coordinate display box in top-right corner
            coord_box_width = 250
            coord_box_height = 50
            coord_x = screen_width - coord_box_width - 20  # Top-right corner
            coord_y = 20  # Top of screen

            self.region_canvas.create_rectangle(
                coord_x - 5,
                coord_y - 5,
                coord_x + coord_box_width + 5,
                coord_y + coord_box_height + 5,
                fill="#2c3e50",
                outline="#aed6f1",
                width=2,
                tags="coords",
            )

            self.region_canvas.create_text(
                coord_x + coord_box_width // 2,
                coord_y + 15,
                text=f"Start: {self.start_x}, {self.start_y}",
                fill="#ffffff",
                font=("Arial", 11, "bold"),
                anchor="center",
                tags="coords",
            )

            self.region_canvas.create_text(
                coord_x + coord_box_width // 2,
                coord_y + 35,
                text=f"Size: {width} x {height}",
                fill="#f7dc6f",
                font=("Arial", 11, "bold"),
                anchor="center",
                tags="coords",
            )

    def end_selection(self, event: tk.Event) -> None:
        """End region selection.

        Args:
            event: The mouse event containing release coordinates.
        """
        if self.start_x is None or self.start_y is None:
            return

        # Calculate final region
        x, y, width, height = selection_to_region(
            self.start_x, self.start_y, event.x, event.y
        )

        # Validate selection
        if not is_region_large_enough((x, y, width, height)):
            screen_width = self.region_overlay.winfo_screenwidth()
            screen_height = self.region_overlay.winfo_screenheight()

            # Create error message box at bottom-center
            error_box_width = 400  # Wider to accommodate text
            error_box_height = 50  # Taller for better text fit
            error_x = (screen_width - error_box_width) // 2
            error_y = screen_height - 100  # Higher up to avoid covering selection

            self.region_canvas.create_rectangle(
                error_x - 5,
                error_y - 5,
                error_x + error_box_width + 5,
                error_y + error_box_height + 5,
                fill="#e74c3c",
                outline="#f9e79f",
                width=3,
                tags="error_box",
            )

            self.region_canvas.create_text(
                error_x + error_box_width // 2,
                error_y + error_box_height // 2,
                text="❌ Selection too small! Try again.",
                fill="white",
                font=("Arial", 14, "bold"),
                anchor="center",
                tags="error_box",
            )
            self.region_overlay.after(SELECTION_CLOSE_DELAY, self.cancel_selection)
            return

        # Confirm selection with nice box
        screen_width = self.region_overlay.winfo_screenwidth()
        screen_height = self.region_overlay.winfo_screenheight()

        # Create success message box at bottom-center
        success_box_width = 450  # Wider to accommodate text
        success_box_height = 50  # Taller for better text fit
        success_x = (screen_width - success_box_width) // 2
        success_y = screen_height - 100  # Higher up to avoid covering selection

        self.region_canvas.create_rectangle(
            success_x - 5,
            success_y - 5,
            success_x + success_box_width + 5,
            success_y + success_box_height + 5,
            fill="#27ae60",
            outline="#a9dfbf",
            width=3,
            tags="success_box",
        )

        self.region_canvas.create_text(
            success_x + success_box_width // 2,
            success_y + success_box_height // 2,
            text="✅ Selection confirmed! Closing in 2 seconds...",
            fill="white",
            font=("Arial", 14, "bold"),
            anchor="center",
            tags="success_box",
        )

        # Set the region
        self.region = (x, y, width, height)
        self.region_label.config(text=f"Region: {x},{y} {width}x{height}")
        self.log(f"Region selected: {self.region}")

        # Clean up visual elements
        if hasattr(self, "corner_markers"):
            for marker in self.corner_markers:
                self.region_canvas.delete(marker)
            self.corner_markers = []

        # Close overlay after delay
        self.region_overlay.after(SELECTION_CLOSE_DELAY, self.close_selection_overlay)

    def cancel_selection(self, event: Optional[tk.Event] = None) -> None:
        """Cancel region selection.

        Args:
            event: Optional tkinter event (for keyboard binding).
        """
        self.log("Region selection cancelled")

        # Clean up visual elements
        if hasattr(self, "corner_markers"):
            for marker in self.corner_markers:
                self.region_canvas.delete(marker)
            self.corner_markers = []

        self.close_selection_overlay()

    def close_selection_overlay(self) -> None:
        """Close the selection overlay and clean up resources."""
        if hasattr(self, "region_overlay"):
            try:
                # Unbind events to prevent memory leaks
                if hasattr(self, "region_canvas"):
                    try:
                        self.region_canvas.unbind("<Button-1>")
                        self.region_canvas.unbind("<B1-Motion>")
                        self.region_canvas.unbind("<ButtonRelease-1>")
                    except Exception:
                        pass
                try:
                    self.region_overlay.unbind_all("<Escape>")
                except Exception:
                    pass
                self.region_overlay.destroy()
            except Exception as e:
                self.log(f"Error closing overlay: {e}")
            finally:
                # Clean up references
                if hasattr(self, "region_overlay"):
                    del self.region_overlay
                if hasattr(self, "region_canvas"):
                    del self.region_canvas
                # Restore main-window Escape (unbind_all removes it)
                self.root.bind("<Escape>", lambda e: self.cancel_if_recording())

    def select_fullscreen(self) -> None:
        """Select full screen region.

        Automatically sets the capture region to cover the entire screen.
        """
        try:
            screen_width, screen_height = pyautogui.size()
            self.region = (0, 0, screen_width, screen_height)
            self.region_label.config(
                text=f"Region: Full Screen ({screen_width}x{screen_height})"
            )
            self.log(f"Full screen selected: {screen_width}x{screen_height}")
        except Exception as e:
            error_msg = (
                f"Error selecting full screen: {e}\n"
                f"Tip: Ensure your display is properly configured."
            )
            self.log(error_msg)

    def pick_window(self) -> None:
        """Pick a real OS window and set capture region to its bounds."""
        if self._window_picker is not None and self._window_picker.winfo_exists():
            self._window_picker.lift()
            return

        self.log("Listing windows…")
        windows = list_capturable_windows(exclude_substrings=("Gif-Maker",))
        if not windows:
            messagebox.showinfo(
                "No windows",
                "No capturable windows found.\n"
                "Tip: Un-minimize the target app, then try again.",
            )
            return

        self._picked_windows = windows
        picker = tk.Toplevel(self.root)
        picker.title("Pick Window")
        picker.configure(bg=COLOR_BG_PRIMARY)
        picker.transient(self.root)
        picker.grab_set()
        self._window_picker = picker

        tk.Label(
            picker,
            text="Select a window to capture:",
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_PRIMARY,
            font=FONT_SECTION,
        ).pack(padx=12, pady=(12, 6))

        list_frame = tk.Frame(picker, bg=COLOR_BG_PRIMARY)
        list_frame.pack(fill="both", expand=True, padx=12, pady=6)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        listbox = tk.Listbox(
            list_frame,
            width=70,
            height=14,
            yscrollcommand=scrollbar.set,
            exportselection=False,
            bg=COLOR_BG_INPUT,
            fg=COLOR_TEXT_PRIMARY,
            selectbackground=COLOR_ACCENT_BLUE,
            selectforeground=COLOR_TEXT_WHITE,
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            font=FONT_LABEL,
        )
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)

        for win in windows:
            label = f"{win.title}  ({win.width}x{win.height} @ {win.left},{win.top})"
            listbox.insert(tk.END, label)
        listbox.selection_set(0)

        btn_row = tk.Frame(picker, bg=COLOR_BG_PRIMARY)
        btn_row.pack(fill="x", padx=12, pady=(6, 12))

        def on_ok() -> None:
            sel = listbox.curselection()
            if not sel:
                messagebox.showwarning("Pick Window", "Select a window first.")
                return
            chosen = self._picked_windows[int(sel[0])]
            self.region = chosen.as_region()
            x, y, w, h = self.region
            self.region_label.config(text=f"Region: {chosen.title[:40]} ({w}x{h})")
            self.log(f"Window selected: {chosen.title} → {self.region}")
            picker.destroy()
            self._window_picker = None

        def on_cancel() -> None:
            picker.destroy()
            self._window_picker = None

        self._make_button(
            btn_row, "Use Window", on_ok, COLOR_ACCENT_GREEN
        ).pack(side="left", padx=(0, 8))
        self._make_button(
            btn_row, "Cancel", on_cancel, COLOR_BROWSE
        ).pack(side="left")
        listbox.bind("<Double-Button-1>", lambda _e: on_ok())
        picker.protocol("WM_DELETE_WINDOW", on_cancel)

    def browse_output(self) -> None:
        """Browse for output file with path validation."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".gif",
            filetypes=[("GIF files", "*.gif"), ("All files", "*.*")],
        )
        if filename:
            # Validate path
            try:
                # Ensure directory exists
                dir_path = os.path.dirname(filename)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)
                self.output_var.set(filename)
            except (OSError, ValueError) as e:
                messagebox.showerror("Error", f"Invalid file path: {e}")

    def toggle_recording(self) -> None:
        """Start or stop recording.

        Toggles between recording and stopped states. If not recording,
        starts a new recording session. If recording, stops the current session.
        """
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self) -> None:
        """Start recording screenshots.

        Validates settings, hides the main window, and starts a background
        thread to capture screenshots at the specified interval.

        Raises:
            Shows error dialog if settings are invalid or region not selected.
        """
        # Validate settings before starting
        is_valid, error_msg = self.validate_settings()
        if not is_valid:
            messagebox.showerror("Error", error_msg or "Invalid settings!")
            return

        self.screenshot_count = int(self.count_var.get())
        self._sync_timing_from_simple()
        self.interval = float(self.interval_var.get())
        self.is_recording = True
        self.record_button.config(text="⏹️ Stop Recording", bg=COLOR_ACCENT_RED)
        self.create_button.config(state="disabled")
        self._set_mutate_controls(False)

        # Hide the window during recording to avoid it appearing in screenshots
        self.root.withdraw()
        self.log("Window hidden for clean recording...")

        # Non-blocking delay — time.sleep on UI thread freezes the app
        self.root.after(WINDOW_HIDE_DELAY_MS, self._start_recording_after_hide)

    def _start_recording_after_hide(self) -> None:
        """Begin capture thread after window hide delay."""
        if not self.is_recording:
            self.root.deiconify()
            self._set_mutate_controls(True)
            return

        with self._lock:
            if self._recording_active:
                self.log("Recording already in progress")
                self.is_recording = False
                self._set_mutate_controls(True)
                self.root.deiconify()
                return
            self._recording_active = True

        self.recording_thread = threading.Thread(target=self.record_screenshots)
        self.recording_thread.daemon = True
        self.recording_thread.start()

    def stop_recording(self) -> None:
        """Stop recording.

        Stops the current recording session, restores the main window,
        and updates UI button states.
        """
        self.is_recording = False
        self.record_button.config(text="🎬 Start Recording", bg=COLOR_ACCENT_RED)
        self.create_button.config(
            state="normal" if self.screenshots else "disabled"
        )
        # Re-enable mutate only if encode not running
        with self._lock:
            encoding = self._encoding_active
        if not encoding:
            self._set_mutate_controls(True)

        # Show the window again after recording
        self.root.deiconify()
        self.log("Window restored after recording")

    def record_screenshots(self) -> None:
        """Record screenshots in a loop (thread-safe).

        Captures screenshots of the selected region at the specified interval.
        Runs in a background thread to keep the UI responsive. Updates progress
        and preview in real-time.

        Note:
            This method should only be called from a background thread.
        """
        try:
            self.log_thread_safe(
                f"Starting recording: {self.screenshot_count} screenshots every {self.interval}s"
            )

            consecutive_failures = 0
            for i in range(self.screenshot_count):
                if not self.is_recording:
                    break

                try:
                    # Take screenshot of selected region
                    screenshot = pyautogui.screenshot(region=self.region)
                    with self._lock:
                        self.screenshots.append(screenshot)
                        frame_count = len(self.screenshots)

                    consecutive_failures = 0
                    self.log_thread_safe(
                        f"Screenshot {i+1}/{self.screenshot_count} captured"
                    )
                    self._set_count_display(f"Screenshots: {frame_count}")

                    # Update progress
                    progress = ((i + 1) / self.screenshot_count) * 100
                    self._set_progress(progress)

                    # Refresh preview after each screenshot
                    self._refresh_preview_thread_safe()

                    if i < self.screenshot_count - 1:  # Don't wait after last screenshot
                        time.sleep(self.interval)

                except Exception as e:
                    consecutive_failures += 1
                    error_msg = (
                        f"Error capturing screenshot {i+1}: {e}\n"
                        f"Tip: Region still visible? pyautogui FAILSAFE trips if "
                        f"mouse hits a screen corner — move mouse and retry.\n"
                        f"Consecutive failures: {consecutive_failures}/{MAX_CAPTURE_FAILURES}"
                    )
                    self.log_thread_safe(error_msg)
                    if consecutive_failures >= MAX_CAPTURE_FAILURES:
                        self.log_thread_safe(
                            "Aborting recording after repeated capture failures."
                        )
                        self.is_recording = False
                        break
        finally:
            # Always release the lock
            with self._lock:
                self._recording_active = False

            self.log_thread_safe("Recording completed!")
            # Window restore + stop are UI operations; schedule on main thread.
            self._ui(self.root.deiconify)
            self.log_thread_safe("Window restored - recording complete")
            self._safe_stop_recording_from_worker()

    def clear_screenshots(self) -> None:
        """Clear all screenshots and free memory.

        Removes all captured screenshots and preview images, explicitly
        closing image objects to free memory. Resets the preview display
        and updates UI state.
        """
        if self._is_busy():
            self.log("Cannot clear while recording or encoding")
            return

        with self._lock:
            frame_count = len(self.screenshots)
        if frame_count and not messagebox.askyesno(
            "Clear screenshots",
            f"Discard all {frame_count} captured screenshots? This cannot be undone.",
        ):
            return

        with self._lock:
            for img in self.screenshots:
                if hasattr(img, "close"):
                    img.close()
            self.screenshots.clear()

        for img in self.preview_images:
            if hasattr(img, "close"):
                img.close()

        self.preview_images.clear()
        self.current_preview_index = 0
        self.count_display.config(text="Screenshots: 0")
        self.progress["value"] = 0
        self.create_button.config(state="disabled")
        self.log("Screenshots cleared")
        self.refresh_preview()

    def create_gif(self) -> None:
        """Create animated GIF from screenshots.

        Validates that screenshots exist, shows estimated file size,
        and starts background GIF creation. Disables UI buttons during
        processing to prevent multiple operations.
        """
        if self._is_busy():
            messagebox.showinfo("Busy", "Wait for recording or encode to finish.")
            return

        frames = self._snapshot_screenshots()
        if not frames:
            messagebox.showerror("Error", "No screenshots to create GIF from!")
            return

        output_path = self.output_var.get()
        if not output_path.endswith(".gif"):
            output_path += ".gif"
        if os.path.exists(output_path):
            if not messagebox.askyesno(
                "Overwrite?",
                f"File already exists:\n{output_path}\n\nOverwrite?",
            ):
                return

        # Show estimated file size
        estimated_size = self.estimate_gif_size()
        self.log(f"Estimated file size: {estimated_size}")

        # Disable buttons during processing to prevent multiple operations
        self._encode_cancel.clear()
        with self._lock:
            self._encoding_active = True
        self.create_button.config(state="disabled")
        self.record_button.config(state="disabled")
        self.cancel_encode_button.config(state="normal")
        self._set_mutate_controls(False)

        # Start GIF creation in background thread (snapshot, not live list)
        self.log("Creating animated GIF... (Escape or Cancel Encode to stop)")
        self.gif_thread = threading.Thread(
            target=self.create_gif_worker, args=(frames, output_path)
        )
        self.gif_thread.daemon = True
        self.gif_thread.start()

    def _finish_encode_ui(self, *, cancelled: bool = False) -> None:
        """Re-enable controls after encode success, error, or cancel."""
        with self._lock:
            self._encoding_active = False
        self._encode_cancel.clear()
        self.create_button.config(state="normal")
        self.record_button.config(state="normal")
        self.cancel_encode_button.config(state="disabled")
        self._set_mutate_controls(True)
        if cancelled:
            self.log("GIF encode cancelled — no output written.")

    def create_gif_worker(self, frames: List, output_path: str) -> None:
        """Worker function for GIF creation in background thread.

        Processes a snapshot of screenshots according to quality settings.
        Runs in separate thread to prevent UI blocking.

        Args:
            frames: Snapshot of PIL images (stable for this encode).
            output_path: Resolved .gif output path.
        """
        try:
            create_gif(
                screenshots=frames,
                output_path=output_path,
                quality_label=self.quality_var.get(),
                speed_label=self.speed_var.get(),
                log_callback=self.log_thread_safe,
                cancel_check=self._encode_cancel.is_set,
                frame_duration_ms=resolve_frame_duration_ms(
                    self.playback_feel_var.get(),
                    float(self.interval_var.get()),
                ),
            )

            def enable_buttons():
                self._finish_encode_ui()
                if messagebox.askyesno(
                    "Success", "GIF created successfully!\n\nOpen file location?"
                ):
                    self.open_file_location(output_path)

            self.root.after(0, enable_buttons)

        except EncodeCancelled:
            self.log_thread_safe("Encode cancelled by user.")
            self.root.after(0, lambda: self._finish_encode_ui(cancelled=True))

        except Exception as e:
            error_msg = (
                f"Error creating GIF: {e}\n"
                f"Tip: Try a lower quality setting or ensure sufficient disk space."
            )
            self.log_thread_safe(error_msg)

            def enable_buttons_error():
                self._finish_encode_ui()
                messagebox.showerror(
                    "Error",
                    f"Failed to create GIF: {e}\n\n"
                    "Tip: Try a lower quality setting or check disk space.",
                )

            self.root.after(0, enable_buttons_error)
