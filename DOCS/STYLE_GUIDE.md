# Gif-Maker Style Guide

*Version 1.0.1 - December 2024*

## Overview

This style guide defines coding standards, conventions, and best practices for the Gif-Maker project. Following these guidelines ensures code consistency, maintainability, and readability.

## Table of Contents

1. [Python Style](#python-style)
2. [Naming Conventions](#naming-conventions)
3. [Code Organization](#code-organization)
4. [Type Hints](#type-hints)
5. [Documentation](#documentation)
6. [Error Handling](#error-handling)
7. [Constants](#constants)
8. [Thread Safety](#thread-safety)
9. [UI/UX Guidelines](#uiux-guidelines)

---

## Python Style

### General Principles

- **PEP 8 Compliance**: Follow PEP 8 style guide for Python code
- **Line Length**: Maximum 100 characters per line
- **Indentation**: Use 4 spaces (no tabs)
- **Imports**: Group imports in this order:
  1. Standard library
  2. Third-party packages
  3. Local application imports

### Import Organization

```python
# Standard library
import os
import sys
import threading
from datetime import datetime
from typing import Optional, Tuple, List

# Third-party
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import pyautogui

# Local (if any)
# (none currently - single file architecture)
```

---

## Naming Conventions

### Variables and Functions

- **snake_case** for variables and functions
- **Descriptive names** that clearly indicate purpose
- **Avoid abbreviations** unless widely understood

```python
# Good
screenshot_count = 10
current_preview_index = 0
def validate_settings() -> Tuple[bool, Optional[str]]:
    pass

# Bad
sc_cnt = 10
idx = 0
def val() -> Tuple[bool, Optional[str]]:
    pass
```

### Classes

- **PascalCase** for class names
- **Descriptive names** that indicate purpose

```python
# Good
class GIFMaker:
    pass

# Bad
class gif_maker:
    pass
class GM:
    pass
```

### Constants

- **SCREAMING_SNAKE_CASE** for module-level constants
- **Grouped by category** with clear section headers
- **Defined at top of file** after imports

```python
# UI Constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
MIN_WIDTH = 900

# Color Scheme
COLOR_BG_PRIMARY = '#2c3e50'
COLOR_ACCENT_RED = '#e74c3c'
```

### Private Attributes

- **Leading underscore** for private/internal attributes
- **Double underscore** only for name mangling (rarely needed)

```python
# Good
self._lock = threading.Lock()
self._recording_active = False

# Bad
self.lock = threading.Lock()
self.__recording_active = False  # Unnecessary name mangling
```

---

## Code Organization

### File Structure

```
gif_maker.py
├── Shebang and module docstring
├── Imports (grouped and sorted)
├── Constants (grouped by category)
├── Class definitions
│   ├── __init__ method
│   ├── Public methods
│   └── Private methods (if any)
└── Main function and entry point
```

### Method Ordering

Within a class, organize methods in this order:

1. `__init__` - Constructor
2. Public methods (alphabetical or logical grouping)
3. Private methods (prefixed with `_`)

### Logical Grouping

Group related methods together:

```python
class GIFMaker:
    # Initialization
    def __init__(self, root: tk.Tk) -> None:
        pass
    
    # UI Setup
    def create_widgets(self) -> None:
        pass
    def setup_preview_panel(self, parent: tk.Frame) -> None:
        pass
    def setup_keyboard_shortcuts(self) -> None:
        pass
    
    # Region Selection
    def select_region(self) -> None:
        pass
    def select_fullscreen(self) -> None:
        pass
    
    # Recording
    def start_recording(self) -> None:
        pass
    def record_screenshots(self) -> None:
        pass
```

---

## Type Hints

### Requirements

- **All function signatures** must include type hints
- **Return types** must be specified (use `None` for void functions)
- **Use `typing` module** for complex types

### Examples

```python
from typing import Optional, Tuple, List
from PIL import Image

# Simple types
def log(self, message: str) -> None:
    pass

# Optional types
def validate_settings(self) -> Tuple[bool, Optional[str]]:
    pass

# Collection types
def process_images(self, images: List[Image.Image]) -> List[Image.Image]:
    pass

# Instance variables
self.screenshots: List[Image.Image] = []
self.region: Optional[Tuple[int, int, int, int]] = None
```

### Type Hint Best Practices

- Use `Optional[T]` instead of `T | None` (for Python < 3.10 compatibility)
- Use `Tuple` for fixed-length tuples
- Use `List[T]` for lists (not `list[T]` for compatibility)
- Import types from `typing` module

---

## Documentation

### Docstring Style

- **Google-style docstrings** for all public methods
- **One-line docstrings** for simple methods
- **Multi-line docstrings** for complex methods

### Docstring Format

```python
def method_name(self, param1: str, param2: int) -> bool:
    """Brief one-line description.
    
    Longer description if needed. Explains what the method does,
    any important behavior, or context.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ExceptionType: When this exception is raised
    
    Note:
        Any important notes or warnings
    """
    pass
```

### Examples

```python
# Simple method
def center_window(self) -> None:
    """Center the window on the screen."""
    pass

# Complex method
def validate_settings(self) -> Tuple[bool, Optional[str]]:
    """Validate all user settings before recording.
    
    Checks screenshot count, interval, and region selection.
    Returns validation result and error message if invalid.
    
    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is None.
    """
    pass
```

### Comments

- **Comment WHY, not WHAT**: Code should be self-explanatory
- **Use comments** for complex logic, algorithms, or non-obvious behavior
- **Avoid obvious comments**: Don't comment what the code clearly shows

```python
# Good
# Use lower quality for better gradients (research-based optimization)
quality = 80

# Bad
# Set quality to 80
quality = 80
```

---

## Error Handling

### Exception Handling

- **Be specific**: Catch specific exceptions, not bare `except:`
- **Provide context**: Include helpful error messages
- **User-friendly messages**: Error messages should guide users

```python
# Good
try:
    count = int(self.count_var.get())
except ValueError:
    return False, "Screenshot count must be a valid number"

# Bad
try:
    count = int(self.count_var.get())
except:
    return False, "Error"
```

### Error Messages

- **Actionable**: Tell users what to do
- **Contextual**: Include relevant information
- **Friendly**: Avoid technical jargon when possible

```python
# Good
error_msg = (
    f"Error capturing screenshot {i+1}: {e}\n"
    f"Tip: Ensure the selected region is still visible and accessible."
)

# Bad
error_msg = f"Error: {e}"
```

---

## Constants

### Constant Organization

- **Group by category** with clear section headers
- **Use descriptive names** that indicate purpose
- **Define at module level** (top of file)
- **Use constants** instead of magic numbers

### Constant Categories

```python
# UI Constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
MIN_WIDTH = 900

# Color Scheme
COLOR_BG_PRIMARY = '#2c3e50'
COLOR_ACCENT_RED = '#e74c3c'

# Timing Constants
WINDOW_HIDE_DELAY = 0.5
MIN_INTERVAL = 0.1
MAX_INTERVAL = 60.0

# Frame Duration Constants (milliseconds)
FRAME_DURATION_SLOW = 333  # 3 FPS
FRAME_DURATION_NORMAL = 200  # 5 FPS
```

### Using Constants

```python
# Good
if width < MIN_REGION_SIZE or height < MIN_REGION_SIZE:
    return False

time.sleep(WINDOW_HIDE_DELAY)

# Bad
if width < 100 or height < 100:
    return False

time.sleep(0.5)
```

---

## Thread Safety

### Threading Guidelines

- **Use locks** for shared state access
- **Daemon threads** for background operations
- **Thread-safe UI updates** using `root.after()`

### Thread Safety Pattern

```python
class GIFMaker:
    def __init__(self, root: tk.Tk) -> None:
        # Thread safety
        self._lock = threading.Lock()
        self._recording_active = False
    
    def start_recording(self) -> None:
        with self._lock:
            if self._recording_active:
                return
            self._recording_active = True
        
        # Start thread
        self.recording_thread = threading.Thread(target=self.record_screenshots)
        self.recording_thread.daemon = True
        self.recording_thread.start()
    
    def record_screenshots(self) -> None:
        try:
            # Recording logic
            pass
        finally:
            with self._lock:
                self._recording_active = False
```

### UI Updates from Threads

```python
# Good - Thread-safe UI update
def log_thread_safe(self, message: str) -> None:
    def update_log():
        self.log(message)
    self.root.after(0, update_log)

# Bad - Direct UI update from thread
def log_thread_safe(self, message: str) -> None:
    self.log(message)  # Not thread-safe!
```

---

## UI/UX Guidelines

### Color Usage

- **Use constants** for all colors
- **Consistent color scheme** throughout application
- **Accessible contrast** ratios

```python
# Good
button = tk.Button(
    parent,
    bg=COLOR_ACCENT_RED,
    fg=COLOR_TEXT_WHITE
)

# Bad
button = tk.Button(
    parent,
    bg="#e74c3c",
    fg="white"
)
```

### Widget Organization

- **Logical grouping** of related widgets
- **Consistent spacing** using `padx` and `pady`
- **Clear labels** for all inputs

### User Feedback

- **Progress indicators** for long operations
- **Status messages** for all operations
- **Error messages** with actionable guidance
- **Confirmation dialogs** for destructive actions

---

## Code Quality Checklist

Before committing code, ensure:

- [ ] All methods have type hints
- [ ] All public methods have docstrings
- [ ] Constants are used instead of magic numbers
- [ ] Error handling is comprehensive
- [ ] Thread-safe operations use locks
- [ ] UI updates from threads use `root.after()`
- [ ] Code follows PEP 8 style guide
- [ ] No linter errors
- [ ] Comments explain WHY, not WHAT

---

## Examples

### Complete Method Example

```python
def validate_settings(self) -> Tuple[bool, Optional[str]]:
    """Validate all user settings before recording.
    
    Checks screenshot count, interval range, and region selection.
    Returns validation result and error message if invalid.
    
    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is None.
    """
    try:
        count = int(self.count_var.get())
        if count < MIN_SCREENSHOT_COUNT or count > MAX_SCREENSHOT_COUNT:
            return False, (
                f"Screenshot count must be between {MIN_SCREENSHOT_COUNT} "
                f"and {MAX_SCREENSHOT_COUNT}"
            )
        
        interval = float(self.interval_var.get())
        if interval < MIN_INTERVAL or interval > MAX_INTERVAL:
            return False, (
                f"Interval must be between {MIN_INTERVAL} and {MAX_INTERVAL} seconds"
            )
            
        if not self.region:
            return False, "Please select a region first"
            
        return True, None
    except ValueError as e:
        return False, f"Invalid input: {e}"
```

---

## References

- [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Python Typing Documentation](https://docs.python.org/3/library/typing.html)

---

**Last Updated**: December 2024  
**Version**: 1.0.1
