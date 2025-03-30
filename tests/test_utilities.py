from __future__ import annotations

import doctest
from typing import Any

import pytest

from sob import _io, _types, utilities
from sob.utilities import (
    get_calling_function_qualified_name,
    get_calling_module_name,
)


def test_utilities() -> None:
    doctest.testmod(utilities)


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
                return get_calling_function_qualified_name()

            def get_method_name(self) -> str | None:
                return get_calling_function_qualified_name()

            def get_module_name(self) -> str:
                return get_calling_module_name()

        return MyClass()

    assert my_function().get_method_name() in (
        # This will be the response if running pytest
        "tests.test_utilities.test_inspect.my_function.MyClass.get_method_name",
        # This will be the response if running this module as a script
        "tests.test_inspect.my_function.MyClass.get_method_name",
    )
    assert my_function()() in (
        "tests.test_utilities.test_inspect.my_function.MyClass."
        "get_method_name",
        "tests.test_inspect.my_function.MyClass.get_method_name",
    )
    # Static methods are defined at the module level...
    assert my_function().get_static_method_name() in (
        "test_utilities.test_utilities.get_static_method_name",
        "test_utilities.get_static_method_name",
    )
    assert my_function().get_module_name() == "tests.test_utilities"


def test_io() -> None:
    doctest.testmod(_io)


def test_types() -> None:
    doctest.testmod(_types)


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vv"])
