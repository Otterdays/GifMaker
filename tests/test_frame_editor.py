"""Tests for gif_maker.core.frame_editor module."""

from PIL import Image

from gif_maker.core.frame_editor import (
    EditorState,
    FrameEditor,
)


def _make_frames(n: int, size: tuple = (100, 80)) -> list:
    """Create n small test frames with distinct colors."""
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
              (255, 0, 255), (0, 255, 255), (128, 128, 128), (64, 64, 64),
              (192, 64, 32), (32, 192, 64)]
    frames = []
    for i in range(n):
        img = Image.new("RGB", size, color=colors[i % len(colors)])
        frames.append(img)
    return frames


class TestLoadFrames:
    def test_load_sets_state(self):
        editor = FrameEditor()
        frames = _make_frames(5)
        editor.load_frames(frames, default_ms=200)
        assert editor.frame_count == 5
        assert editor.selected_index == 0
        assert editor.get_durations() == [200] * 5

    def test_load_resets_history(self):
        editor = FrameEditor()
        editor.load_frames(_make_frames(3), 100)
        editor.delete_selected()
        assert editor.can_undo()
        editor.load_frames(_make_frames(2), 150)
        assert not editor.can_undo()
        assert not editor.can_redo()

    def test_reset_clears_all(self):
        editor = FrameEditor()
        editor.load_frames(_make_frames(4), 200)
        editor.reset()
        assert editor.frame_count == 0
        assert editor.selected_index == 0
        assert not editor.can_undo()


class TestDeleteSelected:
    def test_delete_removes_correct_frame(self):
        editor = FrameEditor()
        frames = _make_frames(5)
        editor.load_frames(frames, 200)
        editor.select(2)
        editor.delete_selected()
        assert editor.frame_count == 4
        # After deleting index 2 (blue), index 2 should be what was index 3 (yellow)
        remaining = editor.get_frames()
        assert remaining[2].getpixel((0, 0)) == (255, 255, 0)

    def test_delete_last_adjusts_selection(self):
        editor = FrameEditor()
        editor.load_frames(_make_frames(3), 200)
        editor.select(2)
        editor.delete_selected()
        assert editor.frame_count == 2
        assert editor.selected_index <= 1

    def test_delete_empty_returns_false(self):
        editor = FrameEditor()
        assert editor.delete_selected() is False


class TestDuplicateSelected:
    def test_duplicate_inserts_after(self):
        editor = FrameEditor()
        editor.load_frames(_make_frames(3), 200)
        editor.select(1)
        editor.duplicate_selected()
        assert editor.frame_count == 4
        # Index 1 and 2 should be the same (both green)
        frames = editor.get_frames()
        assert frames[1].getpixel((0, 0)) == frames[2].getpixel((0, 0))

    def test_duplicate_updates_selection(self):
        editor = FrameEditor()
        editor.load_frames(_make_frames(2), 200)
        editor.select(0)
        editor.duplicate_selected()
        assert editor.selected_index == 1  # now on the duplicate


class TestMoveSelected:
    def test_move_right(self):
        editor = FrameEditor()
        editor.load_frames(_make_frames(4), 200)
        editor.select(1)  # green
        editor.move_selected(1)  # move right -> swap with index 2 (blue)
        frames = editor.get_frames()
        assert frames[1].getpixel((0, 0)) == (0, 0, 255)  # blue moved left
        assert frames[2].getpixel((0, 0)) == (0, 255, 0)  # green moved right

    def test_move_left(self):
        editor = FrameEditor()
        editor.load_frames(_make_frames(3), 200)
        editor.select(1)
        editor.move_selected(-1)
        frames = editor.get_frames()
        assert frames[0].getpixel((0, 0)) == (0, 255, 0)  # green now first

    def test_move_out_of_bounds_returns_false(self):
        editor = FrameEditor()
        editor.load_frames(_make_frames(2), 200)
        editor.select(0)
        assert editor.move_selected(-1) is False
        editor.select(1)
        assert editor.move_selected(1) is False


class TestRotateSelected:
    def test_rotate_90_changes_dimensions(self):
        editor = FrameEditor()
        frames = _make_frames(2, size=(100, 60))
        editor.load_frames(frames, 200)
        editor.select(0)
        editor.rotate_selected(90)
        frame = editor.selected_frame()
        assert frame is not None
        # After 90 rotation, width and height swap
        assert frame.size == (60, 100)

    def test_rotate_180_preserves_dimensions(self):
        editor = FrameEditor()
        frames = _make_frames(1, size=(100, 60))
        editor.load_frames(frames, 200)
        editor.rotate_selected(180)
        frame = editor.selected_frame()
        assert frame.size == (100, 60)

    def test_rotate_invalid_degrees_returns_false(self):
        editor = FrameEditor()
        editor.load_frames(_make_frames(2), 200)
        assert editor.rotate_selected(45) is False


class TestFlipSelected:
    def test_flip_horizontal(self):
        editor = FrameEditor()
        # Create a frame with a distinctive pattern (left half red, right half blue)
        img = Image.new("RGB", (100, 50), (255, 0, 0))
        for x in range(50, 100):
            for y in range(50):
                img.putpixel((x, y), (0, 0, 255))
        editor.load_frames([img], 200)
        editor.flip_selected(horizontal=True)
        flipped = editor.selected_frame()
        assert flipped.getpixel((0, 25)) == (0, 0, 255)  # was right, now left

    def test_flip_vertical(self):
        editor = FrameEditor()
        img = Image.new("RGB", (50, 100), (255, 0, 0))
        for x in range(50):
            for y in range(50, 100):
                img.putpixel((x, y), (0, 255, 0))
        editor.load_frames([img], 200)
        editor.flip_selected(horizontal=False)
        flipped = editor.selected_frame()
        assert flipped.getpixel((25, 0)) == (0, 255, 0)  # was bottom, now top


class TestTrim:
    def test_trim_start(self):
        editor = FrameEditor()
        editor.load_frames(_make_frames(6), 200)
        editor.trim_start(2)
        assert editor.frame_count == 4
        # First frame should now be what was index 2 (blue)
        assert editor.get_frames()[0].getpixel((0, 0)) == (0, 0, 255)

    def test_trim_end(self):
        editor = FrameEditor()
        editor.load_frames(_make_frames(6), 200)
        editor.trim_end(2)
        assert editor.frame_count == 4

    def test_trim_more_than_available(self):
        editor = FrameEditor()
        editor.load_frames(_make_frames(3), 200)
        editor.trim_start(10)
        assert editor.frame_count == 0


class TestDuration:
    def test_set_selected_duration(self):
        editor = FrameEditor()
        editor.load_frames(_make_frames(3), 200)
        editor.select(1)
        editor.set_selected_duration(500)
        durations = editor.get_durations()
        assert durations[1] == 500
        assert durations[0] == 200

    def test_set_all_durations(self):
        editor = FrameEditor()
        editor.load_frames(_make_frames(4), 200)
        editor.set_all_durations(300)
        assert editor.get_durations() == [300, 300, 300, 300]

    def test_minimum_duration(self):
        editor = FrameEditor()
        editor.load_frames(_make_frames(2), 200)
        editor.set_selected_duration(5)  # below minimum
        assert editor.selected_duration() == 20  # clamped to min


class TestUndoRedo:
    def test_undo_delete(self):
        editor = FrameEditor()
        editor.load_frames(_make_frames(5), 200)
        editor.select(2)
        editor.delete_selected()
        assert editor.frame_count == 4
        editor.undo()
        assert editor.frame_count == 5

    def test_redo_after_undo(self):
        editor = FrameEditor()
        editor.load_frames(_make_frames(3), 200)
        editor.delete_selected()
        editor.undo()
        editor.redo()
        assert editor.frame_count == 2

    def test_new_action_clears_redo(self):
        editor = FrameEditor()
        editor.load_frames(_make_frames(4), 200)
        editor.delete_selected()
        editor.undo()
        # Now do a different action
        editor.duplicate_selected()
        assert not editor.can_redo()

    def test_undo_empty_returns_false(self):
        editor = FrameEditor()
        assert editor.undo() is False

    def test_redo_empty_returns_false(self):
        editor = FrameEditor()
        assert editor.redo() is False

    def test_undo_rotate_restores_original(self):
        editor = FrameEditor()
        frames = _make_frames(1, size=(100, 60))
        editor.load_frames(frames, 200)
        editor.rotate_selected(90)
        assert editor.selected_frame().size == (60, 100)
        editor.undo()
        assert editor.selected_frame().size == (100, 60)

    def test_undo_transform_reverts_to_original(self):
        editor = FrameEditor()
        frames = _make_frames(1, size=(80, 50))
        editor.load_frames(frames, 200)
        original = editor.selected_frame()
        original_color = original.getpixel((0, 0))
        editor.rotate_selected(180)
        editor.undo()
        # Should be back to the original
        restored = editor.selected_frame()
        assert restored.getpixel((0, 0)) == original_color


class TestHistoryBound:
    def test_max_history(self):
        editor = FrameEditor()
        editor.load_frames(_make_frames(50), 200)
        # Perform many operations (set duration is safe, doesn't shrink frames)
        for i in range(50):
            editor.set_all_durations(200 + i)
        # History should be capped
        assert len(editor._undo_stack) <= editor.MAX_HISTORY
