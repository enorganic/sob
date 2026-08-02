from __future__ import annotations

import doctest
from io import UnsupportedOperation
from pathlib import Path

import pytest

from sob import _io

RAINBOX_PNG: Path = Path(__file__).parent / "static-data" / "rainbow.png"


def test_doctest() -> None:
    """
    Run docstring tests
    """
    results: doctest.TestResults = doctest.testmod(_io)
    assert results.failed == 0, results


def test_read() -> None:
    with open(RAINBOX_PNG, "rb") as rainbow_io:
        _io.read(rainbow_io)


class UnsupportedReadProxy:
    def read(self) -> str:
        raise UnsupportedOperation


class NotReadableProxy:
    pass


def test_read_unsupported_operation() -> None:
    error_caught: bool = False
    try:
        _io.read(UnsupportedReadProxy())  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


def test_read_type_error() -> None:
    error_caught: bool = False
    try:
        _io.read(NotReadableProxy())  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vv"])
