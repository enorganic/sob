"""
This module defines classes for describing properties of a model.
"""

import collections
import collections.abc
import numbers
from collections.abc import Callable
from copy import deepcopy
from datetime import date, datetime
from typing import (
    Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union
)

from iso8601 import parse_date  # type: ignore
from itertools import chain

from . import abc
from .types import ImmutableTypes, Types
from .utilities import (
    indent, parameters_defaults, properties_values, qualified_name
)
from .utilities.assertion import assert_argument_is_instance
from .utilities.inspect import represent
from .utilities.types import UNDEFINED, Undefined
from .utilities.typing import MarshallableTypes
from .version import Version

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


def _repr_keyword_argument_assignment(
    argument: str,
    value: MarshallableTypes,
    defaults: Optional[Dict[str, MarshallableTypes]] = None
) -> Optional[str]:
    """
    Returns a string representation of an argument assignment, or `None`
    if the argument value is equal to the default value for that argument
    """
    if (
        defaults is not None
    ) and (
        (argument not in defaults) or
        defaults[argument] == value or
        value is None
    ):
        return None
    return '    %s=%s,' % (argument, indent(represent(value)))


# noinspection PyUnresolvedReferences
@abc.properties.Property.register
class Property:
    """
    This is the base class for defining a property.

    Properties

        - types ([type|Property]): One or more expected `type` or
          `Property` instances. A list of more than one types and/or properties
          results in a polymorphic interpretation wherein a value is
          un-marshalled in accordance with each type or property in the list
          (sequentially), until the value is un-marshalled without throwing a
          `TypeError` or `ValueError`. If the list of types and/or properties
          is exhausted without successfully un-marshalling the value, a
          `TypeError` or `ValueError` error is raised.

        - required (bool): If `True`—marshalling a value for this property
          will throw an error if the value is `None`. Please note that `None`
          indicates a value was *not provided*. To indicate an *explicit* null
          value, use `sob.properties.types.NULL`.

        - versions ([str]|{str:Property}):

          The parameter should be one of the following:

            - A `set`, `tuple`, or `list` of version numbers to which this
              property applies.
            - A mapping of version numbers to an instance of
              [Property](#Property) instances applicable to that version.

          Version numbers prefixed by "<" indicating any version less than the
          one specified, so "<3.0" indicates that this property is available in
          versions prior to 3.0. The inverse is true for version numbers
          prefixed by ">". ">=" and "<=" have similar meanings, but are
          inclusive.

          Versioning can be applied to a property by calling
          `sob.meta.set_version` in the `__init__` method of an
          `sob.model.Object` sub-class.

        - name (str): The name of the property when loaded from or dumped into
          a JSON object. Specifying a `name` facilitates mapping of PEP8
          compliant property names to JSON or YAML attribute names which might
          be incompatible with well-formatted python code due to various
          reasons such as being camelCased, or being python keywords. To
          infer an appropriate property name programmatically, use the utility
          function `sob.utilities.string.property_name`.
    """
    _types: Optional[Types] = None

    # noinspection PyShadowingNames
    def __init__(
        self,
        types: Optional[
            Union[
                Types,
                Sequence[Union[type, 'Property']],
                type,
                'Property',
                Undefined
            ]
        ] = UNDEFINED,
        name: Optional[str] = None,
        required: bool = False,
        versions: Optional[Sequence[Union[str, Version]]] = None
    ) -> None:
        self._types: Optional[Types] = getattr(
            type(self), '_types'
        )
        if types is not UNDEFINED:
            setattr(self, 'types', types)
        self.name: Optional[str] = name
        self.required: bool = required
        self._versions: Optional[Sequence[Version]] = None
        if versions is not None:
            setattr(self, 'versions', versions)

    @property
    def types(self) -> Optional[
        Sequence[Union[type, 'Property']]
    ]:
        return self._types

    @types.setter
    def types(
        self,
        types_or_properties: Optional[
            Union[
                Types,
                Sequence[Union[type, 'Property']],
                type,
                'Property'
            ]
        ]
    ) -> None:
        types_class: type = (
            Types
            if type(self) is Property else ImmutableTypes
        )
        if (
            types_or_properties is not None
        ) and not isinstance(
            types_or_properties,
            types_class
        ):
            types_or_properties = types_class(types_or_properties)
        assert (
            (types_or_properties is None) or
            isinstance(types_or_properties, Types)
        )
        self._types = types_or_properties

    @property
    def versions(self) -> Optional[Sequence[Version]]:
        return self._versions

    @versions.setter
    def versions(
        self,
        versions: Optional[
            Union[
                str,
                Version,
                Iterable[
                    Union[
                        str,
                        Version
                    ]
                ]
            ]
        ] = None
    ) -> None:
        versions_tuple: Optional[Tuple[Version, ...]] = None
        if versions is not None:
            assert_argument_is_instance(
                'versions',
                versions,
                (
                    str, Version, collections.abc.Iterable
                )
            )
            version: Union[str, Version]
            if isinstance(versions, str):
                version = Version(versions)
                versions_tuple = (version,)
            elif isinstance(versions, Version):
                versions_tuple = (versions,)
            else:
                versions_list: List[Version] = []
                for version in versions:
                    if not isinstance(version, Version):
                        version = Version(version)
                    versions_list.append(version)
                versions_tuple = tuple(versions_list)
        self._versions = versions_tuple

    def __repr__(self):
        lines = [qualified_name(type(self)) + '(']
        defaults = parameters_defaults(self.__init__)
        for property_name, value in properties_values(self):
            argument_representation = _repr_keyword_argument_assignment(
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
        attribute_name: str
        for attribute_name in dir(self):
            if attribute_name[0] != '_' and attribute_name != 'data':
                value = getattr(self, attribute_name)
                if not callable(value):
                    setattr(new_instance, attribute_name, value)
        return new_instance

    def __deepcopy__(self, memo: dict) -> 'Property':
        new_instance = self.__class__()
        for a, v in properties_values(self):
            setattr(new_instance, a, deepcopy(v, memo=memo))
        return new_instance


# noinspection PyUnresolvedReferences
@abc.properties.String.register
class String(Property):
    """
    See `sob.properties.Property`
    """
    _types: ImmutableTypes = ImmutableTypes((str,))

    def __init__(
        self,
        name: Optional[str] = None,
        required: bool = False,
        versions: Optional[Sequence[Union[str, Version]]] = None
    ) -> None:
        super().__init__(
            name=name,
            required=required,
            versions=versions,
        )


# noinspection PyUnresolvedReferences
@abc.properties.Date.register
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
        required: bool = False,
        versions: Optional[Sequence[Union[str, Version]]] = None,
        date2str: Optional[Callable] = date.isoformat,
        str2date: Callable = parse_date
    ) -> None:
        super().__init__(
            name=name,
            required=required,
            versions=versions,
        )
        self.date2str = date2str
        self.str2date = str2date


# noinspection PyUnresolvedReferences
@abc.properties.DateTime.register
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
        versions: Optional[Sequence[Union[str, Version]]] = None,
        datetime2str: Optional[Callable] = datetime.isoformat,
        str2datetime: Callable = parse_date
    ) -> None:
        self.datetime2str = datetime2str
        self.str2datetime = str2datetime
        super().__init__(
            name=name,
            required=required,
            versions=versions,
        )


# noinspection PyUnresolvedReferences
@abc.properties.Bytes.register
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
        versions: Optional[Sequence[Union[str, Version]]] = None,
    ) -> None:
        super().__init__(
            name=name,
            required=required,
            versions=versions,
        )


# noinspection PyUnresolvedReferences
@abc.properties.Enumerated.register
class Enumerated(Property):
    """
    Parameters:

    This class accepts the following keyword parameters in *addition* to all
    parameters applicable to the base class [Property](#Property).

    - values ([typing.Any]):  A list or set of possible values.

    Properties:

    This class exposes public properties matching its keyword parameters.
    """

    # noinspection PyShadowingNames
    def __init__(
        self,
        types: Optional[
            Union[
                Types,
                Sequence[Union[type, 'Property']],
                type,
                'Property',
                Undefined
            ]
        ] = UNDEFINED,
        values: Optional[Iterable[MarshallableTypes]] = None,
        name: Optional[str] = None,
        required: bool = False,
        versions: Optional[Sequence[Union[str, Version]]] = None
    ) -> None:
        self._values: Optional[Set[MarshallableTypes]] = None
        super().__init__(
            types=types,
            name=name,
            required=required,
            versions=versions
        )
        setattr(self, 'values', values)

    @property
    def values(self) -> Optional[Set[MarshallableTypes]]:
        return self._values

    @values.setter
    def values(self, values: Optional[Iterable[MarshallableTypes]]) -> None:
        if values is None:
            self._values = None
        else:
            assert_argument_is_instance(
                'values',
                values,
                collections.abc.Iterable
            )
            self._values = set(values)


# noinspection PyUnresolvedReferences
@abc.properties.Number.register
class Number(Property):
    """
    See `sob.properties.Property`
    """
    _types: ImmutableTypes = ImmutableTypes((numbers.Number,))

    def __init__(
        self,
        name: Optional[str] = None,
        required: bool = False,
        versions: Optional[Sequence[Union[str, Version]]] = None
    ) -> None:
        super().__init__(
            name=name,
            required=required,
            versions=versions
        )


# noinspection PyUnresolvedReferences
@abc.properties.Integer.register
class Integer(Property):
    """
    See `sob.properties.Property`
    """
    _types: ImmutableTypes = ImmutableTypes((int,))

    def __init__(
        self,
        name: Optional[str] = None,
        required: bool = False,
        versions: Optional[Sequence[Union[str, Version]]] = None
    ) -> None:
        super().__init__(
            name=name,
            required=required,
            versions=versions,
        )


# noinspection PyUnresolvedReferences
@abc.properties.Boolean.register
class Boolean(Property):
    """
    See `sob.properties.Property`
    """
    _types: ImmutableTypes = ImmutableTypes((bool,))

    def __init__(
        self,
        name: Optional[str] = None,
        required: bool = False,
        versions: Optional[Sequence[Union[str, Version]]] = None
    ) -> None:
        super().__init__(
            name=name,
            required=required,
            versions=versions,
        )


# noinspection PyUnresolvedReferences
@abc.properties.Array.register
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
                Sequence[Union[type, Property]],
                Undefined
            ]
        ] = UNDEFINED,
        name: Optional[str] = None,
        required: bool = False,
        versions: Optional[Sequence[Union[str, Version]]] = None
    ) -> None:
        self._item_types: Optional[Types] = getattr(
            type(self),
            '_item_types'
        )
        if item_types is not UNDEFINED:
            setattr(self, 'item_types', item_types)
        super().__init__(
            name=name,
            required=required,
            versions=versions,
        )

    @property
    def item_types(self) -> Optional[Types]:
        return self._item_types

    @item_types.setter
    def item_types(
        self,
        item_types: Optional[
            Union[
                type,
                Property,
                Sequence[Union[type, Property]]
            ]
        ]
    ) -> None:
        if (item_types is not None) and not isinstance(
            item_types, Types
        ):
            item_types_list: List[Union[type, abc.properties.Property]] = []
            if isinstance(item_types, (type, abc.properties.Property)):
                item_types_list.append(item_types)
            else:
                assert isinstance(item_types, collections.abc.Iterable)
                for item_type in item_types:
                    assert isinstance(
                        item_type, (type, abc.properties.Property)
                    )
                    item_types_list.append(item_type)
            item_types = Types(item_types_list)
        self._item_types = item_types


# noinspection PyUnresolvedReferences
@abc.properties.Dictionary.register
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
        versions: Optional[Sequence[Union[str, Version]]] = None
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
        if (value_types is not None) and not isinstance(
            value_types, Types
        ):
            value_types = Types(value_types)
        self._value_types = value_types


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

