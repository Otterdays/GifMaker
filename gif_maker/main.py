"""Main entry point for the Gif-Maker application."""

import tkinter as tk

from gif_maker.gui.main_window import GIFMaker


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

    root = tk.Tk()
    app = GIFMaker(root)

    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")

    root.mainloop()
