from __future__ import (
    nested_scopes, generators, division, absolute_import, with_statement,
    print_function, unicode_literals
)
from . import compatibility
import importlib
import sys
import re
from collections import OrderedDict
from .types import UNDEFINED, Module

compatibility.backport()

Union = compatibility.typing.Union
Optional = compatibility.typing.Optional
Iterable = compatibility.typing.Iterable
Tuple = compatibility.typing.Tuple
Any = compatibility.typing.Any
Callable = compatibility.typing.Callable
AnyStr = compatibility.typing.AnyStr
Iterator = compatibility.typing.Iterator
Sequence = compatibility.typing.Sequence
IO = compatibility.typing.IO


if Any is None:
    Iterator = Sequence = KeyValueIterator = IO = None
else:
    KeyValueIterator = Iterator[Tuple[AnyStr, Any]]


try:
    from inspect import (
        signature, getargs, stack, getmodulename, getsource,
        Parameter, getargvalues
    )
    getargspec = None
except ImportError:
    signature = Parameter = None
    try:
        from inspect import (
            getfullargspec, getargs, stack, getmodulename,
            getsource, getargvalues
        )
    except ImportError:
        from inspect import (
            getargspec as getfullargspec, getargs, stack, getsource,
            getmodulename, getargvalues
        )
try:
    from inspect import FrameInfo
except ImportError:
    FrameInfo = tuple


# The `BUILTINS_DICT` is used to check for namespace conflicts
BUILTINS_DICT = {}


def _index_builtins():
    global BUILTINS_DICT
    builtins = importlib.import_module('builtins')
    for property_name_ in dir(builtins):
        BUILTINS_DICT[property_name_] = getattr(builtins, property_name_)


_index_builtins()


def properties_values(object_):
    # type: (object) -> KeyValueIterator
    """
    This function iterates over an object's public (non-callable)
    properties, yielding a tuple comprised of each attribute/property name and
    value
    """
    for attribute in dir(object_):
        if attribute[0] != '_':
            value = getattr(object_, attribute)
            if not callable(value):
                yield attribute, value


def qualified_name(type_):
    # type: (Union[type, Module]) -> str
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


def calling_functions_qualified_names(depth=1):
    # type: (int) -> Iterator[str]
    """
    >>> def my_function_a():
    ...     return calling_functions_qualified_names()
    >>> def my_function_b():
    ...     return my_function_a()
    >>> print(my_function_b())
    ['my_function_b', 'my_function_a']
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


def _get_module_name(file_name):
    # type: (str) -> str
    """
    Given a frame info's file name, find the module name
    """
    module_name = getmodulename(file_name)
    if module_name is None:
        # Check to see if this is a doctest
        doc_test_prefix = '<doctest '
        if file_name.startswith(doc_test_prefix):
            module_name = re.sub('^' + doc_test_prefix, '', file_name)
            module_name = module_name.rstrip('>')
            if '[' in module_name:
                module_name = '['.join(file_name.split('[')[:-1])
        else:
            raise ValueError(
                'The path "%s" is not a python module' % file_name
            )
    return module_name


def calling_function_qualified_name(depth=1):
    # type: (int) -> Optional[str]
    """
    Return the fully qualified name of the function from within which this is
    being called

    >>> def my_function():
    ...     return calling_function_qualified_name()
    >>> print(my_function())
    my_function
    """
    if not isinstance(depth, int):
        depth_representation = repr(depth)
        raise TypeError(
            'The parameter `depth` for `sob.utilities.calling_function_'
            'qualified_name` must be an `int`, not' +
            (
                (':\n%s' if '\n' in depth_representation else ' %s.') %
                depth_representation
            )
        )
    try:
        stack_ = stack()
    except IndexError:
        return None
    if len(stack_) < (depth + 1):
        return None
    name_list = []
    frame_info = stack_[depth]  # type: FrameInfo
    frame_function = frame_info[3]
    if frame_function != '<module>':
        frame = frame_info[0]
        name_list.append(frame_function)
        arguments, _, _, frame_locals = getargvalues(frame)
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
                name_list.append(qualified_name(argument_value_type))
    if len(name_list) < 2:
        module_name = _get_module_name(frame_info[1])
        if module_name in sys.modules:
            qualified_module_name = qualified_name(
                sys.modules[module_name]
            )
            name_list.append(qualified_module_name)
    return '.'.join(reversed(name_list))


def get_source(object_):
    # type: (object) -> str
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


def parameters_defaults(function):
    # type: (Callable) -> OrderedDict
    """
    Returns an ordered dictionary mapping a function's argument names to
    default values, or `UNDEFINED` in the case of
    positional arguments.

    >>> class X(object):
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
    pd = OrderedDict()
    if signature is None:
        spec = getfullargspec(function)
        i = - 1
        for a in spec.args:
            pd[a] = UNDEFINED
        for a in reversed(spec.args):
            try:
                pd[a] = spec.defaults[i]
            except IndexError:
                break
            i -= 1
    else:
        for pn, p in signature(function).parameters.items():
            if p.default is Parameter.empty:
                pd[pn] = UNDEFINED
            else:
                pd[pn] = p.default
    return pd
