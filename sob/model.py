"""
This module defines the building blocks of an `sob` based data model.
"""
import builtins
import collections
import collections.abc
import json
import sys
from base64 import b64decode, b64encode
from copy import deepcopy, copy
from datetime import date, datetime
from decimal import Decimal
from io import IOBase
from itertools import chain
from numbers import Number
from typing import (
    Any, Callable, Dict, Generator, IO, Iterable, List, Mapping, Optional,
    Sequence, Set, Tuple, Union
)
from urllib.parse import urljoin
from urllib.response import addbase

import yaml
from more_itertools import chunked

from . import (
    __name__ as _parent_module_name, abc, errors, hooks, meta, properties,
    utilities
)
from .properties.types import NULL, Null
from .utilities import indent, qualified_name
from .utilities.assertion import assert_argument_is_instance
from .utilities.io import get_url, read
from .utilities.string import split_long_docstring_lines
from .utilities.types import Module, UNDEFINED, Undefined

_UNMARSHALLABLE_TYPES = tuple(
    set(properties.types.TYPES) | {properties.types.NoneType}
)
_LINE_LENGTH: int = 79


class Model:
    """
    This serves as a base class for the [Object](#Object), [Array](#Array) and
    [Dictionary](#Dictionary) classes. This class should not be instantiated
    directly, and should not be sub-classed directly--please use `Object`,
    `Array` and/or `Dictionary` as a superclass instead.
    """

    _format: Optional[str] = None
    _meta: Optional[meta.Object] = None
    _hooks: Optional[hooks.Object] = None

    def __init__(self) -> None:
        self._meta: Optional[meta.Meta] = None
        self._hooks: Optional[meta.Meta] = None
        self._url: Optional[str] = None
        self._pointer: Optional[str] = None

    def _init_url(
        self,
        data: Optional[Union[Sequence, Set, Dict, 'Model']]
    ) -> None:
        if isinstance(data, IOBase):
            url: Optional[str] = None
            if hasattr(data, 'url'):
                url = data.url
            elif hasattr(data, 'name'):
                url = urljoin('file:', data.name)
            if url is not None:
                meta.url(self, url)

    def _init_format(
        self,
        data: Optional[Union[Sequence, Set, Dict, 'Model']] = None
    ) -> Any:
        deserialized_data: Any
        format_: str
        deserialized_data, format_ = detect_format(data)
        if format_ is not None:
            meta.format_(self, format_)
        return deserialized_data

    def _init_pointer(self) -> None:
        if meta.pointer(self) is None:
            meta.pointer(self, '#')


abc.model.Model.register(Model)


class Object(Model):
    """
    This serves as a base class for representing deserialized and un-marshalled
    data for which a discrete set of properties are known in advance, and for
    which enforcing adherence to a predetermined attribution and type
    requirements is desirable.
    """

    def __init__(
        self,
        _data: Optional[Union[str, bytes, dict, Sequence, IO]] = None,
    ) -> None:
        self._meta: Optional[meta.Object]
        self._hooks: Optional[hooks.Object]
        Model.__init__(self)
        deserialized_data: Any = self._init_format(_data)
        self._data_init(deserialized_data)
        self._init_url(_data)
        self._init_pointer()

    def _data_init(
        self,
        _data: Optional[Union[str, bytes, dict, Sequence, IO]]
    ) -> None:
        if _data is not None:
            if isinstance(_data, Object):
                self._copy_init(_data)
            else:
                url = None
                if isinstance(_data, IOBase):
                    url = get_url(_data)
                _data, format_ = detect_format(_data)
                assert_argument_is_instance('_data', _data, dict)
                self._dict_init(_data)
                meta.format_(self, format_)
                meta.url(self, url)
                meta.pointer(self, '#')

    def _dict_init(self, dictionary: dict) -> None:
        """
        Initialize this object from a dictionary
        """
        for property_name, value in dictionary.items():
            if value is None:
                value = NULL
            try:
                self[property_name] = value
            except KeyError as error:
                raise errors.UnmarshalKeyError(
                    '%s\n\n%s.%s: %s' % (
                        errors.get_exception_text(),
                        qualified_name(type(self)),
                        error.args[0], repr(dictionary)
                    )
                )

    def _copy_init(self, other: abc.model.Object) -> None:
        """
        Initialize this object from another `Object` (copy constructor)
        """
        instance_meta = meta.read(other)
        if meta.read(self) is not instance_meta:
            meta.write(self, deepcopy(instance_meta))
        instance_hooks = hooks.read(other)
        if hooks.read(self) is not instance_hooks:
            hooks.write(self, deepcopy(instance_hooks))
        for property_name in instance_meta.properties.keys():
            try:
                setattr(self, property_name, getattr(other, property_name))
            except TypeError as error:
                label = '\n - %s.%s: ' % (
                    qualified_name(type(self)), property_name
                )
                if error.args:
                    error.args = tuple(
                        chain(
                            (label + error.args[0],),
                            error.args[1:]
                        )
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

    def _get_property_definition(
        self,
        property_name: str
    ) -> abc.properties.Property:
        """
        Get a property's definition
        """
        try:
            return meta.read(self).properties[property_name]
        except KeyError:
            raise KeyError(
                '`%s` has no attribute "%s".' % (
                    qualified_name(type(self)),
                    property_name
                )
            )

    def _unmarshal_value(self, property_name: str, value: Any) -> Any:
        """
        Unmarshall a property value
        """
        property_definition = self._get_property_definition(property_name)

        if value is not None:
            if isinstance(value, Generator):
                value = tuple(value)
            try:
                value = _unmarshal_property_value(property_definition, value)
            except (TypeError, ValueError) as error:
                message = '\n - %s.%s: ' % (
                    qualified_name(type(self)),
                    property_name
                )
                if error.args and isinstance(error.args[0], str):
                    error.args = tuple(
                        chain(
                            (message + error.args[0],),
                            error.args[1:]
                        )
                    )
                else:
                    error.args = (message + repr(value),)

                raise error

        return value

    def __setattr__(self, property_name: str, value: Any) -> None:
        instance_hooks: Optional[hooks.Object] = None
        unmarshalled_value = value
        if property_name[0] != '_':
            instance_hooks = hooks.read(self)
            if instance_hooks and instance_hooks.before_setattr:
                property_name, value = instance_hooks.before_setattr(
                    self, property_name, value
                )
            unmarshalled_value = self._unmarshal_value(property_name, value)
        if instance_hooks and instance_hooks.after_setattr:
            instance_hooks.after_setattr(self, property_name, value)
        super().__setattr__(property_name, unmarshalled_value)

    def _get_key_property_name(self, key: str) -> str:
        instance_meta = meta.read(self)
        if (key in instance_meta.properties) and (
            instance_meta.properties[key].name in (None, )
        ):
            property_name = key
        else:
            property_name = None
            for potential_property_name, property in (
                instance_meta.properties.items()
            ):
                if key == property.name:
                    property_name = potential_property_name
                    break
            if property_name is None:
                raise KeyError(
                    '`%s` has no property mapped to the name "%s"' % (
                        qualified_name(type(self)),
                        key
                    )
                )
        return property_name

    def __setitem__(self, key: str, value: Any) -> None:
        # Before set-item hooks
        hooks_: hooks.Object = hooks.read(self)
        if hooks_ and hooks_.before_setitem:
            key, value = hooks_.before_setitem(self, key, value)
        # Get the corresponding property name
        property_name = self._get_key_property_name(key)
        # Set the attribute value
        setattr(self, property_name, value)
        # After set-item hooks
        if hooks_ and hooks_.after_setitem:
            hooks_.after_setitem(self, key, value)

    def __delattr__(self, key: str) -> None:
        """
        Deleting attributes with defined metadata is not allowed--doing this
        is instead interpreted as setting that attribute to `None`.
        """
        instance_meta = meta.read(self)
        if key in instance_meta.properties:
            setattr(self, key, None)
        else:
            super().__delattr__(key)

    def __getitem__(self, key: str) -> None:
        """
        Retrieve a value using the item assignment operators `[]`.
        """
        # Get the corresponding property name
        instance_meta = meta.read(self)
        if key in instance_meta.properties:
            property_name = key
        else:
            property_definition = None
            property_name = None
            for pn, pd in instance_meta.properties.items():
                if key == pd.name:
                    property_name = pn
                    property_definition = pd
                    break
            if property_definition is None:
                raise KeyError(
                    '`%s` has no property mapped to the name "%s"' % (
                        qualified_name(type(self)),
                        key
                    )
                )
        # Retrieve the value assigned to the corresponding property
        return getattr(self, property_name)

    def __copy__(self) -> 'Object':
        return self.__class__(self)

    def _deepcopy_property(
        self,
        property_name: str,
        other: 'Object',
        memo: dict
    ) -> None:
        """
        Deep-copy a property from this object to another
        """
        try:
            value = getattr(self, property_name)
            if isinstance(value, Generator):
                value = tuple(value)
            if value is not None:
                if not callable(value):
                    value = deepcopy(value, memo)
                setattr(other, property_name, value)
        except TypeError as error:
            label = '%s.%s: ' % (qualified_name(type(self)), property_name)
            if error.args:
                error.args = tuple(
                    chain(
                        (label + error.args[0],),
                        error.args[1:]
                    )
                )
            else:
                error.args = (label + serialize(self),)
            raise error

    def __deepcopy__(self, memo: Optional[dict]) -> 'Object':
        # Perform a regular copy operation
        new_instance = self.__copy__()
        # Retrieve the metadata
        meta_: meta.Object = meta.read(self)
        # If there is metadata--copy it recursively
        if meta_ is not None:
            for property_name in meta_.properties.keys():
                self._deepcopy_property(property_name, new_instance, memo)
        return new_instance

    def _marshal(self) -> Dict[str, Any]:
        object_ = self
        instance_hooks = hooks.read(object_)
        if (instance_hooks is not None) and (
            instance_hooks.before_marshal is not None
        ):
            object_ = instance_hooks.before_marshal(object_)
        data = collections.OrderedDict()
        instance_meta = meta.read(object_)
        for property_name, property_ in instance_meta.properties.items():
            value = getattr(object_, property_name)
            if value is not None:
                key = property_.name or property_name
                data[key] = _marshal_property_value(property_, value)
        if (instance_hooks is not None) and (
            instance_hooks.after_marshal is not None
        ):
            data = instance_hooks.after_marshal(data)
        return data

    def __str__(self) -> str:
        return serialize(self)

    @staticmethod
    def _repr_argument(parameter: str, value: Any) -> str:
        value_representation = (
            qualified_name(value) if isinstance(value, type) else
            repr(value)
        )
        lines = value_representation.split('\n')
        if len(lines) > 1:
            indented_lines = [lines[0]]
            for line in lines[1:]:
                indented_lines.append('    ' + line)
            value_representation = '\n'.join(indented_lines)
        return '    %s=%s,' % (parameter, value_representation)

    def __repr__(self) -> str:
        representation = [
            '%s(' % qualified_name(type(self))
        ]
        instance_meta = meta.read(self)
        for property_name in instance_meta.properties.keys():
            value = getattr(self, property_name)
            if value is not None:
                representation.append(
                    self._repr_argument(property_name, value)
                )
        # Strip the last comma
        if representation:
            representation[-1] = representation[-1].rstrip(',')
        representation.append(')')
        if len(representation) > 2:
            return '\n'.join(representation)
        else:
            return ''.join(representation)

    def __eq__(self, other: Any) -> bool:
        if type(self) is not type(other):
            return False
        instance_meta = meta.read(self)
        om = meta.read(other)
        self_properties = set(instance_meta.properties.keys())
        other_properties = set(om.properties.keys())
        if self_properties != other_properties:
            return False
        for property_name in (self_properties & other_properties):
            value = getattr(self, property_name)
            ov = getattr(other, property_name)
            if value != ov:
                return False
        return True

    def __ne__(self, other: Any) -> bool:
        return False if self == other else True

    def __iter__(self) -> Iterable[str]:
        instance_meta: meta.Object = meta.read(self)
        for property_name, property_ in instance_meta.properties.items():
            yield property_.name or property_name

    def _get_property_validation_error_messages(
        self,
        property_name: str,
        property_: properties.Property,
        value: Any
    ) -> Iterable[str]:
        error_messages: List[str] = []
        if value is None:
            if property_.required:
                yield (
                    'The property `%s` is required for `%s`:\n%s' % (
                        property_name,
                        qualified_name(type(self)),
                        str(self)
                    )
                )
        elif value is NULL:
            if (
                (property_.types is not None) and
                (Null not in property_.types)
            ):
                error_messages.append(
                    'Null values are not allowed in `{}.{}`, '
                    'permitted types include: {}.'.format(
                        qualified_name(type(self)),
                        property_name,
                        ', '.join(
                            f'`{qualified_name(type_)}`'
                            for type_ in property_.types
                        )
                    )
                )
        else:
            error_message: str
            for error_message in validate(
                value,
                property_.types,
                raise_errors=False
            ):
                yield (
                    'Error encountered while attempting to validate '
                    '`{}.{}}`:\n\n{}}'.format(
                        qualified_name(type(self)),
                        property_name,
                        error_message
                    )
                )

    def _validate(self, raise_errors: bool = True) -> None:
        """
        This method verifies that all required properties are present, and
        that all property values are of the correct type.
        """
        validation_error_messages: List[str] = []
        validated_object: Object = self
        instance_hooks: hooks.Object = hooks.read(self)
        if instance_hooks and instance_hooks.before_validate:
            validated_object = instance_hooks.before_validate(self)
        instance_meta: meta.Object = meta.read(validated_object)
        property_name: str
        property_: properties.Property
        error_message: str
        for property_name, property_ in instance_meta.properties.items():
            for error_message in (
                validated_object._get_property_validation_error_messages(
                    property_name,
                    property_,
                    getattr(validated_object, property_name)
                )
            ):
                validation_error_messages.append(error_message)
        if (
            instance_hooks is not None
        ) and (
            instance_hooks.after_validate is not None
        ):
            instance_hooks.after_validate(validated_object)
        if raise_errors and validation_error_messages:
            raise errors.ValidationError(
                '\n'.join(validation_error_messages)
            )
        return validation_error_messages


abc.model.Object.register(Object)


class Array(list, Model):
    """
    This can serve as either a base-class for typed (or untyped) sequences, or
    can be instantiated directly.

    Parameters:

    - items (list|set|io.IOBase|str|bytes)
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

    _hooks: Optional[hooks.Array]
    _meta: Optional[meta.Array]

    def __init__(
        self,
        items: Optional[Union[Sequence, Set, IO, str, bytes]] = None,
        item_types: Optional[
            Union[
                Sequence[
                    Union[
                        type,
                        properties.Property
                    ]
                ],
                type,
                properties.Property
            ]
        ] = None
    ) -> None:
        self._meta: Optional[meta.Array]
        self._hooks: Optional[hooks.Array]
        Model.__init__(self)
        deserialized_items: Any = self._init_format(items)
        self._init_item_types(deserialized_items, item_types)
        self._init_items(deserialized_items)
        self._init_url(items)
        self._init_pointer()

    def _init_item_types(
        self,
        items: Optional[Union[Sequence, Set]],
        item_types: Optional[
            Union[
                Sequence[
                    Union[
                        type,
                        properties.Property
                    ]
                ],
                type,
                properties.Property
            ]
        ]
    ) -> None:
        if item_types is None:
            # If no item types are explicitly attributed, but the initial items
            # are an instance of `Array`, we adopt the item types from that
            # `Array` instance.
            if isinstance(items, Array):
                items_meta = meta.read(items)
                if meta.read(self) is not items_meta:
                    meta.write(self, deepcopy(items_meta))
        else:
            meta.writable(self).item_types = item_types

    def _init_items(
        self,
        items: Optional[Union[Sequence, Set]]
    ) -> None:
        if items is not None:
            for item in items:
                self.append(item)

    def __hash__(self):
        return id(self)

    def __setitem__(
        self,
        index: int,
        value: Any,
    ) -> None:
        instance_hooks: hooks.Object = hooks.read(self)

        if instance_hooks and instance_hooks.before_setitem:
            index, value = instance_hooks.before_setitem(self, index, value)

        m: Optional[meta.Array] = meta.read(self)

        if m is None:
            item_types = None
        else:
            item_types = m.item_types

        value = unmarshal(value, types=item_types)
        super().__setitem__(index, value)

        if instance_hooks and instance_hooks.after_setitem:
            instance_hooks.after_setitem(self, index, value)

    def append(self, value: Any) -> None:
        if not isinstance(value, _UNMARSHALLABLE_TYPES):
            raise errors.UnmarshalTypeError(data=value)
        instance_hooks: hooks.Array = hooks.read(self)
        if instance_hooks and instance_hooks.before_append:
            value = instance_hooks.before_append(self, value)
        instance_meta: Optional[meta.Array] = meta.read(self)
        if instance_meta is None:
            item_types = None
        else:
            item_types = instance_meta.item_types
        value = unmarshal(value, types=item_types)
        super().append(value)
        if instance_hooks and instance_hooks.after_append:
            instance_hooks.after_append(self, value)

    def __copy__(self) -> 'Array':
        return self.__class__(self)

    def __deepcopy__(self, memo: Optional[dict] = None) -> 'Array':
        new_instance = self.__class__()
        im = meta.read(self)
        cm = meta.read(type(self))
        if im is not cm:
            meta.write(new_instance, deepcopy(im, memo=memo))
        ih = hooks.read(self)
        ch = hooks.read(type(self))
        if ih is not ch:
            hooks.write(new_instance, deepcopy(ih, memo=memo))
        for i in self:
            new_instance.append(deepcopy(i, memo=memo))
        return new_instance

    def _marshal(self) -> tuple:
        a = self
        h = hooks.read(a)
        if (h is not None) and (h.before_marshal is not None):
            a = h.before_marshal(a)
        m = meta.read(a)
        a = tuple(
            marshal(
                i,
                types=None if m is None else m.item_types
            ) for i in a
        )
        if (h is not None) and (h.after_marshal is not None):
            a = h.after_marshal(a)
        return a

    def _validate(
        self,
        raise_errors: bool = True
    ) -> List[str]:
        validation_errors = []
        a = self
        h = hooks.read(a)
        if (h is not None) and (h.before_validate is not None):
            a = h.before_validate(a)
        m = meta.read(a)
        if m.item_types is not None:
            for i in a:
                validation_errors.extend(
                    validate(i, m.item_types, raise_errors=False)
                )
        if (h is not None) and (h.after_validate is not None):
            h.after_validate(a)
        if raise_errors and validation_errors:
            raise errors.ValidationError('\n'.join(validation_errors))
        return validation_errors

    @staticmethod
    def _repr_item(item: Any) -> str:
        """
        A string representation of an item in this array which can be used to
        recreate the item
        """
        item_representation = (
            qualified_name(item) if isinstance(item, type) else
            repr(item)
        )
        item_lines = item_representation.split('\n')
        if len(item_lines) > 1:
            item_representation = '\n        '.join(item_lines)
        return '        ' + item_representation + ','

    def __repr__(self):
        """
        A string representation of this array which can be used to recreate the
        array
        """
        instance_meta = meta.read(self)
        class_meta = meta.read(type(self))
        representation_lines = [
            qualified_name(type(self)) + '('
        ]
        if len(self) > 0:
            representation_lines.append('    [')
            for item in self:
                representation_lines.append(
                    self._repr_item(item)
                )
            representation_lines[-1] = representation_lines[-1].rstrip(',')
            representation_lines.append(
                '    ]' + (
                    ','
                    if (
                        instance_meta != class_meta and
                        instance_meta.item_types
                    ) else
                    ''
                )
            )
        if instance_meta != class_meta and instance_meta.item_types:
            representation_lines.append(
                '    item_types=' + indent(repr(instance_meta.item_types))
            )
        representation_lines.append(')')
        if len(representation_lines) > 2:
            representation_lines = '\n'.join(representation_lines)
        else:
            representation_lines = ''.join(representation_lines)
        return representation_lines

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

    def __str__(self):
        return serialize(self)


abc.model.Array.register(Array)


class Dictionary(collections.OrderedDict, Model):
    """
    This can serve as either a base-class for typed (or untyped) dictionaries,
    or can be instantiated directly.

    Parameters:

    - items (list|set|io.IOBase|str|bytes)
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

    _hooks: Optional[hooks.Dictionary]
    _meta: Optional[meta.Dictionary]

    def __init__(
        self,
        items: Optional[Union[Mapping, IO, str, bytes]] = None,
        value_types: Optional[
            Union[
                Sequence[
                    Union[
                        type,
                        properties.Property
                    ]
                ],
                type,
                properties.Property
            ]
        ] = None
    ) -> None:
        self._meta: Optional[meta.Dictionary]
        self._hooks: Optional[hooks.Dictionary]
        Model.__init__(self)
        deserialized_items: Any = self._init_format(items)
        self._init_value_types(deserialized_items, value_types)
        self._init_items(deserialized_items)
        self._init_url(items)
        self._init_pointer()

    def _init_items(
        self,
        items: Optional[Mapping]
    ) -> None:
        if items is None:
            super().__init__()
        else:
            if isinstance(items, (collections.OrderedDict, Dictionary)):
                items = items.items()
            elif isinstance(items, dict):
                items = sorted(
                    items.items(),
                    key=lambda key_value: key_value
                )
            super().__init__(items)

    def _init_value_types(
        self,
        items: Optional[Union[Sequence, Set]],
        value_types: Optional[
            Union[
                Sequence[
                    Union[
                        type,
                        properties.Property
                    ]
                ],
                type,
                properties.Property
            ]
        ]
    ) -> None:
        if value_types is None:
            # If no value types are explicitly attributed, but the initial
            # items are an instance of `Dictionary`, we adopt the item types
            # from that `Array` instance.
            if isinstance(items, Dictionary):
                values_meta = meta.read(items)
                if meta.read(self) is not values_meta:
                    meta.write(self, deepcopy(values_meta))
        else:
            meta.writable(self).value_types = value_types

    def __hash__(self) -> int:
        return id(self)

    def __setitem__(
        self,
        key: int,
        value: Any
    ) -> None:
        instance_hooks: hooks.Dictionary = hooks.read(self)
        if instance_hooks and instance_hooks.before_setitem:
            key, value = instance_hooks.before_setitem(self, key, value)
        instance_meta: Optional[meta.Dictionary] = meta.read(self)
        if instance_meta is None:
            value_types = None
        else:
            value_types = instance_meta.value_types
        try:
            unmarshalled_value = unmarshal(
                value,
                types=value_types
            )
        except TypeError as error:
            message = "\n - %s['%s']: " % (
                qualified_name(type(self)),
                key
            )
            if error.args and isinstance(error.args[0], str):
                error.args = tuple(
                    chain(
                        (message + error.args[0],),
                        error.args[1:]
                    )
                )
            else:
                error.args = (message + repr(value),)
            raise error

        if value is None:
            raise RuntimeError(key)

        super().__setitem__(
            key,
            unmarshalled_value
        )

        if instance_hooks and instance_hooks.after_setitem:
            instance_hooks.after_setitem(self, key, unmarshalled_value)

    def __copy__(self) -> 'Dictionary':
        new_instance = self.__class__()
        im = meta.read(self)
        cm = meta.read(type(self))
        if im is not cm:
            meta.write(new_instance, im)
        ih = hooks.read(self)
        ch = hooks.read(type(self))
        if ih is not ch:
            hooks.write(new_instance, ih)
        for k, v in self.items():
            new_instance[k] = v
        return new_instance

    def __deepcopy__(self, memo: dict = None) -> 'Dictionary':
        new_instance = self.__class__()
        im = meta.read(self)
        cm = meta.read(type(self))
        if im is not cm:
            meta.write(new_instance, deepcopy(im, memo=memo))
        ih = hooks.read(self)
        ch = hooks.read(type(self))
        if ih is not ch:
            hooks.write(new_instance, deepcopy(ih, memo=memo))
        for k, v in self.items():
            new_instance[k] = deepcopy(v, memo=memo)
        return new_instance

    def _marshal(self) -> Dict[str, Any]:
        """
        This method marshals an instance of `Dictionary` as built-in type
        `OrderedDict` which can be serialized into
        JSON/YAML.
        """
        # This variable is needed because before-marshal hooks are permitted to
        # return altered *copies* of `self`, so prior to marshalling--this
        # variable may no longer point to `self`
        data: Union[Dictionary, collections.OrderedDict] = self
        # Check for hooks
        instance_hooks = hooks.read(data)
        # Execute before-marshal hooks, if applicable
        if (instance_hooks is not None) and (
            instance_hooks.before_marshal is not None
        ):
            data = instance_hooks.before_marshal(data)
        # Get the metadata, if any has been assigned
        instance_meta: Optional[meta.Dictionary] = meta.read(data)
        # Check to see if value types are defined in the metadata
        if instance_meta is None:
            value_types = None
        else:
            value_types = instance_meta.value_types
        # Recursively convert the data to generic, serializable, data types
        marshalled_data: Dict[str, Any] = collections.OrderedDict(
            [
                (
                    k,
                    marshal(v, types=value_types)
                ) for k, v in data.items()
            ]
        )
        # Execute after-marshal hooks, if applicable
        if (instance_hooks is not None) and (
            instance_hooks.after_marshal is not None
        ):
            marshalled_data = instance_hooks.after_marshal(
                marshalled_data
            )
        return marshalled_data

    def _validate(self, raise_errors=True) -> List[str]:
        """
        Recursively validate
        """
        validation_errors = []
        d = self
        h = d._hooks or type(d)._hooks
        if (h is not None) and (h.before_validate is not None):
            d = h.before_validate(d)
        m: Optional[meta.Dictionary] = meta.read(d)
        if m is None:
            value_types = None
        else:
            value_types = m.value_types
        if value_types is not None:
            for k, v in d.items():
                value_validation_errors = validate(
                    v, value_types, raise_errors=False
                )
                validation_errors.extend(value_validation_errors)
        if (h is not None) and (h.after_validate is not None):
            h.after_validate(d)
        if raise_errors and validation_errors:
            raise errors.ValidationError('\n'.join(validation_errors))
        return validation_errors

    @staticmethod
    def _repr_item(key: str, value: Any) -> str:
        value_representation = (
            qualified_name(value) if isinstance(value, type) else
            repr(value)
        )
        value_representation_lines = value_representation.split('\n')
        if len(value_representation_lines) > 1:
            indented_lines = [value_representation_lines[0]]
            for line in value_representation_lines[1:]:
                indented_lines.append('            ' + line)
            value_representation = '\n'.join(indented_lines)
            representation = '\n'.join([
                '        (',
                '            %s,' % repr(key),
                '            %s' % value_representation,
                '        ),'
            ])
        else:
            representation = f'        ({repr(key)}, {value_representation}),'
        return representation

    def __repr__(self):
        """
        Return a string representation of this object which can be used to
        re-assemble the object programmatically
        """
        class_meta = meta.read(type(self))
        instance_meta = meta.read(self)

        representation_lines = [
            qualified_name(type(self)) + '('
        ]

        items = tuple(self.items())

        if len(items) > 0:
            representation_lines.append('    [')
            for key, value in items:
                representation_lines.append(self._repr_item(key, value))  # noqa
            # Strip the last comma
            # representation[-1] = representation[-1][:-1]
            representation_lines.append(
                '    ]' + (
                    ','
                    if (
                        instance_meta != class_meta and
                        instance_meta.value_types
                    ) else
                    ''
                )
            )

        if instance_meta != class_meta and instance_meta.value_types:
            representation_lines.append(
                '    value_types=' + indent(repr(instance_meta.value_types)),
            )
        representation_lines.append(')')
        if len(representation_lines) > 2:
            representation = '\n'.join(representation_lines)
        else:
            representation = ''.join(representation_lines)
        return representation

    def __eq__(self, other: Any) -> bool:
        if type(self) is not type(other):
            return False
        keys = tuple(self.keys())
        other_keys = tuple(other.keys())
        if keys != other_keys:
            return False
        for k in keys:
            if self[k] != other[k]:
                return False
        return True

    def __ne__(self, other: Any) -> bool:
        if self == other:
            return False
        else:
            return True

    def __str__(self):
        return serialize(self)


abc.model.Dictionary.register(Dictionary)


def _type_hint_from_property_types(
    property_types: Optional[properties.types.Types]
) -> str:
    type_hint: str = ''
    if property_types is not None:
        if len(property_types) > 1:
            type_hint = 'Union[\n{}\n]'.format(
                ',\n'.join(
                    indent(
                        _type_hint_from_property(item_type),
                        start=0
                    )
                    for item_type in property_types
                )
            )
        else:
            type_hint = _type_hint_from_property(property_types[0])
    return type_hint


def _type_hint_from_type(type_: type) -> str:
    if type_ in (Union, Dict, Any, Sequence, IO):
        type_hint = type_.__name__
    else:
        type_hint = qualified_name(type_)
        # If this class was declared in the same module, we put it in
        # quotes since it won't necessarily have been declared already
        if (
            ('.' not in type_hint)
            and not
            hasattr(builtins, type_hint)
        ):
            if len(type_hint) > 60:
                type_hint_lines: List[str] = ['(']
                for chunk in chunked(type_hint, 57):
                    type_hint_lines.append(
                        f"    '{''.join(chunk)}'"
                    )
                type_hint_lines.append(')')
                type_hint = '\n'.join(type_hint_lines)
            else:
                type_hint = f"'{type_hint}'"
    return type_hint


def _type_hint_from_property(
    property_or_type: Union[properties.Property, type]
) -> str:
    type_hint: str
    if isinstance(property_or_type, type):
        type_hint = _type_hint_from_type(property_or_type)
    elif isinstance(property_or_type, properties.Array):
        item_type_hint: str = _type_hint_from_property_types(
            property_or_type.item_types
        )
        if item_type_hint:
            type_hint = (
                'Sequence[\n'
                f'    {indent(item_type_hint)}\n'
                ']'
            )
        else:
            type_hint = 'Sequence'
    elif isinstance(property_or_type, properties.Dictionary):
        value_type_hint: str = _type_hint_from_property_types(
            property_or_type.item_types
        )
        if value_type_hint:
            type_hint = (
                'Dict[\n'
                '    str,\n'
                f'    {indent(value_type_hint)}\n'
                ']'
            )
        else:
            type_hint = 'dict'
    elif property_or_type and property_or_type.types:
        type_hint = _type_hint_from_property_types(property_or_type.types)
    else:
        type_hint = 'Any'
    return type_hint


def _get_class_declaration(
    name: str,
    superclass: type
) -> str:
    """
    Construct a class declaration
    """
    qualified_superclass_name: str = qualified_name(superclass)
    # If the class declaration line is longer than 79 characters--break it
    # up (attempt to conform to PEP8)
    if 9 + len(name) + len(qualified_superclass_name) <= _LINE_LENGTH:
        class_declaration: str = 'class %s(%s):' % (
            name,
            qualified_superclass_name
        )
    else:
        class_declaration: str = 'class %s(%s\n    %s\n):' % (
            name,
            # If the first line is still too long for PEP8--add a comment to
            # prevent linters from getting hung up
            (
                '  # noqa'
                if len(name) + 7 > _LINE_LENGTH else
                ''
            ),
            qualified_superclass_name
        )
    return class_declaration


def _repr_class_docstring(docstring: str = '') -> str:
    """
    Return a representation of a docstring for use in a class constructor.
    """
    repr_docstring: str = ''
    if docstring:
        repr_docstring = (
            '    """\n'
            '%s\n'
            '    """'
        ) % split_long_docstring_lines(docstring)
    return repr_docstring


def _class_definition_from_meta(
    name: str,
    metadata: meta.Meta,
    docstring: Optional[str] = None
) -> str:
    """
    This returns a `str` defining a model class, as determined by an
    instance of `sob.meta.Meta`.
    """
    repr_docstring: str = _repr_class_docstring(docstring)
    if isinstance(metadata, meta.Dictionary):
        out = [
            _get_class_declaration(
                name,
                Dictionary
            )
        ]
        if repr_docstring is not None:
            out.append(repr_docstring)
        out.append('\n    pass\n\n')
    elif isinstance(metadata, meta.Array):
        out = [
            _get_class_declaration(name, Array)
        ]
        if repr_docstring:
            out.append(repr_docstring)
        out.append('\n    pass\n\n')
    elif isinstance(metadata, meta.Object):
        out = [
            _get_class_declaration(name, Object)
        ]
        if repr_docstring:
            out.append(repr_docstring)
        out += [
            '',
            '    def __init__(',
            '        self,',
            '        _data: Optional[',
            '            Union[str, bytes, dict, Sequence, IO]',
            '        ] = None,'
        ]
        metadata_properties_items: Tuple[
            Tuple[str, abc.properties.Property],
            ...
        ] = tuple(
            metadata.properties.items()
        )
        metadata_properties_items_length: int = len(
            metadata_properties_items
        )
        property_index: int
        name_and_property: Tuple[str, abc.properties.Property]
        for property_index, name_and_property in enumerate(
            metadata_properties_items
        ):
            property_name_: str
            property_: abc.properties.Property
            property_name_, property_ = name_and_property
            repr_comma: str = (
                ''
                if (
                    property_index + 1 ==
                    metadata_properties_items_length
                ) else
                ','
            )
            repr_property_typing: str = indent(
                _type_hint_from_property(property_),
                12
            )
            parameter_declaration: str = (
                f'        {property_name_}: Optional[\n'
                f'            {repr_property_typing}\n'
                f'        ] = None{repr_comma}'
            )
            out.append(parameter_declaration)
        out.append(
            '    ) -> None:'
        )
        for property_name_ in metadata.properties.keys():
            out.append(
                '        self.%s = %s' % (property_name_, property_name_)
            )
        out.append('        super().__init__(_data)\n\n')
    else:
        raise ValueError(metadata)
    return '\n'.join(out)


def from_meta(
    name: str,
    metadata: meta.Meta,
    module: Optional[str] = None,
    docstring: Optional[str] = None
) -> type:
    """
    Constructs an `Object`, `Array`, or `Dictionary` sub-class from an
    instance of `sob.meta.Meta`.

    Parameters:

        - name (str): The name of the class.
        - class_meta ([sob.meta.Meta](#Meta))
        - module (str): Specify the value for the class definition's
          `__module__` property. The invoking module will be
          used if this is not specified (if possible).
        - docstring (str): A docstring to associate with the class definition.
    """
    class_definition: str = _class_definition_from_meta(
        name, metadata, docstring
    )
    namespace: Dict[str, Any] = dict(__name__='from_meta_%s' % name)
    imports = '\n'.join([
        f'import {_parent_module_name}',
        'import numbers',
        'from typing import Union, Dict, Any, Sequence, IO, Optional'
    ])
    source = '%s\n\n\n%s' % (imports, class_definition)
    exec(source, namespace)
    model_class: type = namespace[name]
    model_class._source = source
    # For pickling to work, the __module__ variable needs to be set to the
    # frame where the model class is created. We bypass this step in
    # environments where sys._getframe is not defined or where the user has
    # specified a particular module.
    if module is None:
        try:
            module: Module = getattr(sys, '_getframe')(1).f_globals.get(
                '__name__',
                '__main__'
            )
        except (AttributeError, ValueError):
            pass
    if module is not None:
        model_class.__module__ = module or '__main__'
    model_class._meta = metadata
    return model_class


def _marshal_collection(
    data: Dict[str, Any],
    value_types: Optional[
        Sequence[Union[type, properties.Property, Callable]]
    ] = None,
    item_types: Optional[
        Sequence[Union[type, properties.Property, Callable]]
    ] = None
) -> Union[Dict[str, Any], List[Any]]:
    if isinstance(data, dict):
        return _marshal_dict(
            data,
            value_types
        )
    elif isinstance(data, collections.abc.Sequence):
        return _marshal_sequence(
            data,
            item_types
        )


def _marshal_dict(
    data: Dict[str, Any],
    value_types: Optional[
        Sequence[Union[type, properties.Property, Callable]]
    ] = None
) -> Dict[str, Any]:
    key: str
    value: Any
    marshalled_data: Dict[str, Any] = copy(data)
    for key, value in marshalled_data.items():
        marshalled_data[key] = marshal(value, value_types=value_types)
    return marshalled_data


def _marshal_sequence(
    data: Sequence[Any],
    item_types: Optional[
        Sequence[Union[type, properties.Property, Callable]]
    ] = None
) -> List[str]:
    index: int
    value: Any
    marshalled_data: List[str] = list(data)
    for index, value in enumerate(marshalled_data):
        marshalled_data[index] = marshal(value, item_types=item_types)
    return marshalled_data


def _marshal_typed(
    data: Any,
    types: Sequence[Union[type, properties.Property]] = None
) -> Any:
    """
    This attempts to initialize the provided type(s) with `data`, and accepts
    the first which does not raise an error
    """
    # For each potential type, attempt to marshal the data, and accept the
    # first result which does not throw an error
    marshalled_data: Any = UNDEFINED
    for type_ in types:
        if isinstance(type_, properties.Property):
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
            '%s cannot be interpreted as any of the designated types: %s' %
            (
                repr(data),
                repr(types)
            )
        )
    return marshalled_data


def marshal(
    data: Any,
    types: Optional[
        Sequence[Union[type, properties.Property, Callable]]
    ] = None,
    value_types: Optional[Sequence[Union[type, properties.Property]]] = None,
    item_types: Optional[Sequence[Union[type, properties.Property]]] = None,
) -> Any:
    """
    Recursively converts data which is not serializable using the `json` module
    into formats which *can* be represented as JSON.
    """
    marshalled_data: Any = data
    if data is None:
        # Don't do anything with `None`--this just means an attributes is not
        # used for this instance (an explicit `null` would be passed as
        # `sob.properties.types.NULL`).
        pass
    elif isinstance(data, abc.model.Model):
        marshalled_data = getattr(data, '_marshal')()
    elif types is not None:
        marshalled_data = _marshal_typed(data, types)
    elif isinstance(data, Decimal):
        # Instances of `decimal.Decimal` can'ts be serialized as JSON, so we
        # convert them to `float`
        marshalled_data = float(data)
    elif isinstance(data, (date, datetime)):
        marshalled_data = data.isoformat()
    elif isinstance(data, str):
        marshalled_data = data
    elif isinstance(data, (bytes, bytearray)):
        # Convert `bytes` to base-64 encoded strings
        marshalled_data = str(b64encode(data), 'ascii')
    elif isinstance(
        data,
        (
            dict, set,
            collections.abc.Sequence
        )
    ):
        marshalled_data = _marshal_collection(
            data,
            value_types=value_types,
            item_types=item_types
        )
    elif hasattr(data, '__bytes__'):
        # Convert objects which can be *cast* as `bytes` to
        # base-64 encoded strings
        marshalled_data = str(b64encode(bytes(data)), 'ascii')
    return marshalled_data


def _is_non_string_sequence_or_set_instance(value: Any) -> bool:
    return (
        isinstance(
            value,
            (collections.abc.Set, collections.abc.Sequence)
        )
    ) and (
        not isinstance(value, (str, bytes))
    )


def _is_non_string_sequence_or_set_subclass(type_: type) -> bool:
    return (
        issubclass(
            type_,
            (collections.abc.Set, collections.abc.Sequence)
        )
    ) and (
        not issubclass(type_, (str, bytes))
    )


class _Unmarshal:
    """
    This class should be used exclusively by wrapper function `unmarshal`.
    """

    def __init__(
        self,
        data: Any,
        types: Optional[Sequence[Union[type, properties.Property]]] = None,
        value_types: Optional[
            Sequence[Union[type, properties.Property]]
        ] = None,
        item_types: Optional[Sequence[Union[type, properties.Property]]] = None
    ) -> None:
        # Verify that the data can be parsed before attempting to un-marshalls
        if not isinstance(
            data,
            _UNMARSHALLABLE_TYPES
        ):
            raise errors.UnmarshalTypeError(
                '%s, an instance of `%s`, cannot be un-marshalled. ' % (
                    repr(data), type(data).__name__
                ) +
                'Acceptable types are: ' + ', '.join((
                    qualified_name(data_type)
                    for data_type in _UNMARSHALLABLE_TYPES
                ))
            )
        # If only one type was passed for any of the following parameters--we
        # convert it to a tuple
        if types is not None:
            if not isinstance(types, collections.abc.Sequence):
                types = (types,)
        if value_types is not None:
            if not isinstance(value_types, collections.abc.Sequence):
                value_types = (value_types,)
        if item_types is not None:
            if not isinstance(item_types, collections.abc.Sequence):
                item_types = (item_types,)
        # Instance Attributes
        self.data: Any = data
        self.types: Optional[
            Sequence[Union[type, properties.Property]]
        ] = types
        self.value_types: Optional[
            Sequence[Union[type, properties.Property]]
        ] = value_types
        self.item_types: Optional[
            Sequence[Union[type, properties.Property]]
        ] = item_types
        self.meta: Optional[meta.Meta] = None

    def __call__(self) -> Any:
        """
        Return `self.data` unmarshalled
        """
        unmarshalled_data: Optional[
            Union[
                abc.model.Model,
                Number,
                str, bytes,
                date, datetime,
                tuple
            ]
        ] = self.data
        if (
            (self.data is not None) and
            (self.data is not NULL)
        ):
            # If the data is a sob `Model`, get it's metadata
            if isinstance(self.data, abc.model.Model):
                self.meta = meta.read(self.data)
            # Only un-marshall models if they have no metadata yet (are
            # generic)
            if self.meta is None:
                # If the data provided is a `Generator`, make it static by
                # casting the data into a tuple
                if isinstance(self.data, Generator):
                    self.data = tuple(self.data)
                if self.types is None:
                    # If no types are provided, we unmarshal the data into one
                    # of sob's generic container types
                    unmarshalled_data = self.as_container_or_simple_type
                else:
                    unmarshalled_data = self.as_typed
        return unmarshalled_data

    @property
    def as_container_or_simple_type(self) -> Any:
        """
        This function unmarshalls and returns the data into one of sob's
        container types, or if the data is of a simple data type--it returns
        that data unmodified
        """
        unmarshalled_data = self.data
        if isinstance(self.data, abc.model.Dictionary):
            type_ = type(self.data)
            if self.value_types is not None:
                unmarshalled_data = type_(
                    self.data, value_types=self.value_types
                )
        elif isinstance(self.data, abc.model.Array):
            type_ = type(self.data)
            if self.item_types is not None:
                unmarshalled_data = type_(
                    self.data, item_types=self.item_types
                )
        elif isinstance(self.data, (dict, collections.OrderedDict)):
            unmarshalled_data = Dictionary(
                self.data,
                value_types=self.value_types
            )
        elif _is_non_string_sequence_or_set_instance(self.data):
            unmarshalled_data = Array(
                self.data,
                item_types=self.item_types
            )
        elif not isinstance(
            self.data,
            (
                str, bytes,
                Number, Decimal,
                date, datetime,
                bool,
                abc.model.Model
            )
        ):
            raise errors.UnmarshalValueError(
                '%s cannot be un-marshalled' % repr(self.data)
            )
        return unmarshalled_data

    @property
    def as_typed(self) -> abc.model.Model:
        unmarshalled_data: Union[
            abc.model.Model,
            Number,
            str, bytes,
            date, datetime,
            Undefined
        ] = UNDEFINED
        first_error: Optional[Exception] = None
        first_error_message: Optional[str] = None
        # Attempt to un-marshal the data as each type, in the order
        # provided
        for type_ in self.types:
            try:
                unmarshalled_data = self.as_type(type_)
                # If the data is un-marshalled successfully, we do
                # not need to try any further types
                break
            except (
                AttributeError, KeyError, TypeError, ValueError
            ) as error:
                if first_error is None:
                    first_error = error
                    first_error_message = errors.get_exception_text()
        if unmarshalled_data is UNDEFINED:
            if (
                first_error is None
            ) or isinstance(
                first_error, TypeError
            ):
                raise errors.UnmarshalTypeError(
                    first_error_message,
                    data=self.data,
                    types=self.types,
                    value_types=self.value_types,
                    item_types=self.item_types
                )
            elif isinstance(
                first_error,
                ValueError
            ):
                raise errors.UnmarshalValueError(
                    first_error_message,
                    data=self.data,
                    types=self.types,
                    value_types=self.value_types,
                    item_types=self.item_types
                )
            else:
                raise first_error
        return unmarshalled_data

    def get_dictionary_type(self, dictionary_type: type) -> type:
        """
        Get the dictionary type to use
        """
        if dictionary_type is abc.model.Dictionary:
            dictionary_type = Dictionary
        elif issubclass(dictionary_type, abc.model.Object):
            dictionary_type = None
        elif issubclass(
            dictionary_type,
            abc.model.Dictionary
        ):
            pass
        elif issubclass(
            dictionary_type,
            (dict, collections.OrderedDict)
        ):
            dictionary_type = Dictionary
        else:
            raise TypeError(self.data)
        return dictionary_type

    def before_hook(self, type_: Any) -> Any:
        data = self.data
        hooks_ = hooks.read(type_)
        if hooks_ is not None:
            before_unmarshal_hook = hooks_.before_unmarshal
            if before_unmarshal_hook is not None:
                data = before_unmarshal_hook(deepcopy(data))
        return data

    def after_hook(self, type_: Any, data: Any) -> Any:
        hooks_ = hooks.read(type_)
        if hooks_ is not None:
            after_unmarshal_hook = hooks_.after_unmarshal
            if after_unmarshal_hook is not None:
                data = after_unmarshal_hook(data)
        return data

    def as_dictionary_type(
        self,
        type_: type
    ) -> Union[dict, Dict, abc.model.Model]:
        dictionary_type = self.get_dictionary_type(type_)
        # Determine whether the `type_` is an `Object` or a `Dictionary`
        if dictionary_type is None:
            data = self.before_hook(type_)
            unmarshalled_data = type_(data)
            unmarshalled_data = self.after_hook(type_, unmarshalled_data)
        else:
            type_ = dictionary_type
            data = self.before_hook(type_)
            unmarshalled_data = type_(data, value_types=self.value_types)
            unmarshalled_data = self.after_hook(type_, unmarshalled_data)
        return unmarshalled_data

    def get_array_type(self, type_: type) -> type:
        if type_ is abc.model.Array:
            type_ = Array
        elif issubclass(type_, abc.model.Array):
            pass
        elif _is_non_string_sequence_or_set_subclass(type_):
            type_ = Array
        else:
            raise TypeError(
                '%s is not of type `%s`' % (
                    repr(self.data),
                    repr(type_)
                )
            )
        return type_

    def as_array_type(
        self,
        type_: type
    ) -> 'Array':
        type_ = self.get_array_type(type_)
        unmarshalled_data = type_(self.data, item_types=self.item_types)
        return unmarshalled_data

    def as_type(
        self,
        type_: Union[type, properties.Property],
    ) -> Any:
        unmarshalled_data: Optional[Union[
            abc.model.Model, Number, str, bytes, date, datetime
        ]] = None
        if isinstance(
            type_,
            properties.Property
        ):
            unmarshalled_data = _unmarshal_property_value(type_, self.data)
        elif isinstance(type_, type):
            if isinstance(
                self.data,
                (dict, collections.OrderedDict, abc.model.Model)
            ):
                unmarshalled_data = self.as_dictionary_type(type_)
            elif (
                _is_non_string_sequence_or_set_instance(self.data)
            ):
                unmarshalled_data = self.as_array_type(type_)
            elif isinstance(self.data, type_):
                if isinstance(self.data, Decimal):
                    unmarshalled_data = float(self.data)
                else:
                    unmarshalled_data = self.data
            else:
                raise TypeError(self.data)
        return unmarshalled_data


def unmarshal(
    data: Any,
    types: Optional[
        Union[
            Sequence[
                Union[type, properties.Property]
            ],
            type,
            properties.Property
        ]
    ] = None,
    value_types: Optional[
        Union[
            Sequence[
                Union[type, properties.Property]
            ],
            type,
            properties.Property
        ]
    ] = None,
    item_types: Optional[
        Union[
            Sequence[
                Union[type, properties.Property]
            ],
            type,
            properties.Property
        ]
    ] = None
) -> Optional[Union[abc.model.Model, str, Number, date, datetime]]:
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
        data,
        types=types,
        value_types=value_types,
        item_types=item_types
    )()


def serialize(
    data: Union[abc.model.Model, str, Number],
    format_: str = 'json'
) -> str:
    """
    Serializes instances of `Object` as JSON or YAML.
    """
    instance_hooks = None
    if isinstance(data, abc.model.Model):
        instance_hooks = hooks.read(data)
        if (instance_hooks is not None) and (
            instance_hooks.before_serialize is not None
        ):
            data = instance_hooks.before_serialize(data)
    if format_ not in ('json', 'yaml'):
        format_ = format_.lower()
        if format_ not in ('json', 'yaml'):
            raise ValueError(
                'Supported `sob.model.serialize()` `format_` argument values '
                f'include "json" and "yaml" (not "{format_}").'
            )
    if format_ == 'json':
        data = json.dumps(marshal(data))
    elif format_ == 'yaml':
        data = yaml.dump(marshal(data))
    if (
        instance_hooks is not None
    ) and (
        instance_hooks.after_serialize is not None
    ):
        data = instance_hooks.after_serialize(data)
    return data


def deserialize(
    data: Optional[Union[str, IOBase, addbase]],
    format_: str
) -> Any:
    """
    Parameters:

        - data (str|io.IOBase|io.addbase): This can be a string or file-like
          object containing JSON or YAML serialized information.

        - format_ (str): "json" or "yaml"

    Returns:

        A deserialized representation of the information you provided.
    """
    if format_ not in ('json', 'yaml'):
        raise NotImplementedError(
            'Deserialization of data in the format %s is not currently '
            'supported.' % repr(format_)
        )
    if not isinstance(data, (str, bytes)):
        data = read(data)
    if isinstance(data, bytes):
        data = str(data, encoding='utf-8')
    if isinstance(data, str):
        if format_ == 'json':
            data = json.loads(
                data,
                object_hook=collections.OrderedDict,
                object_pairs_hook=collections.OrderedDict
            )
        elif format_ == 'yaml':
            data = yaml.load(data, yaml.FullLoader)
    return data


def detect_format(
    data: Optional[Union[str, IOBase, addbase]]
) -> Tuple[Any, Optional[str]]:
    """
    This function accepts a string or file-like object and returns a tuple
    containing the deserialized information and a string indicating the format
    of that information.

    Parameters:

    - data (str|io.IOBase|io.addbase): A string or file-like object containing
      JSON or YAML serialized data.

    Returns (tuple):

    - The deserialized (but not unmarshalled) `data`
    - "json" or "yaml"
    """
    string_data: str
    if isinstance(data, str):
        string_data = data
    else:
        try:
            string_data = read(data)
        except TypeError:
            return data, None
    formats = ('json', 'yaml')
    format_ = None
    deserialized_data: Any = string_data
    for potential_format in formats:
        try:
            deserialized_data = deserialize(string_data, potential_format)
            format_ = potential_format
            break
        except (ValueError, yaml.YAMLError):
            pass
    if format_ is None:
        raise ValueError(
            'The data provided could not be parsed:\n' + repr(data)
        )
    return deserialized_data, format_


def _call_validate_method(
    data: Optional[abc.model.Model]
) -> Iterable[str]:
    error_messages: Set[str] = set()
    if '_validate' in dir(data):
        validate_method = getattr(data, '_validate')
        if callable(validate_method):
            error_message: str
            for error_message in validate_method(raise_errors=False):
                if error_message not in error_messages:
                    yield error_message
                    error_messages.add(error_message)


def _validate_typed(
    data: Optional[abc.model.Model],
    types: Optional[
        Union[type, properties.Property, Object, Callable]
    ] = None,
    raise_errors: bool = True
) -> Sequence[str]:
    valid = False
    for type_ in types:
        if isinstance(type_, type) and isinstance(data, type_):
            valid = True
            break
        elif isinstance(type_, properties.Property):
            if type_.types is None:
                valid = True
                break
            try:
                validate(data, type_.types, raise_errors=True)
                valid = True
                break
            except errors.ValidationError:
                pass
    if not valid:
        error_message = (
            'Invalid data:\n\n%s\n\n'
            'The data must be one of the following types:\n\n%s' % (
                '\n'.join(
                    '  ' + line
                    for line in repr(data).split('\n')
                ),
                '\n'.join(chain(
                    ('  (',),
                    (
                        '    %s,' % '\n'.join(
                            '    ' + line
                            for line in repr(type_).split('\n')
                        ).strip()
                        for type_ in types
                    ),
                    ('  )',)
                ))
            )
        )

def validate(
    data: Optional[abc.model.Model],
    types: Optional[
        Union[type, properties.Property, Object, Callable]
    ] = None,
    raise_errors: bool = True
) -> Sequence[str]:
    """
    This function verifies that all properties/items/values in an instance of
    `sob.abc.model.Model` are of the correct data type(s), and that all
    required attributes are present (if applicable). If `raise_errors` is
    `True` (this is the default)--violations will result in a validation error.
    If `raise_errors` is `False`--a list of error messages will be returned if
    invalid/missing information is found, or an empty list otherwise.
    """
    if isinstance(data, Generator):
        data = tuple(data)
    error_messages = []
    error_message: Optional[str] = None
    if types is not None:
        pass
    if error_message is not None:
        if (not error_messages) or (error_message not in error_messages):
            error_messages.append(error_message)
    for error_message in _call_validate_method(data):
        error_messages.append(error_message)
    if raise_errors and error_messages:
        # If there is no top-level error message, include a representation of
        # the top-level data element
        if error_message not in error_messages:
            error_messages.insert(
                0,
                f'\n{repr(data)}'
            )
        raise errors.ValidationError('\n' + '\n\n'.join(error_messages))
    return error_messages


class _UnmarshalProperty:
    """
    This is exclusively for use by wrapper function
    `_unmarshal_property_value`.
    """

    def __init__(
        self,
        property: properties.Property
    ) -> None:
        self.property = property

    def validate_enumerated(self, value: Any) -> Any:
        """
        Verify that a value is one of the enumerated options
        """
        if (
            (value is not None) and
            isinstance(self.property, properties.Enumerated) and
            (self.property.values is not None) and
            (value not in self.property.values)
        ):
            raise ValueError(
                'The value provided is not a valid option:\n{}\n\n'
                'Valid options include:\n{}'.format(
                    repr(value),
                    ', '.join(
                        repr(enumerated_value)
                        for enumerated_value in self.property.values
                    )
                )
            )

    def parse_date(self, value: Optional[str]) -> Union[
        date,
        properties.types.NoneType
    ]:
        if value is None:
            return value
        else:
            if isinstance(value, date):
                date_ = value
            elif isinstance(value, str):
                date_ = self.property.str2date(value)
            else:
                raise TypeError(
                    '%s is not a `str`.' % repr(value)
                )
            if isinstance(date_, date):
                return date_
            else:
                raise TypeError(
                    '"%s" is not a properly formatted date string.' % value
                )

    def parse_datetime(
        self,
        value: Optional[str]
    ) -> Union[datetime, properties.types.NoneType]:
        if value is None:
            return value
        else:
            if isinstance(value, datetime):
                datetime_ = value
            elif isinstance(value, str):
                datetime_ = self.property.str2datetime(value)
            else:
                raise TypeError(
                    '%s is not a `str`.' % repr(value)
                )
            if isinstance(datetime_, datetime):
                return datetime_
            else:
                raise TypeError(
                    f'"{value}" is not a properly formatted date-time string.'
                )

    @staticmethod
    def parse_bytes(
        data: Union[str, bytes]
    ) -> Optional[bytes]:
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
                '`data` must be a base64 encoded `str` or `bytes`--not '
                f'`{qualified_name(type(data))}`'
            )
        return unmarshalled_data

    def __call__(self, value: Any) -> Any:
        unmarshalled_value: Any = value
        if isinstance(self.property, properties.Date):
            unmarshalled_value = self.parse_date(value)
        elif isinstance(self.property, properties.DateTime):
            unmarshalled_value = self.parse_datetime(value)
        elif isinstance(self.property, properties.Bytes):
            unmarshalled_value = self.parse_bytes(value)
        elif isinstance(self.property, properties.Array):
            unmarshalled_value = unmarshal(
                value,
                types=self.property.types,
                item_types=self.property.item_types
            )
        elif isinstance(self.property, properties.Dictionary):
            unmarshalled_value = unmarshal(
                value,
                types=self.property.types,
                value_types=self.property.value_types
            )
        else:
            if isinstance(self.property, properties.Enumerated):
                self.validate_enumerated(value)
            elif isinstance(
                value,
                collections.abc.Iterable
            ) and not isinstance(
                value,
                (str, bytes, bytearray)
            ) and not isinstance(
                value,
                abc.model.Model
            ):
                if isinstance(value, (dict, collections.OrderedDict)):
                    unmarshalled_value = copy(value)
                    for key, item_value in value.items():
                        if item_value is None:
                            unmarshalled_value[key] = NULL
                else:
                    unmarshalled_value = tuple(
                        (
                            properties.types.NULL
                            if item_value is None else
                            item_value
                        )
                        for item_value in value
                    )
            if self.property.types is not None:
                unmarshalled_value = unmarshal(
                    unmarshalled_value,
                    types=self.property.types
                )
        return unmarshalled_value


def _unmarshal_property_value(
    property: properties.Property,
    value: Any
) -> Any:
    """
    Unmarshal a property value
    """
    return _UnmarshalProperty(property)(value)


class _MarshalProperty:
    """
    This is exclusively for use by wrapper function `_marshal_property_value`.
    """

    def __init__(
        self,
        property_: properties.Property
    ) -> None:
        self.property = property_

    def parse_date(self, value: Optional[date]) -> Optional[str]:
        if value is not None:
            value = self.property.date2str(value)
            if not isinstance(value, str):
                raise TypeError(
                    'The date2str function should return a `str`, not a '
                    '`%s`: %s' % (
                        type(value).__name__,
                        repr(value)
                    )
                )
        return value

    def parse_datetime(self, value: Optional[datetime]) -> Optional[str]:
        if value is not None:
            datetime_string = self.property.datetime2str(value)
            if not isinstance(datetime_string, str):
                repr_datetime_string = repr(datetime_string).strip()
                raise TypeError(
                    'The datetime2str function should return a `str`, not:' + (
                        '\n'
                        if '\n' in repr_datetime_string else
                        ' '
                    ) + repr_datetime_string
                )
            value = datetime_string
        return value

    def parse_bytes(self, value: bytes) -> str:
        """
        Marshal bytes into a base-64 encoded string
        """
        if (value is None) or isinstance(value, str):
            return value
        elif isinstance(value, bytes):
            return str(b64encode(value), 'ascii')
        else:
            raise TypeError(
                '`data` must be a base64 encoded `str` or `bytes`--not `%s`' %
                qualified_name(type(value))
            )

    def __call__(self, value: Any) -> Any:
        if isinstance(self.property, properties.Date):
            value = self.parse_date(value)
        elif isinstance(self.property, properties.DateTime):
            value = self.parse_datetime(value)
        elif isinstance(self.property, properties.Bytes):
            value = self.parse_bytes(value)
        elif isinstance(self.property, properties.Array):
            value = marshal(
                value,
                types=self.property.types,
                item_types=self.property.item_types
            )
        elif isinstance(self.property, properties.Dictionary):
            value = marshal(
                value,
                types=self.property.types,
                value_types=self.property.value_types
            )
        else:
            value = marshal(value, types=self.property.types)
        return value


def _marshal_property_value(property_: properties.Property, value: Any) -> Any:
    """
    Marshal a property value
    """
    return _MarshalProperty(property_)(value)


def _replace_object_nulls(
    object_instance: abc.model.Object,
    replacement_value: Any = None
):
    property_name: str
    value: Any
    for property_name, value in utilities.inspect.properties_values(
        object_instance
    ):
        if value is NULL:
            setattr(object_instance, property_name, replacement_value)
        elif isinstance(value, Model):
            replace_nulls(value, replacement_value)


def _replace_array_nulls(
    array_instance: abc.model.Array,
    replacement_value: Any = None
) -> None:
    for index, value in enumerate(array_instance):
        if value is NULL:
            array_instance[index] = replacement_value
        elif isinstance(value, Model):
            replace_nulls(value, replacement_value)


def _replace_dictionary_nulls(
    dictionary_instance: abc.model.Dictionary,
    replacement_value: Any = None
) -> None:
    for key, value in dictionary_instance.items():
        if value is NULL:
            dictionary_instance[key] = replacement_value
        elif isinstance(replacement_value, Model):
            replace_nulls(value, replacement_value)


def replace_nulls(
    model_instance: abc.model.Model,
    replacement_value: Any = None
) -> None:
    """
    This function replaces all instances of `sob.properties.types.NULL`.

    Parameters:

    - model_instance (sob.model.Model)
    - replacement_value (typing.Any):
      The value with which nulls will be replaced. This defaults to `None`.
    """
    if isinstance(model_instance, Object):
        _replace_object_nulls(model_instance, replacement_value)
    elif isinstance(model_instance, Array):
        _replace_array_nulls(model_instance, replacement_value)
    elif isinstance(model_instance, Dictionary):
        _replace_dictionary_nulls(model_instance, replacement_value)
