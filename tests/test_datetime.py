from __future__ import annotations

import doctest
from datetime import date, datetime

import pytest

import sob._datetime


def test_doctest() -> None:
    """
    Run docstring tests
    """
    # Run doctests for the sob._datetime module
    doctest.testmod(sob._datetime)  # noqa: SLF001


def test_raise_date2str_type_error() -> None:
    """
    Test raising of exceptions for invalid types.
    """
    error_caught: bool = False
    try:
        sob._datetime.date2str(  # noqa: SLF001
            datetime(2023, 10, 1)  # noqa: DTZ001
        )
    except TypeError:
        error_caught = True
    assert error_caught


def test_raise_datetime2str_type_error() -> None:
    """
    Test raising of exceptions for invalid types.
    """
    error_caught: bool = False
    try:
        sob._datetime.datetime2str(  # noqa: SLF001
            date(2023, 10, 1)  # type: ignore
        )
    except TypeError:
        error_caught = True
    assert error_caught


def test_raise_str2date_type_error() -> None:
    """
    Test raising of exceptions for invalid types.
    """
    error_caught: bool = False
    try:
        sob._datetime.str2date(  # noqa: SLF001
            "2023-10-01T12:00:00Z"
        )
    except ValueError:
        error_caught = True
    assert error_caught


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vv"])
