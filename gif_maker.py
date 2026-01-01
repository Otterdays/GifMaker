#!/usr/bin/env python3
"""
Gif-Maker V1.0 - Professional Animated GIF Creation Tool
A comprehensive Python GUI application for creating high-quality animated GIFs
with advanced region selection, customizable quality settings, and real-time preview.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pyautogui
import time
import os
from PIL import Image, ImageTk
import threading
from datetime import datetime
import subprocess
import sys
import platform
from typing import Optional, Tuple, List

# ============================================================================
# Constants
# ============================================================================

# UI Constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
MIN_WIDTH = 900
MIN_HEIGHT = 650
PREVIEW_MAX_SIZE = (350, 250)
MIN_REGION_SIZE = 100

# Color Scheme
COLOR_BG_PRIMARY = '#2c3e50'
COLOR_BG_SECONDARY = '#34495e'
COLOR_ACCENT_RED = '#e74c3c'
COLOR_ACCENT_GREEN = '#27ae60'
COLOR_ACCENT_BLUE = '#3498db'
COLOR_ACCENT_PURPLE = '#9b59b6'
COLOR_ACCENT_ORANGE = '#e67e22'
COLOR_ACCENT_YELLOW = '#f39c12'
COLOR_TEXT_WHITE = 'white'
COLOR_TEXT_LIGHT = '#bdc3c7'
COLOR_TEXT_LIGHTBLUE = 'lightblue'

# Timing Constants
WINDOW_HIDE_DELAY = 0.5
SELECTION_CLOSE_DELAY = 2000
MIN_INTERVAL = 0.1
MAX_INTERVAL = 60.0
MIN_SCREENSHOT_COUNT = 1
MAX_SCREENSHOT_COUNT = 1000

# Frame Duration Constants (milliseconds)
FRAME_DURATION_SLOW = 333  # 3 FPS
FRAME_DURATION_NORMAL = 200  # 5 FPS
FRAME_DURATION_FAST = 125  # 8 FPS
FRAME_DURATION_VERY_FAST = 100  # 10 FPS

class GIFMaker:
    def __init__(self, root: tk.Tk) -> None:
        """Initialize the GIFMaker application.
        
        Args:
            root: The main tkinter root window.
        """
        self.root = root
        self.root.title("Gif-Maker V1.0")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.root.configure(bg=COLOR_BG_PRIMARY)
        
        # Thread safety
        self._lock = threading.Lock()
        self._recording_active = False
        
        # Center the window on screen
        self.center_window()
        
        # Variables
        self.screenshots: List[Image.Image] = []
        self.is_recording = False
        self.region: Optional[Tuple[int, int, int, int]] = None
        self.screenshot_count = 10
        self.interval = 0.5
        self.output_path = "demo.gif"
        self.current_preview_index = 0
        self.preview_images: List[Image.Image] = []  # Store resized images for preview
        
        # Create GUI
        self.create_widgets()
        
        # Setup keyboard shortcuts
        self.setup_keyboard_shortcuts()
    
    def center_window(self) -> None:
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def create_widgets(self) -> None:
        """Create and configure all GUI widgets."""
        # Title
        title_label = tk.Label(
            self.root, 
            text="🎬 Gif-Maker V1.0", 
            font=("Arial", 20, "bold"),
            fg=COLOR_TEXT_WHITE,
            bg=COLOR_BG_PRIMARY
        )
        title_label.pack(pady=10)
        
        # Main frame with side panel
        main_frame = tk.Frame(self.root, bg=COLOR_BG_SECONDARY, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Create left and right panels
        left_panel = tk.Frame(main_frame, bg=COLOR_BG_SECONDARY)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        right_panel = tk.Frame(main_frame, bg=COLOR_BG_SECONDARY, width=400)
        right_panel.pack(side="right", fill="y", padx=(10, 0))
        right_panel.pack_propagate(False)  # Prevent shrinking
        
        # Region selection frame
        region_frame = tk.LabelFrame(left_panel, text="📐 Region Selection", fg=COLOR_TEXT_WHITE, bg=COLOR_BG_SECONDARY)
        region_frame.pack(fill="x", pady=(0, 10))
        
        # Region selection buttons
        button_frame = tk.Frame(region_frame, bg=COLOR_BG_SECONDARY)
        button_frame.pack(pady=10)
        
        tk.Button(
            button_frame, 
            text="Manual Coordinates", 
            command=self.select_region,
            bg=COLOR_ACCENT_BLUE,
            fg=COLOR_TEXT_WHITE,
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=5)
        
        tk.Button(
            button_frame, 
            text="Full Screen", 
            command=self.select_fullscreen,
            bg=COLOR_ACCENT_PURPLE,
            fg=COLOR_TEXT_WHITE,
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=5)
        
        tk.Button(
            button_frame, 
            text="Common Browser Size", 
            command=self.select_browser_size,
            bg=COLOR_ACCENT_ORANGE,
            fg=COLOR_TEXT_WHITE,
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=5)
        
        self.region_label = tk.Label(
            region_frame, 
            text="No region selected", 
            fg=COLOR_TEXT_LIGHT,
            bg=COLOR_BG_SECONDARY
        )
        self.region_label.pack()
        
        # Settings frame
        settings_frame = tk.LabelFrame(left_panel, text="⚙️ Settings", fg=COLOR_TEXT_WHITE, bg=COLOR_BG_SECONDARY)
        settings_frame.pack(fill="x", pady=(0, 10))
        
        # Screenshot count
        tk.Label(settings_frame, text="Number of Screenshots:", fg=COLOR_TEXT_WHITE, bg=COLOR_BG_SECONDARY).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.count_var = tk.StringVar(value="10")
        count_entry = tk.Entry(settings_frame, textvariable=self.count_var, width=10)
        count_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # Interval
        tk.Label(settings_frame, text="Interval (seconds):", fg=COLOR_TEXT_WHITE, bg=COLOR_BG_SECONDARY).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.interval_var = tk.StringVar(value="0.5")
        interval_entry = tk.Entry(settings_frame, textvariable=self.interval_var, width=10)
        interval_entry.grid(row=1, column=1, padx=10, pady=5)
        
        # Output path
        tk.Label(settings_frame, text="Output File:", fg=COLOR_TEXT_WHITE, bg=COLOR_BG_SECONDARY).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.output_var = tk.StringVar(value="demo.gif")
        output_entry = tk.Entry(settings_frame, textvariable=self.output_var, width=20)
        output_entry.grid(row=2, column=1, padx=10, pady=5)
        
        # Quality setting
        tk.Label(settings_frame, text="Quality:", fg=COLOR_TEXT_WHITE, bg=COLOR_BG_SECONDARY).grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.quality_var = tk.StringVar(value="MAX")
        quality_combo = ttk.Combobox(settings_frame, textvariable=self.quality_var, width=15, state="readonly")
        quality_combo['values'] = ("MAX (100%)", "High (80%)", "Medium (85%)", "Low (75%)")
        quality_combo.grid(row=3, column=1, padx=10, pady=5)
        
        # Quality tips
        quality_tips = tk.Label(
            settings_frame, 
            text="MAX: Perfect quality, refined processing | High: Smooth gradients | Medium: Balanced | Low: Small files", 
            fg=COLOR_TEXT_LIGHTBLUE, 
            bg=COLOR_BG_SECONDARY,
            font=("Arial", 8),
            wraplength=300
        )
        quality_tips.grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=2)
        
        # Playback speed setting
        tk.Label(settings_frame, text="Playback Speed:", fg=COLOR_TEXT_WHITE, bg=COLOR_BG_SECONDARY).grid(row=5, column=0, sticky="w", padx=10, pady=5)
        self.speed_var = tk.StringVar(value="Normal (5 FPS)")
        speed_combo = ttk.Combobox(settings_frame, textvariable=self.speed_var, width=15, state="readonly")
        speed_combo['values'] = ("Slow (3 FPS)", "Normal (5 FPS)", "Fast (8 FPS)", "Very Fast (10 FPS)")
        speed_combo.grid(row=5, column=1, padx=10, pady=5)
        
        # Speed tips
        speed_tips = tk.Label(
            settings_frame,
            text="Slow: Easy to follow | Normal: Balanced | Fast: Quick preview | Very Fast: Rapid cycling",
            fg=COLOR_TEXT_LIGHTBLUE,
            bg=COLOR_BG_SECONDARY,
            font=("Arial", 8),
            wraplength=300
        )
        speed_tips.grid(row=6, column=0, columnspan=2, sticky="w", padx=10, pady=2)
        
        tk.Button(
            settings_frame, 
            text="Browse", 
            command=self.browse_output,
            bg="#95a5a6",
            fg=COLOR_TEXT_WHITE
        ).grid(row=2, column=2, padx=5, pady=5)
        
        # Control buttons frame
        control_frame = tk.Frame(left_panel, bg=COLOR_BG_SECONDARY)
        control_frame.pack(fill="x", pady=(0, 10))
        
        # Start/Stop recording button
        self.record_button = tk.Button(
            control_frame,
            text="🎬 Start Recording",
            command=self.toggle_recording,
            bg=COLOR_ACCENT_RED,
            fg=COLOR_TEXT_WHITE,
            font=("Arial", 12, "bold"),
            height=2
        )
        self.record_button.pack(side="left", padx=(0, 10))
        
        # Create GIF button
        self.create_button = tk.Button(
            control_frame,
            text="🎞️ Create GIF",
            command=self.create_gif,
            bg=COLOR_ACCENT_GREEN,
            fg=COLOR_TEXT_WHITE,
            font=("Arial", 12, "bold"),
            height=2,
            state="disabled"
        )
        self.create_button.pack(side="left", padx=(0, 10))
        
        # Clear button
        self.clear_button = tk.Button(
            control_frame,
            text="🗑️ Clear",
            command=self.clear_screenshots,
            bg=COLOR_ACCENT_YELLOW,
            fg=COLOR_TEXT_WHITE,
            font=("Arial", 12, "bold"),
            height=2
        )
        self.clear_button.pack(side="left")
        
        # Status frame
        status_frame = tk.LabelFrame(left_panel, text="📊 Status", fg=COLOR_TEXT_WHITE, bg=COLOR_BG_SECONDARY)
        status_frame.pack(fill="both", expand=True)
        
        # Screenshot count display
        self.count_display = tk.Label(
            status_frame,
            text="Screenshots: 0",
            fg=COLOR_TEXT_WHITE,
            bg=COLOR_BG_SECONDARY,
            font=("Arial", 12)
        )
        self.count_display.pack(pady=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(status_frame, mode='determinate')
        self.progress.pack(fill="x", padx=10, pady=5)
        
        # Status text
        self.status_text = tk.Text(
            status_frame,
            height=6,
            bg=COLOR_BG_PRIMARY,
            fg=COLOR_TEXT_WHITE,
            font=("Consolas", 9)
        )
        self.status_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Preview panel
        self.setup_preview_panel(right_panel)
        
        # Scrollbar for status text
        scrollbar = tk.Scrollbar(status_frame)
        scrollbar.pack(side="right", fill="y")
        self.status_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.status_text.yview)
    
    def setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts for common actions."""
        self.root.bind('<space>', lambda e: self.toggle_recording())
        self.root.bind('<Escape>', lambda e: self.cancel_if_recording())
        self.root.bind('<Control-s>', lambda e: self.create_gif())
        self.root.bind('<Control-c>', lambda e: self.clear_screenshots())
    
    def cancel_if_recording(self, event: Optional[tk.Event] = None) -> None:
        """Cancel recording if active.
        
        Args:
            event: Optional tkinter event (for keyboard binding).
        """
        if self.is_recording:
            self.stop_recording()
    
    def setup_preview_panel(self, parent: tk.Frame) -> None:
        """Setup the image preview panel.
        
        Args:
            parent: The parent frame to attach the preview panel to.
        """
        # Preview frame
        preview_frame = tk.LabelFrame(parent, text="🖼️ Image Preview", fg=COLOR_TEXT_WHITE, bg=COLOR_BG_SECONDARY)
        preview_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Preview image display - make it fill the available space
        self.preview_label = tk.Label(
            preview_frame,
            text="No images captured yet",
            bg=COLOR_BG_PRIMARY,
            fg=COLOR_TEXT_WHITE,
            font=("Arial", 10),
            width=40,
            height=20
        )
        self.preview_label.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Navigation controls
        nav_frame = tk.Frame(preview_frame, bg=COLOR_BG_SECONDARY)
        nav_frame.pack(fill="x", padx=10, pady=5)
        
        # Previous button
        self.prev_button = tk.Button(
            nav_frame,
            text="◀",
            command=self.prev_image,
            state="disabled",
            bg=COLOR_ACCENT_BLUE,
            fg=COLOR_TEXT_WHITE,
            font=("Arial", 12, "bold"),
            width=3
        )
        self.prev_button.pack(side="left", padx=2)
        
        # Image counter
        self.image_counter = tk.Label(
            nav_frame,
            text="0/0",
            bg=COLOR_BG_SECONDARY,
            fg=COLOR_TEXT_WHITE,
            font=("Arial", 10, "bold")
        )
        self.image_counter.pack(side="left", expand=True)
        
        # Next button
        self.next_button = tk.Button(
            nav_frame,
            text="▶",
            command=self.next_image,
            state="disabled",
            bg=COLOR_ACCENT_BLUE,
            fg=COLOR_TEXT_WHITE,
            font=("Arial", 12, "bold"),
            width=3
        )
        self.next_button.pack(side="right", padx=2)
        
        # Image info
        self.image_info = tk.Label(
            preview_frame,
            text="",
            bg=COLOR_BG_SECONDARY,
            fg=COLOR_TEXT_LIGHTBLUE,
            font=("Arial", 8),
            wraplength=280
        )
        self.image_info.pack(padx=10, pady=5)
        
        # Action buttons
        action_frame = tk.Frame(preview_frame, bg=COLOR_BG_SECONDARY)
        action_frame.pack(fill="x", padx=10, pady=5)
        
        # Delete current image button
        self.delete_button = tk.Button(
            action_frame,
            text="🗑️ Delete",
            command=self.delete_current_image,
            state="disabled",
            bg=COLOR_ACCENT_RED,
            fg=COLOR_TEXT_WHITE,
            font=("Arial", 9)
        )
        self.delete_button.pack(side="left", padx=2)
        
        # Refresh preview button
        self.refresh_button = tk.Button(
            action_frame,
            text="🔄 Refresh",
            command=self.refresh_preview,
            bg=COLOR_ACCENT_GREEN,
            fg=COLOR_TEXT_WHITE,
            font=("Arial", 9)
        )
        self.refresh_button.pack(side="right", padx=2)
        
    def log(self, message: str) -> None:
        """Add message to status log.
        
        Args:
            message: The message to log.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.root.update()
    
    def log_thread_safe(self, message: str) -> None:
        """Thread-safe logging for background operations.
        
        Args:
            message: The message to log.
        """
        def update_log():
            self.log(message)
        self.root.after(0, update_log)
    
    def refresh_preview(self) -> None:
        """Refresh the image preview with lazy loading."""
        if not self.screenshots:
            self.preview_label.config(text="No images captured yet")
            self.image_counter.config(text="0/0")
            self.image_info.config(text="")
            self.prev_button.config(state="disabled")
            self.next_button.config(state="disabled")
            self.delete_button.config(state="disabled")
            return
        
        # Only create thumbnails if not already created or count changed
        if len(self.preview_images) != len(self.screenshots):
            self.preview_images = []
            for screenshot in self.screenshots:
                resized = screenshot.copy()
                resized.thumbnail(PREVIEW_MAX_SIZE, Image.Resampling.LANCZOS)
                self.preview_images.append(resized)
        
        # Update preview
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
        
        # Convert to PhotoImage for display
        from PIL import ImageTk
        photo = ImageTk.PhotoImage(current_image)
        self.preview_label.config(image=photo, text="")
        self.preview_label.image = photo  # Keep a reference
        
        # Update counter
        self.image_counter.config(text=f"{self.current_preview_index + 1}/{len(self.screenshots)}")
        
        # Update image info
        original = self.screenshots[self.current_preview_index]
        info_text = f"Size: {original.width}x{original.height}\nMode: {original.mode}"
        self.image_info.config(text=info_text)
        
        # Update button states
        self.prev_button.config(state="normal" if self.current_preview_index > 0 else "disabled")
        self.next_button.config(state="normal" if self.current_preview_index < len(self.screenshots) - 1 else "disabled")
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
        """Delete the currently displayed image."""
        if not self.screenshots or self.current_preview_index >= len(self.screenshots):
            return
        
        # Remove the image and free memory
        img = self.screenshots[self.current_preview_index]
        if hasattr(img, 'close'):
            img.close()
        del self.screenshots[self.current_preview_index]
        
        if self.current_preview_index < len(self.preview_images):
            preview_img = self.preview_images[self.current_preview_index]
            if hasattr(preview_img, 'close'):
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
            if count < MIN_SCREENSHOT_COUNT or count > MAX_SCREENSHOT_COUNT:
                return False, f"Screenshot count must be between {MIN_SCREENSHOT_COUNT} and {MAX_SCREENSHOT_COUNT}"
            
            interval = float(self.interval_var.get())
            if interval < MIN_INTERVAL or interval > MAX_INTERVAL:
                return False, f"Interval must be between {MIN_INTERVAL} and {MAX_INTERVAL} seconds"
                
            if not self.region:
                return False, "Please select a region first"
                
            return True, None
        except ValueError as e:
            return False, f"Invalid input: {e}"
    
    def estimate_gif_size(self) -> str:
        """Estimate GIF file size based on current settings.
        
        Returns:
            Estimated file size as a formatted string.
        """
        if not self.screenshots:
            return "No screenshots"
        
        # Rough estimation: average image size * frame count * quality factor
        try:
            avg_size = sum(len(img.tobytes()) for img in self.screenshots) / len(self.screenshots)
            quality_setting = self.quality_var.get().split()[0]
            quality_factor = {'MAX': 1.0, 'High': 0.8, 'Medium': 0.6, 'Low': 0.4}.get(
                quality_setting, 0.6
            )
            estimated = avg_size * len(self.screenshots) * quality_factor
            return f"~{estimated / 1024 / 1024:.1f} MB"
        except Exception:
            return "Unable to estimate"
    
    def open_file_location(self, path: str) -> None:
        """Open file location in system file manager (cross-platform).
        
        Args:
            path: The file path whose directory should be opened.
        """
        folder = os.path.dirname(os.path.abspath(path))
        try:
            if platform.system() == 'Windows':
                os.startfile(folder)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', folder])
            else:  # Linux
                subprocess.run(['xdg-open', folder])
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
        self.region_overlay.attributes('-fullscreen', True)
        self.region_overlay.attributes('-alpha', 0.5)  # More opaque for better contrast
        self.region_overlay.configure(bg='#1a1a1a')  # Darker background
        self.region_overlay.attributes('-topmost', True)
        
        # Create canvas for drawing
        self.region_canvas = tk.Canvas(
            self.region_overlay, 
            highlightthickness=0,
            bg='black',
            cursor='crosshair'
        )
        self.region_canvas.pack(fill='both', expand=True)
        
        # Variables for selection
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.instruction_text = None
        
        # Bind mouse events
        self.region_canvas.bind('<Button-1>', self.start_selection)
        self.region_canvas.bind('<B1-Motion>', self.update_selection)
        self.region_canvas.bind('<ButtonRelease-1>', self.end_selection)
        self.region_canvas.bind('<Escape>', self.cancel_selection)
        
        # Show instructions
        self.show_selection_instructions()
        
        # Focus the overlay
        self.region_overlay.focus_set()
        
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
            box_x - 10, box_y - 10, box_x + box_width + 10, box_y + box_height + 10,
            fill='#34495e', outline='#aed6f1', width=3, tags="instruction_box"
        )
        
        # Add inner shadow effect
        self.region_canvas.create_rectangle(
            box_x - 8, box_y - 8, box_x + box_width + 8, box_y + box_height + 8,
            fill='', outline='#aed6f1', width=1, tags="instruction_box"
        )
        
        # Title
        self.region_canvas.create_text(
            screen_width // 2, 
            box_y + 30,
            text="🎯 REGION SELECTION",
            fill='#ffffff',
            font=("Arial", 18, "bold"),
            anchor="center",
            tags="instruction_box"
        )
        
        # Instructions
        instruction_lines = [
            "Click and drag to select your browser window",
            "",
            "• Click at the TOP-LEFT corner of your browser",
            "• Drag to the BOTTOM-RIGHT corner", 
            "• Release to confirm selection",
            "",
            "Press ESC to cancel"
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
                tags="instruction_box"
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
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='#e74c3c', width=4, fill='#e74c3c', stipple='gray12', 
            tags="selection_rect"
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
            (self.start_x, self.start_y)   # Bottom-right (will update)
        ]
        
        for i, (x, y) in enumerate(corners):
            marker = self.region_canvas.create_oval(
                x - marker_size//2, y - marker_size//2,
                x + marker_size//2, y + marker_size//2,
                fill='#f39c12', outline='#e67e22', width=2,
                tags="corner_markers"
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
            coord_x - 5, coord_y - 5, coord_x + coord_box_width + 5, coord_y + coord_box_height + 5,
            fill='#2c3e50', outline='#aed6f1', width=2, tags="coord_box"
        )
        
        self.region_canvas.create_text(
            coord_x + coord_box_width // 2,
            coord_y + 15,
            text=f"Start: {self.start_x}, {self.start_y}",
            fill="#ffffff",
            font=("Arial", 12, "bold"),
            anchor="center",
            tags="coord_box"
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
                self.start_x, self.start_y, event.x, event.y
            )
            
            # Update corner markers
            if hasattr(self, 'corner_markers') and self.corner_markers:
                # Calculate corners
                x1, y1 = self.start_x, self.start_y
                x2, y2 = event.x, event.y
                
                # Ensure proper corner order
                left = min(x1, x2)
                right = max(x1, x2)
                top = min(y1, y2)
                bottom = max(y1, y2)
                
                corners = [
                    (left, top),    # Top-left
                    (right, top),   # Top-right
                    (left, bottom), # Bottom-left
                    (right, bottom) # Bottom-right
                ]
                
                marker_size = 8
                for i, marker in enumerate(self.corner_markers):
                    if i < len(corners):
                        x, y = corners[i]
                        self.region_canvas.coords(
                            marker,
                            x - marker_size//2, y - marker_size//2,
                            x + marker_size//2, y + marker_size//2
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
                coord_x - 5, coord_y - 5, coord_x + coord_box_width + 5, coord_y + coord_box_height + 5,
                fill='#2c3e50', outline='#aed6f1', width=2, tags="coords"
            )
            
            self.region_canvas.create_text(
                coord_x + coord_box_width // 2,
                coord_y + 15,
                text=f"Start: {self.start_x}, {self.start_y}",
                fill="#ffffff",
                font=("Arial", 11, "bold"),
                anchor="center",
                tags="coords"
            )
            
            self.region_canvas.create_text(
                coord_x + coord_box_width // 2,
                coord_y + 35,
                text=f"Size: {width} x {height}",
                fill="#f7dc6f",
                font=("Arial", 11, "bold"),
                anchor="center",
                tags="coords"
            )
    
    def end_selection(self, event: tk.Event) -> None:
        """End region selection.
        
        Args:
            event: The mouse event containing release coordinates.
        """
        if self.start_x is None or self.start_y is None:
            return
            
        # Calculate final region
        x1, y1 = self.start_x, self.start_y
        x2, y2 = event.x, event.y
        
        x = min(x1, x2)
        y = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        # Validate selection
        if width < MIN_REGION_SIZE or height < MIN_REGION_SIZE:
            screen_width = self.region_overlay.winfo_screenwidth()
            screen_height = self.region_overlay.winfo_screenheight()
            
            # Create error message box at bottom-center
            error_box_width = 400  # Wider to accommodate text
            error_box_height = 50  # Taller for better text fit
            error_x = (screen_width - error_box_width) // 2
            error_y = screen_height - 100  # Higher up to avoid covering selection
            
            self.region_canvas.create_rectangle(
                error_x - 5, error_y - 5, error_x + error_box_width + 5, error_y + error_box_height + 5,
                fill='#e74c3c', outline='#f9e79f', width=3, tags="error_box"
            )
            
            self.region_canvas.create_text(
                error_x + error_box_width // 2,
                error_y + error_box_height // 2,
                text="❌ Selection too small! Try again.",
                fill="white",
                font=("Arial", 14, "bold"),
                anchor="center",
                tags="error_box"
            )
            self.region_overlay.after(2000, self.cancel_selection)
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
            success_x - 5, success_y - 5, success_x + success_box_width + 5, success_y + success_box_height + 5,
            fill='#27ae60', outline='#a9dfbf', width=3, tags="success_box"
        )
        
        self.region_canvas.create_text(
            success_x + success_box_width // 2,
            success_y + success_box_height // 2,
            text="✅ Selection confirmed! Closing in 2 seconds...",
            fill="white",
            font=("Arial", 14, "bold"),
            anchor="center",
            tags="success_box"
        )
        
        # Set the region
        self.region = (x, y, width, height)
        self.region_label.config(text=f"Region: {x},{y} {width}x{height}")
        self.log(f"Region selected: {self.region}")
        
        # Clean up visual elements
        if hasattr(self, 'corner_markers'):
            for marker in self.corner_markers:
                self.region_canvas.delete(marker)
            self.corner_markers = []
        
        # Close overlay after delay
        self.region_overlay.after(2000, self.close_selection_overlay)
    
    def cancel_selection(self, event: Optional[tk.Event] = None) -> None:
        """Cancel region selection.
        
        Args:
            event: Optional tkinter event (for keyboard binding).
        """
        self.log("Region selection cancelled")
        
        # Clean up visual elements
        if hasattr(self, 'corner_markers'):
            for marker in self.corner_markers:
                self.region_canvas.delete(marker)
            self.corner_markers = []
        
        self.close_selection_overlay()
    
    def close_selection_overlay(self) -> None:
        """Close the selection overlay and clean up resources."""
        if hasattr(self, 'region_overlay'):
            try:
                # Unbind events to prevent memory leaks
                if hasattr(self, 'region_canvas'):
                    try:
                        self.region_canvas.unbind_all('<Button-1>')
                        self.region_canvas.unbind_all('<B1-Motion>')
                        self.region_canvas.unbind_all('<ButtonRelease-1>')
                    except Exception:
                        pass  # Events may already be unbound
                self.region_overlay.destroy()
            except Exception as e:
                self.log(f"Error closing overlay: {e}")
            finally:
                # Clean up references
                if hasattr(self, 'region_overlay'):
                    del self.region_overlay
                if hasattr(self, 'region_canvas'):
                    del self.region_canvas
    
    def select_fullscreen(self) -> None:
        """Select full screen region.
        
        Automatically sets the capture region to cover the entire screen.
        """
        try:
            screen_width, screen_height = pyautogui.size()
            self.region = (0, 0, screen_width, screen_height)
            self.region_label.config(text=f"Region: Full Screen ({screen_width}x{screen_height})")
            self.log(f"Full screen selected: {screen_width}x{screen_height}")
        except Exception as e:
            error_msg = (
                f"Error selecting full screen: {e}\n"
                f"Tip: Ensure your display is properly configured."
            )
            self.log(error_msg)
    
    def select_browser_size(self) -> None:
        """Select common browser window size.
        
        Attempts to automatically detect and select a browser-sized region
        centered on the screen. Falls back to manual selection if needed.
        """
        self.log("Selecting common browser window size...")
        
        # Hide main window
        self.root.withdraw()
        time.sleep(WINDOW_HIDE_DELAY)
        
        try:
            # Get screen size
            screen_width, screen_height = pyautogui.size()
            
            print("\n" + "="*60)
            print("BROWSER WINDOW DETECTION")
            print("="*60)
            print("This will try to find your browser window automatically.")
            print("If it doesn't work, use 'Manual Coordinates' instead.")
            print("="*60)
            
            # Try to find browser window by looking for common patterns
            # This is a simple approach - look for a reasonable window size
            browser_width = min(1400, screen_width - 100)  # Leave some margin
            browser_height = min(900, screen_height - 100)
            
            # Center the region
            x = (screen_width - browser_width) // 2
            y = (screen_height - browser_height) // 2
            
            self.region = (x, y, browser_width, browser_height)
            self.region_label.config(text=f"Region: Browser Size ({browser_width}x{browser_height})")
            self.log(f"Browser size selected: {browser_width}x{browser_height} at ({x},{y})")
            
            print(f"\n✅ Browser region selected: {x},{y} {browser_width}x{browser_height}")
            print("If this doesn't capture your browser correctly, use 'Manual Coordinates'")
            
        except Exception as e:
            error_msg = (
                f"Browser size selection error: {e}\n"
                f"Tip: Use 'Manual Coordinates' to select your browser window manually."
            )
            self.log(error_msg)
            print(f"\n❌ Error: {e}")
        finally:
            # Show main window again
            self.root.deiconify()
            
    def browse_output(self) -> None:
        """Browse for output file with path validation."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".gif",
            filetypes=[("GIF files", "*.gif"), ("All files", "*.*")]
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
            
        self.is_recording = True
        self.record_button.config(text="⏹️ Stop Recording", bg="#e74c3c")
        self.create_button.config(state="disabled")
        
        # Get validated values
        self.screenshot_count = int(self.count_var.get())
        self.interval = float(self.interval_var.get())
        
        self.is_recording = True
        self.record_button.config(text="⏹️ Stop Recording", bg=COLOR_ACCENT_RED)
        self.create_button.config(state="disabled")
        
        # Hide the window during recording to avoid it appearing in screenshots
        self.root.withdraw()
        self.log("Window hidden for clean recording...")
        
        # Small delay to ensure window is completely hidden
        time.sleep(WINDOW_HIDE_DELAY)
        
        # Start recording in separate thread with thread safety
        with self._lock:
            if self._recording_active:
                self.log("Recording already in progress")
                self.is_recording = False
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
        self.create_button.config(state="normal" if self.screenshots else "disabled")
        
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
            self.log(f"Starting recording: {self.screenshot_count} screenshots every {self.interval}s")
            
            for i in range(self.screenshot_count):
                if not self.is_recording:
                    break
                    
                try:
                    # Take screenshot of selected region
                    screenshot = pyautogui.screenshot(region=self.region)
                    self.screenshots.append(screenshot)
                    
                    self.log(f"Screenshot {i+1}/{self.screenshot_count} captured")
                    self.count_display.config(text=f"Screenshots: {len(self.screenshots)}")
                    
                    # Update progress
                    progress = ((i + 1) / self.screenshot_count) * 100
                    self.progress['value'] = progress
                    
                    # Refresh preview after each screenshot
                    self.refresh_preview()
                    
                    if i < self.screenshot_count - 1:  # Don't wait after last screenshot
                        time.sleep(self.interval)
                        
                except Exception as e:
                    error_msg = (
                        f"Error capturing screenshot {i+1}: {e}\n"
                        f"Tip: Ensure the selected region is still visible and accessible."
                    )
                    self.log(error_msg)
        finally:
            # Always release the lock
            with self._lock:
                self._recording_active = False
                
            self.log("Recording completed!")
            # Show window again before stopping recording
            self.root.deiconify()
            self.log("Window restored - recording complete")
            self.stop_recording()
        
    def clear_screenshots(self) -> None:
        """Clear all screenshots and free memory.
        
        Removes all captured screenshots and preview images, explicitly
        closing image objects to free memory. Resets the preview display
        and updates UI state.
        """
        # Explicitly delete images to free memory
        for img in self.screenshots:
            if hasattr(img, 'close'):
                img.close()
        for img in self.preview_images:
            if hasattr(img, 'close'):
                img.close()
                
        self.screenshots.clear()
        self.preview_images.clear()
        self.current_preview_index = 0
        self.count_display.config(text="Screenshots: 0")
        self.progress['value'] = 0
        self.create_button.config(state="disabled")
        self.log("Screenshots cleared")
        self.refresh_preview()
        
    def create_gif(self) -> None:
        """Create animated GIF from screenshots.
        
        Validates that screenshots exist, shows estimated file size,
        and starts background GIF creation. Disables UI buttons during
        processing to prevent multiple operations.
        """
        if not self.screenshots:
            messagebox.showerror("Error", "No screenshots to create GIF from!")
            return
        
        # Show estimated file size
        estimated_size = self.estimate_gif_size()
        self.log(f"Estimated file size: {estimated_size}")
            
        # Disable buttons during processing to prevent multiple operations
        self.create_button.config(state="disabled")
        self.record_button.config(state="disabled")
        self.clear_button.config(state="disabled")
        
        # Start GIF creation in background thread
        self.log("Creating animated GIF...")
        self.gif_thread = threading.Thread(target=self.create_gif_worker)
        self.gif_thread.daemon = True
        self.gif_thread.start()
    
    def create_gif_worker(self) -> None:
        """Worker function for GIF creation in background thread.
        
        Processes screenshots according to quality settings and creates
        animated GIF. Runs in separate thread to prevent UI blocking.
        
        Raises:
            Exception: If GIF creation fails, logs error and re-enables UI.
        """
        try:
            # Get output path
            output_path = self.output_var.get()
            if not output_path.endswith('.gif'):
                output_path += '.gif'
                
            # Create GIF with proper animation speed and color optimization
            # Get playback speed from user selection
            speed_setting = self.speed_var.get()
            if speed_setting.startswith("Slow"):
                frame_duration = FRAME_DURATION_SLOW
            elif speed_setting.startswith("Normal"):
                frame_duration = FRAME_DURATION_NORMAL
            elif speed_setting.startswith("Fast"):
                frame_duration = FRAME_DURATION_FAST
            elif speed_setting.startswith("Very Fast"):
                frame_duration = FRAME_DURATION_VERY_FAST
            else:
                frame_duration = FRAME_DURATION_NORMAL  # Default to 5 FPS
            
            # Convert all screenshots to RGB mode for better color handling
            processed_screenshots = []
            for screenshot in self.screenshots:
                # Convert to RGB if not already
                if screenshot.mode != 'RGB':
                    screenshot = screenshot.convert('RGB')
                
                # For High quality, apply noise reduction instead of blur
                if self.quality_var.get() == "High":
                    # Apply noise reduction to smooth gradients without losing detail
                    from PIL import ImageFilter
                    screenshot = screenshot.filter(ImageFilter.MedianFilter(size=3))
                
                processed_screenshots.append(screenshot)
            
            # Get quality settings - RESEARCH-BASED OPTIMIZATION
            # Based on research: HIGH quality was causing MORE banding due to over-quantization
            quality_setting = self.quality_var.get()
            if quality_setting.startswith("MAX"):
                # MAX quality: 100% quality with refined optimization
                quality = 100  # Maximum quality for best color reproduction
                method = 0     # Fast method works best
                palette = 2    # Adaptive palette for best color distribution
                dither = 1     # Floyd-Steinberg dithering for smooth gradients
                use_advanced_quantization = True
            elif quality_setting.startswith("High"):
                # For gradients: Use MEDIUM settings but with better dithering
                quality = 80   # Lower quality actually works BETTER for gradients
                method = 0     # Use FAST method (0) - works better than complex methods
                palette = 2    # Use ADAPTIVE palette (2) - better for gradients
                dither = 1     # Floyd-Steinberg dithering
                use_advanced_quantization = False
            elif quality_setting.startswith("Medium"):
                quality = 85
                method = 0     # Fast method works better
                palette = 1    # Web palette
                dither = 1     # Floyd-Steinberg dithering
                use_advanced_quantization = False
            else:  # Low
                quality = 75
                method = 0     # Fast method
                palette = 0    # Web palette
                dither = 0     # No dithering
                use_advanced_quantization = False
            
            self.log_thread_safe(f"Creating GIF with {quality_setting} quality settings...")
            self.log_thread_safe(f"Playback speed: {speed_setting} ({frame_duration}ms per frame)")
            
            # Create GIF with optimized color settings
            if quality_setting.startswith("MAX"):
                # MAX quality: Refined optimization for 100% quality with minimal impurities
                from PIL import Image
                
                # For MAX quality, use refined processing to minimize artifacts
                self.log_thread_safe("MAX quality processing - this may take a moment...")
                quantized_images = []
                total_frames = len(processed_screenshots)
                for i, img in enumerate(processed_screenshots):
                    try:
                        # Apply refined sharpening with better parameters
                        from PIL import ImageFilter
                        # More conservative sharpening to reduce artifacts
                        sharpened = img.filter(ImageFilter.UnsharpMask(radius=0.8, percent=120, threshold=2))
                        
                        # Use optimized quantization with better color preservation
                        quantized = sharpened.quantize(colors=256, method=Image.MEDIANCUT, kmeans=2)
                        # Convert back to RGB for saving
                        quantized = quantized.convert('RGB')
                        
                        # Skip additional filtering to avoid artifacts
                        # The quantization and sharpening should be sufficient
                        quantized_images.append(quantized)
                        
                        # Update progress for MAX quality (every 10% or last frame)
                        progress_interval = max(1, total_frames // 10)
                        if (i + 1) % progress_interval == 0 or i == total_frames - 1:
                            progress = ((i + 1) / total_frames) * 100
                            self.log_thread_safe(f"Processing frame {i+1}/{total_frames} ({progress:.1f}%)")
                        
                    except Exception as e:
                        # Fallback to basic processing if advanced processing fails
                        self.log_thread_safe(f"Advanced processing failed for frame {i+1}, using basic: {e}")
                        basic_quantized = img.quantize(colors=256, method=Image.MEDIANCUT)
                        quantized_images.append(basic_quantized.convert('RGB'))
                
                # Save with refined MAX quality parameters
                quantized_images[0].save(
                    output_path,
                    save_all=True,
                    append_images=quantized_images[1:],
                    duration=frame_duration,
                    loop=0,
                    optimize=False,  # Don't optimize to preserve quality
                    quality=quality,  # 100% quality
                    dither=1  # Floyd-Steinberg dithering for smooth gradients
                )
            elif quality_setting.startswith("High"):
                # For HIGH quality, use a different approach to avoid banding
                # Create a quantized version first, then save
                from PIL import Image
                
                # Quantize all images to the same palette to ensure consistency
                quantized_images = []
                for img in processed_screenshots:
                    # Convert to P mode with adaptive palette
                    quantized = img.quantize(colors=256, method=Image.MEDIANCUT)
                    # Convert back to RGB for saving
                    quantized = quantized.convert('RGB')
                    quantized_images.append(quantized)
                
                # Save with minimal parameters to avoid over-processing
                quantized_images[0].save(
                    output_path,
                    save_all=True,
                    append_images=quantized_images[1:],
                    duration=frame_duration,
                    loop=0,
                    optimize=False,  # Don't optimize to avoid re-quantization
                    dither=1  # Use dithering for smooth gradients
                )
            else:
                # Use standard approach for Medium and Low
                processed_screenshots[0].save(
                    output_path,
                    save_all=True,
                    append_images=processed_screenshots[1:],
                    duration=frame_duration,  # 100ms per frame for smooth animation
                    loop=0,  # Infinite loop
                    optimize=True,  # Optimize file size
                    quality=quality,  # Quality based on setting
                    method=method,  # Quantization method
                    palette=palette,  # Color palette type
                    dither=dither  # Dithering method for better color reproduction
                )
            
            self.log_thread_safe(f"GIF created successfully: {output_path}")
            self.log_thread_safe(f"File size: {os.path.getsize(output_path)} bytes")
            
            # Re-enable buttons on completion
            def enable_buttons():
                self.create_button.config(state="normal")
                self.record_button.config(state="normal")
                self.clear_button.config(state="normal")
                # Ask if user wants to open the file
                if messagebox.askyesno("Success", f"GIF created successfully!\n\nOpen file location?"):
                    self.open_file_location(output_path)
            
            self.root.after(0, enable_buttons)
                
        except Exception as e:
            error_msg = (
                f"Error creating GIF: {e}\n"
                f"Tip: Try a lower quality setting or ensure sufficient disk space."
            )
            self.log_thread_safe(error_msg)
            
            # Re-enable buttons on error
            def enable_buttons_error():
                self.create_button.config(state="normal")
                self.record_button.config(state="normal")
                self.clear_button.config(state="normal")
                messagebox.showerror("Error", f"Failed to create GIF: {e}\n\nTip: Try a lower quality setting or check disk space.")
            
            self.root.after(0, enable_buttons_error)

def main() -> None:
    """Main entry point for the application."""
    # Check if required packages are installed
    try:
        import pyautogui
        import PIL
    except ImportError as e:
        print(f"Missing required package: {e}")
        print("Please install required packages:")
        print("pip install pyautogui pillow")
        input("Press Enter to exit...")
        return
        
    # Create and run the application
    root = tk.Tk()
    app = GIFMaker(root)
    
    # Center the window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()
