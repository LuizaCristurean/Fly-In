"""Exceptions raised by the Fly-in program."""

from typing import Optional


class FlyInError(Exception):
    """Base class of every error that the program raises on purpose."""


class ParseError(FlyInError):
    """The map file is invalid.

    Args:
        message: What is wrong.
        line_number: Line of the file where the problem was found, or
            None when the problem is about the file as a whole
            (for example a missing start_hub).
    """

    def __init__(self, message: str,
                 line_number: Optional[int] = None) -> None:
        if line_number is None:
            text = message
        else:
            text = f"line {line_number}: {message}"
        super().__init__(text)
        self.message = message
        self.line_number = line_number
