import collections
from inspect import (
    FrameInfo,
    Parameter,
    getargvalues,
    getmodulename,
    getsource,
    signature,
    stack,
)
from types import ModuleType
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

import builtins
import sys

from .string import indent
from .types import UNDEFINED, Undefined


def _is_public(name: str) -> bool:
    return not name.startswith("_")


def properties_values(
    object_: object, include_private: bool = False
) -> Iterable[Tuple[str, Any]]:
    """
    This function iterates over an object's public (non-callable)
    properties, yielding a tuple comprised of each attribute/property name and
    value
    """
    names: Iterable[str] = dir(object_)
    if not include_private:
        names = filter(_is_public, names)

    def get_name_value(name: str) -> Optional[Tuple[str, str]]:
        value: Any = getattr(object_, name, lambda: None)
        if callable(value):
            return None
        return name, value

    return filter(None, map(get_name_value, names))


QUALIFIED_NAME_ARGUMENT_TYPES: Tuple[Any, ...] = (
    type,
    collections.abc.Callable,
    ModuleType,
)


def qualified_name(type_or_module: Union[type, Callable, ModuleType]) -> str:
    """
    >>> print(qualified_name(qualified_name))
    sob.utilities.inspect.qualified_name

    >>> from sob import model
    >>> print(qualified_name(model.marshal))
    sob.model.marshal
    """
    assert isinstance(type_or_module, QUALIFIED_NAME_ARGUMENT_TYPES)
    type_name: str
    # noinspection SpellCheckingInspection
    if isinstance(type_or_module, ModuleType):
        type_name = type_or_module.__name__
    else:
        type_name = ".".join(
            name_part
            for name_part in getattr(
                type_or_module,
                "__qualname__",
                getattr(type_or_module, "__name__"),
            ).split(".")
            if name_part[0] != "<"
        )
        if type_or_module.__module__ not in (
            "builtins",
            "__builtin__",
            "__main__",
            "__init__",
        ):
            type_name = type_or_module.__module__ + "." + type_name
    return type_name


def calling_functions_qualified_names(depth: int = 1) -> List[str]:
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
    names: List[str] = []
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
        doc_test_prefix: str = "<doctest "
        if file_name.startswith(doc_test_prefix):
            doc_test_prefix_length: int = len(doc_test_prefix)
            module_name = file_name[doc_test_prefix_length:]
            module_name = module_name.rstrip(">")
            if "[" in module_name:
                module_name = "[".join(module_name.split("[")[:-1])
        else:
            raise ValueError(f'The path "{file_name}" is not a python module')
    return module_name


def _get_frame_info_names(frame_info: FrameInfo) -> List[str]:
    names: List[str] = []
    if frame_info.function != "<module>":
        names.append(frame_info.function)
        arguments, _, _, frame_locals = getargvalues(frame_info.frame)
        if arguments:
            argument = arguments[0]
            argument_value = frame_locals[argument]
            argument_value_type = type(argument_value)
            if (
                hasattr(argument_value_type, "__name__")
                and hasattr(argument_value_type, "__module__")
                and (
                    (argument_value_type.__name__ not in builtins.__dict__)
                    or (
                        builtins.__dict__[argument_value_type.__name__]
                        is not argument_value_type
                    )
                )
            ):
                names.append(qualified_name(argument_value_type))
    if len(names) < 2:
        module_name = _get_module_name(frame_info.filename)
        if module_name in sys.modules:
            qualified_module_name = qualified_name(sys.modules[module_name])
            names.append(qualified_module_name)
        elif module_name:
            names.append(module_name)
    return names


def calling_module_name(depth: int = 1) -> str:
    """
    This function returns the name of the module from which the function
    which invokes this function was called.

    Parameters:

    - depth (int): This defaults to `1`, indicating we want to return the name
      of the module wherein `calling_module_name` is being called. If set to
      `2`, it would instead indicate the module

    >>> print(calling_module_name())
    sob.utilities.inspect

    >>> print(calling_module_name(2))
    doctest
    """
    name: str
    try:
        name = getattr(sys, "_getframe")(depth).f_globals.get(
            "__name__", "__main__"
        )
    except (AttributeError, ValueError):
        name = "__main__"
    return name


# noinspection PyUnresolvedReferences
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
    ...     # noinspection PyMethodMayBeStatic
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
    return ".".join(reversed(names))


def get_source(object_: Union[type, Callable, ModuleType]) -> str:
    """
    Get the source code which defined an object.
    """
    object_source: str = getattr(object_, "_source", "")
    if not object_source:
        object_source = getsource(object_)
    return object_source


def parameters_defaults(function: Callable[..., Any]) -> Dict[str, Any]:
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
    defaults: Dict[str, Any] = collections.OrderedDict()
    parameter_name: str
    parameter: Parameter
    for parameter_name, parameter in signature(function).parameters.items():
        if parameter.default is Parameter.empty:
            defaults[parameter_name] = UNDEFINED
        else:
            defaults[parameter_name] = parameter.default
    return defaults


def _repr_items(items: Union[Sequence, Set]) -> str:
    """
    Returns a string representation of the items in a `list`, `tuple`, or
    `set`.
    """
    lines: List[str] = []
    for item in items:
        lines.append(indent(represent(item), start=0))
    return ",\n".join(lines)


def _repr_list(list_instance: list) -> str:
    """
    Returns a string representation of `list` argument values
    """
    return f"[\n{_repr_items(list_instance)}\n]"


def _repr_tuple(tuple_instance: tuple) -> str:
    """
    Returns a string representation of `tuple` argument values
    """
    comma: str = "," if len(tuple_instance) == 1 else ""
    return f"(\n{_repr_items(tuple_instance)}{comma}\n)"


def _repr_set(set_instance: set) -> str:
    """
    Returns a string representation of `set` argument values
    """
    items: str = _repr_items(
        sorted(set_instance, key=lambda item: represent(item))
    )
    return f"{{\n{items}\n}}"


def represent(value: Any) -> str:
    """
    Returns a string representation of a value.
    """
    value_representation: str
    if isinstance(value, type):
        value_representation = qualified_name(value)
    else:
        value_type: type = type(value)
        if value_type is list:
            value_representation = _repr_list(value)
        elif value_type is tuple:
            value_representation = _repr_tuple(value)
        elif value_type is set:
            value_representation = _repr_set(value)
        else:
            value_representation = repr(value)
            if (
                value_type is str
                and '"' not in value_representation
                and value_representation.startswith("'")
                and value_representation.endswith("'")
            ):
                value_representation = f'"{value_representation[1:-1]}"'
    return value_representation


def get_method(
    object_instance: object,
    method_name: str,
    default: Union[Callable, Undefined, None] = UNDEFINED,
) -> Optional[Callable[..., Any]]:
    """
    This function attempts to retrieve a method, by name.

    Parameters:

    - object_instance (object)
    - method_name (str)
    - default (collections.Callable|None) = None

    This function returns an object's method, if the method exists.
    If the object does not have a method with the given name, this
    function returns `None`.
    """
    method: Callable
    try:
        method = getattr(object_instance, method_name)
    except AttributeError:
        if isinstance(default, Undefined):
            raise
        else:
            return default
    if callable(method):
        return method
    else:
        if isinstance(default, Undefined):
            raise AttributeError(
                f"{qualified_name(type(object_instance))}.{method_name} "
                "is not callable."
            )
        else:
            return method
