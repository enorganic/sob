"""
This module defines classes for describing properties of a model.
"""

from __future__ import annotations

import collections
import collections.abc
from collections.abc import Iterable, Sequence
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
)

from sob import abc
from sob._datetime import date2str as _date2str
from sob._datetime import datetime2str as _datetime2str
from sob._datetime import str2date as _str2date
from sob._datetime import str2datetime as _str2datetime
from sob._inspect import get_parameters_defaults
from sob._types import UNDEFINED, NoneType, Undefined
from sob.types import MutableTypes, Types
from sob.utilities import (
    get_qualified_name,
    indent,
    iter_properties_values,
    represent,
)
from sob.version import Version

if TYPE_CHECKING:
    from sob.abc import MarshallableTypes


def _repr_keyword_argument_assignment(
    argument: str,
    value: MarshallableTypes,
    defaults: dict[str, MarshallableTypes] | None = None,
) -> str | None:
    """
    Returns a string representation of an argument assignment, or `None`
    if the argument value is equal to the default value for that argument
    """
    if (defaults is not None) and (
        (argument not in defaults)
        or defaults[argument] == value
        or value is None
    ):
        return None
    return f"    {argument}={indent(represent(value))},"


def has_mutable_types(property_: abc.Property | type) -> bool:
    """
    This function returns `True` if modification of the `.types` member of a
    property class or instance is permitted.

    Parameters:

    - property (sob.properties.Property|type)
    """
    property_type: type
    if isinstance(property_, abc.Property):
        property_type = type(property_)
    else:
        if not issubclass(property_, abc.Property):
            raise TypeError(property_)
        property_type = property_
    return property_type._types is None  # noqa: SLF001


class Property(abc.Property):
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
          compliant property names to JSON attribute names which might
          be incompatible with well-formatted python code due to various
          reasons such as being camelCased, or being python keywords. To
          infer an appropriate property name programmatically, use the utility
          function `sob.utilities.property_name`.
    """

    _types: abc.Types | None = None

    def __init__(
        self,
        types: abc.Types
        | Sequence[type | Property]
        | type
        | Property
        | Undefined
        | None = UNDEFINED,
        name: str | None = None,
        *,
        required: bool = False,
        versions: str
        | abc.Version
        | Iterable[str | abc.Version]
        | None = None,
    ) -> None:
        self._types: abc.Types | None = type(self)._types  # noqa: SLF001
        if types is not UNDEFINED:
            self.types = types  # type: ignore
        self.name: str | None = name
        self.required: bool = required
        self._versions: Sequence[abc.Version] | None = None
        if versions is not None:
            self.versions = versions  # type: ignore

    @property
    def types(self) -> abc.Types | None:
        return self._types

    @types.setter
    def types(
        self,
        types_or_properties: abc.Types
        | Sequence[type | abc.Property]
        | type
        | abc.Property
        | None,
    ) -> None:
        # If types are set at the class-level, don't touch them
        if type(self)._types is not None:  # noqa: SLF001
            message: str = (
                f"`{get_qualified_name(type(self))}.types` is immutable"
            )
            raise TypeError(message)
        if (types_or_properties is not None) and not isinstance(
            types_or_properties, abc.Types
        ):
            types_or_properties = MutableTypes(types_or_properties)
        if not (
            (types_or_properties is None)
            or isinstance(types_or_properties, abc.Types)
        ):
            raise TypeError(types_or_properties)
        self._types = types_or_properties

    @property  # type: ignore
    def versions(self) -> Sequence[abc.Version] | None:
        return self._versions

    @versions.setter
    def versions(
        self,
        versions: str
        | abc.Version
        | Iterable[str | abc.Version]
        | None = None,
    ) -> None:
        versions_tuple: tuple[abc.Version, ...] | None = None
        if versions is not None:
            if not isinstance(
                versions, (str, abc.Version, collections.abc.Iterable)
            ):
                raise TypeError(versions)
            version: str | abc.Version
            if isinstance(versions, str):
                version = Version(versions)
                versions_tuple = (version,)
            elif isinstance(versions, abc.Version):
                versions_tuple = (versions,)
            else:
                versions_list: list[abc.Version] = []
                for version in versions:
                    if not isinstance(version, abc.Version):
                        version = Version(version)  # noqa: PLW2901
                    versions_list.append(version)
                versions_tuple = tuple(versions_list)
        self._versions = versions_tuple

    def __repr__(self) -> str:
        lines = [get_qualified_name(type(self)) + "("]
        defaults: dict[str, Any] = get_parameters_defaults(
            self.__init__  # type: ignore
        )
        for property_name, value in iter_properties_values(self):
            argument_representation = _repr_keyword_argument_assignment(
                property_name, value, defaults
            )
            if argument_representation is not None:
                lines.append(argument_representation)
        lines[-1] = lines[-1].rstrip(",")
        lines.append(")")
        if len(lines) > 2:  # noqa: PLR2004
            return "\n".join(lines)
        return "".join(lines)

    def _copy(self, *, deep: bool, memo: dict | None = None) -> abc.Property:
        new_instance = self.__class__()
        attribute_name: str
        for attribute_name in dir(self):
            if attribute_name in (
                "_types",
                "_date2str",
                "_str2date",
                "_datetime2str",
                "_str2datetime",
            ):
                setattr(
                    new_instance, attribute_name, getattr(self, attribute_name)
                )
            elif not (
                attribute_name.startswith("_")
                or (
                    attribute_name
                    in (
                        "types",
                        "date2str",
                        "str2date",
                        "datetime2str",
                        "str2datetime",
                    )
                )
            ):
                value = getattr(self, attribute_name)
                if deep:
                    value = deepcopy(value, memo=memo)
                if not callable(value):
                    setattr(new_instance, attribute_name, value)
        return new_instance

    def __copy__(self) -> abc.Property:
        return self._copy(deep=False)

    def __deepcopy__(self, memo: dict) -> abc.Property:
        return self._copy(deep=True, memo=memo or {})


class StringProperty(Property, abc.String):
    """
    See `sob.Property`
    """

    _types: abc.Types = Types((str,))  # type: ignore

    def __init__(
        self,
        name: str | None = None,
        *,
        required: bool = False,
        versions: str
        | abc.Version
        | Iterable[str | abc.Version]
        | None = None,
    ) -> None:
        super().__init__(
            name=name,
            required=required,
            versions=versions,
        )


# For backwards compatibility
String = StringProperty


class DateProperty(Property, abc.Date):
    """
    ...See `sob.properties.Property`

    + Parameters:

        - date2str (collections.Callable): A function, taking one argument (a
          python `date` json_object), and returning a date string in the
          desired format. The default is `datetime.date.isoformat`--returning
          an ISO-8601 compliant date string.

        - str2date (collections.Callable): A function, taking one argument (a
          date string), and returning a python `date` object. By default,
          this is `iso8601.iso8601.parse_date`.
    """

    _types: abc.Types | None = Types((date,))

    def __init__(
        self,
        name: str | None = None,
        *,
        required: bool = False,
        versions: str
        | abc.Version
        | Iterable[str | abc.Version]
        | None = None,
        date2str: Callable[[date], str] = _date2str,
        str2date: Callable[[str], date] = _str2date,
    ) -> None:
        super().__init__(
            name=name,
            required=required,
            versions=versions,
        )
        self._date2str = date2str
        self._str2date = str2date

    def date2str(self, value: date) -> str:
        return self._date2str(value)

    def str2date(self, value: str) -> date:
        return self._str2date(value)


# For backwards compatibility
Date = DateProperty


class DateTimeProperty(Property, abc.DateTime):
    """
    (See [`sob.properties.Property`](#Property))

    + Parameters:

    - datetime2str (collections.Callable): A function, taking one argument
      (a python `datetime` json_object), and returning a date-time string
      in the desired format. The default is `datetime.datetime.isoformat`,
      returning an ISO-8601 compliant date/time string.
    - str2datetime (collections.Callable): A function, taking one argument
      (a datetime string), and returning a python `datetime.datetime` object.
      By default, this is `iso8601.iso8601.parse_date`.
    """

    _types: abc.Types = Types((datetime,))  # type: ignore

    def __init__(
        self,
        name: str | None = None,
        *,
        required: bool = False,
        versions: str
        | abc.Version
        | Iterable[str | abc.Version]
        | None = None,
        datetime2str: Callable[[datetime], str] = _datetime2str,
        str2datetime: Callable[[str], datetime] = _str2datetime,
    ) -> None:
        self._datetime2str = datetime2str
        self._str2datetime = str2datetime
        super().__init__(
            name=name,
            required=required,
            versions=versions,
        )

    def datetime2str(self, value: datetime) -> str:
        return self._datetime2str(value)

    def str2datetime(self, value: str) -> datetime:
        return self._str2datetime(value)


# For backwards compatibility
DateTime = DateTimeProperty


class BytesProperty(Property, abc.Bytes):
    """
    (See [`sob.properties.Property`](#Property))

    This class represents a property with binary values
    """

    _types: abc.Types = Types((bytes,))  # type: ignore

    def __init__(
        self,
        name: str | None = None,
        *,
        required: bool = False,
        versions: str
        | abc.Version
        | Iterable[str | abc.Version]
        | None = None,
    ) -> None:
        super().__init__(
            name=name,
            required=required,
            versions=versions,
        )


# For backwards compatibility
Bytes = BytesProperty


class EnumeratedProperty(Property, abc.Enumerated):
    """
    Parameters:

    This class accepts the following keyword parameters in *addition* to all
    parameters applicable to the base class [Property](#Property).

    - values ([typing.Any]):  A list or set of possible values.

    Properties:

    This class exposes public properties matching its keyword parameters.
    """

    def __init__(
        self,
        types: abc.Types
        | Sequence[type | Property]
        | type
        | Property
        | Undefined
        | None = UNDEFINED,
        values: Iterable[MarshallableTypes] | None = None,
        name: str | None = None,
        *,
        required: bool = False,
        versions: str
        | abc.Version
        | Iterable[str | abc.Version]
        | None = None,
    ) -> None:
        self._values: set[MarshallableTypes] | None = None
        super().__init__(
            types=types, name=name, required=required, versions=versions
        )
        self.values = values  # type: ignore

    @property  # type: ignore
    def values(self) -> set[MarshallableTypes] | None:
        return self._values

    @values.setter
    def values(self, values: Iterable[MarshallableTypes] | None) -> None:
        if values is None:
            self._values = None
        else:
            if not isinstance(values, collections.abc.Iterable):
                raise TypeError(values)
            self._values = set(values)


# For backwards compatibility
Enumerated = EnumeratedProperty


class NumberProperty(Property, abc.Number):
    """
    See `sob.properties.Property`
    """

    _types: abc.Types = Types((Decimal, float, int))  # type: ignore

    def __init__(
        self,
        name: str | None = None,
        *,
        required: bool = False,
        versions: str
        | abc.Version
        | Iterable[str | abc.Version]
        | None = None,
    ) -> None:
        super().__init__(name=name, required=required, versions=versions)


# For backwards compatibility
Number = NumberProperty


class IntegerProperty(Property, abc.Integer):
    """
    See `sob.properties.Property`
    """

    _types: abc.Types = Types((int,))  # type: ignore

    def __init__(
        self,
        name: str | None = None,
        *,
        required: bool = False,
        versions: str
        | abc.Version
        | Iterable[str | abc.Version]
        | None = None,
    ) -> None:
        super().__init__(
            name=name,
            required=required,
            versions=versions,
        )


# For backwards compatibility
Integer = IntegerProperty


class BooleanProperty(Property, abc.Boolean):
    """
    See `sob.properties.Property`
    """

    _types: abc.Types = Types((bool,))  # type: ignore

    def __init__(
        self,
        name: str | None = None,
        *,
        required: bool = False,
        versions: str
        | abc.Version
        | Iterable[str | abc.Version]
        | None = None,
    ) -> None:
        super().__init__(
            name=name,
            required=required,
            versions=versions,
        )


# For backwards compatibility
Boolean = BooleanProperty


class ArrayProperty(Property, abc.ArrayProperty):
    """
    See `sob.properties.Property`...

    + Properties:

    - item_types (type|Property|[type|Property]): The type(s) of values/objects
      contained in the array. Similar to
      `sob.properties.Property().types`, but applied to items in the
      array, not the array itself.
    """

    _types: abc.Types = Types((abc.Array,))  # type: ignore
    _item_types: abc.Types | None = None

    def __init__(
        self,
        item_types: type
        | Sequence[type | Property]
        | Undefined
        | abc.Types
        | None = UNDEFINED,
        name: str | None = None,
        *,
        required: bool = False,
        versions: str
        | abc.Version
        | Iterable[str | abc.Version]
        | None = None,
    ) -> None:
        self._item_types: Types | None = type(self)._item_types  # noqa: SLF001
        if item_types is not UNDEFINED:
            self.item_types = item_types  # type: ignore
        super().__init__(
            name=name,
            required=required,
            versions=versions,
        )

    @property  # type: ignore
    def item_types(self) -> abc.Types | None:  # type: ignore
        return self._item_types

    @item_types.setter  # type: ignore
    def item_types(
        self,
        item_types: type
        | abc.Property
        | Sequence[type | abc.Property]
        | abc.Types
        | None,
    ) -> None:
        if isinstance(item_types, abc.Types):
            if not isinstance(item_types, abc.MutableTypes):
                item_types = MutableTypes(item_types)
        elif item_types is not None:
            item_types_list: list[type | abc.Property] = []
            if isinstance(item_types, (type, abc.Property)):
                item_types_list.append(item_types)
            else:
                if not isinstance(item_types, Sequence):
                    raise TypeError(item_types)
                for item_type in item_types:
                    if not isinstance(item_type, (type, abc.Property)):
                        raise TypeError(item_type)
                    item_types_list.append(item_type)
            item_types = MutableTypes(item_types_list)
        if not isinstance(item_types, (abc.Types, NoneType)):
            raise TypeError(item_types)
        self._item_types = item_types


# For backwards compatibility
Array = ArrayProperty


class DictionaryProperty(Property, abc.DictionaryProperty):
    """
    See `sob.properties.Property`...

    + Properties:

    - value_types (type|Property|[type|Property]): The type(s) of
      values/objects comprising the mapped values. Similar to
      `sob.properties.Property.types`, but applies to *values* in the
      dictionary object, not the dictionary itself.
    """

    _types: abc.Types = Types((abc.Dictionary,))  # type: ignore
    _value_types: abc.Types | None = None

    def __init__(
        self,
        value_types: type
        | Sequence[type | Property]
        | Undefined
        | abc.Types
        | None = UNDEFINED,
        name: str | None = None,
        *,
        required: bool = False,
        versions: str
        | abc.Version
        | Iterable[str | abc.Version]
        | None = None,
    ) -> None:
        self._value_types: abc.Types | None = type(  # noqa: SLF001
            self
        )._value_types
        if value_types is not UNDEFINED:
            self.value_types = value_types  # type: ignore
        super().__init__(
            name=name,
            required=required,
            versions=versions,
        )

    @property  # type: ignore
    def value_types(self) -> abc.Types | None:
        return self._value_types

    @value_types.setter
    def value_types(
        self,
        value_types: Sequence[type | abc.Property] | abc.Types | None,
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
            value_types, abc.MutableTypes
        ):
            value_types = MutableTypes(value_types)
        if not isinstance(value_types, (abc.Types, NoneType)):
            raise TypeError(value_types)
        self._value_types = value_types


# For backwards compatibility
Dictionary = DictionaryProperty

# This constant maps data types to their corresponding properties
TYPES_PROPERTIES: dict[type, type] = {
    str: StringProperty,
    date: DateProperty,
    datetime: DateTimeProperty,
    bytes: BytesProperty,
    Decimal: NumberProperty,
    float: NumberProperty,
    int: IntegerProperty,
    bool: BooleanProperty,
    abc.Array: ArrayProperty,
    list: ArrayProperty,
    tuple: ArrayProperty,
    abc.Dictionary: DictionaryProperty,
    dict: DictionaryProperty,
}
