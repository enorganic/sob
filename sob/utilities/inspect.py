import importlib
import sys
from collections import OrderedDict
from inspect import (
    FrameInfo, Parameter, getargvalues, getmodulename, getsource, signature,
    stack
)
from typing import (
    Any, AnyStr, Callable, Dict, Iterator, List, Optional, Tuple, Union
)

from .types import Module, UNDEFINED

# `BUILTINS_DICT` is used to check for namespace conflicts
BUILTINS_DICT = {}


def _index_builtins():
    global BUILTINS_DICT
    builtins = importlib.import_module('builtins')
    for property_name_ in dir(builtins):
        BUILTINS_DICT[property_name_] = getattr(builtins, property_name_)


_index_builtins()


def properties_values(
    object_: object,
    include_private: bool = False
) -> Iterator[Tuple[AnyStr, Any]]:
    """
    This function iterates over an object's public (non-callable)
    properties, yielding a tuple comprised of each attribute/property name and
    value
    """
    for attribute in dir(object_):
        if include_private or attribute[0] != '_':
            value = getattr(object_, attribute)
            if not callable(value):
                yield attribute, value


def qualified_name(type_: Union[type, Module]) -> str:
    """
    >>> print(qualified_name(qualified_name))
    sob.utilities.inspect.qualified_name

    >>> from sob import model
    >>> print(qualified_name(model.marshal))
    sob.model.marshal
    """
    if hasattr(type_, '__qualname__'):
        type_name = '.'.join(
            name_part
            for name_part in type_.__qualname__.split('.')
            if name_part[0] != '<'
        )
    else:
        type_name = type_.__name__
    if isinstance(type_, Module):
        if type_name in (
            'builtins', '__builtin__', '__main__', '__init__'
        ):
            type_name = None
    else:
        if type_.__module__ not in (
            'builtins', '__builtin__', '__main__', '__init__'
        ):
            type_name = type_.__module__ + '.' + type_name
    return type_name


def calling_functions_qualified_names(depth: int = 1) -> Iterator[str]:
    """
    This function returns the qualified names of all calling functions in the
    stack, starting with the function at the indicated `depth` (defaults to 1).

    >>> def my_function_a():
    ...     return calling_functions_qualified_names()
    >>> def my_function_b():
    ...     return my_function_a()
    >>> print('\\n'.join(my_function_b()[-2:]))
    sob.utilities.inspect.calling_functions_qualified_names.my_function_b
    sob.utilities.inspect.calling_functions_qualified_names.my_function_a
    """
    depth += 1
    name = calling_function_qualified_name(depth=depth)
    names = []
    while name:
        if name and not (names and names[0] == name):
            names.insert(0, name)
        depth += 1
        name = calling_function_qualified_name(depth=depth)
    return names


def _get_module_name(file_name: str) -> str:
    """
    Given a frame info's file name, find the module name
    """
    module_name = getmodulename(file_name)
    if module_name is None:
        # Check to see if this is a doctest
        doc_test_prefix: str = '<doctest '
        if file_name.startswith(doc_test_prefix):
            module_name = file_name[len(doc_test_prefix):]
            module_name = module_name.rstrip('>')
            if '[' in module_name:
                module_name = '['.join(module_name.split('[')[:-1])
        else:
            raise ValueError(
                'The path "%s" is not a python module' % file_name
            )
    return module_name


def _get_frame_info_names(frame_info: FrameInfo) -> List[str]:
    names: List[str] = []
    if frame_info.function != '<module>':
        names.append(frame_info.function)
        arguments, _, _, frame_locals = getargvalues(
            frame_info.frame
        )
        if arguments:
            argument = arguments[0]
            argument_value = frame_locals[argument]
            argument_value_type = type(argument_value)
            if (
                hasattr(argument_value_type, '__name__') and
                hasattr(argument_value_type, '__module__') and
                (
                    (
                        argument_value_type.__name__
                        not in
                        BUILTINS_DICT
                    ) or (
                        BUILTINS_DICT[argument_value_type.__name__]
                        is not
                        argument_value_type
                    )
                )
            ):
                names.append(qualified_name(argument_value_type))
    if len(names) < 2:
        module_name = _get_module_name(frame_info.filename)
        if module_name in sys.modules:
            qualified_module_name = qualified_name(
                sys.modules[module_name]
            )
            names.append(qualified_module_name)
        elif module_name:
            names.append(module_name)
    return names


def calling_function_qualified_name(depth: int = 1) -> Optional[str]:
    """
    Return the fully qualified name of the function from within which this is
    being called

    >>> def my_function():
    ...     return calling_function_qualified_name()
    >>> print(my_function())
    sob.utilities.inspect.calling_function_qualified_name.my_function

    >>> class MyClass:
    ...
    ...     def __call__(self) -> None:
    ...          return self.my_method()
    ...
    ...     def my_method(self) -> str:
    ...          return calling_function_qualified_name()
    >>> print(MyClass()())
    sob.utilities.inspect.MyClass.my_method
    """
    assert isinstance(depth, int)
    try:
        stack_ = stack()
    except IndexError:
        return None
    if len(stack_) < (depth + 1):
        return None
    names: List[str] = _get_frame_info_names(stack_[depth])
    return '.'.join(reversed(names))


def get_source(object_: object) -> str:
    """
    Get the source code which defined an object.
    """
    try:
        object_source = getattr(object_, '_source')
    except AttributeError:
        object_source = None
    if not isinstance(object_source, str):
        object_source = getsource(object_)
    return object_source


def parameters_defaults(function: Callable) -> OrderedDict:
    """
    Returns an ordered dictionary mapping a function's argument names to
    default values, or `UNDEFINED` in the case of
    positional arguments.

    >>> class X:
    ...
    ...    def __init__(self, a, b, c, d=1, e=2, f=3):
    ...        pass
    ...
    >>> for parameter_name, default in parameters_defaults(X.__init__).items():
    ...     print((parameter_name, default))
    ('self', UNDEFINED)
    ('a', UNDEFINED)
    ('b', UNDEFINED)
    ('c', UNDEFINED)
    ('d', 1)
    ('e', 2)
    ('f', 3)
    """
    defaults: Dict[str, Any] = OrderedDict()
    parameter_name: str
    parameter: Parameter
    for parameter_name, parameter in signature(function).parameters.items():
        if parameter.default is Parameter.empty:
            defaults[parameter_name] = UNDEFINED
        else:
            defaults[parameter_name] = parameter.default
    return defaults
