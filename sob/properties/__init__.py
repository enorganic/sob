"""
This module defines classes for describing properties of a model.
"""

import collections
import collections.abc
import numbers
from copy import deepcopy
from datetime import date, datetime
from typing import (
    Any, Collection, Dict, List, Optional, Sequence, Set, Union
)
from collections.abc import Callable

import iso8601

from .types import Types, NULL
from .. import abc
from ..meta import Version
from ..utilities import (
    calling_function_qualified_name, indent, parameters_defaults,
    properties_values, qualified_name
)
from ..utilities.types import Undefined, UNDEFINED

__all__: List[str] = [
    'types',
    'Array',
    'Boolean',
    'Bytes',
    'Date',
    'Dictionary',
    'Enumerated',
    'Integer',
    'Number',
    'Property',
    'String'
]


def _repr_list_or_tuple(
    list_or_tuple: Union[list, tuple]
) -> str:
    """
    Return a multi-line string representation of a `list` or `tuple`
    """
    lines: List[str] = []
    for item in list_or_tuple:
        if isinstance(item, (list, tuple)):
            repr_item: str = _repr_list_or_tuple(item)
        else:
            repr_item: str = repr(item)
        for line in repr_item.split('\n'):
            lines.append(
                '    ' + line
            )
    if isinstance(list_or_tuple, list):
        return '[\n%s\n]' % ',\n'.join(lines)
    else:
        return '(\n%s\n)' % ',\n'.join(lines)


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

    def __init__(
        self,
        types: Optional[
            Union[
                Sequence[Union[type, 'Property']],
                type,
                property,
                Undefined
            ]
        ] = UNDEFINED,
        name: Optional[str] = None,
        required: bool = False,
        versions: Optional[Sequence[Union[str, abc.meta.Version]]] = None
    ) -> None:
        self._types: Optional[Sequence[Union[type, Property]]] = getattr(
            type(self),
            '_types'
        )
        if types is not UNDEFINED:
            self.types = types
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
        if (
            types_or_properties is not None
        ) and not isinstance(
            types_or_properties, Types
        ):
            types_or_properties = Types(types_or_properties)
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
            else:
                repr_versions = repr(versions)
                raise TypeError(
                    (
                        '`%s` requires a sequence of version strings or ' %
                        calling_function_qualified_name()
                    ) + (
                        '`%s` instances, not' % qualified_name(
                            Version
                        )
                    ) + (
                        ':\n' + repr_versions
                        if '\n' in repr_versions else
                        ' `%s`.' % repr_versions
                    )
                )
        self._versions = versions

    @staticmethod
    def _repr_argument(
        argument: str,
        value: Any,
        defaults: Dict[str, Any]
    ) -> Optional[str]:
        if (
            (argument not in defaults) or
            defaults[argument] == value or
            value is None or
            value is NULL
        ):
            return None
        value_representation = (
            qualified_name(value)
            if isinstance(value, type) else
            "'%s'" % str(value)
            if isinstance(value, abc.meta.Version) else
            _repr_list_or_tuple(value)
            if type(value) in (list, tuple) else
            repr(value)
        )
        return '    %s=%s,' % (argument, indent(value_representation))

    def __repr__(self):
        lines = [qualified_name(type(self)) + '(']
        defaults = parameters_defaults(self.__init__)
        for property_name, value in properties_values(self):
            argument_representation = self._repr_argument(
                property_name, value, defaults
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
    _types: Types = Types((str,))

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
    _types: Types = Types((date,))

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
    _types: Types = Types((datetime,))

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


class Bytes(Property):
    """
    (See [`sob.properties.Property`](#Property))

    This class represents a property with binary values
    """
    _types: Types = Types((bytes,))

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


class Number(Property):
    """
    See `sob.properties.Property`
    """
    _types: Types = Types((numbers.Number,))

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


class Integer(Property):
    """
    See `sob.properties.Property`
    """
    _types: Types = Types((int,))

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


class Boolean(Property):
    """
    See `sob.properties.Property`
    """
    _types: Types = Types((bool,))

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


class Array(Property):
    """
    See `sob.properties.Property`...

    + Properties:

    - item_types (type|Property|[type|Property]): The type(s) of values/objects
      contained in the array. Similar to
      `sob.properties.Property().types`, but applied to items in the
      array, not the array itself.
    """
    _types: Types = Types((abc.model.Array,))
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


class Dictionary(Property):
    """
    See `sob.properties.Property`...

    + Properties:

    - value_types (type|Property|[type|Property]): The type(s) of
      values/objects comprising the mapped values. Similar to
      `sob.properties.Property.types`, but applies to *values* in the
      dictionary object, not the dictionary itself.
    """
    _types: Types = Types((abc.model.Dictionary,))
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
