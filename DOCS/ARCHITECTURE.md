<!-- PRESERVATION RULE: Never delete or replace content. Append or annotate only. -->

# Gif-Maker Architecture Documentation

*Version 1.0.3 - 2025-03-19* [AMENDED: package structure]

## Overview

Gif-Maker is a Python GUI application built with tkinter, pyautogui, and Pillow. As of v1.0.3 it uses a modular package structure (`gif_maker/` with gui/, core/, utils/). This document describes the system architecture, component design, data flow, and technical decisions.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Component Design](#component-design)
3. [Data Flow](#data-flow)
4. [Threading Model](#threading-model)
5. [Image Processing Pipeline](#image-processing-pipeline)
6. [UI Architecture](#ui-architecture)
7. [Constants and Configuration](#constants-and-configuration)
8. [Error Handling Strategy](#error-handling-strategy)
9. [Memory Management](#memory-management)

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Gif-Maker Application                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐         ┌──────────────┐            │
│  │   GUI Layer  │─────────▶│  Core Logic  │            │
│  │  (tkinter)   │         │  (GIFMaker)  │            │
│  └──────────────┘         └──────────────┘            │
│         │                        │                      │
│         │                        │                      │
│         ▼                        ▼                      │
│  ┌──────────────┐         ┌──────────────┐            │
│  │   UI Events  │         │  Background   │            │
│  │  & Updates  │         │   Threads     │            │
│  └──────────────┘         └──────────────┘            │
│                                                          │
│         │                        │                      │
│         └──────────┬─────────────┘                      │
│                    ▼                                    │
│         ┌──────────────────────┐                       │
│         │  External Libraries   │                       │
│         │  (pyautogui, PIL)    │                       │
│         └──────────────────────┘                       │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Architecture Principles

1. **Package Design** [AMENDED 2025-03-19]: Modular `gif_maker/` package (gui/, core/, utils/) for testability and maintainability
2. **Class-Based**: Object-oriented design with clear separation of concerns
3. **Event-Driven**: GUI responds to user events and background operations
4. **Thread-Safe**: Proper synchronization for concurrent operations
5. **Type-Safe**: Comprehensive type hints for better IDE support

---

## Component Design

### GIFMaker Class

The main application class that encapsulates all functionality.

```python
class GIFMaker:
    # State Management
    - screenshots: List[Image.Image]
    - is_recording: bool
    - region: Optional[Tuple[int, int, int, int]]
    
    # Thread Safety
    - _lock: threading.Lock
    - _recording_active: bool
    
    # UI Components
    - root: tk.Tk
    - record_button: tk.Button
    - create_button: tk.Button
    - preview_label: tk.Label
    
    # Methods (grouped by functionality)
    - UI Setup
    - Region Selection
    - Recording
    - GIF Creation
    - Preview Management
```

### Component Responsibilities

#### 1. UI Setup (`create_widgets`, `setup_preview_panel`)
- Creates and configures all GUI widgets
- Sets up layout and styling
- Initializes keyboard shortcuts

#### 2. Region Selection (`select_region`, `select_fullscreen`, `select_browser_size`)
- Visual region selection with overlay
- Multiple selection methods
- Validation and feedback

#### 3. Recording (`start_recording`, `record_screenshots`, `stop_recording`)
- Screenshot capture loop
- Progress tracking
- Thread-safe operations

#### 4. GIF Creation (`create_gif`, `create_gif_worker`)
- Image processing pipeline
- Quality optimization
- Background processing

#### 5. Preview Management (`refresh_preview`, `update_preview_display`)
- Thumbnail generation
- Image navigation
- Memory-efficient display

---

## Data Flow

### Recording Workflow

```
User Action
    │
    ▼
[Start Recording Button]
    │
    ▼
validate_settings() ──┐
    │                  │
    ▼                  │
start_recording()      │
    │                  │
    ▼                  │
Hide Window            │
    │                  │
    ▼                  │
Start Thread ─────────┘
    │
    ▼
record_screenshots() (Background Thread)
    │
    ├─▶ Capture Screenshot
    │       │
    │       ▼
    │   Add to screenshots[]
    │       │
    │       ▼
    │   Update Progress
    │       │
    │       ▼
    │   Refresh Preview
    │
    └─▶ Repeat until count reached
            │
            ▼
        Show Window
            │
            ▼
        stop_recording()
```

### GIF Creation Workflow

```
User Action
    │
    ▼
[Create GIF Button]
    │
    ▼
create_gif()
    │
    ├─▶ Validate screenshots exist
    ├─▶ Show file size estimation
    ├─▶ Disable UI buttons
    │
    ▼
Start Background Thread
    │
    ▼
create_gif_worker() (Background Thread)
    │
    ├─▶ Get output path
    ├─▶ Determine frame duration
    ├─▶ Process images by quality
    │   │
    │   ├─▶ MAX: Advanced quantization
    │   ├─▶ High: Adaptive palette
    │   ├─▶ Medium: Standard processing
    │   └─▶ Low: Basic processing
    │
    ├─▶ Save GIF with settings
    │
    └─▶ Update UI (thread-safe)
            │
            ▼
        Enable buttons
        Show success dialog
```

### Region Selection Workflow

```
User Action
    │
    ▼
[Select Region Button]
    │
    ▼
select_region()
    │
    ├─▶ Create full-screen overlay
    ├─▶ Setup canvas for drawing
    ├─▶ Bind mouse events
    │
    ▼
User Interaction
    │
    ├─▶ Mouse Down → start_selection()
    ├─▶ Mouse Drag → update_selection()
    └─▶ Mouse Up → end_selection()
            │
            ▼
        Validate selection
            │
            ├─▶ Too small → Show error
            └─▶ Valid → Save region
                    │
                    ▼
                Close overlay
```

---

## Threading Model

### Thread Architecture

```
Main Thread (UI Thread)
    │
    ├─▶ User Interactions
    ├─▶ UI Updates
    └─▶ Event Loop
            │
            ├─▶ Recording Thread (daemon)
            │       │
            │       └─▶ record_screenshots()
            │
            └─▶ GIF Creation Thread (daemon)
                    │
                    └─▶ create_gif_worker()
```

### Thread Safety Mechanisms

#### 1. Lock-Based Synchronization

```python
class GIFMaker:
    def __init__(self, root: tk.Tk) -> None:
        self._lock = threading.Lock()
        self._recording_active = False
    
    def start_recording(self) -> None:
        with self._lock:
            if self._recording_active:
                return  # Prevent concurrent recording
            self._recording_active = True
```

#### 2. Thread-Safe UI Updates

```python
def log_thread_safe(self, message: str) -> None:
    """Update UI from background thread."""
    def update_log():
        self.log(message)
    self.root.after(0, update_log)  # Schedule on main thread
```

#### 3. Daemon Threads

```python
self.recording_thread = threading.Thread(target=self.record_screenshots)
self.recording_thread.daemon = True  # Exit when main thread exits
self.recording_thread.start()
```

### Thread Communication

- **State Flags**: `is_recording`, `_recording_active`
- **Shared Data**: `screenshots` list (accessed with locks)
- **UI Updates**: Via `root.after()` for thread safety

---

## Image Processing Pipeline

### Screenshot Capture

```
pyautogui.screenshot(region=region)
    │
    ▼
PIL Image Object
    │
    ▼
Add to screenshots[] list
    │
    ▼
Create thumbnail for preview
    │
    ▼
Store in preview_images[]
```

### GIF Creation Pipeline

```
screenshots[] (List of PIL Images)
    │
    ▼
Convert to RGB (if needed)
    │
    ▼
Quality-Specific Processing
    │
    ├─▶ MAX Quality
    │   │
    │   ├─▶ UnsharpMask filter
    │   ├─▶ Quantize (256 colors, MEDIANCUT)
    │   └─▶ Convert back to RGB
    │
    ├─▶ High Quality
    │   │
    │   ├─▶ MedianFilter (noise reduction)
    │   ├─▶ Quantize (256 colors, MEDIANCUT)
    │   └─▶ Convert back to RGB
    │
    └─▶ Medium/Low Quality
        │
        └─▶ Direct processing
            │
            ▼
Save as GIF
    │
    ├─▶ First frame: save_all=True
    ├─▶ Remaining frames: append_images
    ├─▶ Duration: Based on speed setting
    ├─▶ Quality settings: Based on quality level
    └─▶ Dithering: Floyd-Steinberg for gradients
```

### Quality Settings

| Quality | Processing | Palette | Dithering | Use Case |
|---------|-----------|---------|-----------|----------|
| MAX | Advanced quantization + sharpening | Adaptive | Yes | Professional demos |
| High | Noise reduction + quantization | Adaptive | Yes | Smooth gradients |
| Medium | Standard processing | Web | Yes | General use |
| Low | Basic processing | Web | No | Quick demos |

---

## UI Architecture

### Layout Structure

```
root (tk.Tk)
│
├─▶ Title Label
│
├─▶ Main Frame
│   │
│   ├─▶ Left Panel
│   │   │
│   │   ├─▶ Region Selection Frame
│   │   ├─▶ Settings Frame
│   │   ├─▶ Control Buttons Frame
│   │   └─▶ Status Frame
│   │       ├─▶ Count Display
│   │       ├─▶ Progress Bar
│   │       └─▶ Status Text
│   │
│   └─▶ Right Panel
│       │
│       └─▶ Preview Frame
│           ├─▶ Preview Label
│           ├─▶ Navigation Controls
│           ├─▶ Image Info
│           └─▶ Action Buttons
```

### Widget Hierarchy

- **Frames**: Organize related widgets
- **LabelFrames**: Group with titles
- **Buttons**: Actions and navigation
- **Entries**: User input
- **Comboboxes**: Dropdown selections
- **Text**: Status logging
- **Progressbar**: Progress indication

### Event Handling

- **Button Clicks**: Direct method calls
- **Keyboard Shortcuts**: Bound to root window
- **Mouse Events**: Canvas bindings for region selection
- **Thread Events**: Scheduled via `root.after()`

---

## Constants and Configuration

### Constant Categories

#### 1. UI Constants
- Window dimensions
- Minimum sizes
- Preview sizes
- Region validation

#### 2. Color Scheme
- Background colors
- Accent colors
- Text colors
- Consistent theming

#### 3. Timing Constants
- Delays
- Interval ranges
- Frame durations

### Constant Usage

All magic numbers and hard-coded values are replaced with named constants:

```python
# Instead of
if width < 100:
    pass

# Use
if width < MIN_REGION_SIZE:
    pass
```

Benefits:
- Single source of truth
- Easy theming
- Better maintainability
- Self-documenting code

---

## Error Handling Strategy

### Error Handling Layers

1. **Input Validation**: Validate before processing
2. **Try-Except Blocks**: Catch specific exceptions
3. **User Feedback**: Actionable error messages
4. **Graceful Degradation**: Fallback when possible

### Error Message Pattern

```python
error_msg = (
    f"Error description: {e}\n"
    f"Tip: Actionable guidance for user"
)
```

### Error Recovery

- **Validation Errors**: Show message, don't proceed
- **Processing Errors**: Log error, show message, re-enable UI
- **Thread Errors**: Catch in thread, update UI safely

---

## Memory Management

### Image Storage

- **Screenshots**: Full-resolution PIL Images in list
- **Preview Images**: Thumbnails (350x250) in separate list
- **Lazy Loading**: Thumbnails created only when needed

### Memory Cleanup

```python
def clear_screenshots(self) -> None:
    # Explicitly close images
    for img in self.screenshots:
        if hasattr(img, 'close'):
            img.close()
    
    # Clear lists
    self.screenshots.clear()
    self.preview_images.clear()
```

### Memory Optimization

- **Thumbnails**: Smaller preview images reduce memory
- **Explicit Cleanup**: Close images when deleted
- **Lazy Preview**: Only create thumbnails when needed

---

## Design Decisions

### Why Single-File Architecture? [AMENDED 2025-03-19: Now package-based]

- **Simplicity**: Easy to understand and maintain *(historical; v1.0.3 uses package for testability)*
- **Portability**: Single file to distribute *(now: `python -m gif_maker` or `gif-maker` entrypoint)*
- **No Dependencies**: Beyond standard libraries
- **Quick Development**: No module management overhead *(package adds minimal overhead; tests justify it)*

### Why tkinter?

- **Built-in**: No external dependencies
- **Cross-platform**: Works on Windows, macOS, Linux
- **Lightweight**: Fast startup, low overhead
- **Sufficient**: Meets all UI requirements

### Why Threading?

- **Responsive UI**: Background operations don't freeze interface
- **User Experience**: Users can see progress and cancel
- **Professional Feel**: Smooth, non-blocking operations

### Why Type Hints?

- **IDE Support**: Better autocomplete and error detection
- **Documentation**: Self-documenting code
- **Maintainability**: Easier to understand and modify
- **Future-Proof**: Prepares for potential type checking

---

## Performance Considerations

### Optimization Strategies

1. **Lazy Preview Loading**: Thumbnails created on-demand
2. **Progress Updates**: Reduced frequency for MAX quality
3. **Thread Safety**: Minimal locking overhead
4. **Memory Management**: Explicit cleanup of large images

### Performance Metrics

- **Startup Time**: < 2 seconds
- **Screenshot Capture**: Real-time (limited by interval)
- **GIF Creation**: 2-30 seconds (depends on quality and frame count)
- **Memory Usage**: < 100MB for typical usage

---

## Future Architecture Considerations

### Package Structure [AMENDED 2025-03-19 - Implemented]

Current layout (as of v1.0.3):

```
gif_maker/
├── __init__.py          # Re-exports main, GIFMaker, testable helpers
├── __main__.py          # python -m gif_maker
├── main.py              # Entry point
├── gui/
│   └── main_window.py   # GIFMaker class, region selection, preview
├── core/
│   ├── constants.py     # Shared constants
│   ├── quality_engine.py  # Validation, quality/speed mapping
│   └── gif_creator.py   # GIF encoding
└── utils/
    └── image_utils.py   # Thumbnail generation
```

### Previous: Potential Modularization (pre-v1.0.3)

If the codebase grows, consider splitting into: `gif_maker/gui/main_window.py`, `preview_panel.py`, `region_selector.py`, `core/recorder.py`, `gif_creator.py`, `quality_engine.py`, `utils/image_utils.py`. *[Note: Package structure implemented in v1.0.3; preview_panel and region_selector remain in main_window for now.]*

### Current Status

- **Package design** implemented; tests in `tests/`; `python -m pytest tests/` for regression

---

## References

- [tkinter Documentation](https://docs.python.org/3/library/tkinter.html)
- [Pillow (PIL) Documentation](https://pillow.readthedocs.io/)
- [pyautogui Documentation](https://pyautogui.readthedocs.io/)
- [Python Threading Documentation](https://docs.python.org/3/library/threading.html)

---

**Last Updated**: 2025-03-19  
**Version**: 1.0.3  
**Maintainer**: AfyKirby1
