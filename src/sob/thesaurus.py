"""
This module provides functionality for creating a data model from a
set of example structures.
"""

from __future__ import annotations

import binascii
import collections
import collections.abc
import decimal
import functools
import os
import re
from base64 import b64decode
from collections.abc import (
    Hashable,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    Mapping,
    Sequence,
    ValuesView,
)
from copy import copy, deepcopy
from datetime import date, datetime
from itertools import chain
from pathlib import Path
from types import ModuleType
from typing import (
    Any,
    Callable,
    cast,
)
from urllib.parse import quote_plus

from iso8601.iso8601 import ParseError, parse_date
from typing_extensions import Self

from sob import abc, meta
from sob._io import read
from sob._types import NULL, UNDEFINED, NoneType, Null, Undefined
from sob._utilities import deprecated
from sob.abc import MARSHALLABLE_TYPES
from sob.meta import escape_reference_token
from sob.model import (
    Array,
    Dictionary,
    deserialize,
    get_model_from_meta,
    get_models_source,
    unmarshal,
)
from sob.properties import TYPES_PROPERTIES, Property, has_mutable_types
from sob.types import MutableTypes, Types
from sob.utilities import (
    get_calling_module_name,
    get_class_name,
    get_property_name,
    get_source,
    suffix_long_lines,
)

lru_cache: Callable[..., Any] = functools.lru_cache


def _read(data: abc.Readable) -> str:
    string_data: str
    read_data: str | bytes = read(data)
    if isinstance(read_data, (bytes, bytearray)):
        string_data = str(read_data, encoding="utf-8")
    else:
        string_data = read_data
    return string_data


def _update_types(
    types: abc.MutableTypes, new_types: abc.Types, memo: dict[str, type]
) -> None:
    """
    This function updates `types` to incorporate any additional types from
    `new_types`, as well as to merge definitions for shared types.

    Parameters:

    - types (sob.properties.types.Types)
    - new_types (sob.properties.types.Types)
    - memo (dict)
    """
    new_type: type | abc.Property
    for new_type in new_types:
        if (
            isinstance(new_type, type)
            and issubclass(new_type, abc.Model)
            and (type.__name__ in memo)
        ):
            existing_type: type = memo[type.__name__]
            new_type_meta: abc.Meta | None = meta.read_model_meta(new_type)
            if not isinstance(
                new_type_meta,
                (abc.ObjectMeta, abc.ArrayMeta, abc.DictionaryMeta),
            ):
                raise TypeError(new_type_meta)
            _update_model_class_from_meta(
                existing_type, new_type_meta, memo=memo
            )
            new_type = existing_type  # noqa: PLW2901
        if new_type not in types:
            types.append(new_type)


def _update_array_meta(
    metadata: abc.ArrayMeta,
    new_metadata: abc.ArrayMeta,
    memo: dict[str, type] | None = None,
) -> None:
    """
    This function updates `metadata` by adding/updating `metadata.item_types`
    to include types from `new_metadata.item_types`.

    Parameters:

    - metadata (sob.meta.Array)
    - new_metadata (sob.meta.Array)
    - memo (dict)
    """
    if memo is None:
        raise ValueError(memo)
    new_item_types: abc.Types | None = new_metadata.item_types
    if new_item_types is not None:
        item_types: abc.MutableTypes = (
            MutableTypes()
            if metadata.item_types is None
            else (
                metadata.item_types
                if isinstance(metadata.item_types, abc.MutableTypes)
                else MutableTypes(metadata.item_types)
            )
        )
        _update_types(item_types, new_item_types, memo)
        metadata.item_types = item_types  # type: ignore


def _update_dictionary_meta(
    metadata: abc.DictionaryMeta,
    new_metadata: abc.DictionaryMeta,
    memo: dict[str, type] | None = None,
) -> None:
    """
    This function updates `metadata` by adding/updating `metadata.value_types`
    to include types from `new_metadata.value_types`.

    Parameters:

        metadata:
        new_metadata:
        memo:
    """
    if memo is None:
        raise ValueError(memo)
    new_value_types: abc.Types | None = new_metadata.value_types
    if new_value_types is not None:
        value_types: abc.MutableTypes = (
            MutableTypes()
            if metadata.value_types is None
            else (
                metadata.value_types
                if isinstance(metadata.value_types, abc.MutableTypes)
                else MutableTypes(metadata.value_types)
            )
        )
        _update_types(value_types, new_value_types, memo)
        metadata.value_types = value_types  # type: ignore


def _update_object_meta(
    metadata: abc.ObjectMeta,
    new_metadata: abc.ObjectMeta,
    memo: dict[str, type] | None = None,
) -> None:
    """
    This function updates `metadata` by adding any properties from
    `new_metadata` not yet part of `metadata`, and updating the property
    types for all shared properties.

    Parameters:

    - metadata (sob.meta.Array)
    - new_metadata (sob.meta.Array)
    - memo (dict)
    """
    if memo is None:
        raise ValueError(memo)
    if metadata.properties is None:
        raise ValueError(metadata.properties)
    if new_metadata.properties is None:
        raise ValueError(new_metadata.properties)
    metadata_keys: set[str] = set(metadata.properties.keys())
    new_metadata_keys: set[str] = set(new_metadata.properties.keys())
    # Add properties that don't exist
    key: str
    for key in sorted(metadata_keys - new_metadata_keys):
        metadata.properties[key] = new_metadata.properties[key]
    # Update shared properties
    for key in sorted(metadata_keys & new_metadata_keys):
        types_: abc.Types | None = metadata.properties[key].types
        new_types: abc.Types | None = new_metadata.properties[key].types
        if new_types is not None:
            mutable_types: abc.MutableTypes = (
                MutableTypes()
                if types_ is None
                else (
                    types_
                    if isinstance(types_, abc.MutableTypes)
                    else MutableTypes(types_)
                )
            )
            _update_types(
                mutable_types,
                new_types,
                memo=memo,
            )
            types_ = mutable_types
        property_: abc.Property = metadata.properties[key]
        if has_mutable_types(property_):
            metadata.properties[key].types = types_  # type: ignore
        else:
            # If a property's types are immutable, we need to replace
            # it with a generic property
            metadata.properties[key] = Property(
                types=types_,
                name=property_.name,
                required=property_.required,
                versions=property_.versions,
            )


def _update_object_class_from_meta(
    object_class: type[abc.Model],
    new_object_metadata: abc.ObjectMeta,
    memo: dict[str, type],
) -> None:
    """
    This function merges new metadata into an existing object model's metadata.

    Parameters:

    - object_class (type)
    - new_object_metadata (sob.meta.Object)
    - memo (dict)
    """
    if not isinstance(new_object_metadata, abc.ObjectMeta):
        raise TypeError(new_object_metadata)
    object_metadata: abc.Meta | None = meta.read_model_meta(object_class)
    if not isinstance(object_metadata, (abc.ObjectMeta, NoneType)):
        raise TypeError(object_metadata)
    _update_object_meta(object_metadata, new_object_metadata, memo)
    # Recreate the object class
    updated_object_class: type = get_model_from_meta(
        object_class.__name__,
        object_metadata,
        module=object_class.__module__,
        docstring=object_class.__doc__,
    )
    # Apply the rest of the changes to the existing model class
    object_class.__init__ = updated_object_class.__init__  # type: ignore
    object_class._source = get_source(updated_object_class)  # noqa: SLF001


def _update_array_class_from_meta(
    array_class: type,
    new_array_metadata: abc.ArrayMeta,
    memo: dict[str, type],
) -> None:
    """
    This function merges new metadata into an existing array model's metadata.

    Parameters:

    - array_class (type)
    - new_array_metadata (sob.meta.Array)
    - memo (dict)
    """
    if not isinstance(new_array_metadata, abc.ArrayMeta):
        raise TypeError(new_array_metadata)
    array_metadata: abc.Meta = meta.get_writable_model_meta(array_class)
    if not isinstance(array_metadata, abc.ArrayMeta):
        raise TypeError(array_metadata)
    _update_array_meta(array_metadata, new_array_metadata, memo=memo)
    # Since the two array classes have the same name--the class
    # definition/declaration won't change, so updating the metadata is all that
    # is necessary


def _update_dictionary_class_from_meta(
    dictionary_class: type,
    new_dictionary_metadata: abc.DictionaryMeta,
    memo: dict[str, type],
) -> None:
    """
    This function merges new metadata into an existing array model's metadata.

    Parameters:

    - dictionary_class (type)
    - new_array_metadata (sob.meta.Array)
    - memo (dict)
    """
    if not isinstance(new_dictionary_metadata, abc.ArrayMeta):
        raise TypeError(new_dictionary_metadata)
    dictionary_metadata: abc.Meta = meta.get_writable_model_meta(
        dictionary_class
    )
    if not isinstance(dictionary_metadata, abc.DictionaryMeta):
        raise TypeError(dictionary_metadata)
    _update_dictionary_meta(
        dictionary_metadata, new_dictionary_metadata, memo=memo
    )
    # Since the two dictionary classes have the same name--the class
    # definition/declaration won't change, so updating the metadata is all that
    # is necessary


def _update_model_class_from_meta(
    model_class: type,
    new_metadata: abc.ArrayMeta | abc.ObjectMeta | abc.DictionaryMeta,
    memo: dict[str, type],
) -> None:
    """
    This function merges new metadata into an existing model's metadata.

    Parameters:

    - model_class (type)
    - new_metadata (sob.meta.Array|sob.meta.Object)
    - memo (dict)
    """
    if not issubclass(model_class, (abc.Array, abc.Object, abc.Dictionary)):
        raise TypeError(model_class)
    # Update the model metadata in-place
    if issubclass(model_class, abc.Array):
        if not isinstance(new_metadata, abc.ArrayMeta):
            raise TypeError(new_metadata)
        _update_array_class_from_meta(model_class, new_metadata, memo=memo)
    elif issubclass(model_class, abc.Object):
        if not issubclass(model_class, abc.Object):
            raise TypeError(model_class)
        if not isinstance(new_metadata, abc.ObjectMeta):
            raise TypeError(new_metadata)
        _update_object_class_from_meta(model_class, new_metadata, memo=memo)
    else:
        if not issubclass(model_class, abc.Dictionary):
            raise TypeError(model_class)
        if not isinstance(new_metadata, abc.DictionaryMeta):
            raise TypeError(new_metadata)
        _update_dictionary_class_from_meta(
            model_class, new_metadata, memo=memo
        )


def get_class_name_from_pointer(pointer: str) -> str:
    """
    This function creates a class name based on the `sob.Thesaurus` key of the
    `sob.Synonyms` instance to which an element belongs,
    combined with the *JSON pointer* of the applicable element. This function
    can be substituted for another, when generating a module from a thesaurus,
    by passing a function to the `name` parameter of
    `sob.Thesaurus.get_module_source`, `sob.Thesaurus.get_module`, or
    `sob.Thesaurus.save_module`.

    Parameters:

    - pointer (str): The synonyms key + JSON pointer of the element for which
      the class is being generated.
    """
    return get_class_name(
        f"{pointer[:-2]}/item"
        if pointer.endswith("/0")
        else pointer.replace("/0/", "/item/")
    )


class_name_from_pointer = deprecated(
    "`sob.thesaurus.class_name_from_pointer` is deprecated and will be "
    "removed in sob 3. Please use "
    "`sob.thesaurus.get_class_name_from_pointer` instead."
)(get_class_name_from_pointer)


def _get_models_from_meta(
    pointer: str,
    metadata: abc.ArrayMeta | abc.ObjectMeta | abc.DictionaryMeta,
    module: str,
    memo: dict[str, type] | None,
    name: Callable[[str], str] = get_class_name_from_pointer,
) -> list[type]:
    """
    This function generates and updates classes from metadata.

    Parameters:
        pointer:
        metadata:
        module:
        memo:
    """
    if memo is None:
        memo = {}
    new_models: list[type] = []
    # If the object has no attributes, interpret it an an empty dictionary
    if isinstance(metadata, abc.ObjectMeta) and not metadata.properties:
        metadata = meta.DictionaryMeta()
    # If a model of the same pointer already exists, we update it to
    # reflect our metadata, otherwise--we create a new model
    if pointer in memo:
        _update_model_class_from_meta(memo[pointer], metadata, memo=memo)
    else:
        new_model: type = get_model_from_meta(
            name(pointer), metadata, module=module
        )
        memo[pointer] = new_model
        new_models.append(new_model)
    return new_models


def _is_base64(value: Any) -> bool:
    """
    Test to see if `value` can be interpreted as base-64 encoded binary data.
    """
    if isinstance(value, str):
        try:
            b64decode(bytes(value, encoding="utf-8"), validate=True)
        except binascii.Error:
            pass
        else:
            return True
    return False


@lru_cache(maxsize=128)
def _str_date_or_datetime(value: str) -> type:
    """
    Test to see if `value` can be interpreted as an ISO-8601 encoded `date` or
    `datetime`.
    """
    try:
        timestamp: datetime = parse_date(value)
        if (
            timestamp.hour
            or timestamp.minute
            or timestamp.second
            or timestamp.microsecond
            or "T" in value
            or " " in value
            or "Z" in value
        ):
            return datetime
    except ParseError:
        return str
    else:
        return date


def _is_datetime_str(value: Any) -> bool:
    """
    Test to see if `value` can be interpreted as an ISO-8601 encoded
    `datetime`.

    >>> _is_datetime_str("1999-12-31T00:00:00.000")
    True
    """
    return isinstance(value, str) and _str_date_or_datetime(value) is datetime


def _is_date_str(value: Any) -> bool:
    """
    Test to see if `value` can be interpreted as an ISO-8601 encoded
    `date`.
    """
    return isinstance(value, str) and _str_date_or_datetime(value) is date


def _is_not_null_or_none(item: Any) -> bool:
    return item not in (None, NULL)


@collections.abc.MutableSet.register
class Synonyms:
    """
    This class is a set-like object containing deserialized data,
    implied to represent variations of one type of entity, and is used to
    infer a model for that entity.
    """

    __module__: str = "sob"

    __slots__ = ("_type", "_nullable", "_set")

    def __init__(
        self, items: Iterable[abc.Readable | abc.MarshallableTypes] = ()
    ) -> None:
        self._type: set[type] = set()
        self._nullable: bool = False
        self._set: set[abc.MarshallableTypes] = set()
        if items:
            self.__ior__(items)

    def add(  # noqa: C901
        self, item: abc.Readable | abc.MarshallableTypes
    ) -> None:
        """
        This method adds a synonymous item to the set. If the item is a
        file-like (input/output) object, that object is first read,
        deserialized, and unmarshalled.

        Parameters:
            item: A file-like or a JSON-serializable python object.
        """
        if not isinstance(item, (abc.Readable, *abc.MARSHALLABLE_TYPES)):
            raise TypeError(item)
        if isinstance(item, abc.Readable):
            # Deserialize and unmarshal file-like objects
            item = unmarshal(deserialize(_read(item))[0])
        elif isinstance(item, Iterable) and not isinstance(
            item, (str, abc.Model, Mapping)
        ):
            if isinstance(item, Iterable) and not isinstance(item, Sequence):
                item = tuple(item)
            # Unmarshal items which appear to not have been part of an
            # unmarshalled container
            item = unmarshal(item)
        if isinstance(item, Null):
            self._nullable = True
        elif item is not None:
            if not isinstance(item, MARSHALLABLE_TYPES):
                raise TypeError(item)
            item_type: type = (
                list
                if isinstance(item, abc.Array)
                else dict
                if isinstance(item, abc.Dictionary)
                else type(item)
            )
            if (item_type is int) and float in self._type:
                pass
            elif (item_type is float) and int in self._type:
                self._type.remove(int)
                self._type.add(item_type)
            else:
                self._type.add(item_type)
            if not isinstance(item, Hashable):
                if isinstance(item, Mapping):
                    item = Dictionary(item)
                if isinstance(item, Sequence):
                    item = Array(item)
            self._set.add(item)  # type: ignore

    def discard(self, item: abc.MarshallableTypes) -> None:
        self_set: set[abc.MarshallableTypes] = copy(self._set)
        self_set.discard(item)
        self.clear()
        self.__ior__(self_set)

    def remove(self, item: abc.MarshallableTypes) -> None:
        self_set: set[abc.MarshallableTypes] = copy(self._set)
        self_set.remove(item)
        self.clear()
        self.__ior__(self_set)

    def pop(self) -> abc.MarshallableTypes:
        self_set: set[abc.MarshallableTypes] = copy(self._set)
        item: abc.MarshallableTypes = self_set.pop()
        self.clear()
        self.__ior__(self_set)
        return item

    def clear(self) -> None:
        self._type.clear()
        self._nullable = False
        self._set.clear()

    def union(
        self, other: Iterable[abc.Readable | abc.MarshallableTypes]
    ) -> Synonyms:
        """
        This method returns an instance of `Synonyms` which incorporates
        all (non-redundant) items from both `self` and `other`.
        """
        new_synonyms: Synonyms = copy(self)
        new_synonyms |= other
        return new_synonyms

    def __ior__(
        self, other: Iterable[abc.Readable | abc.MarshallableTypes]
    ) -> Self:
        if not isinstance(other, Iterable):
            raise TypeError(other)
        if isinstance(other, (Mapping, abc.Dictionary)):
            raise TypeError(other)
        item: abc.Readable | abc.MarshallableTypes
        for item in other:
            self.add(item)
        return self

    def __or__(
        self, other: Iterable[abc.Readable | abc.MarshallableTypes]
    ) -> Synonyms:
        return copy(self).__ior__(other)

    @staticmethod
    def _get_set(
        other: Iterable[abc.Readable | abc.MarshallableTypes],
    ) -> set[abc.MarshallableTypes]:
        return (
            other._set  # noqa: SLF001
            if isinstance(other, Synonyms)
            else other
            if isinstance(other, set)
            else Synonyms(other)._set  # noqa: SLF001
        )

    def __iand__(
        self,
        other: Synonyms | Iterable[abc.Readable | abc.MarshallableTypes],
    ) -> Self:
        other_set: set[abc.MarshallableTypes] = self._get_set(other)
        self_set: set[abc.MarshallableTypes] = copy(self._set)
        self.clear()
        return self.__ior__(self_set & other_set)

    def __ixor__(
        self,
        other: Synonyms | Iterable[abc.Readable | abc.MarshallableTypes],
    ) -> Self:
        self_set: set[abc.MarshallableTypes] = copy(self._set)
        other_set: set[abc.MarshallableTypes] = self._get_set(other)
        self.clear()
        if self_set is not other_set:
            self.__ior__(self_set ^ other_set)
        return self

    def __isub__(
        self,
        other: Synonyms | Iterable[abc.Readable | abc.MarshallableTypes],
    ) -> Self:
        self_set: set[abc.MarshallableTypes] = self._set
        other_set: set[abc.MarshallableTypes] = self._get_set(other)
        self.clear()
        if self_set is not other_set:
            self.__ior__(self_set.__isub__(other_set))
        return self

    def __sub__(
        self, other: Synonyms | Iterable[abc.MarshallableTypes]
    ) -> Self:
        other_set: set[abc.MarshallableTypes] = self._get_set(other)
        return self.__class__(self._set.__sub__(other_set))

    def __xor__(
        self,
        other: Synonyms | Iterable[abc.Readable | abc.MarshallableTypes],
    ) -> Self:
        other_set: set[abc.MarshallableTypes] = self._get_set(other)
        return self.__class__(self._set.__xor__(other_set))

    def __copy__(self) -> Self:
        new_synonyms: Self = self.__class__()
        new_synonyms._set = copy(self._set)  # noqa: SLF001
        new_synonyms._type = copy(self._type)  # noqa: SLF001
        new_synonyms._nullable = self._nullable  # noqa: SLF001
        return new_synonyms

    def __deepcopy__(self, memo: dict | None = None) -> Self:
        new_synonyms: Self = self.__class__()
        new_synonyms._set = deepcopy(self._set, memo=memo)  # noqa: SLF001
        new_synonyms._type = self._type  # noqa: SLF001
        new_synonyms._nullable = self._nullable  # noqa: SLF001
        return new_synonyms

    def _iter_simple_types(self) -> Iterable[type]:
        type_: type
        if self._type and len(self._type) == 1:
            type_ = next(iter(self._type))
            # Determine if this is a string encoded to represent a `date`,
            # `datetime`, or base-64 encoded `bytes`.
            if issubclass(type_, str):
                if all(map(_is_base64, filter(_is_not_null_or_none, self))):
                    yield bytes
                    return
                elif all(
                    map(_is_datetime_str, filter(_is_not_null_or_none, self))
                ):
                    yield datetime
                    return
                elif all(
                    map(_is_date_str, filter(_is_not_null_or_none, self))
                ):
                    yield date
                    return
        yield from sorted(
            filter(
                lambda type_: issubclass(
                    type_,
                    (
                        str,
                        bytes,
                        bytearray,
                        bool,
                        int,
                        float,
                        decimal.Decimal,
                        date,
                        datetime,
                    ),
                ),
                self._type,
            ),
            key=lambda type_: type_.__name__,
        )

    def _get_property_names_values(
        self,
    ) -> dict[str, list[abc.MarshallableTypes]]:
        keys_values: dict[str, list[abc.MarshallableTypes]] = {}
        item: abc.MarshallableTypes
        for item in self:
            if not isinstance(item, (Mapping, abc.Dictionary)):
                continue
            value: abc.MarshallableTypes
            item_: tuple[str, Any]
            for key, value in sorted(
                item.items(),
                key=lambda item_: (
                    (1 if re.match(r"^[^A-Za-z0-9]", item_[0]) else 0),
                    item_[0],
                ),
            ):
                if key not in keys_values:
                    keys_values[key] = []
                keys_values[key].append(value)
        return keys_values

    def _iter_object_models(  # noqa: C901
        self,
        pointer: str,
        module: str = "__main__",
        name: Callable[[str], str] = get_class_name_from_pointer,
        memo: dict[str, type] | None = None,
    ) -> Iterable[type]:
        metadata: abc.ObjectMeta = meta.ObjectMeta()
        metadata.properties = meta.Properties()  # type: ignore
        key: str
        property_name_: str
        property_: abc.Property
        values: list[abc.MarshallableTypes]
        visited_property_names: set[str] = set()
        for key, values in self._get_property_names_values().items():
            property_name_ = get_property_name(key)
            while property_name_ in visited_property_names:
                property_name_ = f"{property_name_}_"
            visited_property_names.add(property_name_)
            item_type: type | None = None
            property_synonyms: Synonyms = type(self)(values)
            for item_type in property_synonyms._iter_types(  # noqa: SLF001
                pointer=f"{pointer}/{escape_reference_token(property_name_)}",
                module=module,
                memo=memo,
                name=name,
            ):
                if issubclass(item_type, abc.Model):
                    yield item_type
                if property_name_ in metadata.properties:
                    if item_type not in cast(
                        abc.MutableTypes,
                        cast(
                            Property,
                            metadata.properties[property_name_],
                        ).types,
                    ):
                        cast(
                            abc.MutableTypes,
                            cast(
                                Property,
                                metadata.properties[property_name_],
                            ).types,
                        ).append(item_type)
                else:
                    metadata.properties[property_name_] = Property(
                        name=key,
                        types=MutableTypes(
                            (item_type,)
                            + (
                                (Null,)
                                if property_synonyms._nullable  # noqa: SLF001
                                else ()
                            )
                        ),
                    )
            if property_name_ not in metadata.properties:
                metadata.properties[property_name_] = Property(name=key)
        if metadata.properties:
            for property_name_, property_ in metadata.properties.items():
                if property_.types:
                    if len(property_.types) == 1:
                        property_type: type | abc.Property = next(
                            iter(property_.types)
                        )
                        if (
                            isinstance(property_type, type)
                            and property_type in TYPES_PROPERTIES
                        ):
                            metadata.properties[property_name_] = (
                                TYPES_PROPERTIES[property_type]
                            )(name=property_.name)
                    else:
                        # Make the property types immutable
                        property_.types = Types(property_.types)
            yield from _get_models_from_meta(
                pointer, metadata, module=module, memo=memo, name=name
            )

    def _iter_array_models(
        self,
        pointer: str,
        module: str = "__main__",
        name: Callable[[str], str] = get_class_name_from_pointer,
        memo: dict[str, type] | None = None,
    ) -> Iterable[type]:
        unified_items: Synonyms = type(self)()
        items: abc.MarshallableTypes
        for items in self:
            if isinstance(items, Iterable) and not isinstance(
                items, (str, Mapping, abc.Dictionary, abc.Object)
            ):
                unified_items |= items
        if not unified_items:
            return
        metadata: abc.ArrayMeta = meta.ArrayMeta(
            item_types=Types(
                filter(
                    None,
                    unified_items._iter_types(  # noqa: SLF001
                        pointer=f"{pointer}/0",
                        module=module,
                        memo=memo,
                        name=name,
                    ),
                )
            )
        )
        yield from _get_models_from_meta(
            pointer, metadata, module=module, memo=memo, name=name
        )

    def _iter_types(
        self,
        pointer: str,
        module: str = "__main__",
        name: Callable[[str], str] = get_class_name_from_pointer,
        memo: dict[str, type] | None = None,
    ) -> Iterable[type]:
        # `_memo` holds a dictionary of all classes which have been created,
        # and is passed recursively to facilitate de-duplication
        memo_is_new: bool = False
        if memo is None:
            memo = {}
            memo_is_new = True
        type_iterator: Iterable[type] = chain(
            self._iter_simple_types(),
            self._iter_object_models(
                pointer, module=module, memo=memo, name=name
            ),
            self._iter_array_models(
                pointer, module=module, memo=memo, name=name
            ),
        )
        # If this was the call which initialized our `_memo`, we want to
        # force the iterator to run, in order to fully update all models before
        # returning them to the user (as some will be updated over the course
        # of traversal when analogous elements are encountered).
        if memo_is_new and not isinstance(type_iterator, tuple):
            type_iterator = tuple(type_iterator)
        yield from type_iterator

    def get_models(
        self,
        pointer: str,
        module: str = "__main__",
        name: Callable[[str], str] = get_class_name_from_pointer,
    ) -> Iterable[type]:
        """
        Retrieve a sequence of class definitions representing a data model
        capable of describing these synonyms.

        Parameters:

        - pointer (str): A JSON pointer for the top-level model class, used to
          infer class names.
        - module (str): The name of the module in which model classes will be
          defined. This defaults to "__main__".
        - name (str) = sob.thesaurus.get_class_name_from_pointer:
          A function which accepts one `str` argument—a synonym key
          concatenated with "#" and JSON pointer (for example:
          "key#/body/items/0") and which returns a `str` which will be the
          resulting class name (for example: "KeyBodyItemsItem").
        """
        if not callable(name):
            raise TypeError(name)
        # This assertion ensures `self` contains data which can be described by
        # a model class.
        message: str
        if not self._type:
            message = "No type could be identified"
            raise RuntimeError(message)
        quoted_pointer: str = "{}#".format(quote_plus(pointer, safe="/+"))
        for model_class in self._iter_types(
            pointer=quoted_pointer,
            module=module,
            name=name,
        ):
            if not issubclass(model_class, abc.Model):
                raise TypeError((quoted_pointer, model_class))
            yield model_class

    def __len__(self) -> int:
        return self._set.__len__()

    def __iter__(self) -> Iterator[abc.MarshallableTypes]:
        return self._set.__iter__()

    def __contains__(self, item: abc.MarshallableTypes) -> bool:
        return self._set.__contains__(item)

    def __le__(
        self, other: Iterable[abc.Readable | abc.MarshallableTypes]
    ) -> bool:
        return self._set.__le__(self._get_set(other))

    def __lt__(
        self, other: Iterable[abc.Readable | abc.MarshallableTypes]
    ) -> bool:
        return self._set.__lt__(self._get_set(other))

    def __gt__(
        self, other: Iterable[abc.Readable | abc.MarshallableTypes]
    ) -> bool:
        return self._set.__gt__(self._get_set(other))

    def __ge__(
        self, other: Iterable[abc.Readable | abc.MarshallableTypes]
    ) -> bool:
        return self._set.__ge__(self._get_set(other))

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Synonyms)
            and (type(other) is type(self))
            and self._set.__eq__(self._get_set(other))
        )

    def __and__(
        self, other: Iterable[abc.Readable | abc.MarshallableTypes]
    ) -> Self:
        return copy(self).__iand__(other)

    def isdisjoint(
        self, other: Iterable[abc.Readable | abc.MarshallableTypes]
    ) -> bool:
        return self._set.isdisjoint(self._get_set(other))


def get_class_meta_attribute_assignment_source(
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
            f"{writable_function_name}(  # type: ignore\n"
            f"    {suffix_long_lines(class_name_, -4)}\n"
            f").{attribute_name} = {getattr(metadata, attribute_name)!r}"
        ),
        -4,
    )


@collections.abc.MutableMapping.register
class Thesaurus:
    """
    An instance of `sob.Thesaurus` is a dictionary-like object wherein
    each value is an instance of `sob.Synonyms`.

    For example, if you have an API with several GET endpoints, the endpoint
    paths relative to the API base URL would make ideal keys for your
    `sob.Thesaurus` instance. After adding a representative sample of responses
    from each endpoint to the corresponding `sob.Synonyms` instance in your
    `sob.Thesaurus` instance, your thesaurus will be able to generate a
    python module with an `sob` based data model for all of your endpoints,
    including polymorphism where encountered.

    The keys of an `sob.Thesaurus` dictionary are meaningful in that they
    contribute to the naming of classes (which are formatted to comply with
    PEP-8, and to avoid collision with builtins, language keywords, etc.).

    For background: The `sob` library was designed for authoring a data model
    representing schemas defined by an OpenAPI specification. Although
    OpenAPI specifications are increasingly ubiquitous, there are scenarios
    where you might need to interact with an API which does not have an
    OpenAPI specification, or for which the OpenAPI specification is simply
    not available to *you*. In these cases, you can generate an `sob`
    model to validate your API responses using `sob.Thesaurus`.
    """

    __module__: str = "sob"

    __slots__ = ("_dict",)

    def __init__(
        self,
        _items: Mapping[
            str, Iterable[abc.Readable | abc.MarshallableTypes] | Synonyms
        ]
        | Iterable[
            tuple[
                str, Iterable[abc.Readable | abc.MarshallableTypes] | Synonyms
            ]
        ]
        | Thesaurus
        | None = None,
        **kwargs: Iterable[abc.Readable | abc.MarshallableTypes],
    ) -> None:
        """
        Parameters:
            _items: A mapping of keys to values, where each value is
                an iterable of items which are synonymous with the key.
                This can either be an iterable of key/value pair tuples,
                or a dictionary-like object.
        """
        self._dict: dict[str, Synonyms] = {}
        key: str
        value: Iterable[abc.Readable | abc.MarshallableTypes]
        for key, value in dict(
            *((_items,) if _items else ()), **kwargs
        ).items():
            self[key] = value

    def __setitem__(
        self,
        key: str,
        value: Synonyms | Iterable[abc.Readable | abc.MarshallableTypes],
    ) -> None:
        """
        This method adds/overwrites the synonyms for the specified `key`.
        If the `value` is not an instance of `sob.Synonyms`, a new instance
        of `sob.Synonyms` is created and JSON data items from `value` are
        added to it.

        Parameters:
            key: A string to utilize when attributing a unique name to the
                class representing these synonyms.
            value: An iterable of JSON data which should be considered
                synonymous.
        """
        if not isinstance(value, Synonyms):
            value = Synonyms(value)
        return self._dict.__setitem__(key, value)

    def __delitem__(self, key: str) -> None:
        """
        This method deletes the synonyms assigned the specified `key`.

        Parameters:
            key:
        """
        self._dict.__delitem__(key)

    def pop(
        self, key: str, default: Synonyms | Undefined = UNDEFINED
    ) -> Synonyms:
        """
        This method removes and returns the synonyms assigned to the specified
        `key`.

        Parameters:
            key:
            default: A value to return if the specified `key` does not exist.
                If no default is provided, a `KeyError` will be raised if the
                key is not found.
        """
        return self._dict.pop(
            key,
            **({} if isinstance(default, Undefined) else {"default": default}),
        )

    def popitem(self) -> tuple[str, Synonyms]:
        """
        This method removes and returns a tuple of the most recently added
        key/synonyms pair (by default), or the first added key/synonyms pair
        if `last` is set to `False`.
        """
        return self._dict.popitem()

    def clear(self) -> None:
        """
        This method clears the thesaurus, removing all synonyms.
        """
        self._dict.clear()

    def update(
        self,
        **kwargs: Synonyms | Iterable[abc.Readable | abc.MarshallableTypes],
    ) -> None:
        """
        This method updates the thesaurus with one or more specified synonyms.

        Parameters:
            kwargs: A mapping of keys to values, where each value is
                an iterable of items which are synonymous with the key,
                or is an instance of `sob.Synonyms`.
        """
        key: str
        value: Iterable[abc.Readable | abc.MarshallableTypes]
        for key, value in kwargs.items():
            self[key] = value

    def setdefault(
        self,
        key: str,
        default: Iterable[abc.Readable | abc.MarshallableTypes],
    ) -> Synonyms:
        """
        This method assigns `default` synonyms to the specified `key` if
        no synonyms have previously been assigned to the key, and returns
        either the existing or newly assigned synonyms.
        """
        if not isinstance(default, Synonyms):
            default = Synonyms(default)
        return self._dict.setdefault(key, default)

    def __getitem__(self, key: str) -> Synonyms:
        try:
            return self._dict.__getitem__(key)
        except KeyError:
            self[key] = Synonyms()
            return self[key]

    def get(
        self, key: str, default: Undefined | Synonyms = UNDEFINED
    ) -> Synonyms:
        return self._dict.get(  # type: ignore
            key,
            **({} if isinstance(default, Undefined) else {"default": default}),
        )

    def __contains__(self, key: str) -> bool:
        return self._dict.__contains__(key)

    def keys(self) -> KeysView[str]:
        return self._dict.keys()

    def items(self) -> ItemsView[str, Synonyms]:
        return self._dict.items()

    def values(self) -> ValuesView[Synonyms]:
        return self._dict.values()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self._dict == other._dict
        return False

    def __copy__(self) -> Self:
        return self.__class__(copy(self._dict))

    def __reversed__(self) -> Self:
        return self.__class__(reversed(self._dict.items()))

    def __deepcopy__(self, memo: dict | None = None) -> Self:
        return self.__class__(deepcopy(self._dict, memo=memo))

    def __iadd__(self, other: Thesaurus) -> Self:
        if not isinstance(other, Thesaurus):
            raise TypeError(other)
        key: str
        value: Synonyms
        for key, value in other.items():
            self[key] |= value
        return self

    def __add__(self, other: Thesaurus) -> Self:
        return copy(self).__iadd__(other)

    def get_models(
        self,
        module: str = "__main__",
        name: Callable[[str], str] = get_class_name_from_pointer,
    ) -> Iterable[type]:
        key: str
        synonyms: Synonyms
        for key, synonyms in self.items():
            model_class: type
            yield from synonyms.get_models(key, module=module, name=name)

    def _get_module_source(
        self,
        module_name: str = "__main__",
        name: Callable[[str], str] = get_class_name_from_pointer,
    ) -> str:
        return get_models_source(
            *self.get_models(module=module_name, name=name)
        )

    def get_module_source(
        self, name: Callable[[str], str] = get_class_name_from_pointer
    ) -> str:
        """
        This method generates and returns the source code for a module
        defining data models applicable to the data contained in this
        thesaurus.

        Parameters:

        - name (str) = sob.thesaurus.get_class_name_from_pointer:
          A function which accepts one `str` argument—a synonym key
          concatenated with "#" and JSON pointer (for example:
          "key#/body/items/0") and which returns a `str` which will be the
          resulting class name (for example: "KeyBodyItemsItem").
        """
        return get_models_source(
            *self.get_models(module="__main__", name=name)
        )

    def get_module(
        self, name: Callable[[str], str] = get_class_name_from_pointer
    ) -> ModuleType:
        """
        This method generates and returns a module defining data models
        applicable to the data contained in this thesaurus. This module is not
        suitable for writing out for static use--use `Thesaurus.save_module`
        to generate and write a model suitable for static use.

        Parameters:

        - name (str) = sob.thesaurus.get_class_name_from_pointer:
          A function which accepts one `str` argument—a synonym key
          concatenated with "#" and JSON pointer (for example:
          "key#/body/items/0") and which returns a `str` which will be the
          resulting class name (for example: "KeyBodyItemsItem").
        """
        # For pickling to work, the `__module__` variable needs to be set to
        # the calling module.
        module_name: str = get_calling_module_name(2)
        module: ModuleType = ModuleType(module_name)
        exec(  # noqa: S102
            self._get_module_source(module_name, name=name), module.__dict__
        )
        return module

    def save_module(
        self,
        path: str | Path,
        name: Callable[[str], str] = get_class_name_from_pointer,
    ) -> None:
        """
        This method generates and saves the source code for a module
        defining data models applicable to the data contained in this
        thesaurus.

        Parameters:

        - path (str): The file path where the data will be written.
        - name (str) = sob.thesaurus.get_class_name_from_pointer:
          A function which accepts one `str` argument—a synonym key
          concatenated with "#" and JSON pointer (for example:
          "key#/body/items/0") and which returns a `str` which will be the
          resulting class name (for example: "KeyBodyItemsItem").
        """
        if isinstance(path, str):
            path = Path(path)
        os.makedirs(path.parent, exist_ok=True)
        module_source: str = self.get_module_source(name=name)
        with open(path, "w") as module_io:
            module_io.write(f"{module_source}\n")
