from __future__ import annotations

import doctest
from datetime import date, datetime

import pytest

import sob._datetime


def test_doctest() -> None:
    """
    Run docstring tests
    """
    results: doctest.TestResults = doctest.testmod(
        sob._datetime  # noqa: SLF001
    )
    assert results.failed == 0, results


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


def test_raise_str2datetime_type_error() -> None:
    """
    Test raising of exceptions for invalid types.
    """
    error_caught: bool = False
    try:
        sob._datetime.str2datetime(123)  # type: ignore  # noqa: SLF001
    except TypeError:
        error_caught = True
    assert error_caught


def test_raise_str2date_non_str_type_error() -> None:
    """
    Test raising of exceptions for invalid types.
    """
    error_caught: bool = False
    try:
        sob._datetime.str2date(123)  # type: ignore  # noqa: SLF001
    except TypeError:
        error_caught = True
    assert error_caught


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vv"])
