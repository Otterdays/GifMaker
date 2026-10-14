"""Frame editor with command-pattern undo/redo for GIF frame manipulation.

Pure-logic module (no tkinter dependency) managing the frame list, per-frame
durations, and edit history. Designed to be tested without a GUI.
"""

from __future__ import annotations

from typing import List, Optional

from PIL import Image


# ---------------------------------------------------------------------------
# Editor State
# ---------------------------------------------------------------------------


class EditorState:
    """Mutable state: frames + per-frame durations + selected index."""

    def __init__(self) -> None:
        self.frames: List[Image.Image] = []
        self.durations: List[int] = []  # per-frame duration in ms
        self.selected_index: int = 0

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    def clamp_selection(self) -> None:
        """Ensure selected_index is within bounds."""
        if self.frames:
            self.selected_index = max(0, min(self.selected_index, len(self.frames) - 1))
        else:
            self.selected_index = 0


# ---------------------------------------------------------------------------
# Command base
# ---------------------------------------------------------------------------


class EditCommand:
    """Base class for undoable editing operations."""

    def redo(self, state: EditorState) -> None:
        raise NotImplementedError

    def undo(self, state: EditorState) -> None:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Concrete commands
# ---------------------------------------------------------------------------


class DeleteFrame(EditCommand):
    """Delete a frame at a specific index."""

    def __init__(self, index: int, frame: Image.Image, duration: int) -> None:
        self._index = index
        self._frame = frame
        self._duration = duration

    def redo(self, state: EditorState) -> None:
        if 0 <= self._index < len(state.frames):
            state.frames.pop(self._index)
            state.durations.pop(self._index)
        state.clamp_selection()

    def undo(self, state: EditorState) -> None:
        idx = min(self._index, len(state.frames))
        state.frames.insert(idx, self._frame)
        state.durations.insert(idx, self._duration)
        state.selected_index = idx


class DuplicateFrame(EditCommand):
    """Insert a copy of the frame at index right after it."""

    def __init__(self, index: int) -> None:
        self._index = index
        self._copy: Optional[Image.Image] = None

    def redo(self, state: EditorState) -> None:
        original = state.frames[self._index]
        self._copy = original.copy()
        insert_at = self._index + 1
        state.frames.insert(insert_at, self._copy)
        state.durations.insert(insert_at, state.durations[self._index])
        state.selected_index = insert_at

    def undo(self, state: EditorState) -> None:
        insert_at = self._index + 1
        if insert_at < len(state.frames):
            removed = state.frames.pop(insert_at)
            state.durations.pop(insert_at)
            if hasattr(removed, "close"):
                removed.close()
        state.selected_index = self._index


class MoveFrame(EditCommand):
    """Move a frame from one index to another (swap with neighbor)."""

    def __init__(self, from_idx: int, to_idx: int) -> None:
        self._from = from_idx
        self._to = to_idx

    def redo(self, state: EditorState) -> None:
        frame = state.frames.pop(self._from)
        duration = state.durations.pop(self._from)
        state.frames.insert(self._to, frame)
        state.durations.insert(self._to, duration)
        state.selected_index = self._to

    def undo(self, state: EditorState) -> None:
        frame = state.frames.pop(self._to)
        duration = state.durations.pop(self._to)
        state.frames.insert(self._from, frame)
        state.durations.insert(self._from, duration)
        state.selected_index = self._from


class TransformFrame(EditCommand):
    """Apply a PIL transpose operation to a single frame."""

    def __init__(self, index: int, method: int) -> None:
        """
        Args:
            index: Frame index to transform.
            method: One of Image.Transpose.* constants (ROTATE_90, etc.)
        """
        self._index = index
        self._method = method
        self._original: Optional[Image.Image] = None

    def redo(self, state: EditorState) -> None:
        self._original = state.frames[self._index]
        state.frames[self._index] = self._original.transpose(self._method)

    def undo(self, state: EditorState) -> None:
        if self._original is not None:
            # Close the transformed copy to free memory
            new_frame = state.frames[self._index]
            if new_frame is not self._original and hasattr(new_frame, "close"):
                new_frame.close()
            state.frames[self._index] = self._original


class TrimStart(EditCommand):
    """Remove N frames from the beginning."""

    def __init__(self, count: int) -> None:
        self._count = count
        self._saved_frames: List[Image.Image] = []
        self._saved_durations: List[int] = []

    def redo(self, state: EditorState) -> None:
        n = min(self._count, len(state.frames))
        self._saved_frames = state.frames[:n]
        self._saved_durations = state.durations[:n]
        state.frames = state.frames[n:]
        state.durations = state.durations[n:]
        state.selected_index = 0

    def undo(self, state: EditorState) -> None:
        state.frames = self._saved_frames + state.frames
        state.durations = self._saved_durations + state.durations
        state.selected_index = min(self._count, len(state.frames) - 1)


class TrimEnd(EditCommand):
    """Remove N frames from the end."""

    def __init__(self, count: int) -> None:
        self._count = count
        self._saved_frames: List[Image.Image] = []
        self._saved_durations: List[int] = []

    def redo(self, state: EditorState) -> None:
        n = min(self._count, len(state.frames))
        if n > 0:
            self._saved_frames = state.frames[-n:]
            self._saved_durations = state.durations[-n:]
            state.frames = state.frames[:-n]
            state.durations = state.durations[:-n]
        state.clamp_selection()

    def undo(self, state: EditorState) -> None:
        state.frames = state.frames + self._saved_frames
        state.durations = state.durations + self._saved_durations
        state.clamp_selection()


class SetDuration(EditCommand):
    """Change duration for a specific frame."""

    def __init__(self, index: int, new_ms: int) -> None:
        self._index = index
        self._new_ms = new_ms
        self._old_ms: int = 0

    def redo(self, state: EditorState) -> None:
        if 0 <= self._index < len(state.durations):
            self._old_ms = state.durations[self._index]
            state.durations[self._index] = self._new_ms

    def undo(self, state: EditorState) -> None:
        if 0 <= self._index < len(state.durations):
            state.durations[self._index] = self._old_ms


class SetAllDurations(EditCommand):
    """Set uniform duration for all frames."""

    def __init__(self, ms: int) -> None:
        self._new_ms = ms
        self._old_durations: List[int] = []

    def redo(self, state: EditorState) -> None:
        self._old_durations = list(state.durations)
        state.durations = [self._new_ms] * len(state.frames)

    def undo(self, state: EditorState) -> None:
        state.durations = self._old_durations


# ---------------------------------------------------------------------------
# Frame Editor (dispatcher)
# ---------------------------------------------------------------------------


class FrameEditor:
    """Command dispatcher with bounded undo/redo history."""

    MAX_HISTORY = 40

    def __init__(self) -> None:
        self.state = EditorState()
        self._undo_stack: List[EditCommand] = []
        self._redo_stack: List[EditCommand] = []

    # --- Public state queries ---

    @property
    def frame_count(self) -> int:
        return self.state.frame_count

    @property
    def selected_index(self) -> int:
        return self.state.selected_index

    def selected_frame(self) -> Optional[Image.Image]:
        if 0 <= self.state.selected_index < len(self.state.frames):
            return self.state.frames[self.state.selected_index]
        return None

    def selected_duration(self) -> Optional[int]:
        idx = self.state.selected_index
        if 0 <= idx < len(self.state.durations):
            return self.state.durations[idx]
        return None

    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    # --- Load / reset ---

    def load_frames(self, frames: List[Image.Image], default_ms: int) -> None:
        """Replace editor contents with a new frame list (resets history)."""
        self.state.frames = list(frames)
        self.state.durations = [default_ms] * len(frames)
        self.state.selected_index = 0
        self._undo_stack.clear()
        self._redo_stack.clear()

    def get_frames(self) -> List[Image.Image]:
        """Return the current frame list (reference, not copy)."""
        return self.state.frames

    def get_durations(self) -> List[int]:
        """Return per-frame durations."""
        return list(self.state.durations)

    def reset(self) -> None:
        """Clear all state."""
        self.state = EditorState()
        self._undo_stack.clear()
        self._redo_stack.clear()

    # --- Editing operations ---

    def select(self, index: int) -> None:
        """Change the selected frame index (not undoable)."""
        self.state.selected_index = index
        self.state.clamp_selection()

    def delete_selected(self) -> bool:
        """Delete the currently selected frame. Returns True if successful."""
        idx = self.state.selected_index
        if idx < 0 or idx >= len(self.state.frames):
            return False
        frame = self.state.frames[idx]
        duration = self.state.durations[idx]
        cmd = DeleteFrame(idx, frame, duration)
        self._execute(cmd)
        return True

    def duplicate_selected(self) -> bool:
        """Duplicate the selected frame (insert copy after)."""
        idx = self.state.selected_index
        if idx < 0 or idx >= len(self.state.frames):
            return False
        cmd = DuplicateFrame(idx)
        self._execute(cmd)
        return True

    def move_selected(self, direction: int) -> bool:
        """Move selected frame left (-1) or right (+1). Returns True if moved."""
        idx = self.state.selected_index
        target = idx + direction
        if idx < 0 or target < 0 or target >= len(self.state.frames):
            return False
        cmd = MoveFrame(idx, target)
        self._execute(cmd)
        return True

    def rotate_selected(self, degrees: int) -> bool:
        """Rotate selected frame by 90/180/270 degrees. Returns True if applied."""
        idx = self.state.selected_index
        if idx < 0 or idx >= len(self.state.frames):
            return False
        transpose_map = {
            90: Image.Transpose.ROTATE_90,
            180: Image.Transpose.ROTATE_180,
            270: Image.Transpose.ROTATE_270,
        }
        method = transpose_map.get(degrees)
        if method is None:
            return False
        cmd = TransformFrame(idx, method)
        self._execute(cmd)
        return True

    def flip_selected(self, horizontal: bool) -> bool:
        """Flip selected frame horizontally or vertically. Returns True if applied."""
        idx = self.state.selected_index
        if idx < 0 or idx >= len(self.state.frames):
            return False
        method = Image.Transpose.FLIP_LEFT_RIGHT if horizontal else Image.Transpose.FLIP_TOP_BOTTOM
        cmd = TransformFrame(idx, method)
        self._execute(cmd)
        return True

    def trim_start(self, count: int) -> bool:
        """Remove count frames from the beginning. Returns True if any removed."""
        if count <= 0 or not self.state.frames:
            return False
        cmd = TrimStart(count)
        self._execute(cmd)
        return True

    def trim_end(self, count: int) -> bool:
        """Remove count frames from the end. Returns True if any removed."""
        if count <= 0 or not self.state.frames:
            return False
        cmd = TrimEnd(count)
        self._execute(cmd)
        return True

    def set_selected_duration(self, ms: int) -> bool:
        """Set duration for the selected frame."""
        idx = self.state.selected_index
        if idx < 0 or idx >= len(self.state.frames):
            return False
        ms = max(20, ms)  # minimum 20ms
        cmd = SetDuration(idx, ms)
        self._execute(cmd)
        return True

    def set_all_durations(self, ms: int) -> bool:
        """Set uniform duration for all frames."""
        if not self.state.frames:
            return False
        ms = max(20, ms)
        cmd = SetAllDurations(ms)
        self._execute(cmd)
        return True

    # --- Undo / Redo ---

    def undo(self) -> bool:
        """Undo the last command. Returns True if something was undone."""
        if not self._undo_stack:
            return False
        cmd = self._undo_stack.pop()
        cmd.undo(self.state)
        self._redo_stack.append(cmd)
        return True

    def redo(self) -> bool:
        """Redo the last undone command. Returns True if something was redone."""
        if not self._redo_stack:
            return False
        cmd = self._redo_stack.pop()
        cmd.redo(self.state)
        self._undo_stack.append(cmd)
        return True

    # --- Internal ---

    def _execute(self, command: EditCommand) -> None:
        """Apply command and push to undo stack, clearing redo stack."""
        command.redo(self.state)
        self._undo_stack.append(command)
        self._redo_stack.clear()
        # Bound history
        if len(self._undo_stack) > self.MAX_HISTORY:
            self._undo_stack.pop(0)
