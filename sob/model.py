"""
This module defines the building blocks of an `sob` based data model.
"""
from __future__ import (
    nested_scopes, generators, division, absolute_import, with_statement,
    print_function, unicode_literals
)
from .utilities import compatibility
# Built-In Imports
import re
import sys
import json
import collections
from future.utils import native_str
from copy import deepcopy
from io import IOBase
from decimal import Decimal
from base64 import b64encode, b64decode
from numbers import Number
from datetime import date, datetime
from itertools import chain
# 3rd-Party Maintained Imports
import yaml
# Relative Imports
from .utilities import qualified_name, get_io_url, read, indent
from . import (
    properties, meta, errors, hooks, abc, __name__ as _parent_module_name
)
# (
#     collections, Generator, BACKWARDS_COMPATIBILITY_IMPORTS,
#     typing, urljoin, collections_abc, include_native_str
# )

compatibility.backport()

Union = compatibility.typing.Union
Dict = compatibility.typing.Dict
Any = compatibility.typing.Any
AnyStr = compatibility.typing.AnyStr
IO = compatibility.typing.IO
Sequence = compatibility.typing.Sequence
Mapping = compatibility.typing.Mapping
Callable = compatibility.typing.Callable
Tuple = compatibility.typing.Tuple
Optional = compatibility.typing.Optional
Generator = compatibility.Generator
BACKWARDS_COMPATIBILITY_IMPORTS = compatibility.BACKWARDS_COMPATIBILITY_IMPORTS
urljoin = compatibility.urljoin
collections_abc = compatibility.collections_abc
include_native_str = compatibility.include_native_str

# Constants
_UNMARSHALLABLE_TYPES = tuple(
    set(properties.types.TYPES) | {properties.types.NoneType}
)
# region Model Classes


class Model(object):

    pass


abc.model.Model.register(Model)


class Object(Model):

    _format = None  # type: Optional[str]
    _meta = None  # type: Optional[meta.Object]
    _hooks = None  # type: Optional[hooks.Object]

    def __init__(
        self,
        _data=None,  # type: Optional[Union[str, bytes, dict, Sequence, IO]]
    ):
        # type: (...) -> None
        self._meta = None  # type: Optional[meta.Object]
        self._hooks = None  # type: Optional[hooks.Object]
        self._url = None  # type: Optional[str]
        self._xpath = None  # type: Optional[str]
        self._pointer = None  # type: Optional[str]
        if _data is not None:
            self._data_init(_data)

    def _data_init(self, _data):
        # type: (Union[str, bytes, dict, Sequence, IO]) -> None
        if isinstance(_data, Object):
            self._copy_init(_data)
        else:
            url = None
            if isinstance(_data, IOBase):
                url = get_io_url(_data)
            _data, format_ = detect_format(_data)
            if isinstance(_data, dict):
                self._dict_init(_data)
            else:
                raise TypeError(
                    'The `_data` parameter must be a string, file-like object, or dictionary, not `%s`' %
                    repr(_data)
                )
            meta.format_(self, format_)
            meta.url(self, url)
            meta.pointer(self, '#')
            meta.xpath(self, '')

    def _dict_init(self, dictionary):
        # type: (dict) -> None
        """
        Initialize this object from a dictionary
        """
        for property_name, value in dictionary.items():
            if value is None:
                value = properties.NULL
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

    def _copy_init(self, other):
        # type: (Object) -> None
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
                label = '\n - %s.%s: ' % (qualified_name(type(self)), property_name)
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
        meta.xpath(self, meta.xpath(other))
        meta.format_(self, meta.format_(other))

    def __hash__(self):
        # type (...) -> None
        """
        Make this usable in contexts requiring a hashable object
        """
        return id(self)

    def _get_property_definition(self, property_name):
        # type: (str) -> Property
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

    def _unmarshal_value(self, property_name, value):
        # type: (str, Any) -> Any
        """
        Unmarshall a property value
        """
        property_definition = self._get_property_definition(property_name)

        if value is not None:
            if isinstance(value, Generator):
                value = tuple(value)
            try:
                value = unmarshal_property_value(property_definition, value)
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

    def __setattr__(self, property_name, value):
        # type: (Object, str, Any) -> None
        instance_hooks = None
        unmarshalled_value = value

        if property_name[0] != '_':
            instance_hooks = hooks.read(self)  # type: hooks.Object
            if instance_hooks and instance_hooks.before_setattr:
                property_name, value = instance_hooks.before_setattr(self, property_name, value)
            unmarshalled_value = self._unmarshal_value(property_name, value)

        if instance_hooks and instance_hooks.after_setattr:
            instance_hooks.after_setattr(self, property_name, value)

        super().__setattr__(property_name, unmarshalled_value)

    def _get_key_property_name(self, key):
        # type: (str) -> str
        instance_meta = meta.read(self)
        if (key in instance_meta.properties) and (
            instance_meta.properties[key].name in (None, )
        ):
            property_name = key
        else:
            property_name = None
            for potential_property_name, property in instance_meta.properties.items():
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

    def __setitem__(self, key, value):
        # type: (str, Any) -> None
        # Before set-item hooks
        hooks_ = hooks.read(self)  # type: hooks.Object
        if hooks_ and hooks_.before_setitem:
            key, value = hooks_.before_setitem(self, key, value)
        # Get the corresponding property name
        property_name = self._get_key_property_name(key)
        # Set the attribute value
        setattr(self, property_name, value)
        # After set-item hooks
        if hooks_ and hooks_.after_setitem:
            hooks_.after_setitem(self, key, value)

    def __delattr__(self, key):
        # type: (str) -> None
        """
        Deleting attributes with defined metadata is not allowed--doing this is instead interpreted as setting that
        attribute to `None`
        """
        instance_meta = meta.read(self)
        if key in instance_meta.properties:
            setattr(self, key, None)
        else:
            super().__delattr__(key)

    def __getitem__(self, key):
        # type: (str, Any) -> None
        """
        Retrieve a value using the item assignment operators `[]`
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

    def __copy__(self):
        # type: () -> Object
        return self.__class__(self)

    def _deepcopy_property(self, property_name, other, memo):
        # type: (Object, str, dict) -> None
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

    def __deepcopy__(self, memo):
        # type: (Optional[dict]) -> Object

        # Perform a regular copy operation
        new_instance = self.__copy__()

        # Retrieve the metadata
        meta_ = meta.read(self)

        # If there is metadata--copy it recursively
        if meta_ is not None:
            for property_name in meta_.properties.keys():
                self._deepcopy_property(property_name, new_instance, memo)

        return new_instance

    def _marshal(self):
        # type: (...) -> collections.OrderedDict
        object_ = self
        instance_hooks = hooks.read(object_)
        if (instance_hooks is not None) and (instance_hooks.before_marshal is not None):
            object_ = instance_hooks.before_marshal(object_)
        data = collections.OrderedDict()
        instance_meta = meta.read(object_)
        for property_name, property in instance_meta.properties.items():
            value = getattr(object_, property_name)
            if value is not None:
                key = property.name or property_name
                data[key] = marshal_property_value(property, value)
        if (instance_hooks is not None) and (instance_hooks.after_marshal is not None):
            data = instance_hooks.after_marshal(data)
        return data

    def __str__(self):
        # type: (...) -> str
        return serialize(self)

    @staticmethod
    def _repr_argument(parameter, value):
        # type: (str, Any) -> str
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

    def __repr__(self):
        # type: (...) -> str
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

    def __eq__(self, other):
        # type: (Any) -> bool
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

    def __ne__(self, other):
        # type: (Any) -> bool
        return False if self == other else True

    def __iter__(self):
        instance_meta = meta.read(self)
        for property_name, property in instance_meta.properties.items():
            yield property.name or property_name

    def _validate(self, raise_errors=True):
        # type: (bool) -> None

        validation_errors = []
        object_ = self

        instance_hooks = hooks.read(self)

        if (instance_hooks is not None) and (instance_hooks.before_validate is not None):
            object_ = instance_hooks.before_validate(object_)

        instance_meta = meta.read(object_)

        for property_name, property in instance_meta.properties.items():

            value = getattr(object_, property_name)

            if value is None:

                if callable(property.required):
                    required = property.required(object_)
                else:
                    required = property.required

                if required:

                    validation_errors.append(
                        'The property `%s` is required for `%s`:\n%s' % (
                            property_name,
                            qualified_name(type(object_)),
                            str(object_)
                        )
                    )
            else:

                if value is properties.NULL:

                    types = property.types

                    if callable(types):
                        types = types(value)

                    if types is not None:
                        types = include_native_str(types)
                        if properties.Null not in types:
                            validation_errors.append(
                                'Null values are not allowed in `%s.%s`, ' % (
                                    qualified_name(type(object_)), property_name
                                ) +
                                'permitted types include: %s.' % ', '.join(
                                    '`%s`' % qualified_name(type_) for type_ in types
                                )
                            )
                else:

                    try:
                        value_validation_error_messages = validate(value, property.types, raise_errors=False)

                        if value_validation_error_messages:

                            index = 0

                            for error_message in value_validation_error_messages:
                                value_validation_error_messages[index] = (
                                    'Error encountered ' +
                                    'while attempting to validate property `%s`:\n\n' % property_name +
                                    error_message
                                )

                            validation_errors.extend(value_validation_error_messages)

                    except errors.ValidationError as error:

                        message = '%s.%s:\n' % (qualified_name(type(object_)), property_name)

                        if error.args:
                            error.args = tuple(chain(
                                (error.args[0] + message,),
                                error.args[1:]
                            ))
                        else:
                            error.args = (
                                message,
                            )

        if (instance_hooks is not None) and (instance_hooks.after_validate is not None):
            instance_hooks.after_validate(object_)
        if raise_errors and validation_errors:
            raise errors.ValidationError('\n'.join(validation_errors))
        return validation_errors


abc.model.Object.register(Object)


class Array(list, Model):

    _format = None  # type: Optional[str]
    _hooks = None  # type: Optional[hooks.Array]
    _meta = None  # type: Optional[meta.Array]

    def __init__(
        self,
        items=None,  # type: Optional[Union[Sequence, Set]]
        item_types=(
            None
        ),  # type: Optional[Union[Sequence[Union[type, properties.Property]], type, properties.Property]]
    ):
        self._meta = None  # type: Optional[meta.Array]
        self._hooks = None  # type: Optional[hooks.Array]
        self._url = None  # type: Optional[str]
        self._xpath = None  # type: Optional[str]
        self._pointer = None  # type: Optional[str]

        url = None

        if isinstance(items, IOBase):
            if hasattr(items, 'url'):
                url = items.url
            elif hasattr(items, 'name'):
                url = urljoin('file:', items.name)
        items, format_ = detect_format(items)
        if item_types is None:
            if isinstance(items, Array):
                m = meta.read(items)
                if meta.read(self) is not m:
                    meta.write(self, deepcopy(m))
        else:
            meta.writable(self).item_types = item_types
        if items is not None:
            for item in items:
                self.append(item)
            if meta.pointer(self) is None:
                meta.pointer(self, '#')
            if meta.xpath(self) is None:
                meta.xpath(self, '')
        if url is not None:
            meta.url(self, url)
        if format_ is not None:
            meta.format_(self, format_)

    def _copy_init(self, other):
        pass

    def __hash__(self):
        return id(self)

    def __setitem__(
        self,
        index,  # type: int
        value,  # type: Any
    ):
        instance_hooks = hooks.read(self)  # type: hooks.Object

        if instance_hooks and instance_hooks.before_setitem:
            index, value = instance_hooks.before_setitem(self, index, value)

        m = meta.read(self)  # type: Optional[meta.Array]

        if m is None:
            item_types = None
        else:
            item_types = m.item_types

        value = unmarshal(value, types=item_types)
        super().__setitem__(index, value)

        if instance_hooks and instance_hooks.after_setitem:
            instance_hooks.after_setitem(self, index, value)

    def append(self, value):
        # type: (Any) -> None
        if not isinstance(value, _UNMARSHALLABLE_TYPES):
            raise errors.UnmarshalTypeError(data=value)

        instance_hooks = hooks.read(self)  # type: hooks.Array

        if instance_hooks and instance_hooks.before_append:
            value = instance_hooks.before_append(self, value)

        instance_meta = meta.read(self)  # type: Optional[meta.Array]

        if instance_meta is None:
            item_types = None
        else:
            item_types = instance_meta.item_types

        value = unmarshal(value, types=item_types)

        super().append(value)

        if instance_hooks and instance_hooks.after_append:
            instance_hooks.after_append(self, value)

    def __copy__(self):
        # type: () -> Array
        return self.__class__(self)

    def __deepcopy__(self, memo=None):
        # type: (Optional[dict]) -> Array
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

    def _marshal(self):
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
        raise_errors=True
    ):
        # type: (bool) -> None
        validation_errors = []
        a = self
        h = hooks.read(a)

        if (h is not None) and (h.before_validate is not None):
            a = h.before_validate(a)

        m = meta.read(a)

        if m.item_types is not None:

            for i in a:

                validation_errors.extend(validate(i, m.item_types, raise_errors=False))

        if (h is not None) and (h.after_validate is not None):
            h.after_validate(a)

        if raise_errors and validation_errors:
            raise errors.ValidationError('\n'.join(validation_errors))

        return validation_errors

    @staticmethod
    def _repr_item(item):
        # type: (Any) -> str
        """
        A string representation of an item in this array which can be used to recreate the item
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
        A string representation of this array which can be used to recreate the array
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
                    if instance_meta != class_meta and instance_meta.item_types else
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

    def __eq__(self, other):
        # type: (Any) -> bool
        if type(self) is not type(other):
            return False
        length = len(self)
        if length != len(other):
            return False
        for i in range(length):
            if self[i] != other[i]:
                return False
        return True

    def __ne__(self, other):
        # type: (Any) -> bool
        if self == other:
            return False
        else:
            return True

    def __str__(self):
        return serialize(self)


abc.model.Array.register(Array)


class Dictionary(collections.OrderedDict, Model):

    _format = None  # type: Optional[str]
    _hooks = None  # type: Optional[hooks.Dictionary]
    _meta = None  # type: Optional[meta.Dictionary]

    def __init__(
        self,
        items=None,  # type: Optional[Mapping]
        value_types=(
            None
        ),  # type: Optional[Union[Sequence[Union[type, properties.Property]], type, properties.Property]]
    ):
        self._meta = None  # type: Optional[meta.Dictionary]
        self._hooks = None  # type: Optional[hooks.Dictionary]
        self._url = None  # type: Optional[str]
        self._xpath = None  # type: Optional[str]
        self._pointer = None  # type: Optional[str]

        url = None

        if isinstance(items, IOBase):

            if hasattr(items, 'url'):
                url = items.url
            elif hasattr(items, 'name'):
                url = urljoin('file:', items.name)

        items, format_ = detect_format(items)

        if value_types is None:

            if isinstance(items, Dictionary):

                m = meta.read(items)

                if meta.read(self) is not m:
                    meta.write(self, deepcopy(m))
        else:

            meta.writable(self).value_types = value_types

        if items is None:

            super().__init__()

        else:

            if isinstance(items, (collections.OrderedDict, Dictionary)):
                items = items.items()
            elif isinstance(items, dict):
                items = sorted(items.items(), key=lambda kv: kv)

            super().__init__(items)

            if meta.pointer(self) is None:
                meta.pointer(self, '#')

            if meta.xpath(self) is None:
                meta.xpath(self, '')

        if url is not None:
            meta.url(self, url)

        if format_ is not None:
            meta.format_(self, format_)

    def __hash__(self):
        return id(self)

    def __setitem__(
        self,
        key,  # type: int
        value  # type: Any
    ):
        instance_hooks = hooks.read(self)  # type: hooks.Dictionary

        if instance_hooks and instance_hooks.before_setitem:
            key, value = instance_hooks.before_setitem(self, key, value)

        instance_meta = meta.read(self)  # type: Optional[meta.Dictionary]

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

    def __copy__(self):
        # type: (Dictionary) -> Dictionary
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

    def __deepcopy__(self, memo=None):
        # type: (dict) -> Dictionary
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

    def _marshal(self):
        """
        This method marshals an instance of `Dictionary` as built-in type `OrderedDict` which can be serialized into
        JSON/YAML.
        """

        # This variable is needed because before-marshal hooks are permitted to return altered *copies* of `self`, so
        # prior to marshalling--this variable may no longer point to `self`
        data = self  # type: Union[Dictionary, collections.OrderedDict]

        # Check for hooks
        instance_hooks = hooks.read(data)

        # Execute before-marshal hooks, if applicable
        if (instance_hooks is not None) and (instance_hooks.before_marshal is not None):
            data = instance_hooks.before_marshal(data)

        # Get the metadata, if any has been assigned
        instance_meta = meta.read(data)  # type: Optional[meta.Dictionary]

        # Check to see if value types are defined in the metadata
        if instance_meta is None:
            value_types = None
        else:
            value_types = instance_meta.value_types

        # Recursively convert the data to generic, serializable, data types
        unmarshalled_data = collections.OrderedDict(
            [
                (
                    k,
                    marshal(v, types=value_types)
                ) for k, v in data.items()
            ]
        )  # type: collections.OrderedDict

        # Execute after-marshal hooks, if applicable
        if (instance_hooks is not None) and (instance_hooks.after_marshal is not None):
            unmarshalled_data = instance_hooks.after_marshal(unmarshalled_data)

        return unmarshalled_data

    def _validate(self, raise_errors=True):
        # type: (Callable) -> None
        """
        Recursively validate
        """

        validation_errors = []
        d = self
        h = d._hooks or type(d)._hooks

        if (h is not None) and (h.before_validate is not None):
            d = h.before_validate(d)

        m = meta.read(d)  # type: Optional[meta.Dictionary]

        if m is None:
            value_types = None
        else:
            value_types = m.value_types

        if value_types is not None:

            for k, v in d.items():

                value_validation_errors = validate(v, value_types, raise_errors=False)\

                validation_errors.extend(value_validation_errors)

        if (h is not None) and (h.after_validate is not None):
            h.after_validate(d)

        if raise_errors and validation_errors:
            raise errors.ValidationError('\n'.join(validation_errors))

        return validation_errors

    @staticmethod
    def _repr_item(key, value):
        # type: (str, Any) -> str
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
            representation = '        (%s, %s),' % (repr(key), value_representation)
        return representation

    def __repr__(self):
        """
        Return a string representation of this object which can be used to re-assemble the object programmatically
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
                    if instance_meta != class_meta and instance_meta.value_types else
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

    def __eq__(self, other):
        # type: (Any) -> bool
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

    def __ne__(self, other):
        # type: (Any) -> bool
        if self == other:
            return False
        else:
            return True

    def __str__(self):
        return serialize(self)


abc.model.Dictionary.register(Dictionary)

# endregion


def _typing_from_property(property_):
    # type: (properties.Property) -> str
    if isinstance(property_, type):
        if property_ in (Union, Dict, Any, Sequence, IO):
            type_hint = property_.__name__
        else:
            type_hint = qualified_name(property_)
    elif isinstance(property_, properties.DateTime):
        type_hint = 'datetime'
    elif isinstance(property_, properties.Date):
        type_hint = 'date'
    elif isinstance(property_, properties.Bytes):
        type_hint = 'bytes'
    elif isinstance(property_, properties.Integer):
        type_hint = 'int'
    elif isinstance(property_, properties.Number):
        type_hint = qualified_name(Number)
    elif isinstance(property_, properties.Boolean):
        type_hint = 'bool'
    elif isinstance(property_, properties.String):
        type_hint = 'str'
    elif isinstance(property_, properties.Array):
        item_types = None
        if property_.item_types:
            if len(property_.item_types) > 1:
                item_types = 'Union[%s]' % (', '.join(
                    _typing_from_property(it) for it in property_.item_types))
            else:
                item_types = _typing_from_property(property_.item_types[0])
        type_hint = 'Sequence' + ('[%s]' % item_types if item_types else '')
    elif isinstance(property_, properties.Dictionary):
        value_types = None
        if property_.value_types:
            if len(property_.value_types) > 1:
                value_types = 'Union[%s]' % (', '.join(
                    _typing_from_property(vt) for vt in property_.value_types))
            else:
                value_types = _typing_from_property(property_.value_types[0])
        type_hint = ('Dict[str, %s]' % value_types if value_types else 'dict')
    elif property_ and property_.types:
        if len(property_.types) > 1:
            type_hint = 'Union[%s]' % ', '.join(
                _typing_from_property(t) for t in property_.types)
        else:
            type_hint = _typing_from_property(property_.types[0])
    else:
        type_hint = 'Any'
    return type_hint


def from_meta(name, metadata, module=None, docstring=None):
    # type: (str, meta.Meta, Optional[str], Optional[str]) -> type
    """
    Constructs an `Object`, `Array`, or `Dictionary` sub-class from an
    instance of `sob.meta.Meta`.

    Arguments:

        - name (str): The name of the class.

        - class_meta (sob.meta.Meta)

        - module (str): Specify the value for the class definition's
          `__module__` property. The invoking module will be
          used if this is not specified (if possible).

        - docstring (str): A docstring to associate with the class definition.
    """
    if docstring is not None:
        if '\t' in docstring:
            docstring = docstring.replace('\t', '    ')
        lines = docstring.split('\n')
        indentation_length = float('inf')
        for line in lines:
            match = re.match(r'^[ ]+', line)
            if match:
                indentation_length = min(
                    indentation_length,
                    len(match.group())
                )
            else:
                indentation_length = 0
                break
        wrapped_lines = []
        for line in lines:
            line = '    ' + line[indentation_length:]
            if len(line) > 120:
                indent = re.match(r'^[ ]*', line).group()
                indent_length = len(indent)
                words = re.split(
                    r'([\w]*[\w,/"\'.;\-?`])',
                    line[indent_length:]
                )
                wrapped_line = ''
                for word in words:
                    if (len(wrapped_line) + len(word) + indent_length) <= 120:
                        wrapped_line += word
                    else:
                        wrapped_lines.append(indent + wrapped_line)
                        wrapped_line = '' if not word.strip() else word
                if wrapped_line:
                    wrapped_lines.append(indent + wrapped_line)
            else:
                wrapped_lines.append(line)
        docstring = '\n'.join(
            ['    """'] +
            wrapped_lines +
            ['    """']
        )
    if isinstance(metadata, meta.Dictionary):
        out = [
            'class %s(%s):' % (name, qualified_name(Dictionary))
        ]
        if docstring is not None:
            out.append(docstring)
        out.append('\n    pass\n\n')
    elif isinstance(metadata, meta.Array):
        out = [
            'class %s(%s):' % (name, qualified_name(Array))
        ]
        if docstring is not None:
            out.append(docstring)
        out.append('\n    pass\n\n')
    elif isinstance(metadata, meta.Object):
        out = [
            'class %s(%s):' % (name, qualified_name(Object))
        ]
        if docstring is not None:
            out.append(docstring)
        out += [
            '',
            '    def __init__(',
            '        self,',
            '        _data=None,  # type: Optional[Union[str, bytes, dict, '
            'Sequence, IO]]'
        ]
        for property_name_, property_ in metadata.properties.items():
            out.append(
                '        %s=None,  # type: Optional[%s]' % (
                    property_name_,
                    _typing_from_property(property_)
                )
            )
        out.append(
            '    ):'
        )
        for property_name_ in metadata.properties.keys():
            out.append(
                '        self.%s = %s' % (property_name_, property_name_)
            )
        out.append('        super().__init__(_data)\n\n')
    else:
        raise ValueError(metadata)
    class_definition = '\n'.join(out)
    namespace = dict(__name__='from_meta_%s' % name)
    imports = '\n'.join([
        '# pylint: disable=wrong-import-position',
        BACKWARDS_COMPATIBILITY_IMPORTS,
        'import %s' % _parent_module_name,
        'try:',
        '    from typing import Union, Dict, Any, Sequence, IO',
        'except ImportError:',
        '    Union = Dict = Any = Sequence = IO = None',
    ])
    source = '%s\n\n\n%s' % (imports, class_definition)
    exec(source, namespace)
    result = namespace[name]
    result._source = source
    if module is None:
        try:
            module = sys._getframe(1).f_globals.get('__name__', '__main__')
        except (AttributeError, ValueError):
            pass
    if module is not None:
        result.__module__ = module
    result._meta = metadata
    return result


class _Marshal(object):

    def __init__(
        self,
        data,  # type: Any
        types=None,  # type: Optional[Sequence[Union[type, properties.Property, Callable]]]
        value_types=None,  # type: Optional[Sequence[Union[type, properties.Property]]]
        item_types=None,  # type: Optional[Sequence[Union[type, properties.Property]]]
    ):
        # type: (...) -> None
        pass


def marshal(
    data,  # type: Any
    types=None,  # type: Optional[Sequence[Union[type, properties.Property, Callable]]]
    value_types=None,  # type: Optional[Sequence[Union[type, properties.Property]]]
    item_types=None,  # type: Optional[Sequence[Union[type, properties.Property]]]
):
    # type: (...) -> Any

    """
    Recursively converts instances of `sob.abc.model.Model` into JSON/YAML serializable objects.
    """

    if hasattr(data, '_marshal'):
        return data._marshal()  # noqa (this is *our* protected member, so linters can piss off)

    # Don't do anything with `None`--this just means an attributes is not used for this instance (and explicit
    # `null` would be passed as `.properties.NULL`
    if data is None:
        return data

    # If `types` is a callable function, it should return an iterator of types and/or property definitions
    if callable(types):
        types = types(data)

    # If data types have been provided, validate the un-marshalled data by attempting to initialize the provided type(s)
    # with `data`
    if types is not None:

        # For compatibility - include `native_str` in `types` when it is not the same as `str`, and `str` is one of the
        # `types`.
        types = include_native_str(types)

        # For each potential type, attempt to marshal the data, and accept the first result which does not throw an
        # error
        matched = False
        for type_ in types:
            if isinstance(type_, properties.Property):
                try:
                    data = marshal_property_value(type_, data)
                    matched = True
                    break
                except TypeError:
                    pass
            elif isinstance(type_, type) and isinstance(data, type_):
                matched = True
                break

        # If no matches are found, raise a `TypeError` with sufficient information about the data and `types` to debug
        if not matched:
            raise TypeError(
                '%s cannot be interpreted as any of the designated types: %s' % (
                    repr(data),
                    repr(types)
                )
            )

    if value_types is not None:
        for k, v in data.items():
            data[k] = marshal(v, types=value_types)

    if item_types is not None:

        for i in range(len(data)):
            data[i] = marshal(data[i], types=item_types)

    if isinstance(data, Decimal):
        return float(data)

    if isinstance(data, (date, datetime)):
        return data.isoformat()

    if isinstance(data, native_str):
        return data

    if isinstance(data, (bytes, bytearray)):
        return str(b64encode(data), 'ascii')

    if hasattr(data, '__bytes__'):
        return str(b64encode(bytes(data)), 'ascii')

    return data


class _Unmarshal(object):
    """
    This class should be used exclusively by wrapper function `unmarshal`.
    """

    def __init__(
        self,
        data,  # type: Any
        types=None,  # type: Optional[Sequence[Union[type, properties.Property]]]
        value_types=None,  # type: Optional[Sequence[Union[type, properties.Property]]]
        item_types=None  # type: Optional[Sequence[Union[type, properties.Property]]]
    ):
        # type: (...) -> None
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
            if not isinstance(types, collections_abc.Sequence):
                types = (types,)
        if value_types is not None:
            if not isinstance(value_types, collections_abc.Sequence):
                value_types = (value_types,)
        if item_types is not None:
            if not isinstance(item_types, collections_abc.Sequence):
                item_types = (item_types,)
        # Instance Attributes
        self.data = data  # type: Any
        self.types = types  # type: Optional[Sequence[Union[type, properties.Property]]]
        self.value_types = value_types   # type: Optional[Sequence[Union[type, properties.Property]]]
        self.item_types = item_types   # type: Optional[Sequence[Union[type, properties.Property]]]
        self.meta = None  # type: Optional[meta.Meta]

    def __call__(self):
        # type: (...) -> Any
        """
        Return `self.data` unmarshalled
        """
        unmarshalled_data = self.data
        if (
            (self.data is not None) and
            (self.data is not properties.NULL)
        ):
            # If the data is a sob `Model`, get it's metadata
            if isinstance(self.data, abc.model.Model):
                self.meta = meta.read(self.data)

            if self.meta is None:  # Only un-marshall models if they have no metadata yet (are generic)

                # If `types` is a function, it should be one which expects to receive marshalled data and returns a list
                # of types which are applicable
                if callable(self.types):
                    self.types = self.types(self.data)

                # If the data provided is a `Generator`, make it static by casting the data into a tuple
                if isinstance(self.data, Generator):
                    self.data = tuple(self.data)

                if self.types is None:

                    # If no types are provided, we unmarshal the data into one of sob's generic container types
                    unmarshalled_data = self.as_container_or_simple_type

                else:
                    self.types = include_native_str(self.types)
                    unmarshalled_data = (  # type: Optional[Union[abc.model.Model, Number, str, bytes, date, datetime]]
                        None
                    )
                    successfully_unmarshalled = False  # type: bool
                    first_error = None  # type: Optional[Exception]
                    first_error_message = None  # type: Optional[str]
                    # Attempt to un-marshal the data as each type, in the order
                    # provided
                    for type_ in self.types:
                        error = None  # type: Optional[Union[AttributeError, KeyError, TypeError, ValueError]]
                        error_message = None  # type: Optional[str]
                        try:
                            unmarshalled_data = self.as_type(type_)
                            # If the data is un-marshalled successfully, we do
                            # not need to try any further types
                            successfully_unmarshalled = True
                            break
                        except (
                            AttributeError, KeyError, TypeError, ValueError
                        ) as e:
                            error = e
                            error_message = errors.get_exception_text()
                        if (error is not None) and (first_error is None):
                            first_error = error
                            first_error_message = error_message
                    if not successfully_unmarshalled:
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
                        elif isinstance(first_error, ValueError):
                            raise errors.UnmarshalValueError(
                                first_error_message,
                                data=self.data,
                                types=self.types,
                                value_types=self.value_types,
                                item_types=self.item_types
                            )
                        else:
                            # pylint erroneously identifies this as raising
                            # `None`
                            raise first_error  # noqa
        return unmarshalled_data

    @property
    def as_container_or_simple_type(self):
        # type: (...) -> Any
        """
        This function unmarshalls and returns the data into one of sob's container types, or if the data is of a
        simple data type--it returns that data unmodified
        """
        unmarshalled_data = self.data
        if isinstance(self.data, abc.model.Dictionary):
            type_ = type(self.data)
            if self.value_types is not None:
                unmarshalled_data = type_(self.data, value_types=self.value_types)
        elif isinstance(self.data, abc.model.Array):
            type_ = type(self.data)
            if self.item_types is not None:
                unmarshalled_data = type_(self.data, item_types=self.item_types)
        elif isinstance(self.data, (dict, collections.OrderedDict)):
            unmarshalled_data = Dictionary(self.data, value_types=self.value_types)
        elif (
            isinstance(self.data, (collections_abc.Set, collections_abc.Sequence))
        ) and (
            not isinstance(self.data, (str, bytes, native_str))
        ):
            unmarshalled_data = Array(self.data, item_types=self.item_types)
        elif not isinstance(
            self.data,
            (str, bytes, native_str, Number, Decimal, date, datetime, bool, abc.model.Model)
        ):
            raise errors.UnmarshalValueError(
                '%s cannot be un-marshalled' % repr(self.data)
            )
        return unmarshalled_data

    def get_dictionary_type(self, dictionary_type):
        # type: (type) -> type
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

    def before_hook(self, type_):
        # type: (Any) -> Any
        data = self.data
        hooks_ = hooks.read(type_)
        if hooks_ is not None:
            before_unmarshal_hook = hooks_.before_unmarshal
            if before_unmarshal_hook is not None:
                data = before_unmarshal_hook(deepcopy(data))
        return data

    def after_hook(self, type_, data):
        # type: (Any, Any) -> Any
        hooks_ = hooks.read(type_)
        if hooks_ is not None:
            after_unmarshal_hook = hooks_.after_unmarshal
            if after_unmarshal_hook is not None:
                data = after_unmarshal_hook(data)
        return data

    def as_dictionary_type(
        self,
        type_  # type: type
    ):
        # type: (...) -> Union[dict, collections.OrderedDict, abc.model.Model]
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

    def get_array_type(self, type_):
        # type: (type) -> type
        if type_ is abc.model.Array:
            type_ = Array
        elif issubclass(type_, abc.model.Array):
            pass
        elif issubclass(
            type_,
            (collections_abc.Set, collections_abc.Sequence)
        ) and not issubclass(
            type_,
            (str, bytes, native_str)
        ):
            type_ = Array
        else:
            raise TypeError('%s is not of type `%s`' % (repr(self.data), repr(type_)))
        return type_

    def as_array_type(
        self,
        type_  # type: type
    ):
        # type: (...) -> Array
        type_ = self.get_array_type(type_)
        unmarshalled_data = type_(self.data, item_types=self.item_types)
        return unmarshalled_data

    def as_type(
        self,
        type_,  # type: Union[type, properties.Property]
    ):
        # type: (...) -> Any

        unmarshalled_data = None  # type: Union[abc.model.Model, Number, str, bytes, date, datetime]

        if isinstance(
            type_,
            properties.Property
        ):
            unmarshalled_data = unmarshal_property_value(type_, self.data)
        elif isinstance(type_, type):
            if isinstance(
                self.data,
                (dict, collections.OrderedDict, abc.model.Model)
            ):
                unmarshalled_data = self.as_dictionary_type(type_)
            elif (
                isinstance(self.data, (collections_abc.Set, collections_abc.Sequence, abc.model.Array)) and
                (not isinstance(self.data, (str, bytes, native_str)))
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
    data,  # type: Any
    types=None,  # type: Optional[Union[Sequence[Union[type, properties.Property]], type, properties.Property]]
    value_types=None,  # type: Optional[Union[Sequence[Union[type, properties.Property]], type, properties.Property]]
    item_types=None,  # type: Optional[Union[Sequence[Union[type, properties.Property]], type, properties.Property]]
):
    # type: (...) -> Optional[Union[abc.model.Model, str, Number, date, datetime]]
    """
    Converts `data` into an instance of a sob model, and recursively does the same for all member data.

    Parameters:

     - data ([type|sob.properties.Property]): One or more data types. Each type

    This is done by attempting to cast that data into a series of `types`.

    to "un-marshal" data which has been deserialized from bytes or text, but is still represented
    by generic containers
    """

    unmarshalled_data = _Unmarshal(
        data,
        types=types,
        value_types=value_types,
        item_types=item_types
    )()

    return unmarshalled_data


def serialize(data, format_='json'):
    # type: (Union[abc.model.Model, str, Number], Optional[str]) -> str
    """
    Serializes instances of `Object` as JSON or YAML.
    """
    instance_hooks = None

    if isinstance(data, abc.model.Model):

        instance_hooks = hooks.read(data)

        if (instance_hooks is not None) and (instance_hooks.before_serialize is not None):
            data = instance_hooks.before_serialize(data)

    if format_ not in ('json', 'yaml'):

        format_ = format_.lower()

        if format_ not in ('json', 'yaml'):

            raise ValueError(
                'Supported `sob.model.serialize()` `format_` values include "json" and "yaml" (not "%s").' %
                format_
            )

    if format_ == 'json':
        data = json.dumps(marshal(data))
    elif format_ == 'yaml':
        data = yaml.dump(marshal(data))

    if (instance_hooks is not None) and (instance_hooks.after_serialize is not None):
        data = instance_hooks.after_serialize(data)

    if not isinstance(data, str):
        if isinstance(data, native_str):
            data = str(data)

    return data


def deserialize(data, format_):
    # type: (Optional[Union[str, IOBase, addbase]], str) -> Any
    """
    Parameters:

        - data (str|io.IOBase|io.addbase):

          This can be a string or file-like object containing JSON or YAML serialized information.

        - format_ (str):

          This can be "json" or "yaml".

    Returns:

        A deserialized representation of the information you provided.
    """
    if format_ not in ('json', 'yaml'):
        raise NotImplementedError(
            'Deserialization of data in the format %s is not currently supported.' % repr(format_)
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


def detect_format(data):
    # type: (Optional[Union[str, IOBase, addbase]]) -> Tuple[Any, str]
    """
    Parameters:

        - data (str|io.IOBase|io.addbase):

          This can be a string or file-like object containing JSON or YAML serialized information.

    Returns:

        A tuple containing the deserialized information and a string indicating the format of that information.
    """
    if not isinstance(data, str):
        try:
            data = read(data)
        except TypeError:
            return data, None
    formats = ('json', 'yaml')
    format_ = None
    for potential_format in formats:
        try:
            data = deserialize(data, potential_format)
            format_ = potential_format
            break
        except (ValueError, yaml.YAMLError):
            pass
    if format is None:
        raise ValueError(
            'The data provided could not be parsed:\n' + repr(data)
        )
    return data, format_


if Optional is None:
    _ValidateTypes = None
else:
    _ValidateTypes = Optional[
        Union[type, properties.Property, Object, Callable]
    ]


def validate(
    data,  # type: Optional[abc.model.Model]
    types=None,  # type: _ValidateTypes
    raise_errors=True  # type: bool
):
    # type: (...) -> Sequence[str]
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
    error_message = None
    if types is not None:
        if callable(types):
            types = types(data)
        types = include_native_str(types)
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
    if error_message is not None:
        if (not error_messages) or (error_message not in error_messages):
            error_messages.append(error_message)
    if '_validate' in dir(data):
        validate_method = getattr(data, '_validate')
        if callable(validate_method):
            error_messages.extend(
                error_message for error_message in
                validate_method(raise_errors=False)
                if error_message not in error_messages
            )
    if raise_errors and error_messages:
        # If there is no top-level error message, include a representation of
        # the top-level data element
        if error_message not in error_messages:
            error_messages.insert(
                0,
                '\n'+ repr(data)
            )
        raise errors.ValidationError('\n' + '\n\n'.join(error_messages))
    return error_messages


class _UnmarshalProperty(object):
    """
    This is exclusively for use by wrapper function `unmarshal_property_value`.
    """

    def __init__(
        self,
        property  # type: properties.Property
    ):
        # type: (...) -> None
        self.property = property

    def validate_enumerated(self, value):
        # type: (Any) -> Any
        """
        Verify that a value is one of the enumerated options
        """

        if (
            (value is not None) and
            (self.property.values is not None) and
            (value not in self.property.values)
        ):
            raise ValueError(
                'The value provided is not a valid option:\n%s\n\n' % repr(value) +
                'Valid options include:\n%s' % (
                    ', '.join(repr(t) for t in self.property.values)
                )
            )

    def parse_date(self, value):
        # type: (Optional[str]) -> Union[date, NoneType]
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

    def parse_datetime(self, value):
        # type: (Optional[str]) -> Union[datetime, NoneType]
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
                    '"%s" is not a properly formatted date-time string.' % value
                )

    def parse_bytes(self, data):
        # type: (str) -> Optional[bytes]
        """
        Un-marshal a base-64 encoded string into bytes
        """
        if data is None:
            return data
        elif isinstance(data, str):
            return b64decode(data)
        elif isinstance(data, bytes):
            return data
        else:
            raise TypeError(
                '`data` must be a base64 encoded `str` or `bytes`--not `%s`' % qualified_name(type(data))
            )

    def __call__(self, value):
        # type: (Any) -> Any

        if isinstance(self.property, properties.Date):

            value = self.parse_date(value)

        elif isinstance(self.property, properties.DateTime):

            value = self.parse_datetime(value)

        elif isinstance(self.property, properties.Bytes):

            value = self.parse_bytes(value)

        elif isinstance(self.property, properties.Array):

            value = unmarshal(value, types=self.property.types, item_types=self.property.item_types)

        elif isinstance(self.property, properties.Dictionary):

            value = unmarshal(value, types=self.property.types, value_types=self.property.value_types)

        else:

            if isinstance(self.property, properties.Enumerated):
                self.validate_enumerated(value)
            elif isinstance(
                value,
                collections_abc.Iterable
            ) and not isinstance(
                value,
                (str, bytes, bytearray, native_str)
            ) and not isinstance(
                value,
                abc.model.Model
            ):
                if isinstance(value, (dict, collections.OrderedDict)):
                    for k, v in value.items():
                        if v is None:
                            value[k] = properties.NULL
                else:
                    value = tuple((properties.NULL if i is None else i) for i in value)

            if self.property.types is not None:
                value = unmarshal(value, types=self.property.types)

        return value


def unmarshal_property_value(property, value):
    # type: (properties.Property, Any) -> Any
    """
    Unmarshal a property value
    """
    return _UnmarshalProperty(property)(value)


class _MarshalProperty(object):
    """
    This is exclusively for use by wrapper function `marshal_property_value`.
    """

    def __init__(
        self,
        property  # type: properties.Property
    ):
        # type: (...) -> None
        self.property = property

    def parse_date(self, value):
        # type: (Optional[date]) -> Optional[str]
        if value is not None:
            value = self.property.date2str(value)
            if not isinstance(value, str):
                if isinstance(value, native_str):
                    value = str(value)
                else:
                    raise TypeError(
                        'The date2str function should return a `str`, not a `%s`: %s' % (
                            type(value).__name__,
                            repr(value)
                        )
                    )
        return value

    def parse_datetime(self, value):
        # type: (Optional[datetime]) -> Optional[str]
        if value is not None:
            datetime_string = self.property.datetime2str(value)
            if not isinstance(datetime_string, str):
                if isinstance(datetime_string, native_str):
                    datetime_string = str(datetime_string)
                else:
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

    def parse_bytes(self, value):
        # type: (bytes) -> str
        """
        Marshal bytes into a base-64 encoded string
        """
        if (value is None) or isinstance(value, str):
            return value
        elif isinstance(value, bytes):
            return str(b64encode(value), 'ascii')
        else:
            raise TypeError(
                '`data` must be a base64 encoded `str` or `bytes`--not `%s`' % qualified_name(type(value))
            )

    def __call__(self, value):
        # type: (Any) -> Any
        if isinstance(self.property, properties.Date):
            value = self.parse_date(value)
        elif isinstance(self.property, properties.DateTime):
            value = self.parse_datetime(value)
        elif isinstance(self.property, properties.Bytes):
            value = self.parse_bytes(value)
        elif isinstance(self.property, properties.Array):
            value = marshal(value, types=self.property.types, item_types=self.property.item_types)
        elif isinstance(self.property, properties.Dictionary):
            value = marshal(value, types=self.property.types, value_types=self.property.value_types)
        else:
            value = marshal(value, types=self.property.types)
        return value


def marshal_property_value(property, value):
    # type: (properties.Property, Any) -> Any
    """
    Marshal a property value
    """
    return _MarshalProperty(property)(value)
