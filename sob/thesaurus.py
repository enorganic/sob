"""
This module provides functionality for creating a data model from a
set of example structures.
"""
import collections
import functools
import numbers
import os
from types import ModuleType
from base64 import b64decode
from collections import OrderedDict
from copy import copy, deepcopy
from datetime import date, datetime
from io import IOBase
from typing import (Dict, Iterable, List, Optional, Set, Tuple, Union)
from urllib.response import addbase

import binascii
from iso8601 import ParseError, parse_date

from . import __name__ as _parent_module_name, abc, meta
from .model import detect_format, from_meta, unmarshal
from .properties import Property, TYPES_PROPERTIES
from .utilities import get_source, qualified_name
from .utilities.assertion import (
    assert_argument_is_instance, assert_argument_is_subclass
)
from .utilities.inspect import calling_module_name
from .utilities.io import read
from .utilities.string import class_name, property_name
from .utilities.types import NULL, Null, TYPES

__all__: List[str] = [
    'Synonyms', 'Thesaurus'
]

from .utilities.typing import MarshallableTypes

_READABLE_TYPES: Tuple[type, ...] = (IOBase, addbase)


def _read(data: Union[_READABLE_TYPES]) -> str:
    string_data: str
    read_data: Union[str, bytes] = read(data)
    if isinstance(read_data, (bytes, bytearray)):
        string_data = str(read_data, encoding='utf-8')
    else:
        string_data = read_data
    return string_data


def _update_types(
    types: abc.types.Types,
    new_types: abc.types.Types,
    memo: Optional[Dict[str, type]] = None
) -> None:
    """
    This function updates `types` to incorporate any additional types from
    `new_types`, as well as to merge definitions for shared types.

    Parameters:

    - types (sob.properties.types.Types)
    - new_types (sob.properties.types.Types)
    - memo (dict)
    """
    assert memo is not None
    for new_type in new_types:
        if issubclass(new_type, abc.model.Model):
            if type.__name__ in memo:
                existing_type: type = memo[type.__name__]
                _update_model_class_from_meta(
                    existing_type,
                    meta.read(new_type),
                    memo=memo
                )
                new_type = existing_type
        if new_type not in types:
            types.append(new_type)


def _update_array_meta(
    metadata: abc.meta.Array,
    new_metadata: abc.meta.Array,
    memo: Optional[Dict[str, type]] = None
) -> None:
    """
    This function updates `metadata` by adding/updating `metadata.item_types`
    to include types from `new_metadata.item_types`.

    Parameters:

    - metadata (sob.meta.Array)
    - new_metadata (sob.meta.Array)
    - memo (dict)
    """
    assert memo is not None
    _update_types(
        metadata.item_types,
        new_metadata.item_types,
        memo=memo
    )


def _update_object_meta(
    metadata: abc.meta.Object,
    new_metadata: abc.meta.Object,
    memo: Optional[Dict[str, type]] = None
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
    assert memo is not None
    metadata_keys: Set[str] = set(metadata.properties.keys())
    new_metadata_keys: Set[str] = set(new_metadata.properties.keys())
    # Add properties that don't exist
    key: str
    for key in (metadata_keys - new_metadata_keys):
        metadata.properties[key] = new_metadata.properties[key]
    # Update shared properties
    for key in (metadata_keys & new_metadata_keys):
        _update_types(
            metadata.properties[key].types,
            new_metadata.properties[key].types,
            memo=memo
        )


def _update_object_class_from_meta(
    object_class: type,
    new_object_metadata: abc.meta.Object,
    memo: Optional[Dict[str, type]] = None
) -> None:
    """
    This function merges new metadata into an existing object model's metadata.

    Parameters:

    - object_class (type)
    - new_object_metadata (sob.meta.Object)
    - memo (dict)
    """
    assert memo is not None
    assert isinstance(new_object_metadata, abc.meta.Object)
    object_metadata: abc.meta.Object = meta.read(object_class)
    _update_object_meta(
        object_metadata,
        new_object_metadata,
        memo=memo
    )
    # Recreate the object class
    updated_object_class: type = from_meta(
        object_class.__name__,
        object_metadata,
        module=object_class.__module__,
        docstring=object_class.__doc__
    )
    # Apply the rest of the changes to the existing model class
    object_class.__init__ = updated_object_class.__init__
    object_class._source = get_source(updated_object_class)


def _update_array_class_from_meta(
    array_class: type,
    new_array_metadata: abc.meta.Array,
    memo: Optional[Dict[str, type]] = None
) -> None:
    """
    This function merges new metadata into an existing array model's metadata.

    Parameters:

    - array_class (type)
    - new_array_metadata (sob.meta.Array)
    - memo (dict)
    """
    assert memo is not None
    assert isinstance(new_array_metadata, abc.meta.Array)
    array_metadata: abc.meta.Array = meta.writable(array_class)
    _update_array_meta(
        array_metadata,
        new_array_metadata,
        memo=memo
    )
    # Since the two array classes have the same name--the class
    # definition/declaration won't change, so updating the metadata is all that
    # is necessary


def _update_model_class_from_meta(
    model_class: type,
    new_metadata: Union[abc.meta.Array, abc.meta.Object],
    memo: Optional[Dict[str, type]] = None
) -> None:
    """
    This function merges new metadata into an existing model's metadata.

    Parameters:

    - model_class (type)
    - new_metadata (sob.meta.Array|sob.meta.Object)
    - memo (dict)
    """
    assert memo is not None
    assert issubclass(model_class, (abc.model.Array, abc.model.Object))
    # Update the model metadata in-place
    if issubclass(model_class, abc.model.Array):
        _update_array_class_from_meta(
            model_class,
            new_metadata,
            memo=memo
        )
    else:
        _update_object_class_from_meta(
            model_class,
            new_metadata,
            memo=memo
        )


def _get_models_from_meta(
    name: str,
    metadata: Union[abc.meta.Array, abc.meta.Object],
    module: str = '__main__',
    memo: Optional[Dict[str, type]] = None
) -> List[type]:
    """
    This function generates and updates classes from metadata.

    Parameters:

    - name (str)
    - metadata (sob.meta.Array|sob.meta.Object)
    - module (str)
    - memo (dict)
    """
    assert memo is not None
    new_models: List[type] = []
    # If a model of the same name already exists, we update it to
    # reflect our metadata, otherwise--we create a new model
    if name in memo:
        _update_model_class_from_meta(
            memo[name],
            metadata,
            memo=memo
        )
    else:
        new_model: type = from_meta(
            name,
            metadata,
            module=module
        )
        memo[name] = new_model
        new_models.append(new_model)
    return new_models


def _is_base64(value: str) -> bool:
    """
    Test to see if `value` can be interpreted as base-64 encoded binary data.
    """
    try:
        b64decode(bytes(value, encoding='utf-8'))
        return True
    except binascii.Error:
        return False


@functools.lru_cache(maxsize=128)
def _str_date_or_datetime(value: str) -> type:
    """
    Test to see if `value` can be interpreted as an ISO-8601 encoded `date` or
    `datetime`.
    """
    try:
        timestamp: datetime = parse_date(value)
        if (
            timestamp.hour or
            timestamp.minute or
            timestamp.second or
            timestamp.microsecond
        ):
            return date
        else:
            return datetime
    except ParseError:
        return str


def _is_datetime_str(value: str) -> bool:
    """
    Test to see if `value` can be interpreted as an ISO-8601 encoded
    `datetime`.
    """
    return _str_date_or_datetime(value) is datetime


def _is_date_str(value: str) -> bool:
    """
    Test to see if `value` can be interpreted as an ISO-8601 encoded
    `date`.
    """
    return _str_date_or_datetime(value) is date


class Synonyms(set):
    """
    This class contains deserialized data, implied to represent variations of
    one type of entity, and is used to infer a model for that entity.
    """

    def __init__(
        self,
        items: Iterable[
            Union[
                _READABLE_TYPES + TYPES
            ]
        ] = ()
    ) -> None:
        self._data_type: Optional[type] = None
        self._nullable: bool = False
        super().__init__()
        if items:
            assert_argument_is_instance(
                'items',
                items,
                collections.abc.Iterable
            )
            self.__ior__(items)

    def add(self, item: Union[_READABLE_TYPES + TYPES]) -> None:
        """
        This method adds a synonymous item to the set. If the item is a
        file-like (input/output) object, that object is first read,
        deserialized, and unmarshalled.

Parameters:

- item ({}):
          A file-like or a JSON-serializable python object.
        """.format(
            '|'.join(
                qualified_name(item_type)
                for item_type in (_READABLE_TYPES + TYPES)
            )
        )
        assert isinstance(item, _READABLE_TYPES + TYPES)
        if isinstance(item, _READABLE_TYPES):
            # Deserialize and unmarshal file-like objects
            item = unmarshal(detect_format(_read(item))[0])
        elif (
            isinstance(item, Iterable) and not
            isinstance(item, (str, abc.model.Model))
        ):
            # Unmarshal items which appear to not have been part of an
            # unmarshalled container
            item = unmarshal(item)
        if item is NULL:
            self._nullable = True
        elif item is not None:
            if self._data_type is None:
                self._data_type = type(item)
            else:
                # If there is a data type discrepancy between `float` and
                # `int`, use `float`.
                if (
                    issubclass(self._data_type, (int, float)) and
                    isinstance(item, (int, float)) and
                    (type(item) is not self._data_type)
                ):
                    self._data_type = float
                else:
                    assert isinstance(item, self._data_type)
        super().add(item)

    def union(
        self,
        other: Iterable[Union[_READABLE_TYPES + TYPES]]
    ) -> 'Synonyms':
        """
        This method returns an instance of `Synonyms` which incorporates
        all (non-redundant) items from both `self` and `other`.
        """
        new_synonyms: Synonyms = copy(self)
        new_synonyms |= other
        return new_synonyms

    def __ior__(
        self,
        other: Iterable[Union[_READABLE_TYPES + TYPES]]
    ) -> 'Synonyms':
        for item in other:
            self.add(item)
        return self

    def __copy__(self) -> 'Synonyms':
        return type(self)(self)

    def __deepcopy__(self, memo: Optional[dict] = None) -> 'Synonyms':
        return type(self)(
            deepcopy(item)
            for item in self
        )

    def _get_type(self) -> type:
        # This function should only be invoked for simple types, so we first
        # verify the data type is not a container
        assert not issubclass(self._data_type, (dict, list))
        data_type: type = self._data_type
        # Determine if this is a string encoded to represent a `date`,
        # `datetime`, or base-64 encoded `bytes`.
        if issubclass(self._data_type, str):
            if all(
                _is_base64(item)
                for item in self
                if item not in (None, NULL)
            ):
                data_type = bytes
            elif all(
                _is_datetime_str(item)
                for item in self
                if item not in (None, NULL)
            ):
                data_type = datetime
            elif all(
                _is_date_str(item)
                for item in self
                if item not in (None, NULL)
            ):
                data_type = date
        return data_type

    def _get_property_names_values(self) -> Dict[str, List[Union[TYPES]]]:
        property_names_values: Dict[str, List[Union[TYPES]]] = OrderedDict()
        item: dict
        for item in self:
            assert isinstance(item, dict)
            value: MarshallableTypes
            for name, value in item.items():
                if name not in property_names_values:
                    property_names_values[name] = []
                property_names_values[name].append(value)
        return property_names_values

    def _get_object_models(
        self,
        name: str,
        module: str = '__main__',
        memo: Optional[Dict[str, abc.model.Model]] = None
    ) -> Iterable[type]:
        metadata: abc.meta.Object = meta.Object()
        metadata.properties = meta.Properties()
        key: str
        property_name_: str
        values: List[Union[TYPES]]
        for key, values in (
            self._get_property_names_values().items()
        ):
            property_name_ = property_name(key)
            item_type: Optional[type] = None
            is_model: bool = False
            property_synonyms: Synonyms = type(self)(values)
            for item_type in property_synonyms._get_types(
                name=class_name(f'{name}/{property_name_}'),
                module=module,
                memo=memo
            ):
                if issubclass(item_type, abc.model.Model):
                    is_model = True
                    yield item_type
                else:
                    is_model = False
            if item_type:
                # `float` is represented by `numbers.Number` in
                # `sob.properties` (so that it can also represent `int`
                # values).
                if item_type is float:
                    item_type = numbers.Number
                if is_model:
                    metadata.properties[property_name_] = Property(
                        name=key,
                        types=[item_type] + (
                            [Null]
                            if property_synonyms._nullable else
                            []
                        )
                    )
                elif property_synonyms._nullable:
                    metadata.properties[property_name_] = Property(
                        name=key,
                        types=[
                            TYPES_PROPERTIES[
                                item_type
                            ](),
                            Null
                        ]
                    )
                else:
                    metadata.properties[property_name_] = TYPES_PROPERTIES[
                        item_type
                    ](name=key)
            else:
                metadata.properties[property_name_] = Property(name=key)
        model_class: type
        for model_class in _get_models_from_meta(
            class_name(name),
            metadata,
            module=module,
            memo=memo
        ):
            yield model_class

    def _get_array_models(
        self,
        name: str,
        module: str = '__main__',
        memo: Optional[Dict[str, abc.model.Model]] = None
    ) -> Iterable[type]:
        unified_items: Synonyms = type(self)()
        items: List[TYPES]
        for items in self:
            unified_items |= items
        item_type: Optional[type] = None
        for item_type in unified_items._get_types(
            name=class_name(f'{name}/item'),
            module=module,
            memo=memo
        ):
            yield item_type
        metadata: abc.meta.Array = meta.Array(
            item_types=(
                None
                if item_type is None else
                [item_type]
            )
        )
        array_type: type
        for array_type in _get_models_from_meta(
            class_name(name),
            metadata,
            module=module,
            memo=memo
        ):
            yield array_type

    def _get_types(
        self,
        name: str,
        module: str = '__main__',
        memo: Optional[Dict[str, abc.model.Model]] = None
    ) -> Iterable[type]:
        # `_memo` holds a dictionary of all classes which have been created,
        # and is passed recursively to facilitate de-duplication
        memo_is_new: bool = False
        if memo is None:
            memo = {}
            memo_is_new = True
        if self._data_type is None:
            type_iterator = []
        elif issubclass(self._data_type, dict):
            type_iterator = self._get_object_models(
                name,
                module=module,
                memo=memo
            )
        elif issubclass(self._data_type, list):
            type_iterator = self._get_array_models(
                name,
                module=module,
                memo=memo
            )
        else:
            type_iterator = [
                self._get_type()
            ]
        # If this was the call which initialized our `_memo`, we want to
        # force the iterator to run, in order to fully update all models before
        # returning them to the user (as some will be updated over the course
        # of traversal when analogous elements are encountered).
        if memo_is_new:
            type_iterator = list(type_iterator)
        type_: type
        for type_ in type_iterator:
            yield type_

    def get_models(
        self,
        name: str,
        module: str = '__main__'
    ) -> Iterable[type]:
        """
        Retrieve a sequence of class definitions representing a data model
        capable of describing these synonyms.

        Parameters:

        - name (str): The name of the top-level model class. Please note that
          PEP-8 class-naming conventions are enforced, so a `name` of
          "get some", "get-some" or "get_some" would result in a class name
          of "GetSome".
        - module (str): The name of the module in which model classes will be
          defined. This defaults to "__main__".
        """
        # This assertion ensures `self` contains data which can be described by
        # a model class.
        assert_argument_is_subclass(
            f'{qualified_name(type(self))}._data_type',
            self._data_type,
            (dict, list)
        )
        for model_class in self._get_types(
            name=name,
            module=module
        ):
            assert issubclass(model_class, abc.model.Model)
            yield model_class


class Thesaurus(OrderedDict):

    def __init__(
        self,
        items: Optional[Union[
            Dict[
                str,
                Iterable[Union[_READABLE_TYPES + TYPES]]
            ],
            Iterable[Tuple[
                str,
                Iterable[Union[_READABLE_TYPES + TYPES]]
            ]],
        ]] = None,
        **kwargs: Union[_READABLE_TYPES + TYPES]
    ) -> None:
        super().__init__(
            *(items or ()),
            **kwargs
        )

    def __setitem__(
        self,
        key: str,
        value: Iterable[Union[_READABLE_TYPES + TYPES]]
    ) -> None:
        if not isinstance(value, Synonyms):
            value = Synonyms(value)
        return super().__setitem__(key, value)

    def __getitem__(self, key: str) -> Synonyms:
        try:
            return super().__getitem__(key)
        except KeyError:
            self[key] = Synonyms()
            return self[key]

    def __iadd__(
        self,
        other: 'Thesaurus'
    ) -> None:
        assert isinstance(other, Thesaurus)
        key: str
        value: List[Union[TYPES]]
        for key, value in other.items():
            self[key] |= value

    def __copy__(self) -> 'Thesaurus':
        return type(self)(self.items())

    def __deepcopy__(self, memo: dict) -> 'Thesaurus':
        return type(self)(
            deepcopy(item) for item in self.items()
        )

    def __add__(
        self,
        other: 'Thesaurus'
    ) -> 'Thesaurus':
        new_module: Thesaurus = copy(self)
        new_module += other
        return new_module

    def __iter__(self) -> Iterable[Tuple[str, abc.model.Model]]:
        key: str
        value: Synonyms
        for name, data_list in self._items.items():
            model: abc.model.Model
            for model in data_list.get_model(name):
                yield model

    def get_models(
        self,
        module: Optional[str] = None
    ) -> Iterable[Union[abc.model.Array, abc.model.Object]]:
        name: str
        synonyms: Synonyms
        for name, synonyms in self.items():
            model_class: type
            for model_class in synonyms.get_models(name, module=module):
                yield model_class

    def _get_module_source(self, name: Optional[str] = None) -> str:
        class_names_metadata: Dict[
            str, Union[meta.Object, meta.Array]
        ] = OrderedDict()
        imports: List[str] = []
        classes: List[str] = []
        metadatas: List[str] = []
        model: Union[abc.model.Object, abc.model.Array]
        for model in self.get_models(module=name):
            source: str
            imports_str: str
            import_line: str
            imports_str, source = get_source(model).split('\n\n\n')
            for import_line in imports_str.split('\n'):
                if import_line not in imports:
                    imports.append(import_line)
            classes.append(source)
            class_names_metadata[model.__name__] = meta.read(model)
        for negative_index, class_name_metadata in enumerate(
            class_names_metadata.items(),
            -(len(class_names_metadata)-1)
        ):
            separator: str
            class_name_: str
            metadata: Union[abc.meta.Object, abc.meta.Array]
            class_name_, metadata = class_name_metadata
            assert isinstance(metadata, (abc.meta.Object, abc.meta.Array))
            if isinstance(metadata, abc.meta.Object):
                metadatas.append(
                    'sob.meta.writable(\n'
                    f'    {class_name_}\n'
                    f').properties = {repr(metadata.properties)}\n'
                )
            else:
                metadatas.append(
                    'sob.meta.writable(\n'
                    f'    {class_name_}\n'
                    f').item_types = {repr(metadata.item_types)}\n'
                )
        return '\n'.join(
            sorted(
                imports,
                key=lambda line: (
                    1 if line == f'import {_parent_module_name}' else 0
                )
            ) + ['\n'] +
            classes +
            metadatas
        )

    def get_module_source(self) -> str:
        """
        This method generates and returns the source code for a module
        defining data models applicable to the data contained in this
        thesaurus.

        Parameters:

        - name (str): The name to give the module. This defaults to the module
          from where this method is called.
        """
        return self._get_module_source(name='__main__')

    def get_module(self) -> ModuleType:
        """
        This method generates and returns a module defining data models
        applicable to the data contained in this thesaurus. This module is not
        suitable for writing out for static use--use `Thesaurus.save_module`
        to generate and write a model suitable for static use.

        Parameters:

        - name (str): The name to give the module. This defaults to the module
          from where this method is called.
        """
        # For pickling to work, the `__module__` variable needs to be set to
        # the calling module.
        name: str = calling_module_name(2)
        module: ModuleType = ModuleType(name)
        exec(self.get_module_source(name=name), module.__dict__)
        return module

    def save_module(self, path: str) -> None:
        """
        This method generates and saves the source code for a module
        defining data models applicable to the data contained in this
        thesaurus.

        Parameters:

        - path (str): The file path where the data will be written.
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as module_io:
            module_io.write(self.get_module_source())
