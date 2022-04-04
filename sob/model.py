"""
This module defines the building blocks of an `sob` based data model.
"""
import os
import builtins
import collections
import collections.abc
import json
import re
import sys
import yaml  # type: ignore
from abc import abstractmethod
from base64 import b64decode, b64encode
from copy import copy, deepcopy
from datetime import date, datetime
from decimal import Decimal
from inspect import signature
from itertools import chain
from types import GeneratorType
from typing import (
    Any,
    Callable,
    Collection,
    Dict,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Reversible,
    Sequence,
    Set,
    SupportsBytes,
    Tuple,
    Type,
    Union,
    ValuesView,
    TYPE_CHECKING,
)
from urllib.parse import urljoin

from . import __name__ as _parent_module_name
from . import abc
from . import errors
from . import hooks
from . import meta
from . import utilities
from .errors import (
    DeserializeError,
    IsInstanceAssertionError,
    append_exception_text,
    get_exception_text,
)
from .utilities.assertion import (
    assert_in,
    assert_is_instance,
)
from .utilities.inspect import (
    calling_module_name,
    get_method,
    qualified_name,
    represent,
)
from .utilities.io import read
from .utilities.string import (
    MAX_LINE_LENGTH,
    indent as indent_,
    split_long_docstring_lines,
    suffix_long_lines,
)
from .utilities.types import (
    NULL,
    NoneType,
    Null,
    UNDEFINED,
    Undefined,
)


class Model(abc.Model):
    """
    This serves as a base class for the [Object](#Object), [Array](#Array) and
    [Dictionary](#Dictionary) classes. This class should not be instantiated
    directly, and should not be sub-classed directly--please use `Object`,
    `Array` and/or `Dictionary` as a superclass instead.
    """

    _format: Optional[str] = None
    _meta: Optional[abc.Meta] = None
    _hooks: Optional[abc.Hooks] = None

    def __init__(self) -> None:
        self._meta: Optional[abc.Meta] = None
        self._hooks: Optional[abc.Meta] = None
        self._url: Optional[str] = None
        self._pointer: Optional[str] = None

    def _init_url(
        self,
        data: Union[
            Iterable[abc.MarshallableTypes],
            Mapping[str, abc.MarshallableTypes],
            abc.Model,
            abc.Readable,
            None,
        ],
    ) -> None:
        if isinstance(data, abc.Readable):
            url: Optional[str] = None
            if hasattr(data, "url"):
                url = getattr(data, "url")
            elif hasattr(data, "name"):
                url = urljoin("file:", getattr(data, "name"))
            if url is not None:
                meta.set_url(self, url)

    def _init_format(
        self,
        data: Union[
            str,
            bytes,
            abc.Readable,
            Mapping[str, abc.MarshallableTypes],
            Iterable[abc.MarshallableTypes],
            abc.Model,
            None,
        ] = None,
    ) -> Union[
        Iterable[abc.MarshallableTypes],
        Mapping[str, abc.MarshallableTypes],
        abc.Model,
        None,
    ]:
        """
        This function deserializes raw JSON or YAML and remembers what format
        that data came in.
        """
        deserialized_data: Union[
            Iterable[abc.MarshallableTypes],
            Mapping[str, abc.MarshallableTypes],
            abc.Model,
            None,
        ]
        if isinstance(data, (str, bytes, abc.Readable)):
            format_: str
            data_read: abc.JSONTypes
            data_read, format_ = detect_format(data)
            try:
                assert isinstance(data_read, (Iterable, Mapping, abc.Model))
            except AssertionError:
                raise IsInstanceAssertionError(
                    "data_read", data_read, (Iterable, Mapping, abc.Model)
                )
            deserialized_data = data_read
            if format_ is not None:
                meta.set_format(self, format_)
        else:
            assert_is_instance(
                "data",
                data,
                (
                    Iterable,
                    Mapping,
                    abc.Model,
                    NoneType,
                ),
            )
            deserialized_data = data
        return deserialized_data

    def _init_pointer(self) -> None:
        """
        This function sets the root pointer value, and recursively applies
        appropriate pointers to child elements.
        """
        if meta.get_pointer(self) is None:
            meta.set_pointer(self, "#")

    @abstractmethod
    def _marshal(self) -> abc.JSONTypes:
        pass

    @abstractmethod
    def _validate(self, raise_errors: bool = True) -> List[str]:
        pass


class Array(Model, abc.Array):
    """
    This can serve as either a base-class for typed (or untyped) sequences, or
    can be instantiated directly.

    Parameters:

    - items (list|set|abc.Readable|str|bytes)
    - item_types ([type|sob.properties.Property])

    Typing can be enforced at the instance level by
    passing the keyword argument `item_types` with a list of types or
    properties.

    Typing can be enforced at the class level by assigning a list
    of types as follows:

    ```python
    import sob

    class ArraySubClass(sob.model.Array):

        pass

    sob.meta.writable(ArraySubClass).item_types = [
        sob.properties.String,
        sob.properties.Integer
    ]
    ```
    """

    _hooks: Optional[abc.ArrayHooks]
    _meta: Optional[abc.ArrayMeta]

    def __init__(
        self,
        items: Union[
            abc.Array,
            Iterable[abc.MarshallableTypes],
            str,
            bytes,
            abc.Readable,
            None,
        ] = None,
        item_types: Union[
            Iterable[Union[type, abc.Property]],
            abc.Types,
            type,
            abc.Property,
            None,
        ] = None,
    ) -> None:
        Model.__init__(self)
        self._list: List[abc.MarshallableTypes] = []
        self._init_url(items)
        deserialized_items: Union[
            Iterable[abc.MarshallableTypes], abc.Model, None
        ] = self._init_format(items)
        assert isinstance(deserialized_items, (NoneType, Iterable))
        self._init_item_types(deserialized_items, item_types)
        self._init_items(deserialized_items)
        self._init_pointer()

    def _init_item_types(
        self,
        items: Union[Iterable[abc.MarshallableTypes], abc.Model, None],
        item_types: Union[
            Iterable[Union[type, abc.Property]],
            abc.Types,
            type,
            abc.Property,
            None,
        ],
    ) -> None:
        if item_types is None:
            # If no item types are explicitly attributed, but the initial items
            # are an instance of `Array`, we adopt the item types from that
            # `Array` instance.
            if isinstance(items, abc.Array):
                items_meta: Optional[abc.ArrayMeta] = meta.array_read(items)
                if meta.array_read(self) is not items_meta:
                    meta.write(self, deepcopy(items_meta))
        else:
            meta_: abc.ArrayMeta = meta.array_writable(self)
            meta_.item_types = item_types  # type: ignore

    def _init_items(
        self, items: Union[Iterable[abc.MarshallableTypes], abc.Array, None]
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
        stop: Optional[int] = None,
    ) -> int:
        return self._list.index(
            value, start, *([] if stop is None else [stop])
        )

    def count(self, value: abc.MarshallableTypes) -> int:
        return self._list.count(value)

    def __hash__(self) -> int:  # type: ignore
        return id(self)

    def __setitem__(self, index: int, value: abc.MarshallableTypes) -> None:
        instance_hooks: Optional[abc.ArrayHooks] = hooks.array_read(self)
        if instance_hooks and instance_hooks.before_setitem:
            index, value = instance_hooks.before_setitem(self, index, value)
        meta_: Optional[abc.ArrayMeta] = meta.array_read(self)
        item_types: Optional[abc.Types] = (
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
        if not isinstance(value, abc.MARSHALLABLE_TYPES + (NoneType,)):
            raise errors.UnmarshalTypeError(data=value)
        instance_hooks: Optional[abc.ArrayHooks] = hooks.array_read(self)
        if instance_hooks and instance_hooks.before_append:
            value = instance_hooks.before_append(self, value)
        instance_meta: Optional[abc.ArrayMeta] = meta.array_read(self)
        item_types: Optional[abc.Types] = None
        if instance_meta:
            item_types = instance_meta.item_types
        value = unmarshal(value, types=item_types or ())
        self._list.append(value)
        if instance_hooks and instance_hooks.after_append:
            instance_hooks.after_append(self, value)

    def clear(self) -> None:
        self._list.clear()

    def reverse(self) -> None:
        self._list.reverse()

    def sort(
        self,
        key: Optional[Callable[[Any], Any]] = None,
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

    def __iadd__(self, values: Iterable[abc.MarshallableTypes]) -> abc.Array:
        self.extend(values)
        return self

    def __add__(self, values: Iterable[abc.MarshallableTypes]) -> abc.Array:
        new_array: abc.Array = copy(self)
        return new_array.__iadd__(values)

    def __copy__(self) -> abc.Array:
        return self.__class__(self)

    def __deepcopy__(self, memo: Optional[dict] = None) -> abc.Array:
        new_instance: Array = self.__class__()
        assert isinstance(new_instance, abc.Model)
        instance_meta: Optional[abc.ArrayMeta] = meta.array_read(self)
        class_meta: Optional[abc.ArrayMeta] = meta.array_read(type(self))
        if instance_meta is not class_meta:
            meta.write(
                new_instance, deepcopy(instance_meta, memo=memo)
            )  # noqa
        instance_hooks: Optional[abc.ArrayHooks] = hooks.array_read(self)
        class_hooks: Optional[abc.ArrayHooks] = hooks.array_read(type(self))
        if instance_hooks is not class_hooks:
            hooks.write(
                new_instance, deepcopy(instance_hooks, memo=memo)  # noqa
            )  # noqa
        item: abc.MarshallableTypes
        for item in self:
            new_instance.append(deepcopy(item, memo=memo))  # noqa
        return new_instance

    def _marshal(self) -> Sequence[abc.JSONTypes]:
        assert isinstance(self, abc.Array)
        data: abc.Model = self
        instance_hooks: Optional[abc.ArrayHooks] = hooks.array_read(self)
        if instance_hooks and instance_hooks.before_marshal:
            data = instance_hooks.before_marshal(data)
        metadata: Optional[abc.ArrayMeta] = meta.array_read(self)
        assert isinstance(data, abc.Array)
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
            assert isinstance(after_marshal_data, Sequence)
            marshalled_data = after_marshal_data
        return marshalled_data

    def _validate(self, raise_errors: bool = True) -> List[str]:
        validation_errors: List[str] = []
        instance_hooks: Optional[abc.ArrayHooks] = hooks.array_read(self)
        data: abc.Model = self
        if instance_hooks and instance_hooks.before_validate:
            data = instance_hooks.before_validate(self)
        instance_meta: Optional[abc.ArrayMeta] = meta.array_read(self)
        if instance_meta and instance_meta.item_types:
            item: Any
            assert isinstance(data, abc.Array)
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
            qualified_name(item) if isinstance(item, type) else repr(item)
        )
        item_lines = item_representation.split("\n")
        if len(item_lines) > 1:
            item_representation = "\n        ".join(item_lines)
        return f"        {item_representation},"

    def __repr__(self) -> str:
        """
        A string representation of this array which can be used to recreate the
        array
        """
        assert isinstance(self, abc.Array)
        instance_meta: Optional[abc.ArrayMeta] = meta.array_read(self)
        class_meta: Optional[abc.ArrayMeta] = meta.array_read(type(self))
        representation_lines = [qualified_name(type(self)) + "("]
        if len(self) > 0:
            representation_lines.append("    [")
            item: Any
            for item in self:
                representation_lines.append(self._repr_item(item))
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
        if len(representation_lines) > 2:
            representation = "\n".join(representation_lines)
        else:
            representation = "".join(representation_lines)
        return representation

    def __eq__(self, other: Any) -> bool:
        if type(self) is not type(other):
            return False
        length = len(self)
        if length != len(other):
            return False
        for i in range(length):
            if self[i] != other[i]:
                return False
        return True

    def __ne__(self, other: Any) -> bool:
        if self == other:
            return False
        else:
            return True

    def __str__(self) -> str:
        return serialize(self)

    def __len__(self) -> int:
        return self._list.__len__()


class Dictionary(Model, abc.Dictionary):
    """
    This can serve as either a base-class for typed (or untyped) dictionaries,
    or can be instantiated directly.

    Parameters:

    - items (list|set|abc.Readable|str|bytes)
    - value_types ([type|sob.properties.Property])

    Typing can be enforced at the instance level by
    passing the keyword argument `value_types` with a list of types or
    properties.

    Typing can be enforced at the class level by assigning a list
    of types as follows:

    ```python
    import sob

    class DictionarySubClass(sob.model.Dictionary):

        pass

    sob.meta.writable(DictionarySubClass).value_types = [
        sob.properties.String,
        sob.properties.Integer
    ]
    ```
    """

    _hooks: Optional[abc.DictionaryHooks]
    _meta: Optional[abc.DictionaryMeta]

    def __init__(
        self,
        items: Union[
            abc.Dictionary,
            Mapping[str, abc.MarshallableTypes],
            Iterable[Tuple[str, abc.MarshallableTypes]],
            abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        value_types: Union[
            Iterable[Union[type, abc.Property]],
            type,
            abc.Property,
            abc.Types,
            None,
        ] = None,
    ) -> None:
        Model.__init__(self)
        self._dict: "abc.OrderedDict[str, abc.MarshallableTypes]" = (
            collections.OrderedDict()
        )
        self._meta: Optional[abc.DictionaryMeta]
        self._hooks: Optional[abc.DictionaryHooks]
        self._init_url(items)
        deserialized_items: Union[
            Iterable[abc.MarshallableTypes],
            Mapping[str, abc.MarshallableTypes],
            abc.Model,
            None,
        ] = self._init_format(items)
        self._init_value_types(deserialized_items, value_types)  # type: ignore
        self._init_items(deserialized_items)  # type: ignore
        self._init_pointer()

    def _init_format(
        self,
        data: Union[
            str,
            bytes,
            abc.Readable,
            Mapping[str, abc.MarshallableTypes],
            Iterable[abc.MarshallableTypes],
            abc.Model,
            None,
        ] = None,
    ) -> Union[
        Iterable[abc.MarshallableTypes],
        Mapping[str, abc.MarshallableTypes],
        abc.Model,
        None,
    ]:
        deserialized_items: Union[
            Iterable[abc.MarshallableTypes],
            Mapping[str, abc.MarshallableTypes],
            abc.Model,
            None,
        ] = super()._init_format(data)
        if not isinstance(
            deserialized_items, (abc.Dictionary, Mapping, NoneType)
        ) and isinstance(deserialized_items, Iterable):
            deserialized_items = collections.OrderedDict(
                deserialized_items  # type: ignore
            )
        assert_is_instance(
            "deserialized_items",
            deserialized_items,
            (abc.Dictionary, Mapping, NoneType),
        )
        return deserialized_items

    def _init_items(
        self,
        data: Union[
            Mapping[str, abc.MarshallableTypes],
            Iterable[Tuple[str, abc.MarshallableTypes]],
            abc.Dictionary,
            None,
        ],
    ) -> None:
        if data is not None:
            items: Iterable[Tuple[str, abc.MarshallableTypes]]
            if isinstance(data, (collections.OrderedDict, abc.Dictionary)) or (
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
        items: Union[
            Mapping[str, abc.MarshallableTypes], abc.Dictionary, None
        ],
        value_types: Union[
            Iterable[Union[type, abc.Property]],
            type,
            abc.Property,
            abc.Types,
            None,
        ],
    ) -> None:
        if value_types is None:
            # If no value types are explicitly attributed, but the initial
            # items are an instance of `Dictionary`, we adopt the item types
            # from that `Array` instance.
            if isinstance(items, abc.Dictionary):
                meta_: Optional[abc.DictionaryMeta] = meta.dictionary_read(
                    self
                )
                values_meta: Optional[
                    abc.DictionaryMeta
                ] = meta.dictionary_read(items)
                if meta_ is not values_meta:
                    meta.write(self, deepcopy(values_meta))
        else:
            writable_meta: abc.Meta = meta.writable(self)
            assert isinstance(writable_meta, abc.DictionaryMeta)
            writable_meta.value_types = value_types  # type: ignore

    def __hash__(self) -> int:
        return id(self)

    def __setitem__(self, key: str, value: abc.MarshallableTypes) -> None:
        instance_hooks: Optional[abc.DictionaryHooks] = hooks.dictionary_read(
            self
        )
        if instance_hooks and instance_hooks.before_setitem:
            key, value = instance_hooks.before_setitem(self, key, value)
        instance_meta: Optional[abc.DictionaryMeta] = meta.dictionary_read(
            self
        )
        value_types: Optional[abc.Types] = None
        if instance_meta:
            value_types = instance_meta.value_types
        try:
            unmarshalled_value: abc.MarshallableTypes = unmarshal(
                value, types=value_types or ()
            )
        except TypeError as error:
            message = f"\n - {qualified_name(type(self))}['{key}']: {{}}"
            if error.args and isinstance(error.args[0], str):
                error.args = tuple(
                    chain((message.format(error.args[0]),), error.args[1:])
                )
            else:
                error.args = (message.format(repr(value)),)
            raise error
        if unmarshalled_value is None:
            raise RuntimeError(f"{key} = {repr(unmarshalled_value)}")
        self._dict.__setitem__(key, unmarshalled_value)
        if instance_hooks and instance_hooks.after_setitem:
            instance_hooks.after_setitem(self, key, unmarshalled_value)

    def __copy__(self) -> abc.Dictionary:
        new_instance: abc.Dictionary = self.__class__()
        instance_meta: Optional[abc.DictionaryMeta] = meta.dictionary_read(
            self
        )
        class_meta: Optional[abc.DictionaryMeta] = meta.dictionary_read(
            type(self)
        )
        if instance_meta is not class_meta:
            meta.write(new_instance, instance_meta)
        instance_hooks: Optional[abc.DictionaryHooks] = hooks.dictionary_read(
            self
        )
        class_hooks: Optional[abc.DictionaryHooks] = hooks.dictionary_read(
            type(self)
        )
        if instance_hooks is not class_hooks:
            hooks.write(new_instance, instance_hooks)
        key: str
        value: abc.MarshallableTypes
        for key, value in self.items():
            new_instance[key] = value
        return new_instance

    def __deepcopy__(self, memo: dict = None) -> "Dictionary":
        new_instance = self.__class__()
        instance_meta: Optional[abc.DictionaryMeta] = meta.dictionary_read(
            self
        )
        class_meta: Optional[abc.DictionaryMeta] = meta.dictionary_read(
            type(self)
        )
        if instance_meta is not class_meta:
            meta.write(
                new_instance, deepcopy(instance_meta, memo=memo)
            )  # noqa
        instance_hooks: Optional[abc.DictionaryHooks] = hooks.dictionary_read(
            self
        )
        class_hooks: Optional[abc.DictionaryHooks] = hooks.dictionary_read(
            type(self)
        )
        if instance_hooks is not class_hooks:
            hooks.write(
                new_instance, deepcopy(instance_hooks, memo=memo)
            )  # noqa
        key: str
        value: abc.MarshallableTypes
        for key, value in self.items():
            new_instance[key] = deepcopy(value, memo=memo)
        return new_instance

    def _marshal(self) -> "abc.OrderedDict[str, abc.JSONTypes]":
        """
        This method marshals an instance of `Dictionary` as built-in type
        `OrderedDict` which can be serialized into
        JSON/YAML.
        """
        # Check for hooks
        instance_hooks: Optional[abc.DictionaryHooks] = hooks.dictionary_read(
            self
        )
        # This variable is needed because before-marshal hooks are permitted to
        # return altered *copies* of `self`, so prior to marshalling--this
        # variable may no longer point to `self`
        data: abc.Model = self
        # Execute before-marshal hooks, if applicable
        if instance_hooks and instance_hooks.before_marshal:
            data = instance_hooks.before_marshal(data)
        assert isinstance(data, abc.Dictionary)
        # Get the metadata, if any has been assigned
        instance_meta: Optional[abc.DictionaryMeta] = meta.dictionary_read(
            data
        )
        # Check to see if value types are defined in the metadata
        value_types: Optional[abc.Types] = (
            instance_meta.value_types if instance_meta else None
        )
        # Recursively convert the data to generic, serializable, data types
        marshalled_data: "abc.OrderedDict[str, abc.JSONTypes]" = (
            collections.OrderedDict(
                [
                    (key, marshal(value, types=value_types))
                    for key, value in data.items()
                ]
            )
        )
        # Execute after-marshal hooks, if applicable
        if (instance_hooks is not None) and (
            instance_hooks.after_marshal is not None
        ):
            after_marshal_data: abc.JSONTypes = instance_hooks.after_marshal(
                marshalled_data
            )
            after_marshal_dictionary: "abc.OrderedDict[str, abc.JSONTypes]"
            if isinstance(after_marshal_data, collections.OrderedDict):
                after_marshal_dictionary = after_marshal_data
            elif isinstance(after_marshal_data, Reversible) and isinstance(
                after_marshal_data, (Mapping, abc.Dictionary)
            ):
                after_marshal_dictionary = collections.OrderedDict(
                    after_marshal_data.items()
                )
            else:
                assert isinstance(after_marshal_data, Mapping)
                after_marshal_dictionary = collections.OrderedDict(
                    sorted(
                        after_marshal_data.items(), key=lambda item: item[0]
                    )
                )
            marshalled_data = after_marshal_dictionary
        return marshalled_data

    def _validate(self, raise_errors: bool = True) -> List[str]:
        """
        Recursively validate
        """
        validation_errors: List[str] = []
        hooks_: Optional[abc.DictionaryHooks] = hooks.dictionary_read(self)
        data: abc.Model = self
        if hooks_ and hooks_.before_validate:
            data = hooks_.before_validate(data)
        assert isinstance(data, (NoneType, abc.Dictionary))
        meta_: Optional[abc.DictionaryMeta] = meta.dictionary_read(data)
        value_types: Optional[abc.Types] = meta_.value_types if meta_ else None
        if value_types is not None:
            assert isinstance(data, abc.Dictionary)
            key: str
            value: abc.MarshallableTypes
            for key, value in data.items():
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
            qualified_name(value) if isinstance(value, type) else repr(value)
        )
        value_representation_lines = value_representation.split("\n")
        if len(value_representation_lines) > 1:
            indented_lines = [value_representation_lines[0]]
            for line in value_representation_lines[1:]:
                indented_lines.append(f"            {line}")
            value_representation = "\n".join(indented_lines)
            representation = "\n".join(
                [
                    "        (",
                    f"            {repr(key)},",
                    f"            {value_representation}",
                    "        ),",
                ]
            )
        else:
            representation = f"        ({repr(key)}, {value_representation}),"
        return representation

    def __repr__(self) -> str:
        """
        Return a string representation of this object which can be used to
        re-assemble the object programmatically
        """
        class_meta: Optional[abc.DictionaryMeta] = meta.dictionary_read(
            type(self)
        )
        instance_meta: Optional[abc.DictionaryMeta] = meta.dictionary_read(
            self
        )
        representation_lines: List[str] = [qualified_name(type(self)) + "("]
        items: Tuple[Tuple[str, abc.MarshallableTypes], ...] = tuple(  # noqa
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
        if len(representation_lines) > 2:
            representation = "\n".join(representation_lines)
        else:
            representation = "".join(representation_lines)
        return representation

    def __eq__(self, other: Any) -> bool:
        if type(self) is not type(other):
            return False
        keys = tuple(self.keys())
        other_keys = tuple(other.keys())
        if keys != other_keys:
            return False
        key: str
        for key in keys:
            if self[key] != other[key]:
                return False
        return True

    def __ne__(self, other: Any) -> bool:
        if self == other:
            return False
        else:
            return True

    def __str__(self) -> str:
        return serialize(self)

    def __delitem__(self, key: str) -> None:
        self._dict.__delitem__(key)

    def pop(self, key: str, default: Undefined = UNDEFINED) -> Any:
        return self._dict.pop(
            key, *([] if default is UNDEFINED else [default])
        )

    def popitem(self) -> Tuple[str, Any]:
        return self._dict.popitem()

    def clear(self) -> None:
        self._dict.clear()

    def update(
        self,
        *args: Union[
            Mapping[str, abc.MarshallableTypes],
            Iterable[Tuple[str, abc.MarshallableTypes]],
            abc.Dictionary,
        ],
        **kwargs: abc.MarshallableTypes,
    ) -> None:
        other: Union[
            Mapping[str, abc.MarshallableTypes],
            Iterable[Tuple[str, abc.MarshallableTypes]],
            abc.Dictionary,
        ]
        key: str
        value: abc.MarshallableTypes
        items: Iterable[Tuple[str, abc.MarshallableTypes]] = ()
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
    ) -> Optional[Any]:
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


class Object(Model, abc.Object):
    """
    This serves as a base class for representing deserialized and un-marshalled
    data for which a discrete set of properties are known in advance, and for
    which enforcing adherence to a predetermined attribution and type
    requirements is desirable.
    """

    def __init__(
        self,
        _data: Union[
            abc.Object,
            abc.Dictionary,
            Mapping[str, abc.MarshallableTypes],
            Iterable[Tuple[str, abc.MarshallableTypes]],
            abc.Readable,
            str,
            bytes,
            None,
        ] = None,
    ) -> None:
        Model.__init__(self)
        self._meta: Optional[abc.ObjectMeta] = None
        self._hooks: Optional[abc.ObjectHooks] = None
        self._init_url(_data)
        deserialized_data: Union[
            Iterable[abc.MarshallableTypes],
            Mapping[str, abc.MarshallableTypes],
            abc.Model,
            None,
        ] = self._init_format(_data)
        try:
            assert isinstance(deserialized_data, (abc.Object, dict, NoneType))
        except AssertionError:
            raise IsInstanceAssertionError(
                "deserialized_data",
                deserialized_data,
                (abc.Object, dict, NoneType),
            )
        self._data_init(deserialized_data)
        self._init_pointer()

    def _data_init(
        self,
        data: Union[
            Mapping[str, abc.MarshallableTypes],
            abc.Object,
            abc.Dictionary,
            None,
        ],
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
        dictionary: Union[Mapping[str, abc.MarshallableTypes], abc.Dictionary],
    ) -> None:
        """
        Initialize this object from a dictionary
        """
        key: str
        value: abc.MarshallableTypes
        for key, value in dictionary.items():
            if value is None:
                value = NULL
            try:
                self.__setitem__(key, value)
            except KeyError as error:
                raise errors.UnmarshalKeyError(
                    "{}\n\n{}.{}: {}".format(
                        errors.get_exception_text(),
                        qualified_name(type(self)),
                        error.args[0],
                        represent(dictionary),
                    )
                )

    def _copy_init(self, other: abc.Object) -> None:
        """
        Initialize this object from another `Object` (copy constructor)
        """
        other_meta: Optional[abc.ObjectMeta] = meta.object_read(other)
        if meta.object_read(self) is not other_meta:
            meta.write(self, deepcopy(other_meta))
        instance_hooks: Optional[abc.ObjectHooks] = hooks.object_read(other)
        if hooks.object_read(self) is not instance_hooks:
            hooks.write(self, deepcopy(instance_hooks))
        if other_meta and other_meta.properties:
            for property_name_ in other_meta.properties.keys():
                try:
                    setattr(
                        self, property_name_, getattr(other, property_name_)
                    )
                except TypeError as error:
                    label = "\n - %s.%s: " % (
                        qualified_name(type(self)),
                        property_name_,
                    )
                    if error.args:
                        error.args = tuple(
                            chain((label + error.args[0],), error.args[1:])
                        )
                    else:
                        error.args = (label + serialize(other),)
                    raise error
            meta.url(self, meta.url(other))
            meta.pointer(self, meta.pointer(other))
            meta.format_(self, meta.format_(other))

    def __hash__(self) -> int:
        """
        Make this usable in contexts requiring a hashable object
        """
        return id(self)

    def _get_property_definition(self, property_name_: str) -> abc.Property:
        """
        Get a property's definition
        """
        meta_: Optional[abc.ObjectMeta] = meta.object_read(self)
        if meta_ and meta_.properties:
            try:
                return meta_.properties[property_name_]
            except (KeyError, AttributeError):
                pass
        raise KeyError(
            '`%s` has no attribute "%s".'
            % (qualified_name(type(self)), property_name_)
        )

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
                message = "\n - %s.%s: " % (
                    qualified_name(type(self)),
                    property_name_,
                )
                if error.args and isinstance(error.args[0], str):
                    error.args = tuple(
                        chain((message + error.args[0],), error.args[1:])
                    )
                else:
                    error.args = (message + repr(value),)
                raise error
        return value

    def __setattr__(
        self, property_name_: str, value: abc.MarshallableTypes
    ) -> None:
        unmarshalled_value: abc.MarshallableTypes = value
        instance_hooks: Optional[abc.ObjectHooks] = hooks.object_read(self)
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

    def _get_key_property_name(self, key: str) -> str:
        property_name_: Optional[str] = None
        instance_meta: Optional[abc.ObjectMeta] = meta.object_read(self)
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
        if property_name_ is None:
            found_in: str = ""
            type_module_name: str = getattr(type(self), "__module__", "")
            if type_module_name:
                type_module: Any = sys.modules.get(type_module_name, None)
                if type_module:
                    type_module_file: str = os.path.abspath(
                        getattr(type_module, "__file__", "")
                    )
                    found_in = f"found in {type_module_file}, "
            raise KeyError(
                f"`{qualified_name(type(self))}`, {found_in}"
                f'has no property mapped to the name "{key}"'
            )
        return property_name_

    def __setitem__(self, key: str, value: abc.MarshallableTypes) -> None:
        # Before set-item hooks
        hooks_: Optional[abc.ObjectHooks] = hooks.object_read(self)
        if hooks_ and hooks_.before_setitem:
            key, value = hooks_.before_setitem(self, key, value)
        # Get the corresponding property name
        property_name_: str = self._get_key_property_name(key)
        # Set the attribute value
        self.__setattr__(property_name_, value)
        # After set-item hooks
        if hooks_ and hooks_.after_setitem:
            hooks_.after_setitem(self, key, value)

    def __delattr__(self, key: str) -> None:
        """
        Deleting attributes with defined metadata is not allowed--doing this
        is instead interpreted as setting that attribute to `None`.
        """
        instance_meta: Optional[abc.ObjectMeta] = meta.object_read(self)
        if (
            instance_meta
            and instance_meta.properties
            and (key in instance_meta.properties)
        ):
            setattr(self, key, None)
        else:
            object.__delattr__(self, key)

    def __delitem__(self, key: str) -> None:
        self.__delattr__(self._get_key_property_name(key))

    def __getitem__(self, key: str) -> None:
        """
        Retrieve a value using the item assignment operators `[]`.
        """
        return getattr(self, self._get_key_property_name(key))

    def __copy__(self) -> abc.Object:
        return self.__class__(self)

    def _deepcopy_property(
        self,
        property_name_: str,
        other: abc.Object,
        memo: Optional[dict],
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
                    value = deepcopy(value, memo=memo)  # noqa
                setattr(other, property_name_, value)
        except TypeError as error:
            label = "%s.%s: " % (qualified_name(type(self)), property_name_)
            if error.args:
                error.args = tuple(
                    chain((label + error.args[0],), error.args[1:])
                )
            else:
                error.args = (label + serialize(self),)
            raise error

    def __deepcopy__(self, memo: Optional[dict]) -> abc.Object:
        # Perform a regular copy operation
        new_instance: abc.Object = self.__copy__()
        # Retrieve the metadata
        meta_: Optional[abc.ObjectMeta] = meta.object_read(self)
        # If there is metadata--copy it recursively
        if meta_ and meta_.properties:
            for property_name_ in meta_.properties.keys():
                self._deepcopy_property(property_name_, new_instance, memo)
        return new_instance

    def _marshal(self) -> "abc.OrderedDict[str, abc.JSONTypes]":
        object_: abc.Object = self
        instance_hooks: Optional[abc.ObjectHooks] = hooks.object_read(self)
        if instance_hooks and instance_hooks.before_marshal:
            before_marshal_object: abc.Model = instance_hooks.before_marshal(
                self
            )
            if TYPE_CHECKING:
                assert isinstance(before_marshal_object, abc.Object)
            object_ = before_marshal_object
        data: "abc.OrderedDict[str, abc.JSONTypes]" = collections.OrderedDict()
        instance_meta: Optional[abc.ObjectMeta] = meta.object_read(object_)
        if instance_meta and instance_meta.properties is not None:
            property_name_: str
            property_: abc.Property
            for property_name_, property_ in instance_meta.properties.items():
                value: abc.JSONTypes = getattr(object_, property_name_)
                if value is not None:
                    data[
                        property_.name or property_name_
                    ] = _marshal_property_value(property_, value)
        if instance_hooks and instance_hooks.after_marshal:
            after_marshal_data: abc.JSONTypes = instance_hooks.after_marshal(
                data
            )
            if TYPE_CHECKING:
                assert isinstance(after_marshal_data, collections.OrderedDict)
            data = after_marshal_data
        return data

    def __str__(self) -> str:
        return serialize(self)

    @staticmethod
    def _repr_argument(parameter: str, value: abc.MarshallableTypes) -> str:
        value_representation: str
        if isinstance(value, type):
            value_representation = qualified_name(value)
        else:
            value_representation = repr(value)
        lines = value_representation.split("\n")
        if len(lines) > 1:
            indented_lines = [lines[0]]
            for line in lines[1:]:
                indented_lines.append("    " + line)
            value_representation = "\n".join(indented_lines)
        return f"    {parameter}={value_representation},"

    def __repr__(self) -> str:
        representation = ["%s(" % qualified_name(type(self))]
        instance_meta: Optional[abc.ObjectMeta] = meta.object_read(self)
        if instance_meta and instance_meta.properties:
            property_name_: str
            value: abc.MarshallableTypes
            for property_name_ in instance_meta.properties.keys():
                value = getattr(self, property_name_)
                if value is not None:
                    representation.append(
                        self._repr_argument(property_name_, value)
                    )
            # Strip the last comma
            if representation:
                representation[-1] = representation[-1].rstrip(",")
        representation.append(")")
        if len(representation) > 2:
            return "\n".join(representation)
        else:
            return "".join(representation)

    def __eq__(self, other: abc.Any) -> bool:
        if type(self) is not type(other):
            return False
        instance_meta: Optional[abc.ObjectMeta] = meta.object_read(self)
        self_properties = set(
            instance_meta.properties.keys()
            if instance_meta and instance_meta.properties
            else ()
        )
        other_meta: Optional[abc.ObjectMeta] = meta.object_read(other)
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

    def __ne__(self, other: Any) -> bool:
        return False if self == other else True

    def __iter__(self) -> Iterator[str]:
        instance_meta: Optional[abc.ObjectMeta] = meta.object_read(self)
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
        error_messages: List[str] = []
        if value is None:
            if property_.required:
                yield (
                    "The property `%s` is required for `%s`:\n%s"
                    % (property_name_, qualified_name(type(self)), str(self))
                )
        elif value is NULL:
            if (property_.types is not None) and (Null not in property_.types):
                error_messages.append(
                    "Null values are not allowed in `{}.{}`, "
                    "permitted types include: {}.".format(
                        qualified_name(type(self)),
                        property_name_,
                        ", ".join(
                            "`{}`".format(
                                qualified_name(type_)
                                if isinstance(type_, type)
                                else qualified_name(type(type_))
                            )
                            for type_ in getattr(property_, "types")
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
                    "`{}.{}`:\n\n{}".format(
                        qualified_name(type(self)),
                        property_name_,
                        error_message,
                    )
                )

    def _validate(self, raise_errors: bool = True) -> List[str]:
        """
        This method verifies that all required properties are present, and
        that all property values are of the correct type.
        """
        validation_error_messages: List[str] = []
        validated_object: abc.Object = self
        instance_hooks: Optional[abc.ObjectHooks] = hooks.object_read(self)
        if instance_hooks and instance_hooks.before_validate:
            validated_model: abc.Model = instance_hooks.before_validate(self)
            if TYPE_CHECKING:
                assert isinstance(validated_model, abc.Object)
            validated_object = validated_model
        instance_meta: Optional[abc.ObjectMeta] = meta.object_read(
            validated_object
        )
        if instance_meta and instance_meta.properties:
            property_name_: str
            property_: abc.Property
            error_message: str
            for (
                property_name_,
                property_,
            ) in instance_meta.properties.items():
                for error_message in (
                    validated_object
                )._get_property_validation_error_messages(
                    property_name_,
                    property_,
                    getattr(validated_object, property_name_),
                ):
                    validation_error_messages.append(error_message)
            if instance_hooks and instance_hooks.after_validate:
                instance_hooks.after_validate(validated_object)
            if raise_errors and validation_error_messages:
                raise errors.ValidationError(
                    "\n".join(validation_error_messages)
                )
        return validation_error_messages


# region marshal


def _marshal_collection(
    data: Union[
        Mapping[str, abc.MarshallableTypes],
        Collection[abc.MarshallableTypes],
        abc.Dictionary,
    ],
    value_types: Optional[Iterable[Union[type, abc.Property]]] = None,
    item_types: Union[
        Iterable[Union[type, abc.Property]], abc.Types, None
    ] = None,
) -> Union[Mapping[str, abc.MarshallableTypes], List[abc.MarshallableTypes]]:
    if isinstance(data, (Mapping, abc.Dictionary)):
        return _marshal_mapping(data, value_types)
    else:
        value: abc.MarshallableTypes
        marshalled_data: List[abc.MarshallableTypes] = []
        for value in data:
            marshalled_data.append(marshal(value, types=item_types))
        return marshalled_data


def _marshal_mapping(
    data: Union[Mapping[str, abc.MarshallableTypes], abc.Dictionary],
    value_types: Union[
        Iterable[Union[type, abc.Property]], abc.Types, None
    ] = None,
) -> "abc.OrderedDict[str, abc.MarshallableTypes]":
    key: str
    value: abc.MarshallableTypes
    marshalled_data: "abc.OrderedDict[str, abc.MarshallableTypes]" = (
        collections.OrderedDict()
    )
    items: Iterable[Tuple[str, abc.MarshallableTypes]]
    if isinstance(data, (abc.Dictionary, collections.OrderedDict)) or (
        isinstance(data, Reversible) and isinstance(data, Mapping)
    ):
        items = data.items()
    else:
        assert isinstance(data, Mapping)
        # This gives consistent sorting for non-ordered mappings
        items = sorted(data.items(), key=lambda item: item[0])
    for key, value in items:
        marshalled_data[key] = marshal(value, types=value_types)
    return marshalled_data


def _marshal_typed(
    data: abc.MarshallableTypes,
    types: Union[Iterable[Union[type, abc.Property]], abc.Types],
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
        raise TypeError(
            f"{repr(data)} cannot be interpreted as any of the designated "
            f"types: {repr(types)}"
        )
    return marshalled_data


def marshal(
    data: abc.MarshallableTypes,
    types: Union[Iterable[Union[type, abc.Property]], abc.Types, None] = None,
    value_types: Union[
        Iterable[Union[type, abc.Property]], abc.Types, None
    ] = None,
    item_types: Union[
        Iterable[Union[type, abc.Property]], abc.Types, None
    ] = None,
) -> abc.JSONTypes:
    """
    Recursively converts data which is not serializable using the `json` module
    into formats which *can* be represented as JSON.
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
        marshalled_data = getattr(data, "_marshal")()
    elif types is not None:
        marshalled_data = _marshal_typed(data, types)
    elif isinstance(data, (date, datetime)):
        marshalled_data = data.isoformat()
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
        raise ValueError(f"Cannot unmarshal: {repr(data)}")
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
        types: Union[
            Iterable[Union[type, abc.Property]],
            abc.Types,
            type,
            abc.Property,
        ] = (),
        value_types: Union[
            Iterable[Union[type, abc.Property]],
            abc.Types,
            type,
            abc.Property,
        ] = (),
        item_types: Union[
            Iterable[Union[type, abc.Property]],
            abc.Types,
            type,
            abc.Property,
        ] = (),
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
        self.types: Union[
            Iterable[Union[type, abc.Property]],
            abc.Types,
        ] = types
        self.value_types: Union[
            Iterable[Union[type, abc.Property]],
            abc.Types,
        ] = value_types
        self.item_types: Union[
            Iterable[Union[type, abc.Property]],
            abc.Types,
        ] = item_types
        self.meta: Optional[abc.Meta] = None

    def __call__(self) -> abc.MarshallableTypes:
        """
        Return `self.data` unmarshalled
        """
        try:
            unmarshalled_data: abc.MarshallableTypes = self.data
            if self.data is not NULL:
                # If the data is a sob `Model`, get it's metadata
                if isinstance(self.data, abc.Model):
                    self.meta = meta.read(self.data)
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
            raise error
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
            items: List[abc.MarshallableTypes] = [
                (NULL if item is None else item) for item in self.data
            ]
            unmarshalled_data = Array(
                items, item_types=self.item_types or None
            )
        elif not isinstance(self.data, abc.MARSHALLABLE_TYPES):
            raise errors.UnmarshalValueError(
                f"{repr(self.data)} cannot be un-marshalled"
            )
        return unmarshalled_data

    @property  # type: ignore
    def as_typed(self) -> abc.MarshallableTypes:
        unmarshalled_data: Union[abc.MarshallableTypes, Undefined] = UNDEFINED
        first_error: Optional[Exception] = None
        error_messages: List[str] = []
        # Attempt to un-marshal the data as each type, in the order
        # provided
        assert self.types
        for type_ in self.types:
            try:
                unmarshalled_data = self.as_type(type_)
                # If the data is un-marshalled successfully, we do
                # not need to try any further types
                break
            except (AttributeError, KeyError, TypeError, ValueError) as error:
                if first_error is None:
                    first_error = error
                error_messages.append(errors.get_exception_text())
        if isinstance(unmarshalled_data, Undefined):
            if (first_error is None) or isinstance(first_error, TypeError):
                raise errors.UnmarshalTypeError(
                    "\n".join(error_messages),
                    data=self.data,
                    types=self.types,
                    value_types=self.value_types,
                    item_types=self.item_types,
                )
            elif isinstance(first_error, ValueError):
                raise errors.UnmarshalValueError(
                    "\n".join(error_messages),
                    data=self.data,
                    types=self.types,
                    value_types=self.value_types,
                    item_types=self.item_types,
                )
            else:
                raise first_error
        return unmarshalled_data

    def get_dictionary_type(self, type_: type) -> Optional[type]:
        """
        Get the dictionary type to use
        """
        dictionary_type: Optional[type]
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
        hooks_ = hooks.read(type_)
        if hooks_:
            before_unmarshal_hook = hooks_.before_unmarshal
            if before_unmarshal_hook:
                data = before_unmarshal_hook(deepcopy(data))
        return data

    @staticmethod
    def after_hook(type_: type, data: abc.Model) -> abc.Model:
        hooks_ = hooks.read(type_)
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

    def get_array_type(self, type_: type) -> Type[abc.Array]:
        if type_ is abc.Array:
            type_ = Array
        elif issubclass(type_, abc.Array):
            pass
        elif _is_non_string_sequence_or_set_subclass(type_):
            type_ = Array
        else:
            raise TypeError(
                f"{repr(self.data)} is not of type `{repr(type_)}`"
            )
        return type_

    def as_array_type(self, type_: type) -> abc.Array:
        type_ = self.get_array_type(type_)
        if "item_types" in signature(type_).parameters:
            unmarshalled_data = type_(
                self.data, item_types=self.item_types or None  # type: ignore
            )
        else:
            unmarshalled_data = type_(self.data)  # type: ignore
        return unmarshalled_data

    def as_type(
        self,
        type_: Union[type, abc.Property],
    ) -> abc.MarshallableTypes:
        unmarshalled_data: abc.MarshallableTypes = None
        if isinstance(type_, abc.Property):
            unmarshalled_data = _unmarshal_property_value(type_, self.data)
        elif isinstance(type_, type):
            if isinstance(
                self.data, (dict, collections.OrderedDict, abc.Model, Mapping)
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
            "unmarshal(\n"
            f"   data={indent_(repr(self.data))},"
            f"   types={indent_(repr(self.types))},"
            f"   value_types={indent_(repr(self.value_types))},"
            f"   item_types={indent_(repr(self.item_types))},"
            ")"
        )


def unmarshal(
    data: abc.MarshallableTypes,
    types: Union[
        Iterable[Union[type, abc.Property]],
        type,
        abc.Property,
        abc.Types,
    ] = (),
    value_types: Union[
        Iterable[Union[type, abc.Property]],
        type,
        abc.Property,
        abc.Types,
    ] = (),
    item_types: Union[
        Iterable[Union[type, abc.Property]],
        type,
        abc.Property,
        abc.Types,
    ] = (),
) -> abc.MarshallableTypes:
    """
    Converts `data` into an instance of a [sob.model.Model](#Model) sub-class,
    and recursively does the same for all member data.

    Parameters:

     - data ([type|sob.properties.Property]): One or more data types. Each type

    This is done by attempting to cast that data into a series of `types`, to
    "un-marshal" data which has been deserialized from bytes or text, but is
    still represented by generic `Model` sub-class instances.
    """
    return _Unmarshal(
        data, types=types, value_types=value_types, item_types=item_types
    )()


# endregion
# region serialize


def _get_serialize_instance_hooks(
    data: abc.Model,
) -> Tuple[
    Optional[Callable[[abc.JSONTypes], abc.JSONTypes]],
    Optional[Callable[[str], str]],
]:
    before_serialize: Optional[Callable[[abc.JSONTypes], abc.JSONTypes]] = None
    after_serialize: Optional[Callable[[str], str]] = None
    instance_hooks: Optional[abc.Hooks] = hooks.read(data)
    if instance_hooks is not None:
        before_serialize = instance_hooks.before_serialize
        after_serialize = instance_hooks.after_serialize
    return before_serialize, after_serialize


def serialize(
    data: abc.MarshallableTypes,
    format_: str = "json",
    indent: Optional[int] = None,
) -> str:
    """
    This function serializes data as JSON or YAML.

    Parameters:

    - data ([Model](#Model)|str|dict|list|int|float|bool|None)
    - format_ (str): "json" or "yaml".
    """
    assert_in("format_", format_, ("json", "yaml"))
    string_data: str
    dumps: Callable[..., str]
    if format_ == "json":
        dumps = json.dumps
    else:
        dumps = yaml.dump
    if isinstance(data, abc.Model):
        instance_hooks: Optional[abc.Hooks]
        before_serialize: Optional[Callable[[abc.JSONTypes], abc.JSONTypes]]
        after_serialize: Optional[Callable[[str], str]]
        before_serialize, after_serialize = _get_serialize_instance_hooks(data)
        marshalled_data: abc.JSONTypes = marshal(data)
        if before_serialize is not None:
            marshalled_data = before_serialize(marshalled_data)
        string_data = dumps(marshalled_data, indent=indent)
        if after_serialize is not None:
            string_data = after_serialize(string_data)
    else:
        assert isinstance(data, abc.JSON_TYPES)
        string_data = dumps(data, indent=indent)
    return string_data


# endregion
# region deserialize


def _object_pairs_hook(
    pairs: Iterable[Tuple[str, Any]]
) -> "abc.OrderedDict[str, Any]":
    return collections.OrderedDict(pairs)


def deserialize(
    data: Optional[Union[str, bytes, abc.Readable]], format_: str = "json"
) -> Any:
    """
    This function deserializes JSON or YAML encoded data.

    Parameters:

    - data (str|abc.Readable): This can be a string or file-like object
      containing JSON or YAML serialized data.
    - format_ (str) = "json": "json" or "yaml".

    This function returns `None` (for JSON null values), or an instance of
    `str`, `dict`, `list`, `int`, `float` or `bool`.
    """
    deserialized_data: abc.JSONTypes
    assert_in("format_", format_, ("json", "yaml"))
    if isinstance(data, str):
        try:
            if format_ == "json":
                deserialized_data = json.loads(
                    data,
                    object_hook=collections.OrderedDict,
                    object_pairs_hook=_object_pairs_hook,
                    strict=False,
                )
            else:
                deserialized_data = yaml.safe_load(data)
        except Exception as error:
            # Append the data which couldn't be deserialized to the exception
            append_exception_text(
                error,
                "Errors occurred while attempting to deserialize:\n" f"{data}",
            )
            raise error
    elif isinstance(data, bytes):
        deserialized_data = deserialize(str(data, encoding="utf-8"), format_)
    else:
        assert isinstance(data, abc.Readable)
        deserialized_data = deserialize(read(data), format_)
    return deserialized_data


# endregion


def detect_format(
    data: Optional[Union[str, bytes, abc.Readable]]
) -> Tuple[Any, str]:
    """
    This function accepts a string or file-like object and returns a tuple
    containing the deserialized information and a string indicating the format
    of that information.

    Parameters:

    - data (str|abc.Readable): A string or file-like object containing
      JSON or YAML serialized data.

    This function returns a `tuple` of two items:

    - (str|dict|list|int|float|bool): The deserialized (but not un-marshalled)
      data.
    - (str): Either "json" or "yaml".
    """
    data_read: Union[str, bytes]
    if isinstance(data, str):
        data_read = data
    elif isinstance(data, bytes):
        data_read = str(data, encoding="utf-8")
    else:
        assert_is_instance("data", data, abc.Readable)
        assert isinstance(data, abc.Readable)
        data_read = read(data)
    formats: Tuple[str, str] = ("json", "yaml")
    format_: Optional[str] = None
    deserialized_data: Any = data_read
    formats_error_messages: List[Tuple[str, str]] = []
    for potential_format in formats:
        try:
            deserialized_data = deserialize(data_read, potential_format)
            format_ = potential_format
            break
        except (ValueError, yaml.YAMLError):
            formats_error_messages.append(
                (potential_format, get_exception_text())
            )
    if format_ is None:
        assert isinstance(data, str)
        raise DeserializeError(
            data=data,
            message="\n\n".join(
                f"{format_}:\n{error_message}"
                for format_, error_message in formats_error_messages
            ),
        )
    return deserialized_data, format_


# region validate


def _call_validate_method(data: abc.Model) -> Iterable[str]:
    error_message: str
    error_messages: Set[str] = set()
    validate_method: Optional[Callable[[bool], Iterable[str]]] = get_method(
        data, "_validate", lambda *args, **kwargs: []
    )
    assert validate_method is not None
    for error_message in validate_method(False):
        if error_message not in error_messages:
            yield error_message
            error_messages.add(error_message)


def _validate_typed(
    data: Optional[abc.Model],
    types: Union[Iterable[Union[type, abc.Property]], abc.Types],
) -> List[str]:
    error_messages: List[str] = []
    valid: bool = False
    for type_ in types:
        if isinstance(type_, type) and isinstance(data, type_):
            valid = True
            break
        elif isinstance(type_, abc.Property):
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
    types: Union[abc.Types, Iterable[Union[type, abc.Property]], None] = None,
    raise_errors: bool = True,
) -> Sequence[str]:
    """
    This function verifies that all properties/items/values in model instance
    are of the correct data type(s), and that all required attributes are
    present (if applicable).

    Parameters:

    - data ([Model](#Model))
    - types
      (type|[Property](#Property)|[Object](#Object)|collections.Callable|None)
      = None

    If `raise_errors` is `True` (this is the default), violations will result
    in a validation error. If `raise_errors` is `False`, a list of error
    messages will be returned.
    """
    if isinstance(data, GeneratorType):
        data = tuple(data)
    error_messages: List[str] = []
    if types is not None:
        error_messages.extend(_validate_typed(data, types))
    error_messages.extend(_call_validate_method(data))
    if raise_errors and error_messages:
        data_representation: str = f"\n\n    {indent_(represent(data))}"
        error_messages_representation: str = "\n\n".join(error_messages)
        if data_representation not in error_messages_representation:
            error_messages_representation = "\n\n".join(
                [data_representation, error_messages_representation]
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

    def __init__(self, property: abc.Property) -> None:
        self.property = property

    def validate_enumerated(self, value: abc.MarshallableTypes) -> None:
        """
        Verify that a value is one of the enumerated options
        """
        if (
            (value is not None)
            and isinstance(self.property, abc.Enumerated)
            and (self.property.values is not None)
            and (value not in self.property.values)
        ):
            raise ValueError(
                "The value provided is not a valid option:\n{}\n\n"
                "Valid options include:\n{}".format(
                    repr(value),
                    ", ".join(
                        repr(enumerated_value)
                        for enumerated_value in self.property.values
                    ),
                )
            )

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

    def parse_date(self, value: Optional[str]) -> Optional[date]:
        if value is None:
            return value
        else:
            assert_is_instance("value", value, (date, str))
            if isinstance(value, date):
                date_instance = value
            else:
                assert isinstance(self.property, abc.Date)
                date_instance = self.property.str2date(value)
            assert isinstance(date_instance, date)
            return date_instance

    def parse_datetime(
        self, value: Union[str, datetime, None]
    ) -> Optional[datetime]:
        datetime_instance: Optional[datetime] = None
        if value is not None:
            assert_is_instance("value", value, (datetime, str))
            if isinstance(value, datetime):
                datetime_instance = value
            else:
                assert isinstance(self.property, abc.DateTime)
                datetime_instance = self.property.str2datetime(value)
            assert isinstance(datetime_instance, datetime)
        return datetime_instance

    @staticmethod
    def parse_bytes(data: Union[str, bytes]) -> Optional[bytes]:
        """
        Un-marshal a base-64 encoded string into bytes
        """
        unmarshalled_data: Optional[bytes]
        if data is None:
            unmarshalled_data = data
        elif isinstance(data, str):
            unmarshalled_data = b64decode(data)
        elif isinstance(data, bytes):
            unmarshalled_data = data
        else:
            raise TypeError(
                "`data` must be a base64 encoded `str` or `bytes`--not "
                f"`{qualified_name(type(data))}`"
            )
        return unmarshalled_data

    def unmarshall_array(
        self, value: abc.MarshallableTypes
    ) -> abc.MarshallableTypes:
        assert isinstance(self.property, abc.ArrayProperty)
        return unmarshal(
            value,
            types=self.property.types or (),
            item_types=self.property.item_types or (),
        )

    def unmarshall_dictionary(
        self, value: abc.MarshallableTypes
    ) -> abc.MarshallableTypes:
        assert isinstance(self.property, abc.DictionaryProperty)
        return unmarshal(
            value,
            types=self.property.types or (),
            value_types=self.property.value_types or (),
        )

    def represent_function_call(self, value: abc.MarshallableTypes) -> str:
        return (
            "_unmarshal_property_value(\n"
            f"   {indent_(repr(self.property))},"
            f"   {indent_(repr(value))},"
            ")"
        )

    def _call(self, value: abc.MarshallableTypes) -> abc.MarshallableTypes:
        type_: type
        matched: bool = False
        unmarshalled_value: abc.MarshallableTypes = value
        method: Callable[..., abc.MarshallableTypes]
        for type_, method in (
            (abc.Date, self.parse_date),
            (abc.DateTime, self.parse_datetime),
            (abc.Bytes, self.parse_bytes),
            (abc.ArrayProperty, self.unmarshall_array),
            (abc.DictionaryProperty, self.unmarshall_dictionary),
            (abc.Enumerated, self.unmarshal_enumerated),
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
                    assert isinstance(value, (MutableMapping, abc.Dictionary))
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
                    "An error was encountered during execution of:\n"
                    f"{self.represent_function_call(value)}"
                ),
            )
            raise error


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

    def parse_date(self, value: Optional[date]) -> Optional[str]:
        date_string: Optional[str] = None
        if value is not None:
            assert isinstance(self.property, abc.Date)
            date_string = self.property.date2str(value)
            if not isinstance(date_string, str):
                raise TypeError(
                    "The date2str function should return a `str`, not a "
                    f"`{type(date_string).__name__}`: "
                    f"{repr(date_string)}"
                )
        return date_string

    def parse_datetime(self, value: Optional[datetime]) -> Optional[str]:
        datetime_string: Optional[str] = None
        if value is not None:
            assert isinstance(self.property, abc.DateTime)
            datetime_string = self.property.datetime2str(value)
            if not isinstance(datetime_string, str):
                raise TypeError(
                    "The datetime2str function should return a `str`, not a "
                    f"`{type(datetime_string).__name__}`: "
                    f"{repr(datetime_string)}"
                )
        return datetime_string

    def parse_bytes(self, value: bytes) -> str:
        """
        Marshal bytes into a base-64 encoded string
        """
        if (value is None) or isinstance(value, str):
            return value
        elif isinstance(value, bytes):
            return str(b64encode(value), "ascii")
        else:
            raise TypeError(
                "`data` must be a base64 encoded `str` or `bytes`--not `%s`"
                % qualified_name(type(value))
            )

    def __call__(self, value: abc.MarshallableTypes) -> abc.JSONTypes:
        if value is not None:
            if isinstance(self.property, abc.Date):
                assert isinstance(value, date)
                value = self.parse_date(value)
            elif isinstance(self.property, abc.DateTime):
                assert isinstance(value, datetime)
                value = self.parse_datetime(value)
            elif isinstance(self.property, abc.Bytes):
                assert isinstance(value, bytes)
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
    for property_name_, value in utilities.inspect.properties_values(
        object_instance
    ):
        if value is NULL:
            setattr(object_instance, property_name_, replacement_value)
        elif isinstance(value, abc.Model):
            replace_nulls(value, replacement_value)


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
            replace_nulls(value, replacement_value)


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
            replace_nulls(value, replacement_value)


def replace_nulls(
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


# endregion
# region from_meta


def _type_hint_from_property_types(
    property_types: Optional[abc.Types], module: str
) -> str:
    type_hint: str = (
        f"typing.Optional[{_parent_module_name}.abc.MarshallableTypes]"
    )
    if property_types is not None:
        if len(property_types) > 1:
            type_hint = "typing.Union[\n{}\n]".format(
                ",\n".join(
                    indent_(
                        _type_hint_from_property(item_type, module), start=0
                    )
                    for item_type in property_types
                )
            )
        else:
            type_hint = _type_hint_from_property(property_types[0], module)
    return type_hint


def _type_hint_from_type(type_: type, module: str) -> str:
    type_hint: str
    type_hint = qualified_name(type_)
    # If this class was declared in the same module, we put it in
    # quotes since it won't necessarily have been declared already
    if (("." not in type_hint) and not hasattr(builtins, type_hint)) or (
        type_.__module__ == module
    ):
        type_hint = f'"{type_hint}"'
    return type_hint


def _type_hint_from_property(
    property_or_type: Union[abc.Property, type], module: str
) -> str:
    type_hint: str
    if isinstance(property_or_type, type):
        type_hint = _type_hint_from_type(property_or_type, module)
    elif isinstance(property_or_type, abc.ArrayProperty):
        item_type_hint: str = _type_hint_from_property_types(
            property_or_type.item_types, module
        )
        if item_type_hint:
            type_hint = (
                f"typing.Sequence[\n    {indent_(item_type_hint)}\n" "]"
            )
        else:
            type_hint = "typing.Sequence"
    elif isinstance(property_or_type, abc.DictionaryProperty):
        value_type_hint: str = _type_hint_from_property_types(
            property_or_type.value_types, module
        )
        if value_type_hint:
            type_hint = (
                "typing.Mapping[\n"
                "    str,\n"
                f"    {indent_(value_type_hint)}\n"
                "]"
            )
        else:
            type_hint = "dict"
    elif isinstance(property_or_type, abc.Number):
        type_hint = (
            "typing.Union[\n"
            "    float,\n"
            "    int,\n"
            "    decimal.Decimal\n"
            "]"
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
    qualified_abc_name_list: List[str] = qualified_superclass_name.split(".")
    qualified_abc_name_list.insert(1, "abc")
    return ".".join(qualified_abc_name_list)


def _get_class_declaration(name: str, superclass_: type) -> str:
    """
    Construct a class declaration
    """
    class_declaration: str
    qualified_superclass_name: str = qualified_name(superclass_)
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
        repr_docstring = '    """\n{}\n    """'.format(
            split_long_docstring_lines(docstring)
        )
    return repr_docstring


def _model_class_from_meta(
    metadata: abc.Meta,
) -> Type[Union[Array, Dictionary, Object]]:
    return (
        Object
        if isinstance(metadata, abc.ObjectMeta)
        else Array
        if isinstance(metadata, abc.ArrayMeta)
        else Dictionary
    )


_REPR_MARSHALLABLE_TYPING: str = f"{_parent_module_name}.abc.MarshallableTypes"


def _repr_class_init_from_meta(metadata: abc.Meta, module: str) -> str:
    out: List[str] = []
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
            "        items: typing.Union[\n"
            f"            {_parent_module_name}.abc.Dictionary,\n"
            "            typing.Mapping[\n"
            "                str,\n"
            f"                {mapping_repr_value_typing}\n"
            "            ],\n"
            "            typing.Iterable[\n"
            "                typing.Tuple[\n"
            "                    str,\n"
            f"                    {iterable_repr_value_typing}\n"
            "                ]\n"
            "            ],\n"
            f"            {_parent_module_name}.abc.Readable,\n"
            "            str,\n"
            "            bytes,\n"
            "            None,\n"
            "        ] = None,\n"
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
            "        items: typing.Union[\n"
            "            typing.Iterable[\n"
            f"                {repr_item_typing}\n"
            "            ],\n"
            f"            {_parent_module_name}.abc.Readable,\n"
            "            str,\n"
            "            bytes,\n"
            "            None,\n"
            "        ] = None\n"
            "    ) -> None:\n"
            "        super().__init__(items)\n\n"
        )
    elif isinstance(metadata, abc.ObjectMeta):
        out.append(
            "\n"
            "    def __init__(\n"
            "        self,\n"
            "        _data: typing.Union[\n"
            f"            {_parent_module_name}.abc.Dictionary,\n"
            "            typing.Mapping[\n"
            "                str,\n"
            f"                {_REPR_MARSHALLABLE_TYPING}\n"
            "            ],\n"
            "            typing.Iterable[\n"
            "                typing.Tuple[\n"
            "                    str,\n"
            f"                    {_REPR_MARSHALLABLE_TYPING}\n"
            "                ]\n"
            "            ],\n"
            f"            {_parent_module_name}.abc.Readable,\n"
            "            str,\n"
            "            bytes,\n"
            "            None,\n"
            "        ] = None,"
        )
        metadata_properties_items: Tuple[Tuple[str, abc.Property], ...] = (
            ()
            if metadata.properties is None
            else tuple(metadata.properties.items())
        )
        metadata_properties_items_length: int = len(metadata_properties_items)
        property_index: int
        name_and_property: Tuple[str, abc.Property]
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
            parameter_declaration: str = (
                f"        {property_name_}: typing.Optional[\n"
                f"            {repr_property_typing}\n"
                f"        ] = None{repr_comma}"
            )
            out.append(parameter_declaration)
        out.append("    ) -> None:")
        if metadata.properties is not None:
            for property_name_ in metadata.properties.keys():
                property_assignment: str = "        self.%s = %s" % (
                    property_name_,
                    property_name_,
                )
                # Ensure line-length aligns with PEP-8
                if len(property_assignment) > MAX_LINE_LENGTH:
                    property_assignment = (
                        f"        self.{property_name_} = (\n"
                        f"            {property_name_}\n"
                        f"        )"
                    )
                out.append(property_assignment)
        out.append("        super().__init__(_data)\n\n")
    else:
        raise ValueError(metadata)
    return "\n".join(out)


def _class_definition_from_meta(
    name: str,
    metadata: abc.Meta,
    docstring: Optional[str] = None,
    module: str = None,
    pre_init_source: str = "",
    post_init_source: str = "",
) -> str:
    """
    This returns a `str` defining a model class, as determined by an
    instance of `sob.meta.Meta`.
    """
    assert module is not None
    repr_docstring: Optional[str] = (
        None if docstring is None else _repr_class_docstring(docstring)
    )
    out: List[str] = [
        _get_class_declaration(name, _model_class_from_meta(metadata))
    ]
    if repr_docstring:
        out.append(repr_docstring)
    if pre_init_source:
        out.append("\n" + utilities.string.indent(pre_init_source, start=0))
    out.append(_repr_class_init_from_meta(metadata, module))
    if post_init_source:
        out.append(f"\n{utilities.string.indent(post_init_source, start=0)}")
    return "\n".join(out)


def from_meta(
    name: str,
    metadata: abc.Meta,
    module: Optional[str] = None,
    docstring: Optional[str] = None,
    pre_init_source: str = "",
    post_init_source: str = "",
) -> Type[abc.Model]:
    """
    Constructs an `Object`, `Array`, or `Dictionary` sub-class from an
    instance of `sob.meta.Meta`.

    Parameters:

    - name (str): The name of the class.
    - class_meta ([sob.meta.Meta](#Meta))
    - module (str): Specify the value for the class definition's
      `__module__` property. The invoking module will be
      used if this is not specified. Note: If using the result of this
      function with `sob.utilities.inspect.get_source` to generate static
      code--this should be set to "__main__". The default behavior is only
      appropriate when using this function as a factory.
    - docstring (str): A docstring to associate with the class definition.
    - pre_init_source (str): Source code to insert *before* the `__init__`
      function in the class definition.
    - post_init_source (str): Source code to insert *after* the `__init__`
      function in the class definition.
    """
    # For pickling to work, the __module__ variable needs to be set...
    module = module or calling_module_name(2)
    class_definition: str = _class_definition_from_meta(
        name,
        metadata,
        docstring=docstring,
        module=module,
        pre_init_source=pre_init_source,
        post_init_source=post_init_source,
    )
    namespace: Dict[str, Any] = dict(__name__="from_meta_%s" % name)
    imports = [
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
    imports.append(f"import {_parent_module_name}")
    source: str = suffix_long_lines(
        "%s\n\n\n%s" % ("\n".join(imports), class_definition)
    )
    error: Exception
    try:
        exec(source, namespace)
    except Exception as error:  # noqa
        append_exception_text(error, f"\n\n{source}")
        raise
    model_class: type = namespace[name]
    setattr(model_class, "_source", source)
    setattr(model_class, "__module__", module)
    setattr(model_class, "_meta", metadata)
    return model_class


# endregion
