import collections
import numbers
import operator
import re
from collections import OrderedDict
from copy import copy, deepcopy
from itertools import chain
from numbers import Number
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from . import errors
from .properties.types import Types
from .utilities import (
    calling_function_qualified_name, properties_values, qualified_name
)
from .utilities.assertion import assert_argument_is_instance
from . import abc

_DOT_SYNTAX_RE = re.compile(
    r'^\d+(\.\d+)*$'
)


class Meta:

    def __copy__(self):
        new_instance = self.__class__()
        for a in dir(self):
            if a[0] != '_':
                v = getattr(self, a)
                if not isinstance(v, collections.Callable):
                    setattr(new_instance, a, v)
        return new_instance

    def __deepcopy__(self, memo: dict = None) -> 'Meta':
        new_instance = self.__class__()
        for a, v in properties_values(self):
            setattr(new_instance, a, deepcopy(v, memo=memo))
        return new_instance

    def __bool__(self) -> bool:
        return True

    def __repr__(self) -> str:
        lines: List[str] = ['%s(' % qualified_name(type(self))]
        property_name: str
        value: Any
        for property_name, value in properties_values(self):
            if isinstance(value, type):
                value_representation = qualified_name(value)
            else:
                value_representation = repr(value)
            lines.append('    %s=%s,' % (property_name, value_representation))
        # Strip the trailing comma
        lines[-1] = lines[-1][:-1]
        lines.append(')')
        return '\n'.join(lines)


abc.meta.Meta.register(Meta)


class Version(Meta):

    def __init__(
        self,
        version_number: Optional[str] = None,
        specification: Optional[Sequence[str]] = None,
        equals: Optional[Sequence[Union[str, Number]]] = None,
        not_equals: Optional[Sequence[Union[str, Number]]] = None,
        less_than: Optional[Sequence[Union[str, Number]]] = None,
        less_than_or_equal_to: Optional[Sequence[Union[str, Number]]] = None,
        greater_than: Optional[Sequence[Union[str, Number]]] = None,
        greater_than_or_equal_to: Optional[Sequence[Union[str, Number]]] = None
    ) -> None:
        if isinstance(version_number, str) and (
            (specification is None) and
            (equals is None) and
            (not_equals is None) and
            (less_than is None) and
            (less_than_or_equal_to is None) and
            (greater_than is None) and
            (greater_than_or_equal_to is None)
        ):
            specification = None
            for s in version_number.split('&'):
                if '==' in s:
                    s, equals = s.split('==')
                elif '<=' in s:
                    s, less_than_or_equal_to = s.split('<=')
                elif '>=' in s:
                    s, greater_than_or_equal_to = s.split('>=')
                elif '<' in s:
                    s, less_than = s.split('<')
                elif '>' in s:
                    s, greater_than = s.split('>')
                elif '!=' in s:
                    s, not_equals = s.split('!=')
                elif '=' in s:
                    s, equals = s.split('=')
                if specification:
                    if s != specification:
                        raise ValueError(
                            'Multiple specifications cannot be associated '
                            'with an instance of ' +
                            '`sob.meta.Version`: ' + repr(version_number)
                        )
                elif s:
                    specification = s
            self.specification = specification
        self.equals = equals
        self.not_equals = not_equals
        self.less_than = less_than
        self.less_than_or_equal_to = less_than_or_equal_to
        self.greater_than = greater_than
        self.greater_than_or_equal_to = greater_than_or_equal_to

    def __eq__(self, other: Any) -> bool:
        compare_properties_functions = (
            ('equals', operator.eq),
            ('not_equals', operator.ne),
            ('less_than', operator.lt),
            ('less_than_or_equal_to', operator.le),
            ('greater_than', operator.gt),
            ('greater_than_or_equal_to', operator.ge),
        )
        if (
            (isinstance(other, str) and _DOT_SYNTAX_RE.match(other)) or
            isinstance(other, (collections.abc.Sequence, int))
        ):
            if isinstance(other, (bytes, numbers.Number)):
                other = str(other)
            if isinstance(other, str):
                other = other.rstrip('.0')
                if other == '':
                    other_components = (0,)
                else:
                    other_components = tuple(
                        int(other_component)
                        for other_component in other.split('.')
                    )
            else:
                other_components = tuple(other)
            for compare_property, compare_function in (
                compare_properties_functions
            ):
                compare_value = getattr(self, compare_property)
                if compare_value is not None:
                    compare_values = tuple(
                        int(number_string)
                        for number_string in compare_value.split('.')
                    )
                    other_values = copy(other_components)
                    length_difference = len(other_values) - len(compare_values)
                    if length_difference < 0:
                        other_values = tuple(
                            chain(
                                other_values,
                                [0] * (-length_difference)
                            )
                        )
                    elif length_difference > 0:
                        compare_values = tuple(
                            chain(
                                compare_values,
                                [0] * length_difference
                            )
                        )
                    if not compare_function(other_values, compare_values):
                        return False
        else:
            for compare_property, compare_function in (
                compare_properties_functions
            ):
                compare_value = getattr(self, compare_property)
                if (
                    compare_value is not None
                ) and not compare_function(
                    other,
                    compare_value
                ):
                    return False
        return True

    def __str__(self) -> str:
        representation: List[str] = []
        property_name: str
        repr_operator: str
        for property_name, repr_operator in (
            ('equals', '=='),
            ('not_equals', '!='),
            ('greater_than', '>'),
            ('greater_than_or_equal_to', '>='),
            ('less_than', '<'),
            ('less_than_or_equal_to', '<='),
        ):
            v = getattr(self, property_name)
            if v is not None:
                representation.append(
                    self.specification + repr_operator + v
                )
        return '&'.join(representation)


abc.meta.Version.register(Version)


class Object(Meta):

    def __init__(
        self,
        properties: Optional['Properties'] = None
    ) -> None:
        self._properties: Optional[Properties] = None
        self.properties = properties

    @property
    def properties(self) -> Optional['Properties']:
        return self._properties

    @properties.setter
    def properties(
        self,
        properties_: Optional[
            Union[
                Dict[
                    str,
                    abc.properties.Property
                ],
                Sequence[
                    Tuple[str, abc.properties.Property]
                ]
            ]
        ]
    ) -> None:
        self._properties = Properties(properties_)


abc.meta.Object.register(Object)


class Dictionary(Meta):

    def __init__(
        self,
        value_types: Optional[
            Sequence[
                Union[
                    abc.properties.Property, type
                ]
            ]
        ] = None
    ) -> None:
        self._value_types: Optional[Tuple] = None
        self.value_types = value_types

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
                    abc.properties.Property,
                    abc.model.Object
                ]
            ]
        ]
    ) -> None:
        if value_types is not None:
            if isinstance(value_types, (type, abc.properties.Property)):
                value_types = (value_types,)
            value_types = Types(value_types)
        self._value_types = value_types


abc.meta.Dictionary.register(Dictionary)


class Array(Meta):

    def __init__(
        self,
        item_types: Optional[
            Sequence[
                Union[
                    abc.properties.Property, type
                ]
            ]
        ] = None
    ):
        self._item_types: Optional[Tuple] = None
        self.item_types = item_types

    @property
    def item_types(self):
        return self._item_types

    @item_types.setter
    def item_types(
        self,
        item_types: Optional[
            Sequence[
                Union[
                    type,
                    abc.properties.Property,
                    abc.model.Object
                ]
            ]
        ]
    ) -> None:
        if item_types is not None:
            if isinstance(item_types, (type, abc.properties.Property)):
                item_types = (item_types,)
            item_types = Types(item_types)
        self._item_types = item_types


abc.meta.Array.register(Array)


class Properties(OrderedDict):

    def __init__(
        self,
        items: Optional[
            Union[
                Dict[
                    str,
                    abc.properties.Property
                ],
                List[
                    Tuple[
                        str,
                        abc.properties.Property
                    ]
                ]
            ]
        ] = None
    ) -> None:
        if items is None:
            super().__init__()
        else:
            if isinstance(items, OrderedDict):
                items = items.items()
            elif isinstance(items, dict):
                items = sorted(items.items())
            super().__init__(items)

    def __setitem__(self, key: str, value: abc.properties.Property) -> None:
        if not isinstance(value, abc.properties.Property):
            raise ValueError(value)
        super().__setitem__(key, value)

    def __copy__(self) -> 'Properties':
        return self.__class__(self)

    def __deepcopy__(self, memo: dict = None) -> 'Properties':
        key: str
        value: abc.properties.Property
        return self.__class__(
            tuple(
                (key, deepcopy(value, memo=memo))
                for key, value in self.items()
            )
        )

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
                indented_lines.append('        ' + line)
            value_representation = '\n'.join(indented_lines)
            representation = '\n'.join([
                '    (',
                '        %s,' % repr(key),
                '        %s' % value_representation,
                '    ),'
            ])
        else:
            representation = '    (%s, %s),' % (
                repr(key),
                value_representation
            )
        return representation

    def __repr__(self) -> str:
        representation = [
            qualified_name(type(self)) + '('
        ]
        items = tuple(self.items())
        if len(items) > 0:
            representation[0] += '['
            for key, value in items:
                representation.append(self._repr_item(key, value))
            representation[-1] = representation[-1].rstrip(',')
            representation.append(
                ']'
            )
        representation[-1] += ')'
        if len(representation) > 2:
            return '\n'.join(representation)
        else:
            return ''.join(representation)


abc.meta.Properties.register(Properties)


def read(
    model: Union[type, abc.model.Model]
) -> Optional[Meta]:
    if isinstance(
        model,
        abc.model.Model
    ):
        return getattr(model, '_meta') or read(type(model))
    elif isinstance(model, type):
        if issubclass(model, abc.model.Model):
            return getattr(model, '_meta')
        else:
            raise TypeError(
                '%s requires a parameter which is an instance or sub-class of '
                '`%s`, not `%s`' % (
                    calling_function_qualified_name(),
                    qualified_name(abc.model.Model),
                    qualified_name(model)
                )
            )
    else:
        repr_model = repr(model)
        raise TypeError(
            '%s requires a parameter which is an instance or sub-class of '
            '`%s`, not%s' % (
                calling_function_qualified_name(),
                qualified_name(abc.model.Model),
                (
                    ':\n' + repr_model
                    if '\n' in repr_model else
                    ' `%s`' % repr_model
                )
            )
        )


def writable(
    model: Union[type, abc.model.Model]
) -> Optional[Meta]:
    """
    This function returns an instance of [sob.meta.Meta](#Meta) which can
    be safely modified. If the class or model instance inherits its metadata
    from a class or base class, this function will create and return a
    duplicate of that metadata assigned directly to the class or instance
    represented by `model`.
    """
    if isinstance(model, abc.model.Model):
        if getattr(model, '_meta') is None:
            model._meta = deepcopy(writable(type(model)))
    elif isinstance(model, type) and issubclass(model, abc.model.Model):
        model_meta: Optional[Meta] = getattr(model, '_meta')
        if model_meta is None:
            # If this model doesn't have any metadata yet--create an
            # appropriate metadata instance
            model._meta = (
                Object()
                if issubclass(model, abc.model.Object) else
                Array()
                if issubclass(model, abc.model.Array) else
                Dictionary()
                if issubclass(model, abc.model.Dictionary)
                else None
            )
        else:
            # Ensure that the metadata is not being inherited from a base
            # class by copying the metadata if it has the same ID as any
            # base class
            for base in model.__bases__:
                base_meta: Optional[Meta] = None
                try:
                    base_meta = getattr(base, '_meta')
                except AttributeError:
                    pass
                if base_meta is not None:
                    if model_meta is base_meta:
                        model._meta = deepcopy(model_meta)
                        break
    else:
        repr_model = repr(model)
        raise TypeError(
            '%s requires a parameter which is an instance or sub-class of '
            '`%s`, not%s' % (
                calling_function_qualified_name(),
                qualified_name(abc.model.Model),
                (
                    ':\n' + repr_model
                    if '\n' in repr_model else
                    ' `%s`' % repr_model
                )
            )
        )
    return getattr(model, '_meta')


def write(
    model: Union[type, abc.model.Object],
    meta: Meta
) -> None:
    if isinstance(model, abc.model.Model):
        model_type = type(model)
    elif isinstance(model, type) and issubclass(model, abc.model.Model):
        model_type = model
    else:
        repr_model = repr(model)
        raise TypeError(
            '%s requires a value for the parameter `model` which is an '
            'instance or sub-class of `%s`, not%s' % (
                calling_function_qualified_name(),
                qualified_name(abc.model.Model),
                (
                    ':\n' + repr_model
                    if '\n' in repr_model else
                    ' `%s`' % repr_model
                )
            )
        )
    metadata_type = (
        Object
        if issubclass(model_type, abc.model.Object) else
        Array
        if issubclass(model_type, abc.model.Array) else
        Dictionary
        if issubclass(model_type, abc.model.Dictionary)
        else None
    )
    if not isinstance(meta, metadata_type):
        raise ValueError(
            'Metadata assigned to `%s` must be of type `%s`' % (
                qualified_name(model_type),
                qualified_name(metadata_type)
            )
        )
    model._meta = meta


def get_pointer(model: abc.model.Model) -> Optional[str]:
    return getattr(model, '_pointer')


def set_pointer(
    model: abc.model.Model,
    pointer_: str
) -> None:
    assert_argument_is_instance('pointer_', pointer_, str)
    model._pointer = pointer_
    if isinstance(model, abc.model.Dictionary):
        for key, value in model.items():
            if isinstance(value, abc.model.Model):
                pointer(value, '%s/%s' % (
                    pointer_, key.replace('~', '~0').replace('/', '~1'))
                )
    elif isinstance(model, abc.model.Object):
        for property_name, property_ in read(model).properties.items():
            key: str = property_.name or property_name
            value: Any = getattr(model, property_name)
            if isinstance(value, abc.model.Model):
                pointer(
                    value,
                    '%s/%s' % (
                        pointer_,
                        key.replace('~', '~0').replace('/', '~1')
                    )
                )
    elif isinstance(model, abc.model.Array):
        index: int
        for index in range(len(model)):
            value: Any = model[index]
            if isinstance(value, abc.model.Model):
                pointer(value, '%s/%s' % (pointer_, str(index)))


def pointer(
    model: abc.model.Model,
    pointer_: Optional[str] = None
) -> Optional[str]:
    """
    Get or set a model's pointer
    """
    assert_argument_is_instance('model', model, abc.model.Model)
    if pointer_ is not None:
        set_pointer(model, pointer_)
    return get_pointer(model)


def set_url(
    model: abc.model.Model,
    url_: Optional[str]
) -> None:
    assert_argument_is_instance('model', model, abc.model.Model)
    if url_ is not None:
        assert_argument_is_instance('url_', url_, str)
    model._url = url_
    if isinstance(model, abc.model.Dictionary):
        for value in model.values():
            if isinstance(value, abc.model.Model):
                set_url(value, url_)
    elif isinstance(model, abc.model.Object):
        for property_name in read(model).properties.keys():
            value = getattr(model, property_name)
            if isinstance(value, abc.model.Model):
                set_url(value, url_)
    elif isinstance(model, abc.model.Array):
        for value in model:
            if isinstance(value, abc.model.Model):
                set_url(value, url_)


def get_url(model: abc.model.Model) -> Optional[str]:
    return getattr(model, '_url')


def url(
    model: abc.model.Model,
    url_: Optional[str] = None
) -> Optional[str]:
    if url_ is not None:
        set_url(model, url_)
    return get_url(model)


def set_format(
    model: abc.model.Model,
    serialization_format: Optional[str] = None
) -> None:
    assert_argument_is_instance('model', model, abc.model.Model)
    assert_argument_is_instance(
        'serialization_format',
        serialization_format,
        str
    )
    model._format = serialization_format
    if isinstance(model, abc.model.Dictionary):
        for value in model.values():
            if isinstance(value, abc.model.Model):
                set_format(value, serialization_format)
    elif isinstance(model, abc.model.Object):
        for property_name in read(model).properties.keys():
            value = getattr(model, property_name)
            if isinstance(value, abc.model.Model):
                set_format(value, serialization_format)
    elif isinstance(model, abc.model.Array):
        for value in model:
            if isinstance(value, abc.model.Model):
                set_format(value, serialization_format)


def get_format(model: abc.model.Model) -> Optional[str]:
    return getattr(model, '_format')


def format_(
    model: abc.model.Model,
    serialization_format: Optional[str] = None
) -> Optional[str]:
    if serialization_format is not None:
        set_format(model, serialization_format)
    return get_format(model)


def _version_match(
    property_: abc.properties.Property,
    specification: str,
    version_number: Union[str, int, Sequence[int]]
) -> bool:
    if property_.versions is not None:
        version_matched = False
        specification_matched = False
        for applicable_version in property_.versions:
            if applicable_version.specification == specification:
                specification_matched = True
                if applicable_version == version_number:
                    version_matched = True
                    break
        if specification_matched and (not version_matched):
            return False
    return True


def _version_properties(
    properties_: Sequence[abc.properties.Property],
    specification: str,
    version_number: Union[str, int, Sequence[int]]
) -> Optional[Sequence[abc.properties.Property]]:
    changed: bool = False
    new_properties = []
    for property_ in properties_:
        if isinstance(property_, abc.properties.Property):
            if _version_match(
                property_,
                specification,
                version_number
            ):
                new_property = _version_property(
                    property_,
                    specification,
                    version_number
                )
                if new_property is not property_:
                    changed = True
                new_properties.append(new_property)
            else:
                changed = True
        else:
            new_properties.append(property_)
    if changed:
        return tuple(new_properties)
    else:
        return None


def _version_property(
    property_: abc.properties.Property,
    specification: str,
    version_number: Union[str, int, Sequence[int]]
) -> abc.properties.Property:
    changed: bool = False
    if isinstance(
        property_,
        abc.properties.Array
    ) and (
        property_.item_types is not None
    ):
        item_types = _version_properties(
            property_.item_types,
            specification,
            version_number
        )
        if item_types is not None:
            if not changed:
                property_ = deepcopy(property_)
            property_.item_types = item_types
            changed = True
    elif isinstance(
        property_,
        abc.properties.Dictionary
    ) and (
            property_.value_types is not None
    ):
        value_types = _version_properties(
            property_.value_types,
            specification,
            version_number
        )
        if value_types is not None:
            if not changed:
                property_ = deepcopy(property_)
            property_.value_types = value_types
            changed = True
    if property_.types is not None:
        types = _version_properties(
            property_.types,
            specification,
            version_number
        )
        if types is not None:
            if not changed:
                property_ = deepcopy(property_)
            property_.types = types
    return property_


def version(
    data: abc.model.Model,
    specification: str,
    version_number: Union[str, int, Sequence[int]]
) -> None:
    """
    Recursively alters model class or instance metadata based on version number
    metadata associated with an object's properties. This allows one data model
    to represent multiple versions of a specification and dynamically change
    based on the version of a specification represented.

    Parameters:

    - data (sob.abc.model.Model)
    - specification (str): The specification to which the `version_number`
      argument applies.
    - version_number (str|int|[int]): A version number represented as text
      (in the form of integers separated by periods), an integer, or a
      sequence of integers.
    """
    assert_argument_is_instance('data', data, abc.model.Model)
    instance_meta = read(data)
    class_meta = read(type(data))
    if isinstance(data, abc.model.Object):
        for property_name in tuple(instance_meta.properties.keys()):
            property_ = instance_meta.properties[property_name]
            if _version_match(
                property_,
                specification,
                version_number
            ):
                new_property = _version_property(
                    property_,
                    specification,
                    version_number
                )
                if new_property is not property_:
                    if instance_meta is class_meta:
                        instance_meta = writable(data)
                    instance_meta.properties[property_name] = new_property
            else:
                if instance_meta is class_meta:
                    instance_meta = writable(data)
                del instance_meta.properties[property_name]
                version_ = getattr(data, property_name)
                if version_ is not None:
                    raise errors.VersionError(
                        '%s - the property `%s` is not applicable in %s '
                        'version %s:\n%s' % (
                            qualified_name(type(data)),
                            property_name,
                            specification,
                            version_number,
                            str(data)
                        )
                    )
            value = getattr(data, property_name)
            if isinstance(value, abc.model.Model):
                version(value, specification, version_number)
    elif isinstance(data, abc.model.Dictionary):
        if instance_meta and instance_meta.value_types:
            new_value_types = _version_properties(
                instance_meta.value_types,
                specification,
                version_number
            )
            if new_value_types:
                if instance_meta is class_meta:
                    instance_meta = writable(data)
                instance_meta.value_types = new_value_types
        for value in data.values():
            if isinstance(value, abc.model.Model):
                version(value, specification, version_number)
    elif isinstance(data, abc.model.Array):
        if instance_meta and instance_meta.item_types:
            new_item_types = _version_properties(
                instance_meta.item_types,
                specification,
                version_number
            )
            if new_item_types:
                if instance_meta is class_meta:
                    instance_meta = writable(data)
                instance_meta.item_types = new_item_types
        for item in data:
            if isinstance(item, abc.model.Model):
                version(item, specification, version_number)


def copy_to(
    source: abc.model.Model,
    target: abc.model.Model
) -> None:
    if source != target:
        assert_argument_is_instance('source', source, abc.model.Model)
        if type(source) is not type(target):
            raise ValueError(
                'The source and target must be of the same type'
            )
        source_meta = read(source)
        target_meta = read(target)
        if source_meta is not target_meta:
            write(target, source_meta)
        if isinstance(source, abc.model.Object):
            for property_name in source_meta.properties.keys():
                source_property_value = getattr(source, property_name)
                target_property_value = getattr(target, property_name)
                if isinstance(source_property_value, abc.model.Model):
                    copy_to(source_property_value, target_property_value)
        elif isinstance(source, abc.model.Array):
            for index in range(len(source)):
                copy_to(source[index], target[index])
        elif isinstance(source, abc.model.Dictionary):
            for key in source.keys():
                copy_to(source[key], target[key])
