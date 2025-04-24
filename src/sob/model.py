"""
This module defines the building blocks of an `sob` based data model.
"""

from __future__ import annotations

import collections
import collections.abc
import json
import re
from abc import abstractmethod
from base64 import b64decode, b64encode
from collections.abc import (
    Collection,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    Mapping,
    MutableMapping,
    Reversible,
    Sequence,
    ValuesView,
)
from copy import copy, deepcopy
from datetime import date, datetime
from decimal import Decimal
from inspect import signature
from itertools import chain
from types import GeneratorType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    SupportsBytes,
    cast,
)

from typing_extensions import Self

from sob import abc, errors, hooks, meta, utilities
from sob._datetime import date2str, datetime2str
from sob._io import read
from sob._types import NULL, UNDEFINED, NoneType, Null, Undefined
from sob._utilities import deprecated, get_readable_url
from sob.errors import (
    DeserializeError,
    append_exception_text,
    get_exception_text,
)
from sob.utilities import (
    MAX_LINE_LENGTH,
    get_calling_module_name,
    get_method,
    get_qualified_name,
    get_source,
    represent,
    split_long_docstring_lines,
    suffix_long_lines,
)
from sob.utilities import indent as indent_


class Model(abc.Model):
    """
    This class serves as a base class for
    [`sob.Object`](https://sob.enorganic.org/api/model/#sob.model.Object),
    [`sob.Dictionary`](https://sob.enorganic.org/api/model/#sob.model.Dictionary),
    and [`sob.Array`](https://sob.enorganic.org/api/model/#sob.model.Array).
    This class should not be instantiated or sub-classed directly.
    """

    __module__: str = "sob"

    __slots__: tuple[str, ...] = (
        "_instance_meta",
        "_instance_hooks",
        "_url",
        "_pointer",
    )

    _source: str | None = None
    _class_meta: abc.Meta | None = None
    _class_hooks: abc.Hooks | None = None

    def __init__(self) -> None:
        self._instance_meta: abc.Meta | None = None
        self._instance_hooks: abc.Hooks | None = None
        self._url: str | None = None
        self._pointer: str | None = None

    def _init_url(
        self,
        data: Iterable[abc.MarshallableTypes]
        | Mapping[str, abc.MarshallableTypes]
        | abc.Model
        | abc.Readable
        | None,
    ) -> None:
        if isinstance(data, abc.Readable):
            url: str | None = get_readable_url(data)
            if url is not None:
                meta.set_model_url(self, url)

    def _init_format(
        self,
        data: str
        | bytes
        | abc.Readable
        | Mapping[str, abc.MarshallableTypes]
        | Iterable[abc.MarshallableTypes]
        | abc.Model
        | None = None,
    ) -> (
        Iterable[abc.MarshallableTypes]
        | Mapping[str, abc.MarshallableTypes]
        | abc.Model
        | None
    ):
        """
        This method deserializes JSON data.
        """
        deserialized_data: (
            Iterable[abc.MarshallableTypes]
            | Mapping[str, abc.MarshallableTypes]
            | abc.Model
            | None
        )
        if isinstance(data, (str, bytes, abc.Readable)):
            data_read: abc.JSONTypes = deserialize(data)
            if not isinstance(data_read, (Iterable, Mapping, abc.Model)):
                raise TypeError(data_read)
            deserialized_data = data_read
        else:
            if (data is not None) and not isinstance(
                data,
                (
                    Iterable,
                    Mapping,
                    abc.Model,
                ),
            ):
                raise TypeError(data)
            deserialized_data = data
        return deserialized_data

    def _init_pointer(self) -> None:
        """
        This function sets the root pointer value, and recursively applies
        appropriate pointers to child elements.
        """
        if meta.get_model_pointer(self) is None:
            meta.set_model_pointer(self, "#")

    @abstractmethod
    def _marshal(self) -> abc.JSONTypes:
        pass

    @abstractmethod
    def _validate(self, *, raise_errors: bool = True) -> list[str]:
        pass


class Array(Model, abc.Array, abc.Model):
    '''
    This class may either be instantiated directly or serve as a base
    class for defining typed JSON arrays (python lists).

    Typing can be set at the instance level by
    providing the keyword argument `item_types` when initializing an
    instance of `sob.Array`, or by assigning item types to the class
    or instance metadata.

    Example:

        from __future__ import annotations
        from io import StringIO
        from typing import IO, Iterable
        import sob
        from datetime import datetime, date

        class ObjectA(sob.Object):
            __slots__: tuple[str, ...] = (
                "name",
                "iso8601_datetime",
            )

            def __init__(
                self,
                _data: str | IO | dict | None = None,
                name: str | None = None,
                iso8601_datetime: datetime | None = None,
            ) -> None:
                self.name: str | None = name
                self.iso8601_datetime: datetime | None = iso8601_datetime
                super().__init__(_data)


        sob.get_writable_object_meta(ObjectA).properties = sob.Properties([
            ("name", sob.StringProperty()),
            (
                "iso8601_datetime",
                sob.DateTimeProperty(name="iso8601DateTime")
            ),
        ])

        class ObjectB(sob.Object):
            __slots__: tuple[str, ...] = (
                "name",
                "iso8601_date",
            )

            def __init__(
                self,
                _data: str | IO | dict | None = None,
                name: str | None = None,
                iso8601_date: date | None = None,
            ) -> None:
                self.name: str | None = name
                self.iso8601_date: date | None = iso8601_date
                super().__init__(_data)


        sob.get_writable_object_meta(ObjectB).properties = sob.Properties([
            ("name", sob.StringProperty()),
            ("iso8601_date", sob.DateProperty(name="iso8601Date")),
        ])

        class ArrayA(sob.Array):
            def __init__(
                self,
                items: (
                    Iterable[ObjectA|ObjectB|dict]
                    | IO
                    | str
                    | bytes
                    | None
                ) = None,
            ) -> None:
                super().__init__(items)


        sob.get_writable_array_meta(ArrayA).item_types = sob.Types([
            ObjectA, ObjectB
        ])


        # Instances can be initialized using attribute parameters
        array_a_instance_1: ArrayA = ArrayA(
            [
                ObjectA(
                    name="Object A",
                    iso8601_datetime=datetime(1999, 12, 31, 23, 59, 59),
                ),
                ObjectB(
                    name="Object B",
                    iso8601_date=date(1999, 12, 31),
                ),
            ]
        )

        # ...or by passing the JSON data, either as a string, bytes, sequence,
        # or file-like object, as the first positional argument when
        # initializing the class:
        assert array_a_instance_1 == ArrayA(
            """
            [
                {
                    "name": "Object A",
                    "iso8601DateTime": "1999-12-31T23:59:59Z"
                },
                {
                    "name": "Object B",
                    "iso8601Date": "1999-12-31"
                }
            ]
            """
        ) == ArrayA(
            [
                {
                    "name": "Object A",
                    "iso8601DateTime": datetime(1999, 12, 31, 23, 59, 59)
                },
                {
                    "name": "Object B",
                    "iso8601Date": date(1999, 12, 31)
                }
            ]
        ) == ArrayA(
            StringIO(
                """
                [
                    {
                        "name": "Object A",
                        "iso8601DateTime": "1999-12-31T23:59:59Z"
                    },
                    {
                        "name": "Object B",
                        "iso8601Date": "1999-12-31"
                    }
                ]
                """
            )
        )

        # An array instance can be serialized to JSON using the `sob.serialize`
        # function, or by simply casting it as a string

        assert sob.serialize(array_a_instance_1, indent=4) == """
        [
            {
                "name": "Object A",
                "iso8601DateTime": "1999-12-31T23:59:59Z"
            },
            {
                "name": "Object B",
                "iso8601Date": "1999-12-31"
            }
        ]
        """.strip()

        assert str(array_a_instance_1) == (
            '[{"name": "Object A", "iso8601DateTime": "1999-12-31T23:59:59Z"}'
            ', {"name": "Object B", "iso8601Date": "1999-12-31"}]'
        )

        # An array can be converted into a list of JSON-serializable
        # python objects using `sob.marshal`
        assert sob.marshal(array_a_instance_1) == [
            {
                "name": "Object A",
                "iso8601DateTime": "1999-12-31T23:59:59Z"
            },
            {
                "name": "Object B",
                "iso8601Date": "1999-12-31"
            }
        ]
    '''

    __module__: str = "sob"

    __slots__: tuple[str, ...] = (
        "_list",
        "_instance_meta",
        "_instance_hooks",
        "_url",
        "_pointer",
    )

    _class_meta: abc.ArrayMeta | None = None
    _class_hooks: abc.ArrayHooks | None = None

    def __init__(
        self,
        items: abc.Array
        | Iterable[abc.MarshallableTypes]
        | str
        | bytes
        | abc.Readable
        | None = None,
        item_types: Iterable[type | abc.Property]
        | abc.Types
        | type
        | abc.Property
        | None = None,
    ) -> None:
        """
        Parameters:
            items:
            item_types:
        """
        Model.__init__(self)
        self._instance_meta: abc.ArrayMeta | None = None
        self._instance_hooks: abc.ArrayHooks | None = None
        self._list: list[abc.MarshallableTypes] = []
        self._init_url(items)
        deserialized_items: (
            Iterable[abc.MarshallableTypes] | abc.Model | None
        ) = self._init_format(items)
        if not isinstance(deserialized_items, (NoneType, Iterable)):
            raise TypeError(deserialized_items)
        self._init_item_types(deserialized_items, item_types)
        self._init_items(deserialized_items)
        self._init_pointer()

    def _init_item_types(
        self,
        items: Iterable[abc.MarshallableTypes] | abc.Model | None,
        item_types: Iterable[type | abc.Property]
        | abc.Types
        | type
        | abc.Property
        | None,
    ) -> None:
        if item_types is None:
            # If no item types are explicitly attributed, but the initial items
            # are an instance of `Array`, we adopt the item types from that
            # `Array` instance.
            if isinstance(items, abc.Array):
                items_meta: abc.ArrayMeta | None = meta.read_array_meta(items)
                if meta.read_array_meta(self) is not items_meta:
                    meta.write_model_meta(self, deepcopy(items_meta))
        else:
            meta_: abc.ArrayMeta = meta.get_writable_array_meta(self)
            meta_.item_types = item_types  # type: ignore

    def _init_items(
        self, items: Iterable[abc.MarshallableTypes] | abc.Array | None
    ) -> None:
        if items is not None:
            for item in items:
                self.append(item)

    def __getitem__(self, index: int) -> Any:
        return self._list.__getitem__(index)

    def __iter__(self) -> Iterator[Any]:
        return self._list.__iter__()

    def __contains__(self, value: abc.MarshallableTypes) -> bool:
        return self._list.__contains__(value)

    def __reversed__(self) -> abc.Array:
        new_instance: abc.Array = copy(self)
        new_instance.reverse()
        return new_instance

    def index(
        self,
        value: abc.MarshallableTypes,
        start: int = 0,
        stop: int | None = None,
    ) -> int:
        return self._list.index(
            value, start, *([] if stop is None else [stop])
        )

    def count(self, value: abc.MarshallableTypes) -> int:
        return self._list.count(value)

    def __hash__(self) -> int:
        # For the purpose of use in sets and dictionary keys,
        # we want to consider the memory ID of the object to be the hash
        return id(self)

    def __setitem__(self, index: int, value: abc.MarshallableTypes) -> None:
        instance_hooks: abc.ArrayHooks | None = hooks.read_array_hooks(self)
        if instance_hooks and instance_hooks.before_setitem:
            index, value = instance_hooks.before_setitem(self, index, value)
        meta_: abc.ArrayMeta | None = meta.read_array_meta(self)
        item_types: abc.Types | None = (
            None if meta_ is None else meta_.item_types
        )
        value = unmarshal(value, types=item_types or ())
        self._list.__setitem__(index, value)
        if instance_hooks and instance_hooks.after_setitem:
            instance_hooks.after_setitem(self, index, value)

    def __delitem__(self, index: int) -> None:
        self._list.__delitem__(index)

    def insert(self, index: int, value: abc.MarshallableTypes) -> None:
        self._list.insert(index, NULL)
        self.__setitem__(index, value)

    def append(self, value: abc.MarshallableTypes) -> None:
        if not isinstance(value, (*abc.MARSHALLABLE_TYPES, NoneType)):
            raise errors.UnmarshalTypeError(data=value)
        instance_hooks: abc.ArrayHooks | None = hooks.read_array_hooks(self)
        if instance_hooks and instance_hooks.before_append:
            value = instance_hooks.before_append(
                self, cast(abc.MarshallableTypes, value)
            )
        instance_meta: abc.ArrayMeta | None = meta.read_array_meta(self)
        item_types: abc.Types | None = None
        if instance_meta:
            item_types = instance_meta.item_types
        value = unmarshal(
            cast(abc.MarshallableTypes, value), types=item_types or ()
        )
        self._list.append(value)
        if instance_hooks and instance_hooks.after_append:
            instance_hooks.after_append(self, value)

    def clear(self) -> None:
        self._list.clear()

    def reverse(self) -> None:
        self._list.reverse()

    def sort(
        self,
        key: Callable[[Any], Any] | None = None,
        *,
        reverse: bool = False,
    ) -> None:
        self._list.sort(key=key, reverse=reverse)

    def extend(self, values: Iterable[abc.MarshallableTypes]) -> None:
        for value in values:
            self.append(value)

    def pop(self, index: int = -1) -> abc.MarshallableTypes:
        return self._list.pop(index)

    def remove(self, value: abc.MarshallableTypes) -> None:
        self._list.remove(value)

    def __iadd__(self, values: Iterable[abc.MarshallableTypes]) -> Self:
        self.extend(values)
        return self

    def __add__(self, values: Iterable[abc.MarshallableTypes]) -> Self:
        new_array: Self = copy(self)
        return new_array.__iadd__(values)

    def __copy__(self) -> abc.Array:
        return self.__class__(self)

    def __deepcopy__(self, memo: dict | None = None) -> abc.Array:
        new_instance: Array = self.__class__()
        if not isinstance(new_instance, abc.Model):
            raise TypeError(new_instance)
        instance_meta: abc.ArrayMeta | None = meta.read_array_meta(self)
        class_meta: abc.ArrayMeta | None = meta.read_array_meta(type(self))
        if instance_meta is not class_meta:
            meta.write_model_meta(
                new_instance, deepcopy(instance_meta, memo=memo)
            )
        instance_hooks: abc.ArrayHooks | None = hooks.read_array_hooks(self)
        class_hooks: abc.ArrayHooks | None = hooks.read_array_hooks(type(self))
        if instance_hooks is not class_hooks:
            hooks.write_model_hooks(
                new_instance,
                deepcopy(instance_hooks, memo=memo),
            )
        item: abc.MarshallableTypes
        for item in self:
            new_instance.append(deepcopy(item, memo=memo))
        return new_instance

    def _marshal(self) -> Sequence[abc.JSONTypes]:
        data: abc.Model = self
        instance_hooks: abc.ArrayHooks | None = hooks.read_array_hooks(self)
        if instance_hooks and instance_hooks.before_marshal:
            data = instance_hooks.before_marshal(data)
        metadata: abc.ArrayMeta | None = meta.read_array_meta(self)
        if not isinstance(data, abc.Array):
            raise TypeError(data)
        marshalled_data: Sequence[abc.JSONTypes] = [
            marshal(
                item, types=None if metadata is None else metadata.item_types
            )
            for item in data
        ]
        if instance_hooks and instance_hooks.after_marshal:
            after_marshal_data: abc.JSONTypes = instance_hooks.after_marshal(
                marshalled_data
            )
            if not isinstance(after_marshal_data, Sequence):
                raise TypeError(after_marshal_data)
            marshalled_data = after_marshal_data
        return marshalled_data

    def _validate(self, *, raise_errors: bool = True) -> list[str]:
        validation_errors: list[str] = []
        instance_hooks: abc.ArrayHooks | None = hooks.read_array_hooks(self)
        data: abc.Model = self
        if instance_hooks and instance_hooks.before_validate:
            data = instance_hooks.before_validate(self)
        instance_meta: abc.ArrayMeta | None = meta.read_array_meta(self)
        if instance_meta and instance_meta.item_types:
            item: Any
            if not isinstance(data, abc.Array):
                raise TypeError(data)
            for item in data:
                validation_errors.extend(
                    validate(
                        item, instance_meta.item_types, raise_errors=False
                    )
                )
        if instance_hooks and instance_hooks.after_validate:
            instance_hooks.after_validate(data)
        if raise_errors and validation_errors:
            raise errors.ValidationError("\n".join(validation_errors))
        return validation_errors

    @staticmethod
    def _repr_item(item: Any) -> str:
        """
        A string representation of an item in this array which can be used to
        recreate the item
        """
        item_representation = (
            get_qualified_name(item) if isinstance(item, type) else repr(item)
        )
        item_lines = item_representation.split("\n")
        if len(item_lines) > 1:
            item_representation = "\n        ".join(item_lines)
        return f"        {item_representation},"

    def __repr__(self) -> str:
        # This returns a string representation of this array which can be
        # used to recreate the array
        instance_meta: abc.ArrayMeta | None = meta.read_array_meta(self)
        class_meta: abc.ArrayMeta | None = meta.read_array_meta(type(self))
        representation_lines = [get_qualified_name(type(self)) + "("]
        if len(self) > 0:
            representation_lines.append("    [")
            representation_lines.extend(map(self._repr_item, self))
            representation_lines[-1] = representation_lines[-1].rstrip(",")
            representation_lines.append(
                "    ]"
                + (
                    ","
                    if (
                        (instance_meta is not None)
                        and instance_meta != class_meta
                        and instance_meta.item_types
                    )
                    else ""
                )
            )
        if (
            instance_meta
            and instance_meta != class_meta
            and instance_meta.item_types
        ):
            representation_lines.append(
                "    item_types=" + indent_(repr(instance_meta.item_types))
            )
        representation_lines.append(")")
        representation: str
        if len(representation_lines) > 2:  # noqa: PLR2004
            representation = "\n".join(representation_lines)
        else:
            representation = "".join(representation_lines)
        return representation

    def __len__(self) -> int:
        return self._list.__len__()

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        length: int = len(self)
        if TYPE_CHECKING:
            assert isinstance(other, Sequence)
        if length != len(other):
            return False
        index: int
        return all(self[index] == other[index] for index in range(length))

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __str__(self) -> str:
        return serialize(self)


class Dictionary(Model, abc.Dictionary, abc.Model):
    '''
    This class may either be instantiated directly or serve as a base
    class for defining JSON objects for which there is not a
    predetermined set of properties/attributes, but for which there may
    be a pre-determined set of permitted value types.

    Typing can be set at the instance level by
    providing the keyword argument `value_types` when initializing an
    instance of `sob.Dictionary`, or by assigning value types to the class
    or instance metadata.

    Example:

        from __future__ import annotations
        import sob
        from io import StringIO
        from typing import IO, Any, Iterable, Mapping
        from datetime import datetime, date

        class ObjectA(sob.Object):
            __slots__: tuple[str, ...] = (
                "name",
                "iso8601_datetime",
            )

            def __init__(
                self,
                _data: str | IO | dict | None = None,
                name: str | None = None,
                iso8601_datetime: datetime | None = None,
            ) -> None:
                self.name: str | None = name
                self.iso8601_datetime: datetime | None = iso8601_datetime
                super().__init__(_data)


        sob.get_writable_object_meta(ObjectA).properties = sob.Properties([
            ("name", sob.StringProperty()),
            (
                "iso8601_datetime",
                sob.DateTimeProperty(name="iso8601DateTime")
            ),
        ])

        class ObjectB(sob.Object):
            __slots__: tuple[str, ...] = (
                "name",
                "iso8601_date",
            )

            def __init__(
                self,
                _data: str | IO | dict | None = None,
                name: str | None = None,
                iso8601_date: date | None = None,
            ) -> None:
                self.name: str | None = name
                self.iso8601_date: date | None = iso8601_date
                super().__init__(_data)


        sob.get_writable_object_meta(ObjectB).properties = sob.Properties([
            ("name", sob.StringProperty()),
            ("iso8601_date", sob.DateProperty(name="iso8601Date")),
        ])

        class DictionaryA(sob.Dictionary):
            def __init__(
                self,
                items: (
                    Mapping[str, Any]
                    | Iterable[tuple[str, ObjectA|ObjectB|dict]]
                    | IO
                    | str
                    | bytes
                    | None
                ) = None,
            ) -> None:
                super().__init__(items)


        sob.get_writable_dictionary_meta(DictionaryA).value_types = sob.Types([
            ObjectA, ObjectB
        ])


        # Instances can be initialized with a dictionary
        dictionary_a_instance_1: DictionaryA = DictionaryA(
            {
                "a": ObjectA(
                    name="Object A",
                    iso8601_datetime=datetime(1999, 12, 31, 23, 59, 59),
                ),
                "b": ObjectB(
                    name="Object B",
                    iso8601_date=date(1999, 12, 31),
                ),
            }
        )

        # ...or by passing the JSON data, either as a string, bytes, sequence,
        # or file-like object, as the first positional argument when
        # initializing the class:
        assert dictionary_a_instance_1 == DictionaryA(
            """
            {
                "a": {
                    "name": "Object A",
                    "iso8601DateTime": "1999-12-31T23:59:59Z"
                },
                "b": {
                    "name": "Object B",
                    "iso8601Date": "1999-12-31"
                }
            }
            """
        ) == DictionaryA(
            StringIO(
                """
                {
                    "a": {
                        "name": "Object A",
                        "iso8601DateTime": "1999-12-31T23:59:59Z"
                    },
                    "b": {
                        "name": "Object B",
                        "iso8601Date": "1999-12-31"
                    }
                }
                """
            )
        ) == DictionaryA(
            (
                (
                    "a",
                    ObjectA(
                        name="Object A",
                        iso8601_datetime=datetime(1999, 12, 31, 23, 59, 59),
                    )
                ),
                (
                    "b",
                    ObjectB(
                        name="Object B",
                        iso8601_date=date(1999, 12, 31),
                    )
                ),
            )
        )

        # A dictionary instance can be serialized to JSON using the
        # `sob.serialize` function, or by simply casting it as a string
        assert sob.serialize(dictionary_a_instance_1, indent=4) == """
        {
            "a": {
                "name": "Object A",
                "iso8601DateTime": "1999-12-31T23:59:59Z"
            },
            "b": {
                "name": "Object B",
                "iso8601Date": "1999-12-31"
            }
        }
        """.strip()

        assert str(dictionary_a_instance_1) == (
            '{"a": {"name": "Object A", "iso8601DateTime": '
            '"1999-12-31T23:59:59Z"}, "b": {"name": "Object B", '
            '"iso8601Date": "1999-12-31"}}'
        )

        # A dictionary can be converted into a JSON-serializable
        # objects using `sob.marshal`
        assert sob.marshal(dictionary_a_instance_1) == {
            "a": {
                "name": "Object A",
                "iso8601DateTime": "1999-12-31T23:59:59Z"
            },
            "b": {
                "name": "Object B",
                "iso8601Date": "1999-12-31"
            }
        }
    '''

    __module__: str = "sob"

    __slots__: tuple[str, ...] = (
        "_dict",
        "_instance_meta",
        "_instance_hooks",
        "_url",
        "_pointer",
    )

    _class_hooks: abc.DictionaryHooks | None = None
    _class_meta: abc.DictionaryMeta | None = None

    def __init__(
        self,
        items: abc.Dictionary
        | Mapping[str, abc.MarshallableTypes]
        | Iterable[tuple[str, abc.MarshallableTypes]]
        | abc.Readable
        | str
        | bytes
        | None = None,
        value_types: Iterable[type | abc.Property]
        | type
        | abc.Property
        | abc.Types
        | None = None,
    ) -> None:
        Model.__init__(self)
        self._instance_hooks: abc.DictionaryHooks | None = None
        self._instance_meta: abc.DictionaryMeta | None = None
        self._dict: dict[str, abc.MarshallableTypes] = {}
        self._init_url(items)
        deserialized_items: (
            Iterable[abc.MarshallableTypes]
            | Mapping[str, abc.MarshallableTypes]
            | abc.Model
            | None
        ) = self._init_format(items)
        self._init_value_types(deserialized_items, value_types)  # type: ignore
        self._init_items(deserialized_items)  # type: ignore
        self._init_pointer()

    def _init_format(
        self,
        data: str
        | bytes
        | abc.Readable
        | Mapping[str, abc.MarshallableTypes]
        | Iterable[abc.MarshallableTypes]
        | abc.Model
        | None = None,
    ) -> (
        Iterable[abc.MarshallableTypes]
        | Mapping[str, abc.MarshallableTypes]
        | abc.Model
        | None
    ):
        deserialized_items: (
            Iterable[abc.MarshallableTypes]
            | Mapping[str, abc.MarshallableTypes]
            | abc.Model
            | None
        ) = super()._init_format(data)
        if not isinstance(
            deserialized_items, (abc.Dictionary, Mapping, NoneType)
        ) and isinstance(deserialized_items, Iterable):
            deserialized_items = dict(
                deserialized_items  # type: ignore
            )
        if (deserialized_items is not None) and not isinstance(
            deserialized_items,
            (abc.Dictionary, Mapping, NoneType),
        ):
            raise TypeError(deserialized_items)
        return deserialized_items

    def _init_items(
        self,
        data: Mapping[str, abc.MarshallableTypes]
        | Iterable[tuple[str, abc.MarshallableTypes]]
        | abc.Dictionary
        | None,
    ) -> None:
        if data is not None:
            items: Iterable[tuple[str, abc.MarshallableTypes]]
            if isinstance(data, (dict, abc.Dictionary)) or (
                isinstance(data, Mapping) and isinstance(data, Reversible)
            ):
                items = data.items()
            elif isinstance(data, Mapping):
                items = sorted(data.items(), key=lambda item: item[0])
            else:
                items = data
            key: str
            value: abc.MarshallableTypes
            for key, value in items:
                self.__setitem__(key, value)

    def _init_value_types(
        self,
        items: Mapping[str, abc.MarshallableTypes] | abc.Dictionary | None,
        value_types: Iterable[type | abc.Property]
        | type
        | abc.Property
        | abc.Types
        | None,
    ) -> None:
        if value_types is None:
            # If no value types are explicitly attributed, but the initial
            # items are an instance of `Dictionary`, we adopt the item types
            # from that `Array` instance.
            if isinstance(items, abc.Dictionary):
                meta_: abc.DictionaryMeta | None = meta.read_dictionary_meta(
                    self
                )
                values_meta: abc.DictionaryMeta | None = (
                    meta.read_dictionary_meta(items)
                )
                if meta_ is not values_meta:
                    meta.write_model_meta(self, deepcopy(values_meta))
        else:
            writable_meta: abc.Meta = meta.get_writable_dictionary_meta(self)
            if not isinstance(writable_meta, abc.DictionaryMeta):
                raise TypeError(writable_meta)
            writable_meta.value_types = value_types  # type: ignore

    def __hash__(self) -> int:
        # For the purpose of use in sets and dictionary keys,
        # we want to consider the memory ID of the object to be the hash
        return id(self)

    def __setitem__(self, key: str, value: abc.MarshallableTypes) -> None:
        message: str
        instance_hooks: abc.DictionaryHooks | None = (
            hooks.read_dictionary_hooks(self)
        )
        if instance_hooks and instance_hooks.before_setitem:
            key, value = instance_hooks.before_setitem(self, key, value)
        instance_meta: abc.DictionaryMeta | None = meta.read_dictionary_meta(
            self
        )
        value_types: abc.Types | None = None
        if instance_meta:
            value_types = instance_meta.value_types
        try:
            unmarshalled_value: abc.MarshallableTypes = unmarshal(
                value, types=value_types or ()
            )
        except TypeError as error:
            message = f"\n - {get_qualified_name(type(self))}['{key}']: {{}}"
            if error.args and isinstance(error.args[0], str):
                error.args = tuple(
                    chain((message.format(error.args[0]),), error.args[1:])
                )
            else:
                error.args = (message.format(repr(value)),)
            raise
        if unmarshalled_value is None:
            message = f"{key} = {unmarshalled_value!r}"
            raise RuntimeError(message)
        self._dict.__setitem__(key, unmarshalled_value)
        if instance_hooks and instance_hooks.after_setitem:
            instance_hooks.after_setitem(self, key, unmarshalled_value)

    def __copy__(self) -> abc.Dictionary:
        new_instance: abc.Dictionary = self.__class__()
        instance_meta: abc.DictionaryMeta | None = meta.read_dictionary_meta(
            self
        )
        class_meta: abc.DictionaryMeta | None = meta.read_dictionary_meta(
            type(self)
        )
        if instance_meta is not class_meta:
            meta.write_model_meta(new_instance, instance_meta)
        instance_hooks: abc.DictionaryHooks | None = (
            hooks.read_dictionary_hooks(self)
        )
        class_hooks: abc.DictionaryHooks | None = hooks.read_dictionary_hooks(
            type(self)
        )
        if instance_hooks is not class_hooks:
            hooks.write_model_hooks(new_instance, instance_hooks)
        key: str
        value: abc.MarshallableTypes
        for key, value in self.items():
            new_instance[key] = value
        return new_instance

    def __deepcopy__(self, memo: dict | None = None) -> Dictionary:
        new_instance = self.__class__()
        instance_meta: abc.DictionaryMeta | None = meta.read_dictionary_meta(
            self
        )
        class_meta: abc.DictionaryMeta | None = meta.read_dictionary_meta(
            type(self)
        )
        if instance_meta is not class_meta:
            meta.write_model_meta(
                new_instance, deepcopy(instance_meta, memo=memo)
            )
        instance_hooks: abc.DictionaryHooks | None = (
            hooks.read_dictionary_hooks(self)
        )
        class_hooks: abc.DictionaryHooks | None = hooks.read_dictionary_hooks(
            type(self)
        )
        if instance_hooks is not class_hooks:
            hooks.write_model_hooks(
                new_instance, deepcopy(instance_hooks, memo=memo)
            )
        key: str
        value: abc.MarshallableTypes
        for key, value in self.items():
            new_instance[key] = deepcopy(value, memo=memo)
        return new_instance

    def _marshal(self) -> dict[str, abc.JSONTypes]:
        """
        This method marshals an instance of `Dictionary` as built-in type
        `dict` which can be serialized into JSON.
        """
        # Check for hooks
        instance_hooks: abc.DictionaryHooks | None = (
            hooks.read_dictionary_hooks(self)
        )
        # This variable is needed because before-marshal hooks are permitted to
        # return altered *copies* of `self`, so prior to marshalling--this
        # variable may no longer point to `self`
        data: abc.Model = self
        # Execute before-marshal hooks, if applicable
        if instance_hooks and instance_hooks.before_marshal:
            data = instance_hooks.before_marshal(data)
        if not isinstance(data, abc.Dictionary):
            raise TypeError(data)
        # Get the metadata, if any has been assigned
        instance_meta: abc.DictionaryMeta | None = meta.read_dictionary_meta(
            data
        )
        # Check to see if value types are defined in the metadata
        value_types: abc.Types | None = (
            instance_meta.value_types if instance_meta else None
        )
        # Recursively convert the data to generic, serializable, data types
        marshalled_data: dict[str, abc.JSONTypes] = {
            key: marshal(value, types=value_types)
            for key, value in data.items()
        }
        # Execute after-marshal hooks, if applicable
        if (instance_hooks is not None) and (
            instance_hooks.after_marshal is not None
        ):
            after_marshal_data: abc.JSONTypes = instance_hooks.after_marshal(
                marshalled_data
            )
            after_marshal_dictionary: dict[str, abc.JSONTypes]
            if isinstance(after_marshal_data, dict):
                after_marshal_dictionary = after_marshal_data
            elif isinstance(after_marshal_data, Reversible) and isinstance(
                after_marshal_data, (Mapping, abc.Dictionary)
            ):
                after_marshal_dictionary = dict(after_marshal_data.items())
            else:
                if not isinstance(after_marshal_data, Mapping):
                    raise TypeError(after_marshal_data)
                after_marshal_dictionary = dict(
                    sorted(
                        after_marshal_data.items(), key=lambda item: item[0]
                    )
                )
            marshalled_data = after_marshal_dictionary
        return marshalled_data

    def _validate(self, *, raise_errors: bool = True) -> list[str]:
        """
        Recursively validate
        """
        validation_errors: list[str] = []
        hooks_: abc.DictionaryHooks | None = hooks.read_dictionary_hooks(self)
        data: abc.Model = self
        if hooks_ and hooks_.before_validate:
            data = hooks_.before_validate(data)
        if not isinstance(data, (NoneType, abc.Dictionary)):
            raise TypeError(data)
        meta_: abc.DictionaryMeta | None = meta.read_dictionary_meta(data)
        value_types: abc.Types | None = meta_.value_types if meta_ else None
        if value_types is not None:
            if not isinstance(data, abc.Dictionary):
                raise TypeError(data)
            value: abc.MarshallableTypes
            for value in data.values():
                value_validation_errors = validate(
                    value, value_types, raise_errors=False
                )
                validation_errors.extend(value_validation_errors)
        if (hooks_ is not None) and (hooks_.after_validate is not None):
            hooks_.after_validate(data)
        if raise_errors and validation_errors:
            raise errors.ValidationError("\n".join(validation_errors))
        return validation_errors

    @staticmethod
    def _repr_item(key: str, value: Any) -> str:
        value_representation = (
            get_qualified_name(value)
            if isinstance(value, type)
            else repr(value)
        )
        value_representation_lines = value_representation.split("\n")
        if len(value_representation_lines) > 1:
            indented_lines = [value_representation_lines[0]]
            line: str
            indented_lines.extend(
                f"            {line}"
                for line in value_representation_lines[1:]
            )
            value_representation = "\n".join(indented_lines)
            representation = "\n".join(
                [
                    "        (",
                    f"            {key!r},",
                    f"            {value_representation}",
                    "        ),",
                ]
            )
        else:
            representation = f"        ({key!r}, {value_representation}),"
        return representation

    def __repr__(self) -> str:
        # This returns a string representation of this dictionary which can be
        # used to recreate the dictionary
        class_meta: abc.DictionaryMeta | None = meta.read_dictionary_meta(
            type(self)
        )
        instance_meta: abc.DictionaryMeta | None = meta.read_dictionary_meta(
            self
        )
        representation_lines: list[str] = [
            get_qualified_name(type(self)) + "("
        ]
        items: tuple[tuple[str, abc.MarshallableTypes], ...] = tuple(
            self.items()
        )
        if len(items) > 0:
            representation_lines.append("    [")
            key: str
            value: abc.MarshallableTypes
            for key, value in items:
                representation_lines.append(self._repr_item(key, value))
            # Strip the last comma
            # representation[-1] = representation[-1][:-1]
            representation_lines.append(
                "    ]"
                + (
                    ","
                    if (
                        instance_meta != class_meta
                        and instance_meta is not None
                        and instance_meta.value_types
                    )
                    else ""
                )
            )
        if (
            instance_meta != class_meta
            and instance_meta
            and instance_meta.value_types
        ):
            representation_lines.append(
                "    value_types=" + indent_(repr(instance_meta.value_types)),
            )
        representation_lines.append(")")
        if len(representation_lines) > 2:  # noqa: PLR2004
            representation = "\n".join(representation_lines)
        else:
            representation = "".join(representation_lines)
        return representation

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if TYPE_CHECKING:
            assert isinstance(other, Mapping)
        keys = tuple(self.keys())
        other_keys = tuple(other.keys())
        if keys != other_keys:
            return False
        key: str
        return all(self[key] == other[key] for key in keys)

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __str__(self) -> str:
        return serialize(self)

    def __delitem__(self, key: str) -> None:
        self._dict.__delitem__(key)

    def pop(self, key: str, default: Undefined = UNDEFINED) -> Any:
        return self._dict.pop(
            key, *([] if default is UNDEFINED else [default])
        )

    def popitem(self) -> tuple[str, Any]:
        return self._dict.popitem()

    def clear(self) -> None:
        self._dict.clear()

    def update(
        self,
        *args: Mapping[str, abc.MarshallableTypes]
        | Iterable[tuple[str, abc.MarshallableTypes]]
        | abc.Dictionary,
        **kwargs: abc.MarshallableTypes,
    ) -> None:
        other: (
            Mapping[str, abc.MarshallableTypes]
            | Iterable[tuple[str, abc.MarshallableTypes]]
            | abc.Dictionary
        )
        key: str
        value: abc.MarshallableTypes
        items: Iterable[tuple[str, abc.MarshallableTypes]] = ()
        for other in args:
            if isinstance(other, (Mapping, abc.Dictionary)):
                items = chain(items, other.items())
            else:
                items = chain(items, other)
        for key, value in chain(items, kwargs.items()):
            self[key] = value

    def setdefault(
        self, key: str, default: abc.MarshallableTypes = None
    ) -> Any:
        try:
            return self[key]
        except KeyError:
            self[key] = default
        return default

    def __getitem__(self, key: str) -> Any:
        return self._dict.__getitem__(key)

    def get(
        self, key: str, default: abc.MarshallableTypes = None
    ) -> Any | None:
        return self._dict.get(key, default)

    def __contains__(self, key: str) -> bool:
        return self._dict.__contains__(key)

    def keys(self) -> KeysView[str]:
        return self._dict.keys()

    def items(self) -> ItemsView[str, Any]:
        return self._dict.items()

    def values(self) -> ValuesView[Any]:
        return self._dict.values()

    def __len__(self) -> int:
        return self._dict.__len__()

    def __iter__(self) -> Iterator[str]:
        return self._dict.__iter__()

    def __reversed__(self) -> Iterator[str]:
        return reversed(self._dict)  # type: ignore


class Object(Model, abc.Object, abc.Model):
    '''
    This class serves as a base for defining models for JSON objects
    (python dictionaries) which have a predetermined set of properties
    (attributes). This class should not be instantiated directly, but rather
    sub-classed to create object models.

    Example:

        from __future__ import annotations
        from io import StringIO
        from typing import IO, Iterable
        import sob
        from datetime import datetime, date

        class ObjectA(sob.Object):
            __slots__: tuple[str, ...] = (
                "boolean",
                "boolean_or_string",
                "integer",
                "number",
                "object_a",
                "iso8601_datetime",
                "iso8601_date",
            )

            def __init__(
                self,
                _data: str | IO | dict | Iterable | None = None,
                boolean: bool | None = None,
                boolean_or_string: bool | str | None = None,
                integer: int | None = None,
                enumerated: int | None = None,
                number: float | None = None,
                object_a: ObjectA | None = None,
                iso8601_datetime: datetime | None = None,
                iso8601_date: date | None = None,
            ) -> None:
                self.boolean: bool | None = boolean
                self.boolean_or_string: bool | str | None = boolean_or_string
                self.integer: int | None = integer
                self.enumerated: int | None = enumerated
                self.number: float | None = integer
                self.object_a: ObjectA | None = None
                self.iso8601_datetime: datetime | None = iso8601_datetime
                self.iso8601_date: date | None = iso8601_date
                super().__init__(_data)


        sob.get_writable_object_meta(ObjectA).properties = sob.Properties([
            ("boolean", sob.BooleanProperty()),
            (
                "boolean_or_string",
                sob.Property(
                    name="booleanOrString",
                    types=sob.Types([bool, str])
                )
            ),
            ("integer", sob.IntegerProperty()),
            ("enumerated", sob.EnumeratedProperty(values=(1, 2, 3))),
            ("number", sob.NumberProperty()),
            (
                "iso8601_datetime",
                sob.DateTimeProperty(name="iso8601DateTime")
            ),
            ("iso8601_date", sob.DateProperty(name="iso8601Date")),
        ])

        # Instances can be initialized using attribute parameters
        object_a_instance_1: ObjectA = ObjectA(
            boolean=True,
            boolean_or_string="Maybe",
            integer=99,
            enumerated=2,
            number=3.14,
            iso8601_datetime=datetime(1999, 12, 31, 23, 59, 59),
            iso8601_date=date(1999, 12, 31),
        )

        # ...or by passing the JSON data, either as a string, bytes, dict, or
        # file-like object, as the first positional argument when initializing
        # the class:
        assert object_a_instance_1 == ObjectA(
            """
            {
                "boolean": true,
                "booleanOrString": "Maybe",
                "integer": 99,
                "enumerated": 2,
                "number": 99,
                "iso8601DateTime": "1999-12-31T23:59:59Z",
                "iso8601Date": "1999-12-31"
            }
            """
        ) == ObjectA(
            {
                "boolean": True,
                "booleanOrString": "Maybe",
                "integer": 99,
                "enumerated": 2,
                "number": 99,
                "iso8601DateTime": datetime(1999, 12, 31, 23, 59, 59),
                "iso8601Date": date(1999, 12, 31)
            }
        ) == ObjectA(
            (
                ("boolean", True),
                ("booleanOrString", "Maybe"),
                ("integer", 99),
                ("enumerated", 2),
                ("number", 99),
                ("iso8601DateTime", datetime(1999, 12, 31, 23, 59, 59)),
                ("iso8601Date", date(1999, 12, 31))
            )
        ) == ObjectA(
            StringIO(
                """
                {
                    "boolean": true,
                    "booleanOrString": "Maybe",
                    "integer": 99,
                    "enumerated": 2,
                    "number": 99,
                    "iso8601DateTime": "1999-12-31T23:59:59Z",
                    "iso8601Date": "1999-12-31"
                }
                """
            )
        )

        # An object instance can be serialized to JSON using the
        # `sob.serialize` function, or by simply casting it as a string

        assert sob.serialize(object_a_instance_1, indent=4) == """
        {
            "boolean": true,
            "booleanOrString": "Maybe",
            "integer": 99,
            "enumerated": 2,
            "number": 99,
            "iso8601DateTime": "1999-12-31T23:59:59Z",
            "iso8601Date": "1999-12-31"
        }
        """.strip()

        assert str(object_a_instance_1) == (
            '{"boolean": true, "booleanOrString": "Maybe", "integer": 99, '
            '"enumerated": 2, "number": 99, '
            '"iso8601DateTime": "1999-12-31T23:59:59Z", '
            '"iso8601Date": "1999-12-31"}'
        )

        # An object can be converted into a dictionary of JSON-serializable
        # python objects using `sob.marshal`
        assert sob.marshal(object_a_instance_1) == {
            "boolean": True,
            "booleanOrString": "Maybe",
            "integer": 99,
            "enumerated": 2,
            "number": 99,
            "iso8601DateTime": "1999-12-31T23:59:59Z",
            "iso8601Date": "1999-12-31"
        }
    '''

    __module__: str = "sob"

    __slots__: tuple[str, ...] = (
        "_instance_meta",
        "_instance_hooks",
        "_url",
        "_pointer",
    )
    _class_meta: abc.ObjectMeta | None = None
    _class_hooks: abc.ObjectHooks | None = None

    def __init__(
        self,
        _data: abc.Object
        | abc.Dictionary
        | Mapping[str, abc.MarshallableTypes]
        | Iterable[tuple[str, abc.MarshallableTypes]]
        | abc.Readable
        | str
        | bytes
        | None = None,
    ) -> None:
        """
        Parameters:
            _data: JSON data with which to initialize this object. This may
                be a dictionary/mapping, a JSON string or bytes, a
                file-like object containing JSON data, or an iterable of
                key/value tuples.
        """
        self._instance_meta: abc.ObjectMeta | None = None
        self._instance_hooks: abc.ObjectHooks | None = None
        self._extra: dict[str, abc.MarshallableTypes] | None = None
        Model.__init__(self)
        self._init_url(_data)
        deserialized_data: (
            Iterable[abc.MarshallableTypes]
            | Mapping[str, abc.MarshallableTypes]
            | abc.Model
            | None
        ) = self._init_format(_data)
        if not (
            isinstance(
                deserialized_data, (abc.Object, abc.Dictionary, dict, Mapping)
            )
            or (deserialized_data is None)
        ):
            raise TypeError(deserialized_data)
        self._data_init(deserialized_data)
        self._init_pointer()

    def _data_init(
        self,
        data: Mapping[str, abc.MarshallableTypes]
        | abc.Object
        | abc.Dictionary
        | None,
    ) -> None:
        if data is not None:
            if isinstance(data, abc.Object):
                self._copy_init(data)
            else:
                if TYPE_CHECKING:
                    assert not isinstance(data, abc.Object)
                self._dict_init(data)

    def _dict_init(
        self,
        dictionary: Mapping[str, abc.MarshallableTypes] | abc.Dictionary,
    ) -> None:
        """
        Initialize this object from a dictionary
        """
        key: str
        value: abc.MarshallableTypes
        for key, value in dictionary.items():
            if value is None:
                value = NULL  # noqa: PLW2901
            self.__setitem__(key, value)

    def _copy_init(self, other: abc.Object) -> None:
        """
        Initialize this object from another `Object` (copy constructor)
        """
        other_meta: abc.ObjectMeta | None = meta.read_object_meta(other)
        if meta.read_object_meta(self) is not other_meta:
            meta.write_model_meta(self, deepcopy(other_meta))
        instance_hooks: abc.ObjectHooks | None = hooks.read_object_hooks(other)
        if hooks.read_object_hooks(self) is not instance_hooks:
            hooks.write_model_hooks(self, deepcopy(instance_hooks))
        if other_meta and other_meta.properties:
            for property_name_ in other_meta.properties:
                try:
                    setattr(
                        self, property_name_, getattr(other, property_name_)
                    )
                except TypeError as error:
                    label: str = (
                        f"\n - {get_qualified_name(type(self))}."
                        f"{property_name_}: "
                    )
                    if error.args:
                        error.args = tuple(
                            chain((label + error.args[0],), error.args[1:])
                        )
                    else:
                        error.args = (label + serialize(other),)
                    raise
            meta.set_model_url(self, meta.get_model_url(other))
            meta.set_model_pointer(self, meta.get_model_pointer(other))

    def __hash__(self) -> int:
        # For the purpose of use in sets and dictionary keys,
        # we want to consider the memory ID of the object to be the hash
        return id(self)

    def _get_property_definition(self, property_name_: str) -> abc.Property:
        """
        Get a property's definition
        """
        meta_: abc.ObjectMeta | None = meta.read_object_meta(self)
        if meta_ and meta_.properties:
            try:
                return meta_.properties[property_name_]
            except (KeyError, AttributeError):
                pass
        message: str = (
            f"`{get_qualified_name(type(self))}` has no attribute "
            f'"{property_name_}".'
        )
        raise KeyError(message)

    def _unmarshal_value(
        self, property_name_: str, value: abc.MarshallableTypes
    ) -> abc.MarshallableTypes:
        """
        Unmarshall a property value
        """
        property_definition = self._get_property_definition(property_name_)
        if value is not None:
            if isinstance(value, GeneratorType):
                value = tuple(value)
            try:
                value = _unmarshal_property_value(property_definition, value)
            except (TypeError, ValueError) as error:
                message: str = (
                    f"\n - {get_qualified_name(type(self))}.{property_name_}: "
                )
                if error.args and isinstance(error.args[0], str):
                    error.args = tuple(
                        chain((message + error.args[0],), error.args[1:])
                    )
                else:
                    error.args = (message + repr(value),)
                raise
        return value

    def __setattr__(
        self, property_name_: str, value: abc.MarshallableTypes
    ) -> None:
        unmarshalled_value: abc.MarshallableTypes = value
        instance_hooks: abc.ObjectHooks | None = hooks.read_object_hooks(self)
        if property_name_[0] != "_":
            if instance_hooks and instance_hooks.before_setattr:
                property_name_, value = instance_hooks.before_setattr(
                    self, property_name_, value
                )
            if value is not None:
                unmarshalled_value = self._unmarshal_value(
                    property_name_, value
                )
        object.__setattr__(self, property_name_, unmarshalled_value)
        if (
            property_name_[0] != "_"
            and instance_hooks
            and instance_hooks.after_setattr
        ):
            instance_hooks.after_setattr(self, property_name_, value)

    def _get_key_property_name(self, key: str) -> str | None:
        property_name_: str | None = None
        instance_meta: abc.ObjectMeta | None = meta.read_object_meta(self)
        if instance_meta and instance_meta.properties:
            if (key in instance_meta.properties) and (
                instance_meta.properties[key].name in (None, key)
            ):
                property_name_ = key
            else:
                for (
                    potential_property_name,
                    property_,
                ) in instance_meta.properties.items():
                    if key == property_.name:
                        property_name_ = potential_property_name
                        break
        return property_name_

    def __setitem__(self, key: str, value: abc.MarshallableTypes) -> None:
        # Before set-item hooks
        hooks_: abc.ObjectHooks | None = hooks.read_object_hooks(self)
        if hooks_ and hooks_.before_setitem:
            key, value = hooks_.before_setitem(self, key, value)
        # Get the corresponding property name
        property_name_: str | None = self._get_key_property_name(key)
        if property_name_ is None:
            # Store the extraneous attribute in our extras dictionary
            if self._extra is None:
                self._extra = {}
            self._extra[key] = value
        else:
            # Set the attribute value
            self.__setattr__(property_name_, value)
            # After set-item hooks
            if hooks_ and hooks_.after_setitem:
                hooks_.after_setitem(self, key, value)

    def __delattr__(self, key: str) -> None:
        # Deleting attributes with defined metadata is not allowed—doing this
        # is instead interpreted as setting that attribute to `None`.
        instance_meta: abc.ObjectMeta | None = meta.read_object_meta(self)
        if (
            instance_meta
            and instance_meta.properties
            and (key in instance_meta.properties)
        ):
            setattr(self, key, None)
        else:
            object.__delattr__(self, key)

    def __delitem__(self, key: str) -> None:
        property_name: str | None = self._get_key_property_name(key)
        if property_name is None:
            if self._extra is None:
                raise KeyError(key)
            del self._extra[key]
        else:
            self.__delattr__(property_name)

    def __getitem__(self, key: str) -> abc.MarshallableTypes:
        # This retrieves an attribute value using the item assignment
        # operators `[]` by looking up the attributes in the object metadata.
        property_name: str | None = self._get_key_property_name(key)
        if property_name is None:
            if self._extra is None:
                raise KeyError(key)
            return self._extra[key]
        return cast(abc.MarshallableTypes, getattr(self, property_name))

    def __copy__(self) -> abc.Object:
        return self.__class__(self)

    def _deepcopy_property(
        self,
        property_name_: str,
        other: abc.Object,
        memo: dict | None,
    ) -> None:
        """
        Deep-copy a property from this object to another
        """
        try:
            value = getattr(self, property_name_)
            if isinstance(value, GeneratorType):
                value = tuple(value)
            if value is not None:
                if not callable(value):
                    value = deepcopy(value, memo=memo)
                setattr(other, property_name_, value)
        except TypeError as error:
            label: str = f"{get_qualified_name(type(self))}.{property_name_}: "
            if error.args:
                error.args = tuple(
                    chain((label + error.args[0],), error.args[1:])
                )
            else:
                error.args = (label + serialize(self),)
            raise

    def __deepcopy__(self, memo: dict | None) -> abc.Object:
        # Perform a regular copy operation
        new_instance: abc.Object = self.__copy__()
        # Retrieve the metadata
        meta_: abc.ObjectMeta | None = meta.read_object_meta(self)
        # If there is metadata--copy it recursively
        if meta_ and meta_.properties:
            for property_name_ in meta_.properties:
                self._deepcopy_property(property_name_, new_instance, memo)
        return new_instance

    def _marshal(self) -> dict[str, abc.JSONTypes]:
        object_: abc.Object = self
        instance_hooks: abc.ObjectHooks | None = hooks.read_object_hooks(self)
        if instance_hooks and instance_hooks.before_marshal:
            before_marshal_object: abc.Model = instance_hooks.before_marshal(
                self
            )
            if TYPE_CHECKING:
                assert isinstance(before_marshal_object, abc.Object)
            object_ = before_marshal_object
        data: dict[str, abc.JSONTypes] = {}
        instance_meta: abc.ObjectMeta | None = meta.read_object_meta(object_)
        if instance_meta and instance_meta.properties is not None:
            property_name_: str
            property_: abc.Property
            for property_name_, property_ in instance_meta.properties.items():
                value: abc.JSONTypes = getattr(object_, property_name_)
                if value is not None:
                    data[property_.name or property_name_] = (
                        _marshal_property_value(property_, value)
                    )
        if instance_hooks and instance_hooks.after_marshal:
            after_marshal_data: abc.JSONTypes = instance_hooks.after_marshal(
                data
            )
            if TYPE_CHECKING:
                assert isinstance(after_marshal_data, dict)
            data = after_marshal_data
        return data

    def __str__(self) -> str:
        return serialize(self)

    @staticmethod
    def _repr_argument(parameter: str, value: abc.MarshallableTypes) -> str:
        value_representation: str
        if isinstance(value, type):
            value_representation = get_qualified_name(value)
        else:
            value_representation = repr(value)
        lines = value_representation.split("\n")
        if len(lines) > 1:
            indented_lines = [lines[0]]
            indented_lines.extend(f"    {line}" for line in lines[1:])
            value_representation = "\n".join(indented_lines)
        return f"    {parameter}={value_representation},"

    def __repr__(self) -> str:
        # This returns a string representation of this object which can be
        # used to recreate the object
        representation = [f"{get_qualified_name(type(self))}("]
        instance_meta: abc.ObjectMeta | None = meta.read_object_meta(self)
        if instance_meta and instance_meta.properties:
            property_name_: str
            value: abc.MarshallableTypes
            for property_name_ in instance_meta.properties:
                value = getattr(self, property_name_)
                if value is not None:
                    representation.append(
                        self._repr_argument(property_name_, value)
                    )
            # Strip the last comma
            if representation:
                representation[-1] = representation[-1].rstrip(",")
        representation.append(")")
        if len(representation) > 2:  # noqa: PLR2004
            return "\n".join(representation)
        return "".join(representation)

    def __eq__(self, other: abc.Any) -> bool:
        if type(self) is not type(other):
            return False
        instance_meta: abc.ObjectMeta | None = meta.read_object_meta(self)
        self_properties = set(
            instance_meta.properties.keys()
            if instance_meta and instance_meta.properties
            else ()
        )
        other_meta: abc.ObjectMeta | None = meta.read_object_meta(other)
        other_properties = set(
            other_meta.properties.keys()
            if other_meta and other_meta.properties
            else ()
        )
        if self_properties != other_properties:
            return False
        value: abc.MarshallableTypes
        other_value: abc.MarshallableTypes
        for property_name_ in self_properties & other_properties:
            value = getattr(self, property_name_)
            other_value = getattr(other, property_name_)
            if value != other_value:
                return False
        return True

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __iter__(self) -> Iterator[str]:
        instance_meta: abc.ObjectMeta | None = meta.read_object_meta(self)
        if instance_meta and instance_meta.properties:
            property_name_: str
            property_: abc.Property
            for property_name_, property_ in instance_meta.properties.items():
                yield property_.name or property_name_

    def __contains__(self, key: str) -> bool:
        return key in self.__iter__()

    def _get_property_validation_error_messages(
        self,
        property_name_: str,
        property_: abc.Property,
        value: abc.MarshallableTypes,
    ) -> Iterable[str]:
        if value is None:
            if property_.required:
                yield (
                    f"The property `{property_name_}` is required for "
                    f"`{get_qualified_name(type(self))}`:\n{self!s}"
                )
        elif value is NULL:
            if (property_.types is not None) and (Null not in property_.types):
                yield (
                    "Null values are not allowed in `{}.{}`, "
                    "permitted types include: {}.".format(
                        get_qualified_name(type(self)),
                        property_name_,
                        ", ".join(
                            "`{}`".format(
                                get_qualified_name(type_)
                                if isinstance(type_, type)
                                else get_qualified_name(type(type_))
                            )
                            for type_ in property_.types
                        ),
                    )
                )
        else:
            error_message: str
            for error_message in validate(
                value, property_.types, raise_errors=False
            ):
                yield (
                    "Error encountered while attempting to validate "
                    f"`{get_qualified_name(type(self))}.{property_name_}`:\n\n{error_message}"
                )

    def _validate(self, *, raise_errors: bool = True) -> list[str]:
        """
        This method verifies that all required properties are present,
        that all property values are of the correct type, and that no
        extraneous attributes (attributes having no associated metadata)
        were found.
        """
        validation_error_messages: list[str] = []
        validated_object: abc.Object = self
        instance_hooks: abc.ObjectHooks | None = hooks.read_object_hooks(self)
        if instance_hooks and instance_hooks.before_validate:
            validated_model: abc.Model = instance_hooks.before_validate(self)
            if TYPE_CHECKING:
                assert isinstance(validated_model, abc.Object)
            validated_object = validated_model
        instance_meta: abc.ObjectMeta | None = meta.read_object_meta(
            validated_object
        )
        if instance_meta and instance_meta.properties:
            property_name_: str
            property_: abc.Property
            for (
                property_name_,
                property_,
            ) in instance_meta.properties.items():
                validation_error_messages.extend(
                    (  # noqa: SLF001
                        validated_object
                    )._get_property_validation_error_messages(
                        property_name_,
                        property_,
                        getattr(validated_object, property_name_),
                    )
                )
            if instance_hooks and instance_hooks.after_validate:
                instance_hooks.after_validate(validated_object)
            if self._extra:
                validation_error_messages.append(
                    f"Extraneous attribute(s) were provided for an instance "
                    f"of `{get_qualified_name(type(self))}`:\n"
                    f"{represent(self._extra)}"
                )
            if raise_errors and validation_error_messages:
                raise errors.ValidationError(
                    "\n".join(validation_error_messages)
                )
        return validation_error_messages


# region marshal


def _marshal_collection(
    data: Mapping[str, abc.MarshallableTypes]
    | Collection[abc.MarshallableTypes]
    | abc.Dictionary,
    value_types: Iterable[type | abc.Property] | None = None,
    item_types: Iterable[type | abc.Property] | abc.Types | None = None,
) -> Mapping[str, abc.MarshallableTypes] | list[abc.MarshallableTypes]:
    if isinstance(data, (Mapping, abc.Dictionary)):
        return _marshal_mapping(data, value_types)
    value: abc.MarshallableTypes
    return [marshal(value, types=item_types) for value in data]


def _marshal_mapping(
    data: Mapping[str, abc.MarshallableTypes] | abc.Dictionary,
    value_types: Iterable[type | abc.Property] | abc.Types | None = None,
) -> dict[str, abc.MarshallableTypes]:
    key: str
    value: abc.MarshallableTypes
    marshalled_data: dict[str, abc.MarshallableTypes] = {}
    items: Iterable[tuple[str, abc.MarshallableTypes]]
    if isinstance(data, (abc.Dictionary, dict)) or (
        isinstance(data, Reversible) and isinstance(data, Mapping)
    ):
        items = data.items()
    else:
        if not isinstance(data, Mapping):
            raise TypeError(data)
        # This gives consistent sorting for non-ordered mappings
        items = sorted(data.items(), key=lambda item: item[0])
    for key, value in items:
        marshalled_data[key] = marshal(value, types=value_types)
    return marshalled_data


def _marshal_typed(
    data: abc.MarshallableTypes,
    types: Iterable[type | abc.Property] | abc.Types,
) -> Any:
    """
    This attempts to initialize the provided type(s) with `data`, and accepts
    the first which does not raise an error
    """
    # For each potential type, attempt to marshal the data, and accept the
    # first result which does not throw an error
    marshalled_data: Any = UNDEFINED
    for type_ in types:
        if isinstance(type_, abc.Property):
            try:
                marshalled_data = _marshal_property_value(type_, data)
                break
            except TypeError:
                pass
        elif isinstance(type_, type) and isinstance(data, type_):
            marshalled_data = data
            break
    # If no matches are found, raise a `TypeError` with sufficient
    # information about the data and `types` to debug
    if marshalled_data is UNDEFINED:
        message: str = (
            f"{data!r} cannot be interpreted as any of the designated "
            f"types: {types!r}"
        )
        raise TypeError(message)
    return marshalled_data


def marshal(  # noqa: C901
    data: abc.MarshallableTypes,
    types: Iterable[type | abc.Property] | abc.Types | None = None,
    value_types: Iterable[type | abc.Property] | abc.Types | None = None,
    item_types: Iterable[type | abc.Property] | abc.Types | None = None,
) -> Any:
    """
    This function recursively converts data which is not serializable using
    `json.dumps` into data which *can* be represented as JSON.

    Parameters:
        data: The data to be marshalled, typically an instance of `sob.Model`.
        types: Property definitions or type(s) associated with this data.
            This is typically only used for recursive calls, so not typically
            provided explicitly by client applications.
        value_types: Property definitions or type(s) associated with this
            objects' dictionary values. This is typically only used for
            recursive calls, so not typically provided explicitly by client
            applications.
        item_types: Property definitions or type(s) associated with this
            array's items. This is typically only used for recursive calls,
            so not typically provided explicitly by client applications.
    """
    marshalled_data: abc.JSONTypes
    if isinstance(data, Decimal):
        # Instances of `decimal.Decimal` can'ts be serialized as JSON, so we
        # convert them to `float`
        marshalled_data = float(data)
    elif (data is None) or isinstance(data, (str, int, float)):
        # Don't do anything with `None`--this just means an attributes is not
        # used for this instance (an explicit `null` would be passed as
        # `sob.properties.types.NULL`).
        marshalled_data = data
    elif data is NULL:
        marshalled_data = None
    elif isinstance(data, abc.Model):
        marshalled_data = data._marshal()  # noqa: SLF001
    elif types is not None:
        marshalled_data = _marshal_typed(data, types)
    elif isinstance(data, datetime):
        marshalled_data = datetime2str(data)
    elif isinstance(data, date):
        marshalled_data = date2str(data)
    elif isinstance(data, (bytes, bytearray)):
        # Convert `bytes` to base-64 encoded strings
        marshalled_data = str(b64encode(data), "ascii")
    elif isinstance(data, Collection):
        marshalled_data = _marshal_collection(
            data, value_types=value_types, item_types=item_types
        )
    elif isinstance(data, SupportsBytes):
        # Convert objects which can be *cast* as `bytes` to
        # base-64 encoded strings
        marshalled_data = str(b64encode(bytes(data)), "ascii")
    else:
        message: str = f"Cannot unmarshal: {data!r}"
        raise ValueError(message)
    return marshalled_data


# endregion
# region unmarshal


def _is_non_string_iterable(value: abc.MarshallableTypes) -> bool:
    return (
        (not isinstance(value, (str, bytes)))
        and (not isinstance(value, Mapping))
        and isinstance(value, Iterable)
    )


def _is_non_string_sequence_or_set_subclass(type_: type) -> bool:
    return (
        issubclass(type_, (collections.abc.Set, collections.abc.Sequence))
    ) and (not issubclass(type_, (str, bytes)))


class _Unmarshal:
    """
    This class should be used exclusively by wrapper function `unmarshal`.
    """

    def __init__(
        self,
        data: abc.MarshallableTypes,
        types: Iterable[type | abc.Property]
        | abc.Types
        | type
        | abc.Property = (),
        value_types: Iterable[type | abc.Property]
        | abc.Types
        | type
        | abc.Property = (),
        item_types: Iterable[type | abc.Property]
        | abc.Types
        | type
        | abc.Property = (),
    ) -> None:
        # If only one type was passed for any of the following parameters--we
        # convert it to a tuple
        if isinstance(types, (type, abc.Property)):
            types = (types,)
        if isinstance(value_types, (type, abc.Property)):
            value_types = (value_types,)
        if isinstance(item_types, (type, abc.Property)):
            item_types = (item_types,)
        # Instance Attributes
        self.data: abc.MarshallableTypes = data
        self.types: Iterable[type | abc.Property] | abc.Types = types
        self.value_types: Iterable[type | abc.Property] | abc.Types = (
            value_types
        )
        self.item_types: Iterable[type | abc.Property] | abc.Types = item_types
        self.meta: abc.Meta | None = None

    def __call__(self) -> abc.MarshallableTypes:
        """
        Return `self.data` unmarshalled
        """
        try:
            unmarshalled_data: abc.MarshallableTypes = self.data
            if self.data is not NULL:
                # If the data is a sob `Model`, get it's metadata
                if isinstance(self.data, abc.Model):
                    self.meta = meta.read_model_meta(self.data)
                # Only un-marshall models if they have no metadata yet (are
                # generic)
                if self.meta is None:
                    # If the data provided is a `Generator`, make it static by
                    # casting the data into a tuple
                    if isinstance(self.data, GeneratorType):
                        self.data = tuple(self.data)
                    if not self.types:
                        # If no types are provided, we unmarshal the data into
                        # one of sob's generic container types
                        unmarshalled_data = self.as_container_or_simple_type
                    else:
                        unmarshalled_data = self.as_typed
        except Exception as error:
            append_exception_text(
                error,
                (
                    "An error was encountered during execution of:\n"
                    f"{self.represent_function_call()}"
                ),
            )
            raise
        return unmarshalled_data

    @property  # type: ignore
    def as_container_or_simple_type(self) -> Any:
        """
        This function unmarshals and returns the data into one of sob's
        container types, or if the data is of a simple data type--it returns
        that data unmodified
        """
        type_: type
        unmarshalled_data = self.data
        if unmarshalled_data is None:
            unmarshalled_data = NULL
        elif isinstance(self.data, abc.Dictionary):
            type_ = type(self.data)
            if self.value_types:
                unmarshalled_data = type_(
                    self.data, value_types=self.value_types or None
                )
        elif isinstance(self.data, abc.Array):
            type_ = type(self.data)
            if self.item_types:
                unmarshalled_data = type_(
                    self.data, item_types=self.item_types or None
                )
        elif isinstance(self.data, Mapping):
            unmarshalled_data = Dictionary(
                self.data, value_types=self.value_types or None
            )
        elif isinstance(self.data, Iterable) and not isinstance(
            self.data, (str, bytes, bytearray)
        ):
            # `None` is interpreted as `NULL` during un-marshalling
            items: list[abc.MarshallableTypes] = [
                (NULL if item is None else item) for item in self.data
            ]
            unmarshalled_data = Array(
                items, item_types=self.item_types or None
            )
        elif not isinstance(self.data, abc.MARSHALLABLE_TYPES):
            message: str = f"{self.data!r} cannot be un-marshalled"
            raise errors.UnmarshalValueError(message)
        return unmarshalled_data

    @property  # type: ignore
    def as_typed(self) -> abc.MarshallableTypes:  # noqa: C901
        extra_length: int
        smallest_extra_length: int | None = None
        candidate_unmarshalled_data: abc.MarshallableTypes
        unmarshalled_data: abc.MarshallableTypes | Undefined = UNDEFINED
        first_error: Exception | None = None
        error_messages: list[str] = []
        # Attempt to un-marshal the data as each type, in the order
        # provided
        type_: type | abc.Property
        for type_ in self.types:
            try:
                candidate_unmarshalled_data = self.as_type(type_)
            except (AttributeError, KeyError, TypeError, ValueError) as error:
                if first_error is None:
                    first_error = error
                error_messages.append(errors.get_exception_text())
            else:
                if isinstance(candidate_unmarshalled_data, abc.Object):
                    # If the unmarshalled data is an `sob.Object`, we check to
                    # see if the JSON contained extraneous properties,
                    # and if it did, continue checking types to see
                    # if there is a better match
                    extra_length = (
                        0
                        if (
                            candidate_unmarshalled_data._extra  # noqa: SLF001
                            is None
                        )
                        else len(
                            candidate_unmarshalled_data._extra  # noqa: SLF001
                        )
                    )
                    if not extra_length:
                        # If there is no extraneous data, we've found what
                        # we need and can stop looking
                        unmarshalled_data = candidate_unmarshalled_data
                        break
                    if (
                        smallest_extra_length is None
                    ) or extra_length < smallest_extra_length:
                        # If this is the first candidate, or has fewer
                        # extraneous properties than all previous candidates,
                        # accept it until/unless a better candidate is found
                        smallest_extra_length = extra_length
                        unmarshalled_data = candidate_unmarshalled_data
                else:
                    unmarshalled_data = candidate_unmarshalled_data
                    # If the data is un-marshalled successfully, and is not
                    # an `sob.Object` we do not need to try any further types
                    break
        if isinstance(unmarshalled_data, Undefined):
            if (first_error is None) or isinstance(first_error, TypeError):
                raise errors.UnmarshalTypeError(
                    "\n".join(error_messages),
                    data=self.data,
                    types=self.types,
                    value_types=self.value_types,
                    item_types=self.item_types,
                )
            if isinstance(first_error, ValueError):
                raise errors.UnmarshalValueError(
                    "\n".join(error_messages),
                    data=self.data,
                    types=self.types,
                    value_types=self.value_types,
                    item_types=self.item_types,
                )
            raise first_error
        return unmarshalled_data

    def get_dictionary_type(self, type_: type) -> type | None:
        """
        Get the dictionary type to use
        """
        dictionary_type: type | None
        if type_ is abc.Dictionary:
            dictionary_type = Dictionary
        elif issubclass(type_, abc.Object):
            dictionary_type = None
        elif issubclass(type_, abc.Dictionary):
            dictionary_type = type_
        elif issubclass(type_, Mapping):
            dictionary_type = Dictionary
        else:
            raise TypeError(self.data)
        return dictionary_type

    def before_hook(self, type_: type) -> abc.MarshallableTypes:
        data = self.data
        hooks_ = hooks.read_model_hooks(type_)
        if hooks_:
            before_unmarshal_hook = hooks_.before_unmarshal
            if before_unmarshal_hook:
                data = before_unmarshal_hook(deepcopy(data))
        return data

    @staticmethod
    def after_hook(type_: type, data: abc.Model) -> abc.Model:
        hooks_ = hooks.read_model_hooks(type_)
        if hooks_:
            after_unmarshal_hook = hooks_.after_unmarshal
            if after_unmarshal_hook:
                data = after_unmarshal_hook(data)
        return data

    def as_dictionary_type(self, type_: type) -> abc.Model:
        data: abc.MarshallableTypes
        unmarshalled_data: abc.Model
        dictionary_type = self.get_dictionary_type(type_)
        # Determine whether the `type_` is an `Object` or a `Dictionary`
        if dictionary_type:
            type_ = dictionary_type
            data = self.before_hook(type_)
            if "value_types" in signature(type_).parameters:
                unmarshalled_data = type_(
                    data, value_types=self.value_types or None
                )
            else:
                unmarshalled_data = type_(data)
            unmarshalled_data = self.after_hook(type_, unmarshalled_data)
        else:
            data = self.before_hook(type_)
            unmarshalled_data = type_(data)
            unmarshalled_data = self.after_hook(type_, unmarshalled_data)
        return unmarshalled_data

    def get_array_type(self, type_: type) -> type[abc.Array]:
        if type_ is abc.Array:
            type_ = Array
        elif issubclass(type_, abc.Array):
            pass
        elif _is_non_string_sequence_or_set_subclass(type_):
            type_ = Array
        else:
            message: str = f"{self.data!r} is not of type `{type_!r}`"
            raise TypeError(message)
        return type_

    def as_array_type(self, type_: type) -> abc.Array:
        unmarshalled_data: abc.Array
        type_ = self.get_array_type(type_)
        if "item_types" in signature(type_).parameters:
            unmarshalled_data = type_(
                cast(abc.Array, self.data),
                item_types=self.item_types or None,  # type: ignore
            )
        else:
            unmarshalled_data = type_(self.data)  # type: ignore
        return unmarshalled_data

    def as_type(
        self,
        type_: type | abc.Property,
    ) -> abc.MarshallableTypes:
        unmarshalled_data: abc.MarshallableTypes = None
        if isinstance(type_, abc.Property):
            unmarshalled_data = _unmarshal_property_value(type_, self.data)
        elif isinstance(type_, type):
            if isinstance(
                self.data,
                (
                    dict,
                    abc.Object,
                    abc.Dictionary,
                    Mapping,
                ),
            ):
                unmarshalled_data = self.as_dictionary_type(type_)
            elif _is_non_string_iterable(self.data):
                unmarshalled_data = self.as_array_type(type_)
            elif isinstance(self.data, type_):
                if isinstance(self.data, Decimal):
                    unmarshalled_data = float(self.data)
                else:
                    unmarshalled_data = self.data  # type: ignore
            else:
                raise TypeError(self.data)
        return unmarshalled_data

    def represent_function_call(self) -> str:
        return (
            "sob.model.unmarshal(\n"
            f"    data={indent_(utilities.represent(self.data))},\n"
            f"    types={indent_(utilities.represent(self.types))},\n"
            "    value_types="
            f"{indent_(utilities.represent(self.value_types))},\n"
            "    item_types="
            f"{indent_(utilities.represent(self.item_types))},\n"
            ")"
        )


def unmarshal(
    data: abc.MarshallableTypes,
    types: Iterable[type | abc.Property]
    | type
    | abc.Property
    | abc.Types = (),
    value_types: Iterable[type | abc.Property]
    | type
    | abc.Property
    | abc.Types = (),
    item_types: Iterable[type | abc.Property]
    | type
    | abc.Property
    | abc.Types = (),
) -> Any:
    """
    Converts deserialized data into one of the provided types.

    Parameters:
        data:
        types: Property definitions or type(s) into which to attempt to
            un-marshal the data. If multiple types are provided,
            the first which does not raise an error or contain extraneous
            attributes is accepted. If the data has extraneous attributes
            for all types, the type with the fewest extraneous attributes is
            accepted.
        value_types: For dictionary-like objects, values will be un-marshalled
            as one of the provided property definitions or types.
        item_types: For sequences (lists/tuples), items will be un-marshalled
            as one of the provided property definitions or types.
    """
    return _Unmarshal(
        data, types=types, value_types=value_types, item_types=item_types
    )()


# endregion
# region serialize


def _get_serialize_instance_hooks(
    data: abc.Model,
) -> tuple[
    Callable[[abc.JSONTypes], abc.JSONTypes] | None,
    Callable[[str], str] | None,
]:
    before_serialize: Callable[[abc.JSONTypes], abc.JSONTypes] | None = None
    after_serialize: Callable[[str], str] | None = None
    instance_hooks: abc.Hooks | None = hooks.read_model_hooks(data)
    if instance_hooks is not None:
        before_serialize = instance_hooks.before_serialize
        after_serialize = instance_hooks.after_serialize
    return before_serialize, after_serialize


def serialize(
    data: abc.MarshallableTypes,
    indent: int | None = None,
) -> str:
    """
    This function serializes data, particularly instances of `sob.Model`
    sub-classes, into JSON encoded strings.

    Parameters:
        data:
        indent: The number of spaces to use for indentation. If `None`,
            the JSON will be compacted (no line breaks or indentation).
    """
    string_data: str
    if isinstance(data, abc.Model):
        before_serialize: Callable[[abc.JSONTypes], abc.JSONTypes] | None
        after_serialize: Callable[[str], str] | None
        before_serialize, after_serialize = _get_serialize_instance_hooks(data)
        marshalled_data: abc.JSONTypes = marshal(data)
        if before_serialize is not None:
            marshalled_data = before_serialize(marshalled_data)
        string_data = json.dumps(marshalled_data, indent=indent)
        if after_serialize is not None:
            string_data = after_serialize(string_data)
    else:
        if not isinstance(data, abc.JSON_TYPES):
            raise TypeError(data)
        string_data = json.dumps(data, indent=indent)
    return string_data


# endregion
# region deserialize


def deserialize(
    data: str | bytes | abc.Readable | None,
) -> Any:
    """
    This function deserializes JSON encoded data from a string, bytes,
    or a file-like object.

    Parameters:
        data: This can be a string or file-like object
            containing JSON serialized data.

    This function returns `None` (for JSON null values), or an instance of
    `str`, `dict`, `list`, `int`, `float` or `bool`.
    """
    deserialized_data: abc.JSONTypes
    if isinstance(data, str):
        try:
            deserialized_data = json.loads(
                data,
                strict=False,
            )
        except ValueError as error:
            raise DeserializeError(
                data=data,
                message=get_exception_text(),
            ) from error
    elif isinstance(data, bytes):
        deserialized_data = deserialize(str(data, encoding="utf-8"))
    else:
        if not isinstance(data, abc.Readable):
            raise TypeError(data)
        deserialized_data = deserialize(read(data))
    return deserialized_data


# endregion


# region validate


def _default_validate_method(
    raise_errors: bool,  # noqa: ARG001 FBT001
) -> Iterable[str]:
    return ()


def _call_validate_method(
    data: abc.Model,
) -> Iterable[str]:
    error_message: str
    error_messages: set[str] = set()
    validate_method: Callable[..., Iterable[str]] = get_method(
        data, "_validate", _default_validate_method
    )  # type: ignore
    for error_message in validate_method(raise_errors=False):
        if error_message not in error_messages:
            yield error_message
            error_messages.add(error_message)


def _validate_typed(
    data: abc.Model | None,
    types: Iterable[type | abc.Property] | abc.Types,
) -> list[str]:
    error_messages: list[str] = []
    valid: bool = False
    for type_ in types:
        if isinstance(type_, type) and isinstance(data, type_):
            valid = True
            break
        if isinstance(type_, abc.Property):
            if type_.types is None:
                valid = True
                break
            try:
                validate(data, type_.types, raise_errors=True)
                valid = True
                break
            except errors.ValidationError:
                error_messages.append(get_exception_text())
    if valid:
        error_messages.clear()
    else:
        types_bullet_list: str = "\n\n".join(
            indent_(represent(type_), 4) for type_ in (types or ())
        )
        error_messages.append(
            f"Invalid data:\n\n"
            f"    {indent_(represent(data))}\n\n"
            f"The data must be one of the following types:\n\n"
            f"    {types_bullet_list}"
        )
    return error_messages


def validate(
    data: Any,
    types: abc.Types | Iterable[type | abc.Property] | None = None,
    *,
    raise_errors: bool = True,
) -> Sequence[str]:
    """
    This function verifies that all properties/items/values of a model instance
    are of the correct data type(s), and that all required attributes are
    present (if applicable).

    Parameters:
        data:
        types: Property definitions or types against which to attempt to
            validate the data.
        raise_errors: If `True`, a validation error will be raised if
            the validation fails. If `False`, a list of error message strings
            will be returned.

    If `raise_errors` is `True` (this is the default), violations will result
    in a validation error being raised. If `raise_errors` is `False`, a list
    of error messages will be returned.
    """
    if isinstance(data, GeneratorType):
        data = tuple(data)
    error_messages: list[str] = []
    if types is not None:
        error_messages.extend(_validate_typed(data, types))
    error_messages.extend(_call_validate_method(data))
    if raise_errors and error_messages:
        data_representation: str = f"\n\n    {indent_(represent(data))}"
        error_messages_representation: str = "\n\n".join(error_messages)
        if data_representation not in error_messages_representation:
            error_messages_representation = (
                f"{data_representation}\n\n{error_messages_representation}"
            )
        raise errors.ValidationError(error_messages_representation)
    return error_messages


# endregion
# region _unmarshal_property_value


class _UnmarshalProperty:
    """
    This is exclusively for use by wrapper function
    `_unmarshal_property_value`.
    """

    def __init__(self, property_: abc.Property) -> None:
        self.property = property_

    def validate_enumerated(self, value: abc.MarshallableTypes) -> None:
        """
        Verify that a value is one of the enumerated options
        """
        if (
            (value is not None)
            and isinstance(self.property, abc.EnumeratedProperty)
            and (self.property.values is not None)
            and (value not in self.property.values)
        ):
            message: str = (
                "The value provided is not a valid option:\n{}\n\n"
                "Valid options include:\n{}".format(
                    repr(value),
                    ", ".join(
                        repr(enumerated_value)
                        for enumerated_value in self.property.values
                    ),
                )
            )
            raise ValueError(message)

    def unmarshal_enumerated(
        self, value: abc.MarshallableTypes
    ) -> abc.MarshallableTypes:
        """
        Verify that a value is one of the enumerated options
        """
        unmarshalled_value: abc.MarshallableTypes = value
        self.validate_enumerated(value)
        if self.property.types is not None:
            unmarshalled_value = unmarshal(value, types=self.property.types)
        return unmarshalled_value

    def parse_date(self, value: str | None) -> date | None:
        if value is None:
            return value
        if not isinstance(value, (date, str)):
            raise TypeError(value)
        if isinstance(value, date):
            date_instance = value
        else:
            if not isinstance(self.property, abc.DateProperty):
                raise TypeError(self.property)
            date_instance = self.property.str2date(value)
        if not isinstance(date_instance, date):
            raise TypeError(date_instance)
        return date_instance

    def parse_datetime(self, value: str | datetime | None) -> datetime | None:
        datetime_instance: datetime | None = None
        if value is not None:
            if not isinstance(value, (datetime, str)):
                raise TypeError(value)
            if isinstance(value, datetime):
                datetime_instance = value
            else:
                if not isinstance(self.property, abc.DateTimeProperty):
                    raise TypeError(self.property)
                datetime_instance = self.property.str2datetime(value)
            if not isinstance(datetime_instance, datetime):
                raise TypeError(datetime_instance)
        return datetime_instance

    @staticmethod
    def parse_bytes(data: str | bytes) -> bytes | None:
        """
        Un-marshal a base-64 encoded string into bytes
        """
        unmarshalled_data: bytes | None
        if data is None:
            unmarshalled_data = data
        elif isinstance(data, str):
            unmarshalled_data = b64decode(data)
        elif isinstance(data, bytes):
            unmarshalled_data = data
        else:
            msg = (
                "`data` must be a base64 encoded `str` or `bytes`--not "
                f"`{get_qualified_name(type(data))}`"
            )
            raise TypeError(msg)
        return unmarshalled_data

    def unmarshall_array(
        self, value: abc.MarshallableTypes
    ) -> abc.MarshallableTypes:
        if not isinstance(self.property, abc.ArrayProperty):
            raise TypeError(self.property)
        return unmarshal(
            value,
            types=self.property.types or (),
            item_types=self.property.item_types or (),
        )

    def unmarshall_dictionary(
        self, value: abc.MarshallableTypes
    ) -> abc.MarshallableTypes:
        if not isinstance(self.property, abc.DictionaryProperty):
            raise TypeError(self.property)
        return unmarshal(
            value,
            types=self.property.types or (),
            value_types=self.property.value_types or (),
        )

    def represent_function_call(self, value: abc.MarshallableTypes) -> str:
        return (
            "sob.model._unmarshal_property_value(\n"
            f"    {indent_(utilities.represent(self.property))},\n"
            f"    {indent_(utilities.represent(value))}\n"
            ")"
        )

    def _call(self, value: abc.MarshallableTypes) -> abc.MarshallableTypes:
        type_: type
        matched: bool = False
        unmarshalled_value: abc.MarshallableTypes = value
        method: Callable[..., abc.MarshallableTypes]
        for type_, method in (
            (abc.DateProperty, self.parse_date),
            (abc.DateTimeProperty, self.parse_datetime),
            (abc.BytesProperty, self.parse_bytes),
            (abc.ArrayProperty, self.unmarshall_array),
            (abc.DictionaryProperty, self.unmarshall_dictionary),
            (abc.EnumeratedProperty, self.unmarshal_enumerated),
        ):
            if isinstance(self.property, type_):
                matched = True
                unmarshalled_value = method(value)  # type: ignore
                break
        if not matched:
            if (
                isinstance(value, Iterable)
                and not isinstance(value, (str, bytes, bytearray))
                and not isinstance(value, abc.Model)
            ):
                if isinstance(value, (Mapping, abc.Dictionary)):
                    if not isinstance(value, (MutableMapping, abc.Dictionary)):
                        raise TypeError(value)
                    unmarshalled_value = copy(value)
                    for key, item_value in value.items():
                        if item_value is None:
                            unmarshalled_value[key] = NULL
                else:
                    unmarshalled_value = tuple(
                        (NULL if item_value is None else item_value)
                        for item_value in value
                    )
            if self.property.types:
                unmarshalled_value = unmarshal(
                    unmarshalled_value, types=self.property.types
                )
        return unmarshalled_value

    def __call__(self, value: abc.MarshallableTypes) -> abc.MarshallableTypes:
        try:
            return self._call(value)
        except Exception as error:
            append_exception_text(
                error,
                (
                    "\nAn error was encountered during execution of:\n"
                    f"{self.represent_function_call(value)}"
                ),
            )
            raise


def _unmarshal_property_value(
    property_: abc.Property, value: abc.MarshallableTypes
) -> abc.MarshallableTypes:
    """
    Un-marshal a property value
    """
    return _UnmarshalProperty(property_)(value)


# endregion
# region _marshal_property_value


class _MarshalProperty:
    """
    This is exclusively for use by wrapper function `_marshal_property_value`.
    """

    def __init__(self, property_: abc.Property) -> None:
        self.property = property_

    def parse_date(self, value: date | None) -> str | None:
        date_string: str | None = None
        if value is not None:
            if not isinstance(self.property, abc.DateProperty):
                raise TypeError(self.property)
            date_string = self.property.date2str(value)
            if not isinstance(date_string, str):
                message: str = (
                    "The date2str function should return a `str`, not a "
                    f"`{type(date_string).__name__}`: "
                    f"{date_string!r}"
                )
                raise TypeError(message)
        return date_string

    def parse_datetime(self, value: datetime | None) -> str | None:
        datetime_string: str | None = None
        if value is not None:
            if not isinstance(self.property, abc.DateTimeProperty):
                raise TypeError(self.property)
            datetime_string = self.property.datetime2str(value)
            if not isinstance(datetime_string, str):
                msg = (
                    "The datetime2str function should return a `str`, not a "
                    f"`{type(datetime_string).__name__}`: "
                    f"{datetime_string!r}"
                )
                raise TypeError(msg)
        return datetime_string

    def parse_bytes(self, value: bytes) -> str:
        """
        Marshal bytes into a base-64 encoded string
        """
        if (value is None) or isinstance(value, str):
            return value
        if isinstance(value, bytes):
            return str(b64encode(value), "ascii")
        message: str = (
            f"`data` must be a base64 encoded `str` or `bytes`--not "
            f"`{get_qualified_name(type(value))}`"
        )
        raise TypeError(message)

    def __call__(self, value: abc.MarshallableTypes) -> Any:
        if value is not None:
            if isinstance(self.property, abc.DateProperty):
                if not isinstance(value, date):
                    raise TypeError(value)
                value = self.parse_date(value)
            elif isinstance(self.property, abc.DateTimeProperty):
                if not isinstance(value, datetime):
                    raise TypeError(value)
                value = self.parse_datetime(value)
            elif isinstance(self.property, abc.BytesProperty):
                if not isinstance(value, bytes):
                    raise TypeError(value)
                value = self.parse_bytes(value)
            elif isinstance(self.property, abc.ArrayProperty):
                value = marshal(
                    value,
                    types=self.property.types,
                    item_types=self.property.item_types,
                )
            elif isinstance(self.property, abc.DictionaryProperty):
                value = marshal(
                    value,
                    types=self.property.types,
                    value_types=self.property.value_types,
                )
            else:
                value = marshal(value, types=self.property.types)
        return value


def _marshal_property_value(
    property_: abc.Property, value: abc.MarshallableTypes
) -> abc.JSONTypes:
    """
    Marshal a property value
    """
    return _MarshalProperty(property_)(value)


# endregion
# region replace_object_nulls


def _replace_object_nulls(
    object_instance: abc.Object,
    replacement_value: abc.MarshallableTypes = None,
) -> None:
    property_name_: str
    value: abc.MarshallableTypes
    for property_name_, value in utilities.iter_properties_values(
        object_instance
    ):
        if value is NULL:
            setattr(object_instance, property_name_, replacement_value)
        elif isinstance(value, abc.Model):
            replace_model_nulls(value, replacement_value)


def _replace_array_nulls(
    array_instance: abc.Array,
    replacement_value: abc.MarshallableTypes = None,
) -> None:
    index: int
    value: abc.MarshallableTypes
    for index, value in enumerate(array_instance):
        if value is NULL:
            array_instance[index] = replacement_value
        elif isinstance(value, abc.Model):
            replace_model_nulls(value, replacement_value)


def _replace_dictionary_nulls(
    dictionary_instance: abc.Dictionary,
    replacement_value: abc.MarshallableTypes = None,
) -> None:
    key: str
    value: abc.MarshallableTypes
    for key, value in dictionary_instance.items():
        if value is NULL:
            dictionary_instance[key] = replacement_value
        elif isinstance(value, abc.Model):
            replace_model_nulls(value, replacement_value)


def replace_model_nulls(
    model_instance: abc.Model,
    replacement_value: abc.MarshallableTypes = None,
) -> None:
    """
    This function replaces all instances of `sob.properties.types.NULL`.

    Parameters:

    - model_instance (sob.model.Model)
    - replacement_value (typing.Any):
      The value with which nulls will be replaced. This defaults to `None`.
    """
    if isinstance(model_instance, abc.Object):
        _replace_object_nulls(model_instance, replacement_value)
    elif isinstance(model_instance, abc.Array):
        _replace_array_nulls(model_instance, replacement_value)
    elif isinstance(model_instance, abc.Dictionary):
        _replace_dictionary_nulls(model_instance, replacement_value)


replace_nulls = deprecated(
    "`sob.model.replace_nulls` is deprecated and will be removed in "
    "sob 3. Please use `sob.replace_model_nulls` instead."
)(replace_model_nulls)


# endregion
# region from_meta


def _type_hint_from_property_types(
    property_types: abc.Types | None, module: str
) -> str:
    type_hint: str = "sob.abc.MarshallableTypes | None"
    if property_types is not None:
        if len(property_types) > 1:
            property_type_hints: tuple[str, ...] = tuple(
                dict.fromkeys(
                    _type_hint_from_property(item_type, module)
                    for item_type in property_types
                ).keys()
            )
            property_type_hint: str
            type_hint = "\n".join(
                (
                    property_type_hints[0],
                    *(
                        f"| {property_type_hint}"
                        for property_type_hint in property_type_hints[1:]
                    ),
                )
            )
        else:
            type_hint = _type_hint_from_property(property_types[0], module)
    return type_hint


def _type_hint_from_property(
    property_or_type: abc.Property | type, module: str
) -> str:
    type_hint: str
    if isinstance(property_or_type, type):
        type_hint = get_qualified_name(property_or_type)
    elif isinstance(property_or_type, abc.ArrayProperty):
        item_type_hint: str = _type_hint_from_property_types(
            property_or_type.item_types, module
        )
        if item_type_hint:
            if item_type_hint[0] == "(":
                item_type_hint = indent_(item_type_hint[1:-1].strip())
            type_hint = f"typing.Sequence[\n    {item_type_hint}\n]"
        else:
            type_hint = "typing.Sequence"
    elif isinstance(property_or_type, abc.DictionaryProperty):
        value_type_hint: str = _type_hint_from_property_types(
            property_or_type.value_types, module
        )
        if value_type_hint:
            if value_type_hint[0] == "(":
                value_type_hint = value_type_hint[1:-1].strip()
            type_hint = (
                "typing.Mapping[\n"
                "    str,\n"
                f"    {indent_(value_type_hint)}\n]"
            )
        else:
            type_hint = "dict"
    elif isinstance(property_or_type, abc.NumberProperty):
        type_hint = (
            "float\n"  # -
            "| int\n"  # -a
            "| decimal.Decimal"
        )
    elif property_or_type and property_or_type.types:
        type_hint = _type_hint_from_property_types(
            property_or_type.types, module
        )
    else:
        type_hint = "typing.Any"
    return type_hint


def _get_abc_from_superclass_name(qualified_superclass_name: str) -> str:
    """
    Get the corresponding abstract base class name
    """
    qualified_abc_name_list: list[str] = qualified_superclass_name.split(".")
    qualified_abc_name_list.insert(1, "abc")
    return ".".join(qualified_abc_name_list)


def _get_class_declaration(name: str, superclass_: type) -> str:
    """
    Construct a class declaration
    """
    class_declaration: str
    qualified_superclass_name: str = get_qualified_name(superclass_)
    # If the class declaration line is longer than 79 characters--break it
    # up (attempt to conform to PEP8)
    if 9 + len(name) + len(qualified_superclass_name) <= MAX_LINE_LENGTH:
        class_declaration = f"class {name}({qualified_superclass_name}):"
    else:
        class_declaration = (
            f"class {name}(\n    {qualified_superclass_name}\n):"
        )
    return class_declaration


def _repr_class_docstring(docstring: str = "") -> str:
    """
    Return a representation of a docstring for use in a class constructor.
    """
    repr_docstring: str = ""
    if docstring:
        repr_docstring = (
            f'    """\n{split_long_docstring_lines(docstring)}\n    """'
        )
    return repr_docstring


def _model_class_from_meta(
    metadata: abc.Meta,
) -> type[Array | Dictionary | Object]:
    return (
        Object
        if isinstance(metadata, abc.ObjectMeta)
        else Array
        if isinstance(metadata, abc.ArrayMeta)
        else Dictionary
    )


_REPR_MARSHALLABLE_TYPING: str = "sob.abc.MarshallableTypes"


def _repr_class_init_from_meta(metadata: abc.Meta, module: str) -> str:
    out: list[str] = []
    if isinstance(metadata, abc.DictionaryMeta):
        repr_value_typing: str = _type_hint_from_property_types(
            metadata.value_types, module
        )
        mapping_repr_value_typing: str = indent_(repr_value_typing, 16)
        iterable_repr_value_typing: str = indent_(repr_value_typing, 20)
        out.append(
            "\n"
            "    def __init__(\n"
            "        self,\n"
            "        items: (\n"
            "            sob.abc.Dictionary\n"
            "            | typing.Mapping[\n"
            "                str,\n"
            f"                {mapping_repr_value_typing}\n"
            "            ]\n"
            "            | typing.Iterable[\n"
            "                tuple[\n"
            "                    str,\n"
            f"                    {iterable_repr_value_typing}\n"
            "                ]\n"
            "            ]\n"
            "            | sob.abc.Readable\n"
            "            | str\n"
            "            | bytes\n"
            "            | None\n"
            "        ) = None,\n"
            "    ) -> None:\n"
            "        super().__init__(items)\n\n"
        )
    elif isinstance(metadata, abc.ArrayMeta):
        repr_item_typing: str = indent_(
            _type_hint_from_property_types(metadata.item_types, module), 16
        )
        out.append(
            "\n"
            "    def __init__(\n"
            "        self,\n"
            "        items: (\n"
            "            typing.Iterable[\n"
            f"                {repr_item_typing}\n"
            "            ]\n"
            "            | sob.abc.Readable\n"
            "            | str\n"
            "            | bytes\n"
            "            | None\n"
            "        ) = None\n"
            "    ) -> None:\n"
            "        super().__init__(items)\n\n"
        )
    elif isinstance(metadata, abc.ObjectMeta):
        out.append(
            "\n"
            "    def __init__(\n"
            "        self,\n"
            "        _data: (\n"
            "            sob.abc.Dictionary\n"
            "            | typing.Mapping[\n"
            "                str,\n"
            f"                {_REPR_MARSHALLABLE_TYPING}\n"
            "            ]\n"
            "            | typing.Iterable[\n"
            "                tuple[\n"
            "                    str,\n"
            f"                    {_REPR_MARSHALLABLE_TYPING}\n"
            "                ]\n"
            "            ]\n"
            "            | sob.abc.Readable\n"
            "            | typing.IO\n"
            "            | str\n"
            "            | bytes\n"
            "            | None\n"
            "        ) = None,"
        )
        property_assignments: list[str] = []
        metadata_properties_items: tuple[tuple[str, abc.Property], ...] = (
            ()
            if metadata.properties is None
            else tuple(metadata.properties.items())
        )
        metadata_properties_items_length: int = len(metadata_properties_items)
        property_index: int
        name_and_property: tuple[str, abc.Property]
        for property_index, name_and_property in enumerate(
            metadata_properties_items
        ):
            property_name_: str
            property_: abc.Property
            property_name_, property_ = name_and_property
            repr_comma: str = (
                ""
                if (property_index + 1 == metadata_properties_items_length)
                else ","
            )
            repr_property_typing: str = indent_(
                _type_hint_from_property(property_, module), 12
            )
            property_assignments.append(
                f"        self.{property_name_}: (\n"
                f"            {repr_property_typing}\n"
                "            | None\n"
                f"        ) = {property_name_}"
            )
            out.append(
                f"        {property_name_}: (\n"
                f"            {repr_property_typing}\n"
                "            | None\n"
                f"        ) = None{repr_comma}"
            )
        out.append("    ) -> None:")
        out.extend(property_assignments)
        out.append("        super().__init__(_data)\n\n")
    else:
        raise TypeError(metadata)
    return "\n".join(out)


def _iter_represent_object_metadata_slots(
    metadata: abc.ObjectMeta,
) -> Iterable[str]:
    """
    Yield lines in a representation of the slots for a class
    """
    if metadata.properties is not None:
        yield ""
        yield "    __slots__: tuple[str, ...] = ("
        property_name: str
        for property_name in metadata.properties:
            yield f'        "{property_name}",'
        yield "    )"


def _class_definition_from_meta(
    name: str,
    metadata: abc.Meta,
    docstring: str | None = None,
    module: str = "__main__",
    pre_init_source: str = "",
    post_init_source: str = "",
) -> str:
    """
    This returns a `str` defining a model class, as determined by an
    instance of `sob.meta.Meta`.
    """
    repr_docstring: str | None = (
        None if docstring is None else _repr_class_docstring(docstring)
    )
    out: list[str] = [
        _get_class_declaration(name, _model_class_from_meta(metadata))
    ]
    if repr_docstring:
        out.append(repr_docstring)
    if isinstance(metadata, abc.ObjectMeta):
        out.extend(_iter_represent_object_metadata_slots(metadata))
    if pre_init_source:
        out.append(f"\n{utilities.indent(pre_init_source, start=0)}")
    out.append(_repr_class_init_from_meta(metadata, module))
    if post_init_source:
        out.append(f"\n{utilities.indent(post_init_source, start=0)}")
    return "\n".join(out)


def get_model_from_meta(
    name: str,
    metadata: abc.Meta,
    module: str | None = None,
    docstring: str | None = None,
    pre_init_source: str = "",
    post_init_source: str = "",
) -> type[abc.Model]:
    """
    Constructs an `sob.Object`, `sob.Array`, or `sob.Dictionary` sub-class
    from an instance of `sob.ObjectMeta`, `sob.ArrayMeta`, or
    `sob.DictionaryMeta`.

    Parameters:
        name: The name of the class.
        class_meta:
        module: Specify the value for the class definition's
            `__module__` property. The invoking module will be
            used if this is not specified. Note: If using the result of this
            function with `sob.utilities.get_source` to generate static
            code--this should be set to "__main__". The default behavior is
            only appropriate when using this function as a factory.
        docstring: A docstring to associate with the class definition.
        pre_init_source: Source code to insert *before* the `__init__`
            function in the class definition.
        post_init_source: Source code to insert *after* the `__init__`
            function in the class definition.
    """
    # For pickling to work, the __module__ variable needs to be set...
    module = module or get_calling_module_name(2)
    class_definition: str = _class_definition_from_meta(
        name,
        metadata,
        docstring=docstring,
        module=module,
        pre_init_source=pre_init_source,
        post_init_source=post_init_source,
    )
    namespace: dict[str, Any] = {"__name__": f"from_meta_{name}"}
    imports = [
        "from __future__ import annotations",
        "import typing",
    ]
    # `decimal.Decimal` may or may not be referenced in a given model--so
    # check first
    if re.search(r"\bdecimal\.Decimal\b", class_definition):
        imports.append("import decimal")
    # `datetime` may or may not be referenced in a given model--so check
    # first
    if re.search(r"\bdatetime\b", class_definition):
        imports.append("import datetime")
    imports.append("import sob")
    source: str = suffix_long_lines(
        "{}\n\n\n{}".format("\n".join(imports), class_definition)
    )
    error: Exception
    try:
        exec(source, namespace)  # noqa: S102
    except Exception as error:
        append_exception_text(error, f"\n\n{source}")
        raise
    model_class: type[abc.Model] = namespace[name]
    model_class._source = source  # noqa: SLF001
    model_class.__module__ = module
    model_class._class_meta = metadata  # noqa: SLF001
    return model_class


def _get_class_meta_attribute_assignment_source(
    class_name_: str,
    attribute_name: str,
    metadata: abc.Meta,
) -> str:
    """
    This function generates source code for setting a metadata attribute on
    a class.

    Parameters:

    - class_name (str): The name of the class to which we want to assign a
      metadata attribute.
    - attribute_name (str): The name of the attribute we want to assign.
    - metadata (sob.abc.Meta): The metadata from which to take the assigned
      value.
    """
    writable_function_name: str = "sob.get_writable_{}_meta".format(
        "object"
        if isinstance(metadata, abc.ObjectMeta)
        else ("array" if isinstance(metadata, abc.ArrayMeta) else "dictionary")
    )
    # We insert "  # type: ignore" at the end of the first line where the value
    # is assigned due to mypy issues with properties having getters and setters
    return suffix_long_lines(
        (
            f"{writable_function_name}(\n"
            f"    {suffix_long_lines(class_name_, -4)}\n"
            f").{attribute_name} = {getattr(metadata, attribute_name)!r}"
        ),
        -4,
    )


def get_models_source(*model_classes: type[abc.Model]) -> str:
    """
    Get source code for a series of model classes, organized as a module.
    This is useful for generating a module from classes generated
    using `get_model_from_meta`.
    """
    import_source_lines: list[str] = []
    class_sources: list[str] = []
    model_class: type[abc.Model]
    class_names_metadata: dict[
        str, abc.ObjectMeta | abc.ArrayMeta | abc.DictionaryMeta
    ] = {}
    for model_class in model_classes:
        import_source: str
        class_source: str
        import_source, class_source = (
            get_source(model_class).strip().rpartition("\n\n\n")[::2]
        )
        import_source_lines.extend(import_source.splitlines())
        class_sources.append(class_source)
        meta_instance: abc.Meta | None = meta.read_model_meta(model_class)
        if not isinstance(
            meta_instance,
            (abc.ObjectMeta, abc.ArrayMeta, abc.DictionaryMeta),
        ):
            raise TypeError(meta_instance)
        class_names_metadata[model_class.__name__] = meta_instance
    class_name: str
    metadata: abc.ObjectMeta | abc.ArrayMeta | abc.DictionaryMeta
    metadata_sources: list[str] = []
    for class_name, metadata in class_names_metadata.items():
        if not isinstance(
            metadata, (abc.ObjectMeta, abc.ArrayMeta, abc.DictionaryMeta)
        ):
            raise TypeError(metadata)
        if isinstance(metadata, abc.ObjectMeta):
            metadata_sources.append(
                _get_class_meta_attribute_assignment_source(
                    class_name, "properties", metadata
                )
            )
        elif isinstance(metadata, abc.ArrayMeta):
            metadata_sources.append(
                _get_class_meta_attribute_assignment_source(
                    class_name, "item_types", metadata
                )
            )
        else:
            metadata_sources.append(
                _get_class_meta_attribute_assignment_source(
                    class_name, "value_types", metadata
                )
            )
    # De-duplicate imports while preserving order
    imports_source = "\n".join(dict.fromkeys(import_source_lines).keys())
    classes_source: str = "\n\n\n".join(class_sources)
    metadata_source: str = "\n".join(metadata_sources)
    return f"{imports_source}\n\n\n{classes_source}\n\n\n{metadata_source}"


from_meta = deprecated(
    "`sob.model.from_meta` is deprecated and will be removed in "
    "sob 3. Please use `sob.get_model_from_meta` instead."
)(get_model_from_meta)


# endregion
