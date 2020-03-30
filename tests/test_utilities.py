import doctest

from sob.utilities import (
    inspect, io, string, types
)
from sob.utilities.inspect import (
    calling_module_name, calling_function_qualified_name
)


def test_strings():
    doctest.testmod(string)


def test_inspect():

    def my_function():

        class MyClass:

            def __call__(self) -> str:
                return self.get_method_name()

            @staticmethod
            def get_static_method_name() -> str:
                return calling_function_qualified_name()

            def get_method_name(self) -> str:
                return calling_function_qualified_name()

            def get_module_name(self) -> str:
                return calling_module_name()

        return MyClass()

    assert my_function().get_method_name() in (
        # This will be the response if running pytest
        'test_utilities.test_inspect.my_function.MyClass.get_method_name',
        # This will be the response if running this module as a script
        'test_inspect.my_function.MyClass.get_method_name'
    )
    assert my_function()() in (
        'test_utilities.test_inspect.my_function.MyClass.get_method_name',
        'test_inspect.my_function.MyClass.get_method_name'
    )
    # Static methods are defined at the module level...
    assert my_function().get_static_method_name() in (
        'test_utilities.test_utilities.get_static_method_name',
        'test_utilities.get_static_method_name'
    )
    assert my_function().get_module_name() in (
        'test_utilities',
        '__main__'
    )
    doctest.testmod(inspect)


def test_io():
    doctest.testmod(io)


def test_types():
    doctest.testmod(types)


if __name__ == '__main__':
    test_strings()
    test_io()
    test_strings()
    test_types()
    test_inspect()
