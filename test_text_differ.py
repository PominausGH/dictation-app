"""Tests for TextDiffer class."""
import pytest
from text_differ import TextDiffer


class TestTextDiffer:
    def test_initial_state_empty(self):
        differ = TextDiffer()
        assert differ.last_typed == ""

    def test_first_text_no_backspaces(self):
        differ = TextDiffer()
        backspaces, new_text = differ.calculate_diff("Hello")
        assert backspaces == 0
        assert new_text == "Hello"

    def test_append_only(self):
        differ = TextDiffer()
        differ.update("Hello")
        backspaces, new_text = differ.calculate_diff("Hello world")
        assert backspaces == 0
        assert new_text == " world"

    def test_correction_needed(self):
        differ = TextDiffer()
        differ.update("I want to go")
        backspaces, new_text = differ.calculate_diff("I wanted to go")
        # Common prefix is "I want", need to delete " to go" (6 chars)
        # Then type "ed to go"
        assert backspaces == 6
        assert new_text == "ed to go"

    def test_complete_replacement(self):
        differ = TextDiffer()
        differ.update("Hello")
        backspaces, new_text = differ.calculate_diff("Goodbye")
        assert backspaces == 5
        assert new_text == "Goodbye"

    def test_reset_clears_state(self):
        differ = TextDiffer()
        differ.update("Some text")
        differ.reset()
        assert differ.last_typed == ""

    def test_skip_large_correction(self):
        differ = TextDiffer(max_backspaces=20)
        differ.update("A" * 30)
        backspaces, new_text = differ.calculate_diff("B" * 30)
        # Should skip - return None to signal skip
        assert backspaces is None
        assert new_text is None

    def test_update_tracks_typed_text(self):
        differ = TextDiffer()
        differ.update("Hello")
        assert differ.last_typed == "Hello"
        differ.update("Hello world")
        assert differ.last_typed == "Hello world"
