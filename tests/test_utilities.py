from __future__ import annotations

import doctest
from typing import Any

import pytest

import sob
from sob import _io, _types, _utilities, utilities
from sob._utilities import get_readable_url


def test_doctest() -> None:
    """
    Run docstring tests
    """
    results: doctest.TestResults = doctest.testmod(utilities)
    assert results.failed == 0, results


def test_utilities() -> None:
    assert sob.utilities.get_calling_function_qualified_name() == (
        "tests.test_utilities.test_utilities"
    )

    class TestCallingFunctionQualifiedNameA:
        __module__ = "tests.utilities"

        def __init__(self) -> None:
            assert sob.utilities.get_calling_function_qualified_name() == (
                "tests.utilities.test_utilities."
                "TestCallingFunctionQualifiedNameA.__init__"
            )

    TestCallingFunctionQualifiedNameA()

    class TestCallingFunctionQualifiedNameB:
        def __init__(self) -> None:
            assert sob.utilities.get_calling_function_qualified_name() == (
                "tests.test_utilities.test_utilities.TestCallingFunctionQualif"
                "iedNameB.__init__"
            )

    TestCallingFunctionQualifiedNameB()

    class TestCallingFunctionQualifiedNameC:
        class TestCallingFunctionQualifiedNameD:
            def __init__(self) -> None:
                assert sob.utilities.get_calling_function_qualified_name() == (
                    "tests.test_utilities.test_utilities.TestCallingFunctionQu"
                    "alifiedNameC.TestCallingFunctionQualifiedNameD.__init__"
                )

    TestCallingFunctionQualifiedNameC.TestCallingFunctionQualifiedNameD()
    assert utilities.get_qualified_name(
        TestCallingFunctionQualifiedNameC(
            # -
        ).TestCallingFunctionQualifiedNameD
    ) == (
        "tests.test_utilities.test_utilities.TestCallingFunctionQualifiedNameC"
        ".TestCallingFunctionQualifiedNameD"
    )
    assert sob.utilities.get_qualified_name(sob.Object) == "sob.Object"


def test_inspect() -> None:
    def my_function() -> Any:
        class MyClass:
            """
            TODO
            """

            def __call__(self) -> str | None:
                return self.get_method_name()

            @staticmethod
            def get_static_method_name() -> str | None:
                return sob.utilities.get_calling_function_qualified_name()

            def get_method_name(self) -> str | None:
                return sob.utilities.get_calling_function_qualified_name()

            def get_module_name(self) -> str:
                return sob.utilities.get_calling_module_name()

        return MyClass()

    assert my_function().get_method_name() == (
        "tests.test_utilities.test_inspect.my_function.MyClass.get_method_name"
    )
    assert my_function()() == (
        "tests.test_utilities.test_inspect.my_function.MyClass.get_method_name"
    )
    # Static methods are defined at the module level...
    assert my_function().get_static_method_name() == (
        "tests.test_utilities.get_static_method_name"
    )
    assert my_function().get_module_name() == "tests.test_utilities"


def test_get_calling_function_qualified_name() -> None:
    assert sob.utilities.get_calling_function_qualified_name() == (
        "tests.test_utilities.test_get_calling_function_qualified_name"
    )


def test_io() -> None:
    results: doctest.TestResults = doctest.testmod(_io)
    assert results.failed == 0, results


def test_types() -> None:
    results: doctest.TestResults = doctest.testmod(_types)
    assert results.failed == 0, results


class HTTPResponseProxy1:
    def geturl(self) -> str:
        return "https://example.com"


class HTTPResponseProxy2:
    url = "https://example.com"


class WindowsFileProxy:
    name = r"C:\a\b\c"


class UnixFileProxy:
    name = "/a/b/c"


class URLNonStringProxy:
    url = 123


class NoAttributesProxy:
    pass


def test_get_readable_url() -> None:
    assert get_readable_url(HTTPResponseProxy1()) == "https://example.com"
    assert get_readable_url(HTTPResponseProxy2()) == "https://example.com"
    assert get_readable_url(WindowsFileProxy()) == "file:///C:/a/b/c"
    assert get_readable_url(UnixFileProxy()) == "file:///a/b/c"


def test_get_readable_url_type_error() -> None:
    error_caught: bool = False
    try:
        get_readable_url(URLNonStringProxy())
    except TypeError:
        error_caught = True
    assert error_caught


def test_get_readable_url_none() -> None:
    assert get_readable_url(NoAttributesProxy()) is None


def test_deprecated() -> None:
    @_utilities.deprecated("this is deprecated")
    def old_function(value: int) -> int:
        return value * 2

    with pytest.warns(DeprecationWarning, match="this is deprecated"):
        result: int = old_function(21)
    assert result == 42


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vv"])
