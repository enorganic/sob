from __future__ import annotations

import doctest
from pathlib import Path

import pytest

from sob import _io

RAINBOX_PNG: Path = Path(__file__).parent / "static-data" / "rainbow.png"


def test_doctest() -> None:
    """
    Run docstring tests
    """
    doctest.testmod(_io)


def test_read() -> None:
    with open(RAINBOX_PNG, "rb") as rainbow_io:
        _io.read(rainbow_io)


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vv"])
