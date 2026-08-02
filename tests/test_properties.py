from __future__ import annotations

import pytest

import sob
import sob.properties


def test_has_mutable_types() -> None:
    assert sob.properties.has_mutable_types(sob.Property())
    assert not sob.properties.has_mutable_types(sob.StringProperty)
    error_caught: bool = False
    try:
        sob.properties.has_mutable_types(int)  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


def test_property_types_immutable() -> None:
    string_property: sob.StringProperty = sob.StringProperty()
    error_caught: bool = False
    try:
        string_property.types = [int]  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


def test_property_types_invalid() -> None:
    property_: sob.Property = sob.Property()
    error_caught: bool = False
    try:
        property_.types = "not-a-type"  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


def test_property_versions_invalid() -> None:
    property_: sob.Property = sob.Property()
    error_caught: bool = False
    try:
        property_.versions = 123  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vv"])
