"""
This module defines classes for describing properties of a model.
"""

import collections
import collections.abc
import numbers
from collections.abc import Callable
from copy import copy, deepcopy
from datetime import date, datetime
from itertools import chain
from typing import (
    Any, Collection, Dict, List, Optional, Sequence, Set, Union
)

import iso8601

from .types import ImmutableTypes, Types
from .. import abc
from ..meta import Version
from ..utilities import (
    indent, parameters_defaults, properties_values, qualified_name
)
from ..utilities.assertion import assert_argument_is_instance
from ..utilities.types import NULL, UNDEFINED, Undefined

__all__: List[str] = [
    'types',
    'Property',
    'Array',
    'Boolean',
    'Bytes',
    'Date',
    'Dictionary',
    'Enumerated',
    'Integer',
    'Number',
    'String',
    'TYPES_PROPERTIES'
]


def _repr_items(
    items: Union[Sequence, Set]
) -> str:
    """
    Returns a string representation of the items in a `list`, `tuple`, or
    `set`.
    """
    lines: List[str] = []
    for item in items:
        lines.append(indent(_repr(item), start=0))
    return ',\n'.join(lines)


def _repr_list(list_instance: list) -> str:
    """
    Returns a string representation of `list` argument values
    """
    return '[\n%s\n]' % ',\n'.join(_repr_items(list_instance))


def _repr_tuple(tuple_instance: tuple) -> str:
    """
    Returns a string representation of `tuple` argument values
    """
    return '(\n%s\n)' % ',\n'.join(_repr_items(tuple_instance))


def _repr_set(set_instance: set) -> str:
    """
    Returns a string representation of `set` argument values
    """
    return '{\n%s\n}' % ',\n'.join(_repr_items(sorted(set_instance)))


def _repr(value: Any) -> str:
    """
    Returns a string representation of an argument value.
    """
    repr_value: str
    if isinstance(value, type):
        repr_value = qualified_name(value)
    elif isinstance(value, abc.meta.Version):
        repr_value = "'%s'" % str(value)
    else:
        value_type: type = type(value)
        if value_type is list:
            repr_value = _repr_list(value)
        elif value_type is tuple:
            repr_value = _repr_tuple(value)
        elif value_type is set:
            repr_value = _repr_set(value)
        else:
            repr_value = repr(value)
    return repr_value


def _repr_argument(
    argument: str,
    value: Any,
    defaults: Dict[str, Any]
) -> Optional[str]:
    """
    Returns a string representation of an argument assignment, or `None`
    if the argument value is equal to the default value for that argument
    """
    if (
        (argument not in defaults) or
        defaults[argument] == value or
        value is None or
        value is NULL
    ):
        return None
    return '    %s=%s,' % (argument, indent(_repr(value)))


class Property:
    """
    This is the base class for defining a property.

    Properties

        - value_types ([type|Property]): One or more expected value_types or
          `Property` instances. Values are checked, sequentially, against each
          type or `Property` instance, and the first appropriate match is used.

        - required (bool): If `True`--dumping the
          json_object will throw an error if this value is `None`.

        - versions ([str]|{str:Property}):

          The property should be one of the following:

            - A set/tuple/list of version numbers to which this property
              applies.
            - A mapping of version numbers to an instance of `Property`
              applicable to that version.

          Version numbers prefixed by "<" indicate any version less than the
          one specified, so "<3.0" indicates that this property is available in
          versions prior to 3.0. The inverse is true for version numbers
          prefixed by ">". ">=" and "<=" have similar meanings, but are
          inclusive.

          Versioning can be applied to an json_object by calling
          `sob.meta.set_version` in the `__init__` method of an
          `sob.model.Object` sub-class. For an example, see
          `oapi.model.OpenAPI.__init__`.

        - name (str): The name of the property when loaded from or dumped into
          a JSON/YAML object. Specifying a `name` facilitates mapping of PEP8
          compliant property to JSON or YAML attribute names, which are either
          camelCased, are python keywords, or otherwise not appropriate for
          usage in python code.
    """
    _types: Optional[Types] = None

    # noinspection PyShadowingNames
    def __init__(
        self,
        types: Optional[
            Union[
                Sequence[Union[type, 'Property']],
                type,
                'Property',
                Undefined
            ]
        ] = UNDEFINED,
        name: Optional[str] = None,
        required: bool = False,
        versions: Optional[Sequence[Union[str, abc.meta.Version]]] = None
    ) -> None:
        self._types: Optional[Sequence[Union[type, Property]]] = getattr(
            type(self), '_types'
        )
        if types is not UNDEFINED:
            self.types = copy(types)
        self.name = name
        self.required = required
        self._versions: Optional[Sequence[abc.meta.Version]] = None
        self.versions: Optional[
            Sequence[
                Union[
                    str,
                    collections.abc.Iterable,
                    abc.meta.Version
                ]
            ]
        ] = versions

    @property
    def types(self) -> Optional[Sequence[Union[type, 'Property']]]:
        return self._types

    @types.setter
    def types(
        self,
        types_or_properties: Optional[
            Sequence[
                Union[
                    type,
                    abc.properties.Property,
                    abc.model.Model
                ]
            ]
        ]
    ) -> None:
        types_class: type = (
            Types
            if type(self) is Property else
            ImmutableTypes
        )
        if (
            types_or_properties is not None
        ) and not isinstance(
            types_or_properties,
            types_class
        ):
            types_or_properties = types_class(types_or_properties)
        self._types = types_or_properties

    @property
    def versions(self) -> Optional[Sequence[abc.meta.Version]]:
        return self._versions

    @versions.setter
    def versions(
        self,
        versions: Optional[
            Sequence[
                Union[
                    str,
                    collections.abc.Iterable,
                    abc.meta.Version
                ]
            ]
        ]
    ) -> None:
        if versions is not None:
            assert_argument_is_instance(
                'versions',
                versions,
                (str, Number, abc.meta.Version, collections.abc.Iterable)
            )
            if isinstance(versions, (str, Number, abc.meta.Version)):
                versions = (versions,)
            if isinstance(versions, collections.abc.Iterable):
                versions = tuple(
                    (
                        v
                        if isinstance(v, abc.meta.Version) else
                        Version(v)
                    )
                    for v in versions
                )
        self._versions = versions

    def __repr__(self):
        lines = [qualified_name(type(self)) + '(']
        defaults = parameters_defaults(self.__init__)
        for property_name, value in properties_values(self):
            argument_representation = _repr_argument(
                property_name,
                value,
                defaults
            )
            if argument_representation is not None:
                lines.append(argument_representation)
        lines[-1] = lines[-1].rstrip(',')
        lines.append(')')
        if len(lines) > 2:
            return '\n'.join(lines)
        else:
            return ''.join(lines)

    def __copy__(self) -> 'Property':
        new_instance = self.__class__()
        for a in dir(self):
            if a[0] != '_' and a != 'data':
                v = getattr(self, a)
                if not callable(v):
                    setattr(new_instance, a, v)
        return new_instance

    def __deepcopy__(self, memo: dict) -> 'Property':
        new_instance = self.__class__()
        for a, v in properties_values(self):
            setattr(new_instance, a, deepcopy(v, memo))
        return new_instance


abc.properties.Property.register(Property)


class String(Property):
    """
    See `sob.properties.Property`
    """
    _types: ImmutableTypes = ImmutableTypes((str,))

    def __init__(
        self,
        name: Optional[str] = None,
        required: bool = False,
        versions: Optional[Collection] = None
    ) -> None:
        super().__init__(
            name=name,
            required=required,
            versions=versions,
        )


abc.properties.Property.register(String)
abc.properties.String.register(String)


class Date(Property):
    """
    ...See `sob.properties.Property`

    + Parameters:

        - date2str (collections.Callable): A function, taking one argument (a
          python `date` json_object), and returning a date string in the
          desired format. The default is `date.isoformat`--returning an
          iso8601 compliant date string.

        - str2date (collections.Callable): A function, taking one argument (a
          date string), and returning a python `date` object. By default,
          this is `iso8601.parse_date`.
    """
    _types: ImmutableTypes = ImmutableTypes((date,))

    def __init__(
        self,
        name: Optional[str] = None,
        required: Union[bool, Callable] = False,
        versions: Optional[Collection] = None,
        date2str: Optional[Callable] = date.isoformat,
        str2date: Callable = iso8601.parse_date
    ) -> None:
        super().__init__(
            name=name,
            required=required,
            versions=versions,
        )
        self.date2str = date2str
        self.str2date = str2date


abc.properties.Date.register(Date)
abc.properties.Property.register(Date)


class DateTime(Property):
    """
    (See [`sob.properties.Property`](#Property))

    + Parameters:

    - datetime2str (collections.Callable): A function, taking one argument
      (a python `datetime` json_object), and returning a date-time string
      in the desired format. The default is `datetime.isoformat`--returning
      an iso8601 compliant date-time string.
    - str2datetime (collections.Callable): A function, taking one argument
      (a datetime string), and returning a python `datetime` json_object.
      By default, this is `iso8601.parse_date`.
    """
    _types: ImmutableTypes = ImmutableTypes((datetime,))

    def __init__(
        self,
        name: Optional[str] = None,
        required: bool = False,
        versions: Optional[Collection] = None,
        datetime2str: Optional[Callable] = datetime.isoformat,
        str2datetime: Callable = iso8601.parse_date
    ) -> None:
        self.datetime2str = datetime2str
        self.str2datetime = str2datetime
        super().__init__(
            name=name,
            required=required,
            versions=versions,
        )


abc.properties.DateTime.register(Date)
abc.properties.Property.register(Date)


class Bytes(Property):
    """
    (See [`sob.properties.Property`](#Property))

    This class represents a property with binary values
    """
    _types: ImmutableTypes = ImmutableTypes((bytes,))

    def __init__(
        self,
        name: Optional[str] = None,
        required: bool = False,
        versions: Optional[Collection] = None,
    ) -> None:
        super().__init__(
            name=name,
            required=required,
            versions=versions,
        )


abc.properties.Bytes.register(Date)
abc.properties.Property.register(Date)


class Enumerated(Property):
    """
    (See [`sob.properties.Property`](#Property))

    + Properties:

    - values ([Any]):  A list or set of possible values.
    """

    def __init__(
        self,
        types: Optional[
            Union[
                Sequence[Union[type, Property]],
                type,
                property,
                Undefined
            ]
        ] = UNDEFINED,
        values: Optional[Union[Sequence, Set]] = None,
        name: Optional[str] = None,
        required: bool = False,
        versions: Optional[Collection] = None
    ) -> None:
        self._values: Optional[Set[Any]] = None
        super().__init__(
            types=types,
            name=name,
            required=required,
            versions=versions
        )
        self.values: Optional[Sequence] = values

    @property
    def values(self) -> Optional[Set]:
        return self._values

    @values.setter
    def values(self, values: Optional[Union[Sequence, Set]]) -> None:
        if not (
            (values is None) or
            isinstance(
                values,
                (collections.abc.Sequence, collections.abc.Set)
            )
        ):
            raise TypeError(
                '`values` must be a finite set or sequence, not `%s`.' %
                qualified_name(type(values))
            )
        self._values = (
            set(values)
            if isinstance(values, collections.abc.Sequence) else
            values
        )


abc.properties.Enumerated.register(Enumerated)
abc.properties.Property.register(Enumerated)


class Number(Property):
    """
    See `sob.properties.Property`
    """
    _types: ImmutableTypes = ImmutableTypes((numbers.Number,))

    def __init__(
        self,
        name: Optional[str] = None,
        required: bool = False,
        versions: Optional[Collection] = None
    ) -> None:
        super().__init__(
            name=name,
            required=required,
            versions=versions
        )


abc.properties.Number.register(Number)
abc.properties.Property.register(Number)


class Integer(Property):
    """
    See `sob.properties.Property`
    """
    _types: ImmutableTypes = ImmutableTypes((int,))

    def __init__(
        self,
        name: Optional[str] = None,
        required: bool = False,
        versions: Optional[Collection] = None
    ) -> None:
        super().__init__(
            name=name,
            required=required,
            versions=versions,
        )


abc.properties.Integer.register(Integer)
abc.properties.Property.register(Integer)


class Boolean(Property):
    """
    See `sob.properties.Property`
    """
    _types: ImmutableTypes = ImmutableTypes((bool,))

    def __init__(
        self,
        name: Optional[str] = None,
        required: bool = False,
        versions: Optional[Collection] = None
    ) -> None:
        super().__init__(
            name=name,
            required=required,
            versions=versions,
        )


abc.properties.Boolean.register(Boolean)
abc.properties.Property.register(Boolean)


class Array(Property):
    """
    See `sob.properties.Property`...

    + Properties:

    - item_types (type|Property|[type|Property]): The type(s) of values/objects
      contained in the array. Similar to
      `sob.properties.Property().types`, but applied to items in the
      array, not the array itself.
    """
    _types: ImmutableTypes = ImmutableTypes((abc.model.Array,))
    _item_types: Optional[Types] = None

    def __init__(
        self,
        item_types: Optional[
            Union[
                type,
                Sequence[Union[type, abc.properties.Property]],
                Undefined
            ]
        ] = UNDEFINED,
        name: Optional[str] = None,
        required: bool = False,
        versions: Optional[Collection] = None
    ) -> None:
        self._item_types: Optional[Types] = getattr(
            type(self),
            '_item_types'
        )
        if item_types is not UNDEFINED:
            self.item_types = item_types
        super().__init__(
            name=name,
            required=required,
            versions=versions,
        )

    @property
    def item_types(self) -> Types:
        return self._item_types

    @item_types.setter
    def item_types(
        self,
        item_types: Optional[
            Union[
                type,
                Sequence[Union[type, abc.properties.Property]]
            ]
        ]
    ) -> None:
        if (item_types is not None) and not isinstance(item_types, Types):
            item_types = Types(item_types)
        self._item_types = item_types


abc.properties.Array.register(Array)
abc.properties.Property.register(Array)


class Dictionary(Property):
    """
    See `sob.properties.Property`...

    + Properties:

    - value_types (type|Property|[type|Property]): The type(s) of
      values/objects comprising the mapped values. Similar to
      `sob.properties.Property.types`, but applies to *values* in the
      dictionary object, not the dictionary itself.
    """
    _types: ImmutableTypes = ImmutableTypes((abc.model.Dictionary,))
    _value_types: Optional[Types] = None

    def __init__(
        self,
        value_types: Optional[
            Union[
                type,
                Sequence[Union[type, Property]],
                Undefined
            ]
        ] = UNDEFINED,
        name: Optional[str] = None,
        required: bool = False,
        versions: Optional[Collection] = None
    ) -> None:
        self._value_types: Optional[Types] = getattr(
            type(self),
            '_value_types'
        )
        if value_types is not UNDEFINED:
            self.value_types = value_types
        super().__init__(
            name=name,
            required=required,
            versions=versions,
        )

    @property
    def value_types(self):
        return self._value_types

    @value_types.setter
    def value_types(
        self,
        value_types: Optional[
            Sequence[
                Union[
                    type,
                    Property,
                    abc.model.Object
                ]
            ]
        ]
    ) -> None:
        """
        A sequence of types and/or `sob.properties.Property` instances.

        If more than one type or property definition is provided,
        un-marshalling is attempted using each `value_type`, in sequential
        order. If a value could be cast into more than one of the `types`
        without throwing a `ValueError`, `TypeError`, or
        `sob.errors.ValidationError`, the value type occurring *first* in the
        sequence will be used.
        """
        if (value_types is not None) and not isinstance(value_types, Types):
            value_types = Types(value_types)
        self._value_types = value_types


abc.properties.Dictionary.register(Dictionary)
abc.properties.Property.register(Dictionary)


# This constant maps data types to their corresponding properties
TYPES_PROPERTIES: Dict[type, type] = {
    type_: property_class
    for type_, property_class in chain(
        *map(
            lambda property_class: (
                (type_, property_class)
                for type_ in getattr(property_class, '_types')
            ),
            (
                property_class for property_class in locals().values()
                if (
                    isinstance(property_class, type) and
                    issubclass(property_class, Property) and
                    getattr(property_class, '_types')
                )
            )
        )
    )
}
