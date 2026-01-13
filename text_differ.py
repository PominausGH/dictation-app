"""TextDiffer: Calculate diff between transcription updates for real-time typing."""


class TextDiffer:
    """Tracks typed text and calculates corrections needed for new transcriptions."""

    def __init__(self, max_backspaces: int = 20):
        """Initialize differ.

        Args:
            max_backspaces: Maximum backspaces before skipping correction.
        """
        self.last_typed = ""
        self.max_backspaces = max_backspaces

    def calculate_diff(self, new_text: str) -> tuple[int | None, str | None]:
        """Calculate backspaces and new text needed.

        Args:
            new_text: The new transcription text.

        Returns:
            Tuple of (backspaces_needed, text_to_type).
            Returns (None, None) if correction would exceed max_backspaces.
        """
        # Find common prefix length
        common_len = 0
        for i in range(min(len(self.last_typed), len(new_text))):
            if self.last_typed[i] == new_text[i]:
                common_len += 1
            else:
                break

        backspaces = len(self.last_typed) - common_len
        new_chars = new_text[common_len:]

        # Skip if too many backspaces needed
        if backspaces > self.max_backspaces:
            return None, None

        return backspaces, new_chars

    def update(self, text: str) -> None:
        """Update the tracked typed text.

        Args:
            text: The text that has been typed.
        """
        self.last_typed = text

    def reset(self) -> None:
        """Reset to initial state."""
        self.last_typed = ""
