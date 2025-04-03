from __future__ import annotations

import doctest
from typing import Any

import pytest

import sob
from sob import _io, _types, utilities


def test_doctest() -> None:
    """
    Run docstring tests
    """
    doctest.testmod(utilities)


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
    assert sob.utilities.get_qualified_name(sob.Object) == "sob.model.Object"


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
        "tests.test_utilities.test_inspect.my_function.MyClass."
        "get_method_name"
    )
    assert my_function()() == (
        "tests.test_utilities.test_inspect.my_function.MyClass."
        "get_method_name"
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
    doctest.testmod(_io)


def test_types() -> None:
    doctest.testmod(_types)


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vv"])
