# Tell the linters what's up:
# pylint:disable=wrong-import-position,consider-using-enumerate,useless-object-inheritance
# mccabe:options:max-complexity=999

from __future__ import nested_scopes, generators, division, absolute_import, with_statement, \
   print_function, unicode_literals

from ..utilities.compatibility import backport

backport()  # noqa

from future.utils import native_str

import numbers  # noqa

from copy import deepcopy  # noqa
from datetime import date, datetime  # noqa

try:
    from typing import Union, Optional, Sequence, Mapping, Set, Sequence, Callable, Dict, Any, Hashable, Collection,\
        Tuple
except ImportError:
    Union = Optional = Sequence = Mapping = Set = Sequence = Callable = Dict = Any = Hashable = Collection = Tuple =\
        Iterable = None

import iso8601  # noqa

from ..utilities import collections, collections_abc, qualified_name, properties_values, parameters_defaults, \
    calling_function_qualified_name, indent

from .. import abc, meta
from .types import Types, Null, NULL, NoneType


class Property(object):
    """
    This is the base class for defining a property.

    Properties

        - value_types ([type|Property]): One or more expected value_types or `Property` instances. Values are checked,
          sequentially, against each type or `Property` instance, and the first appropriate match is used.

        - required (bool|collections.Callable): If `True`--dumping the json_object will throw an error if this value
          is `None`.

        - versions ([str]|{str:Property}): The property should be one of the following:

            - A set/tuple/list of version numbers to which this property applies.
            - A mapping of version numbers to an instance of `Property` applicable to that version.

          Version numbers prefixed by "<" indicate any version less than the one specified, so "<3.0" indicates that
          this property is available in versions prior to 3.0. The inverse is true for version numbers prefixed by ">".
          ">=" and "<=" have similar meanings, but are inclusive.

          Versioning can be applied to an json_object by calling `sob.meta.set_version` in the `__init__` method of
          an `sob.model.Object` sub-class. For an example, see `oapi.model.OpenAPI.__init__`.

        - name (str): The name of the property when loaded from or dumped into a JSON/YAML object. Specifying a
          `name` facilitates mapping of PEP8 compliant property to JSON or YAML attribute names,
          which are either camelCased, are python keywords, or otherwise not appropriate for usage in python code.

    """

    def __init__(
        self,
        types=None,  # type: Sequence[Union[type, Property]]
        name=None,  # type: Optional[str]
        required=False,  # type: Union[bool, collections.Callable]
        versions=None,  # type: Optional[Sequence[Union[str, meta.Version]]]
    ):
        self._types = None  # type: Optional[Sequence[Union[type, Property]]]
        self.types = types
        self.name = name
        self.required = required
        self._versions = None  # type: Optional[Union[Mapping[str, Optional[Property]], Set[Union[str, Number]]]]
        self.versions = versions  # type: Optional[Union[Mapping[str, Optional[Property]], Set[Union[str, Number]]]]

    @property
    def types(self):
        return self._types

    @types.setter
    def types(self, types_or_properties):
        # type: (Optional[Sequence[Union[type, Property, abc.model.Model]]]) -> None

        if types_or_properties is not None:
            if callable(types_or_properties):
                if native_str is not str:
                    _types_or_properties = types_or_properties

                    def types_or_properties(d):
                        # type: (Sequence[Union[type, Property, abc.model.Model]]) -> Types
                        return Types(_types_or_properties(d))

            else:
                types_or_properties = Types(types_or_properties)

        self._types = types_or_properties

    @property
    def versions(self):
        # type: () -> Optional[Sequence[meta.Version]]
        return self._versions

    @versions.setter
    def versions(
        self,
        versions  # type: Optional[Sequence[Union[str, collections_abc.Iterable, meta.Version]]]
    ):
        # type: (...) -> Optional[Union[Mapping[str, Optional[Property]], Set[Union[str, Number]]]]
        if versions is not None:

            if isinstance(versions, (str, Number, meta.Version)):
                versions = (versions,)

            if isinstance(versions, collections_abc.Iterable):
                versions = tuple(
                    (v if isinstance(v, meta.Version) else meta.Version(v))
                    for v in versions
                )

            else:

                repr_versions = repr(versions)

                raise TypeError(
                    (
                        '`%s` requires a sequence of version strings or ' %
                        calling_function_qualified_name()
                    ) + (
                        '`%s` instances, not' % qualified_name(meta.Version)
                    ) + (
                        ':\n' + repr_versions
                        if '\n' in repr_versions else
                        ' `%s`.' % repr_versions
                    )
                )

        self._versions = versions

    @staticmethod
    def _repr_argument(argument, value, defaults):
        # type: (str, Any, Dict[str, Any]) -> str

        if (argument not in defaults) or defaults[argument] == value or value is None or value is NULL:
            return None

        value_representation = (
            qualified_name(value)
            if isinstance(value, type) else
            "'%s'" % str(value)
            if isinstance(value, meta.Version) else
            repr(value)
        )

        return '    %s=%s,' % (argument, indent(value_representation))

    def __repr__(self):
        lines = [qualified_name(type(self)) + '(']
        defaults = parameters_defaults(self.__init__)
        for property_name, value in properties_values(self):
            argument_representation = self._repr_argument(property_name, value, defaults)
            if argument_representation is not None:
                lines.append(argument_representation)
        lines[-1] = lines[-1].rstrip(',')
        lines.append(')')
        if len(lines) > 2:
            return '\n'.join(lines)
        else:
            return ''.join(lines)

    def __copy__(self):

        new_instance = self.__class__()

        for a in dir(self):

            if a[0] != '_' and a != 'data':

                v = getattr(self, a)

                if not callable(v):
                    setattr(new_instance, a, v)

        return new_instance

    def __deepcopy__(self, memo):
        # type: (dict) -> Property

        new_instance = self.__class__()

        for a, v in properties_values(self):
            setattr(new_instance, a, deepcopy(v, memo))

        return new_instance


abc.properties.Property.register(Property)


class String(Property):
    """
    See `sob.properties.Property`
    """

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: Union[bool, collections.Callable]
        versions=None,  # type: Optional[Collection]
    ):
        super().__init__(
            types=(str,),
            name=name,
            required=required,
            versions=versions,
        )


abc.properties.String.register(String)


class Date(Property):
    """
    See `sob.properties.Property`

    Additional Properties:

        - date2str (collections.Callable): A function, taking one argument (a python `date` json_object), and returning
          a date string in the desired format. The default is `date.isoformat`--returning an iso8601 compliant date
          string.

        - str2date (collections.Callable): A function, taking one argument (a date string), and returning a python
          `date` json_object. By default, this is `iso8601.parse_date`.
    """

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: Union[bool, collections.Callable]
        versions=None,  # type: Optional[Collection]
        date2str=date.isoformat,  # type: Optional[Callable]
        str2date=iso8601.parse_date  # type: Callable
    ):
        super().__init__(
            types=(date,),
            name=name,
            required=required,
            versions=versions,
        )
        self.date2str = date2str
        self.str2date = str2date


abc.properties.Date.register(Date)


class DateTime(Property):
    """
    See `sob.properties.Property`

    Additional Properties:

        - datetime2str (collections.Callable): A function, taking one argument (a python `datetime` json_object), and
          returning a date-time string in the desired format. The default is `datetime.isoformat`--returning an
          iso8601 compliant date-time string.

        - str2datetime (collections.Callable): A function, taking one argument (a datetime string), and returning a python
          `datetime` json_object. By default, this is `iso8601.parse_date`.
    """

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: Union[bool, collections.Callable]
        versions=None,  # type: Optional[Collection]
        datetime2str=datetime.isoformat,  # type: Optional[Callable]
        str2datetime=iso8601.parse_date  # type: Callable
    ):
        self.datetime2str = datetime2str
        self.str2datetime = str2datetime
        super().__init__(
            types=(datetime,),
            name=name,
            required=required,
            versions=versions,
        )


abc.properties.DateTime.register(Date)


class Bytes(Property):
    """
    See `sob.properties.Property`
    """

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: bool
        versions=None,  # type: Optional[Collection]
    ):
        super().__init__(
            types=(bytes, bytearray),
            name=name,
            required=required,
            versions=versions,
        )


abc.properties.Bytes.register(Date)


class Enumerated(Property):
    """
    See `sob.properties.Property`...

    + Properties:

        - values ([Any]):  A list of possible values.
    """

    def __init__(
        self,
        types=None,  # type: Optional[Sequence[Union[type, Property]]]
        values=None,  # type: Optional[Union[Sequence, Set]]
        name=None,  # type: Optional[str]
        required=False,  # type: Union[bool, collections.Callable]
        versions=None,  # type: Optional[Collection]
    ):
        self._values = None

        super().__init__(
            types=types,
            name=name,
            required=required,
            versions=versions
        )

        self.values = values  # type: Optional[Sequence]

    @property
    def values(self):
        # type: () -> Optional[Union[Tuple, Callable]]
        return self._values

    @values.setter
    def values(self, values):
        # type: (Iterable) -> None

        if not ((values is None) or callable(values)):

            if (values is not None) and (not isinstance(values, (collections_abc.Sequence, collections_abc.Set))):
                raise TypeError(
                    '`values` must be a finite set or sequence, not `%s`.' % qualified_name(type(values))
                )

            # if values is not None:
            #     values = [
            #         sob.model.unmarshal(v, types=self.types)
            #         for v in values
            #     ]

        self._values = values


abc.properties.Enumerated.register(Enumerated)


class Number(Property):
    """
    See `sob.properties.Property`
    """

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: Union[bool, collections.Callable]
        versions=None,  # type: Optional[Collection]
    ):
        # type: (...) -> None
        super().__init__(
            types=(numbers.Number,),
            name=name,
            required=required,
            versions=versions,
        )


abc.properties.Number.register(Number)


class Integer(Property):
    """
    See `sob.properties.Property`
    """

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: Union[bool, collections.Callable]
        versions=None,  # type: Optional[Collection]
    ):
        super().__init__(
            types=(int,),
            name=name,
            required=required,
            versions=versions,
        )


abc.properties.Integer.register(Integer)


class Boolean(Property):
    """
    See `sob.properties.Property`
    """

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: Union[bool, collections.Callable]
        versions=None,  # type: Optional[Collection]
    ):
        # type: (...) -> None
        super().__init__(
            types=(bool,),
            name=name,
            required=required,
            versions=versions,
        )


abc.properties.Boolean.register(Boolean)


class Array(Property):
    """
    See `sob.properties.Property`...

    + Properties:

        - item_types (type|Property|[type|Property]): The type(s) of values/objects contained in the array. Similar to
          `sob.properties.Property().value_types`, but applied to items in the array, not the array itself.
    """

    def __init__(
        self,
        item_types=None,  # type: Optional[Union[type, Sequence[Union[type, Property]]]]
        name=None,  # type: Optional[str]
        required=False,  # type: Union[bool, collections.Callable]
        versions=None,  # type: Optional[Collection]
    ):
        self._item_types = None
        self.item_types = item_types
        super().__init__(
            types=(abc.model.Array,),
            name=name,
            required=required,
            versions=versions,
        )

    @property
    def item_types(self):
        # type: (...) -> Types
        return self._item_types

    @item_types.setter
    def item_types(self, item_types):
        # type: (Optional[Sequence[Union[type, Property, abc.model.Object]]]) -> None
        if item_types is not None:
            if callable(item_types):
                if native_str is not str:
                    _item_types = item_types

                    def item_types(d):
                        # type: (Sequence[Union[type, Property, abc.model.Object]]) -> Types
                        return Types(_item_types(d))
            else:
                item_types = Types(item_types)
        self._item_types = item_types


abc.properties.Array.register(Array)


class Dictionary(Property):
    """
    See `sob.properties.Property`...

    + Properties:

        - value_types (type|Property|[type|Property]): The type(s) of values/objects comprising the mapped
          values. Similar to `sob.properties.Property.types`, but applies to *values* in the dictionary
          object, not the dictionary itself.
    """

    def __init__(
        self,
        value_types=None,  # type: Optional[Union[type, Sequence[Union[type, Property]]]]
        name=None,  # type: Optional[str]
        required=False,  # type: Union[bool, collections.Callable]
        versions=None,  # type: Optional[Collection]
    ):
        self._value_types = None
        self.value_types = value_types
        super().__init__(
            types=(abc.model.Dictionary,),
            name=name,
            required=required,
            versions=versions,
        )

    @property
    def value_types(self):
        return self._value_types

    @value_types.setter
    def value_types(self, value_types_):
        # type: (Optional[Sequence[Union[type, Property, abc.model.Object]]]) -> None
        """
        The `types` can be either:

            - A sequence of types and/or `sob.properties.Property` instances.

            - A function which accepts exactly one argument (a dictionary), and which returns a sequence of types and/or
              `sob.properties.Property` instances.

        If more than one type or property definition is provided, un-marshalling is attempted using each `value_type`,
        in sequential order. If a value could be cast into more than one of the `types` without throwing a
        `ValueError`, `TypeError`, or `sob.errors.ValidationError`, the value type occuring *first* in the sequence
        will be used.
        """

        if value_types_ is not None:

            if callable(value_types_):

                if native_str is not str:

                    original_value_types_ = value_types_

                    def value_types_(data):
                        # type: (Sequence[Union[type, Property, abc.model.Object]]) -> Types
                        return Types(original_value_types_(data))

            else:

                value_types_ = Types(value_types_)

        self._value_types = value_types_


abc.properties.Dictionary.register(Dictionary)
