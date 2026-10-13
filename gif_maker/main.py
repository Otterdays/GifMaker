"""Main entry point for the Gif-Maker application."""

import platform
import tkinter as tk

from gif_maker.gui.main_window import GIFMaker
from gif_maker.utils.app_logging import get_logger


def _enable_windows_dpi_awareness() -> None:
    """Make the process DPI-aware so the UI is crisp on high-DPI displays.

    Must run before the Tk root is created. No-op on non-Windows platforms.
    """
    if platform.system() != "Windows":
        return
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            import ctypes

            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def _apply_tk_scaling(root: tk.Tk) -> None:
    """Scale Tk widgets to the display DPI so physical size stays correct."""
    try:
        dpi = root.winfo_fpixels("1i")
        if dpi and dpi > 0:
            root.tk.call("tk", "scaling", dpi / 72.0)
    except Exception:
        pass


def main() -> None:
    """Main entry point for the application."""
    try:
        import pyautogui  # noqa: F401
        import PIL  # noqa: F401
    except ImportError as e:
        print(f"Missing required package: {e}")
        print("Please install required packages:")
        print("pip install pyautogui pillow")
        input("Press Enter to exit...")
        return

    get_logger().info("Gif-Maker starting")
    _enable_windows_dpi_awareness()

    root = tk.Tk()
    _apply_tk_scaling(root)
    GIFMaker(root)  # centers itself during construction

    root.mainloop()
