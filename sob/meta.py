import collections
import itertools
import re
from collections import OrderedDict
from copy import deepcopy
from typing import (
    Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union, Type
)

from . import abc
from . import errors
from .types import TYPES, Types
from .utilities import (
    calling_function_qualified_name, indent, properties_values, qualified_name
)
from .utilities.assertion import assert_argument_is_instance
from .utilities.inspect import represent
from .utilities.typing import MarshallableTypes

_MODEL_OR_INSTANCE_TYPING = Union[
    Type[abc.model.Object],
    Type[abc.model.Dictionary],
    Type[abc.model.Array],
    abc.model.Object,
    abc.model.Dictionary,
    abc.model.Array
]


# noinspection PyUnresolvedReferences
@abc.meta.Meta.register
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
            lines.append(
                '    %s=%s,' % (
                    property_name,
                    indent(value_representation)
                )
            )
        # Strip the trailing comma
        lines[-1] = lines[-1][:-1]
        lines.append(')')
        return '\n'.join(lines)


# noinspection PyUnresolvedReferences


# noinspection PyUnresolvedReferences
@abc.meta.Object.register
class Object(Meta):

    def __init__(
        self,
        properties: Optional[
            Union[
                Dict[
                    str,
                    abc.properties.Property
                ],
                Sequence[
                    Tuple[str, abc.properties.Property]
                ]
            ]
        ] = None
    ) -> None:
        self._properties: Optional[Properties] = None
        setattr(self, 'properties', properties)

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


# noinspection PyUnresolvedReferences
@abc.meta.Dictionary.register
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
        self._value_types: Optional[Types] = None
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
                    abc.properties.Property
                ]
            ]
        ]
    ) -> None:
        if value_types is not None:
            if isinstance(value_types, (type, abc.properties.Property)):
                value_types = (value_types,)
            value_types = Types(value_types)
        self._value_types = value_types


# noinspection PyUnresolvedReferences
@abc.meta.Array.register
class Array(Meta):

    def __init__(
        self,
        item_types: Optional[
            Sequence[
                Union[
                    abc.properties.Property,
                    type
                ]
            ]
        ] = None
    ):
        self._item_types: Optional[Types] = None
        setattr(self, 'item_types', item_types)

    @property
    def item_types(self) -> Optional[Types]:
        return self._item_types

    @item_types.setter
    def item_types(
        self,
        item_types: Optional[
            Sequence[
                Union[
                    type,
                    abc.properties.Property
                ]
            ]
        ]
    ) -> None:
        if item_types is not None:
            if isinstance(item_types, (type, abc.properties.Property)):
                item_types = (item_types,)
            item_types = Types(item_types)
        self._item_types = item_types


# noinspection PyUnresolvedReferences
@abc.meta.Properties.register
class Properties(OrderedDict):

    def __init__(
        self,
        items: Optional[
            Union[
                Dict[
                    str,
                    abc.properties.Property
                ],
                Iterable[
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

    # noinspection PyArgumentList
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


def read(
    model: _MODEL_OR_INSTANCE_TYPING
) -> Union[abc.meta.Dictionary, abc.meta.Array, abc.meta.Object]:
    if isinstance(
        model,
        (abc.model.Object, abc.model.Dictionary, abc.model.Array)
    ):
        return getattr(model, '_meta') or read(type(model))
    elif isinstance(model, type):
        if issubclass(
            model,
            (abc.model.Object, abc.model.Dictionary, abc.model.Array)
        ):
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
    model: _MODEL_OR_INSTANCE_TYPING
) -> Union[abc.meta.Object, abc.meta.Array, abc.meta.Dictionary]:
    """
    This function returns an instance of [sob.meta.Meta](#Meta) which can
    be safely modified. If the class or model instance inherits its metadata
    from a class or base class, this function will create and return a
    duplicate of that metadata assigned directly to the class or instance
    represented by `model`.
    """
    if isinstance(
        model,
        (
            abc.model.Object,
            abc.model.Dictionary,
            abc.model.Array
        )
    ):
        if getattr(model, '_meta') is None:
            model._meta = deepcopy(writable(type(model)))
    elif isinstance(model, type) and issubclass(
        model,
        (
            abc.model.Object,
            abc.model.Dictionary,
            abc.model.Array
        )
    ):
        model_meta: Union[
            abc.meta.Object,
            abc.meta.Dictionary,
            abc.meta.Array
        ] = getattr(model, '_meta')
        if model_meta is None:
            # If this model doesn't have any metadata yet--create an
            # appropriate metadata instance
            model._meta = (
                Object()
                if issubclass(model, abc.model.Object) else
                Array()
                if issubclass(model, abc.model.Array) else
                Dictionary()
            )
        else:
            # Ensure that the metadata is not being inherited from a base
            # class by copying the metadata if it has the same ID as any
            # base class
            for base in model.__bases__:
                base_meta: Optional[abc.meta.Meta] = None
                try:
                    base_meta = getattr(base, '_meta')
                except AttributeError:
                    pass
                if base_meta is not None:
                    if model_meta is base_meta:
                        model._meta = deepcopy(model_meta)
                        break
    else:
        repr_model = represent(model)
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
    model: _MODEL_OR_INSTANCE_TYPING,
    meta: Union[abc.meta.Array, abc.meta.Object, abc.meta.Dictionary]
) -> None:
    if isinstance(
        model,
        (
            abc.model.Object,
            abc.model.Array,
            abc.model.Dictionary
        )
    ):
        model_type = type(model)
    elif isinstance(model, type) and issubclass(
        model,
        (
            abc.model.Object,
            abc.model.Array,
            abc.model.Dictionary
        )
    ):
        model_type = model
    else:
        repr_model = repr(model)
        raise TypeError(
            '{} requires a value for the parameter `model` which is an '
            'instance or sub-class of `{}`, not{}'.format(
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
    )
    if not isinstance(meta, metadata_type):
        raise ValueError(
            'Metadata assigned to `%s` must be of type `%s`' % (
                qualified_name(model_type),
                qualified_name(metadata_type)
            )
        )
    model._meta = meta


def get_pointer(
    model: Union[
        abc.model.Object,
        abc.model.Dictionary,
        abc.model.Array
    ]
) -> Optional[str]:
    return getattr(model, '_pointer')


def _read_object(
    model: Union[
        abc.model.Object,
        Type[abc.model.Object]
    ]
) -> abc.meta.Object:
    metadata: abc.meta.Meta = read(model)
    assert isinstance(metadata, abc.meta.Object)
    return metadata


def _read_object_properties(
    model: Union[
        abc.model.Object,
        Type[abc.model.Object]
    ]
) -> Iterable[
    Tuple[str, abc.properties.Property]
]:
    metadata: abc.meta.Object = _read_object(model)
    return (metadata.properties or {}).items()


def _read_object_property_names(
    model: Union[
        abc.model.Object,
        Type[abc.model.Object]
    ]
) -> Iterable[str]:
    metadata: abc.meta.Object = _read_object(model)
    return (metadata.properties or {}).keys()


def set_pointer(
    model: Union[
        abc.model.Object,
        abc.model.Dictionary,
        abc.model.Array
    ],
    pointer_: str
) -> None:
    key: str
    value: Any
    assert_argument_is_instance('pointer_', pointer_, str)
    model._pointer = pointer_
    if isinstance(model, abc.model.Dictionary):
        for key, value in model.items():
            if isinstance(
                value,
                (abc.model.Object, abc.model.Dictionary, abc.model.Array)
            ):
                pointer(value, '%s/%s' % (
                    pointer_, key.replace('~', '~0').replace('/', '~1'))
                )
    elif isinstance(model, abc.model.Object):
        property_name: str
        property_: abc.properties.Property
        for property_name, property_ in _read_object_properties(model):
            key = property_.name or property_name
            value = getattr(model, property_name)
            if isinstance(
                value,
                (abc.model.Object, abc.model.Dictionary, abc.model.Array)
            ):
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
            value = model[index]
            if isinstance(
                value,
                (abc.model.Object, abc.model.Dictionary, abc.model.Array)
            ):
                pointer(value, '%s/%s' % (pointer_, str(index)))


def pointer(
    model: Union[
        abc.model.Object,
        abc.model.Dictionary,
        abc.model.Array
    ],
    pointer_: Optional[str] = None
) -> Optional[str]:
    """
    Get or set a model's pointer
    """
    assert_argument_is_instance(
        'model',
        model,
        (
            abc.model.Object,
            abc.model.Dictionary,
            abc.model.Array
        )
    )
    if pointer_ is not None:
        set_pointer(model, pointer_)
    return get_pointer(model)


def _traverse_models(
    model_instance: Union[
        abc.model.Object,
        abc.model.Dictionary,
        abc.model.Array
    ]
) -> Iterable[
    Union[
        abc.model.Object,
        abc.model.Array,
        abc.model.Dictionary
    ]
]:
    """
    Iterate over all child model instances
    """
    if isinstance(model_instance, abc.model.Dictionary):
        for value in model_instance.values():
            if isinstance(
                value,
                (
                    abc.model.Object,
                    abc.model.Dictionary,
                    abc.model.Array
                )
            ):
                yield value
    elif isinstance(model_instance, abc.model.Object):
        property_name: str
        for property_name in _read_object_property_names(model_instance):
            value = getattr(model_instance, property_name)
            if isinstance(
                value,
                (abc.model.Object, abc.model.Dictionary, abc.model.Array)
            ):
                yield value
    elif isinstance(model_instance, abc.model.Array):
        for value in model_instance:
            if isinstance(
                value,
                (abc.model.Object, abc.model.Dictionary, abc.model.Array)
            ):
                yield value


# noinspection PyShadowingNames
def set_url(
    model_instance: Union[
        abc.model.Object,
        abc.model.Dictionary,
        abc.model.Array
    ],
    source_url: Optional[str]
) -> None:
    assert_argument_is_instance(
        'model', model_instance,
        (abc.model.Object, abc.model.Dictionary, abc.model.Array)
    )
    if source_url is not None:
        assert_argument_is_instance('url_', source_url, str)
    model_instance._url = source_url
    child_model: Union[
        abc.model.Object,
        abc.model.Dictionary,
        abc.model.Array
    ]
    itertools.starmap(
        set_url,
        (
            (child_model, source_url)
            for child_model in _traverse_models(model_instance)
        )
    )


def get_url(
    model: Union[
        abc.model.Object,
        abc.model.Dictionary,
        abc.model.Array
    ]
) -> Optional[str]:
    return getattr(model, '_url')


def url(
    model: Union[
        abc.model.Object,
        abc.model.Dictionary,
        abc.model.Array
    ],
    url_: Optional[str] = None
) -> Optional[str]:
    if url_ is not None:
        set_url(model, url_)
    return get_url(model)


def set_format(
    model: Union[
        abc.model.Object,
        abc.model.Dictionary,
        abc.model.Array
    ],
    serialization_format: Optional[str] = None
) -> None:
    assert_argument_is_instance(
        'model',
        model,
        (
            abc.model.Object,
            abc.model.Dictionary,
            abc.model.Array
        )
    )
    assert_argument_is_instance(
        'serialization_format',
        serialization_format,
        str
    )
    model._format = serialization_format
    if isinstance(model, abc.model.Dictionary):
        for value in model.values():
            if isinstance(
                value,
                (abc.model.Object, abc.model.Dictionary, abc.model.Array)
            ):
                set_format(value, serialization_format)
    elif isinstance(model, abc.model.Object):
        for property_name in _read_object_property_names(model):
            value = getattr(model, property_name)
            if isinstance(
                value,
                (abc.model.Object, abc.model.Dictionary, abc.model.Array)
            ):
                set_format(value, serialization_format)
    elif isinstance(model, abc.model.Array):
        for value in model:
            if isinstance(
                value,
                (abc.model.Object, abc.model.Dictionary, abc.model.Array)
            ):
                set_format(value, serialization_format)


def get_format(
    model: Union[
        abc.model.Object,
        abc.model.Dictionary,
        abc.model.Array
    ]
) -> Optional[str]:
    return getattr(model, '_format')


def format_(
    model: Union[
        abc.model.Object,
        abc.model.Dictionary,
        abc.model.Array
    ],
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
    properties_: Union[
        abc.types.Types,
        Iterable[
            Union[
                abc.properties.Property,
                type
            ]
        ]
    ],
    specification: str,
    version_number: Union[str, int, Sequence[int]]
) -> Optional[
    Iterable[
        Union[
            abc.properties.Property,
            type
        ]
    ]
]:
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
                # Exclude this property, as it's not a match
                changed = True
        else:
            new_properties.append(
                property_
            )
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
        item_type_items = _version_properties(
            property_.item_types,
            specification,
            version_number
        )
        if item_type_items is not None:
            if not changed:
                property_ = deepcopy(property_)
            item_types = Types(item_type_items)
            assert isinstance(item_types, abc.types.Types)
            property_.item_types = item_types
            changed = True
    elif isinstance(
        property_,
        abc.properties.Dictionary
    ) and (
        property_.value_types is not None
    ):
        value_types_items = _version_properties(
            property_.value_types,
            specification,
            version_number
        )
        if value_types_items is not None:
            if not changed:
                property_ = deepcopy(property_)
            value_types = Types(value_types_items)
            assert isinstance(value_types, abc.types.Types)
            property_.value_types = value_types
            changed = True
    if property_.types is not None:
        types_items = _version_properties(
            property_.types,
            specification,
            version_number
        )
        if types_items is not None:
            if not changed:
                property_ = deepcopy(property_)
            types = Types(types_items)
            assert isinstance(types, abc.types.Types)
            property_.types = types
    return property_


def _version_object(
    data: abc.model.Object,
    specification: str,
    version_number: Union[str, int, Sequence[int]]
) -> None:
    instance_meta = read(data)
    class_meta = read(type(data))
    property_name: str
    property_: abc.properties.Property
    for property_name, property_ in tuple(
        instance_meta.properties.items()
    ):
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
        if isinstance(
            value, (abc.model.Object, abc.model.Dictionary, abc.model.Array)
        ):
            version(value, specification, version_number)


def _version_dictionary(
    data: abc.model.Dictionary,
    specification: str,
    version_number: Union[str, int, Sequence[int]]
) -> None:
    instance_meta = read(data)
    class_meta = read(type(data))
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
        if isinstance(
            value,
            (abc.model.Object, abc.model.Dictionary, abc.model.Array)
        ):
            version(value, specification, version_number)


def _version_array(
    data: abc.model.Array,
    specification: str,
    version_number: Union[str, int, Sequence[int]]
) -> None:
    instance_meta = read(data)
    class_meta = read(type(data))
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
        if isinstance(
            item, (abc.model.Object, abc.model.Dictionary, abc.model.Array)
        ):
            version(item, specification, version_number)


def version(
    data: Union[abc.model.Object, abc.model.Dictionary, abc.model.Array],
    specification: str,
    version_number: Union[str, int, Sequence[int]]
) -> None:
    """
    Recursively alters model class or instance metadata based on version number
    metadata associated with an object's properties. This allows one data model
    to represent multiple versions of a specification and dynamically change
    based on the version of a specification represented.

    Parameters:

    - data ([sob.model.Model](#Model))
    - specification (str): The specification to which the `version_number`
      argument applies.
    - version_number (str|int|[int]): A version number represented as text
      (in the form of integers separated by periods), an integer, or a
      sequence of integers.
    """
    assert_argument_is_instance(
        'data',
        data,
        (
            abc.model.Object,
            abc.model.Dictionary,
            abc.model.Array
        )
    )
    if isinstance(data, abc.model.Object):
        _version_object(
            data,
            specification,
            version_number
        )
    elif isinstance(data, abc.model.Dictionary):
        _version_dictionary(
            data,
            specification,
            version_number
        )
    else:
        _version_array(
            data,
            specification,
            version_number
        )


def copy_to(
    source: Union[abc.model.Object, abc.model.Dictionary, abc.model.Array],
    target: Union[abc.model.Object, abc.model.Dictionary, abc.model.Array]
) -> None:
    """
    This function copies metadata from one model instance to another
    """
    # Verify both arguments are models
    argument_name: str
    argument_value: Union[
        abc.model.Object, abc.model.Dictionary, abc.model.Array
    ]
    for argument_name, argument_value in (
        ('source', source),
        ('target', target)
    ):
        assert_argument_is_instance(
            argument_name,
            argument_value,
            (abc.model.Object, abc.model.Dictionary, abc.model.Array)
        )
    # Verify both arguments of of the same `type`
    assert type(source) is type(target)
    # Copy the metadata
    source_meta: Union[
        abc.meta.Object,
        abc.meta.Dictionary,
        abc.meta.Array
    ] = read(source)
    target_meta: Union[
        abc.meta.Object,
        abc.meta.Dictionary,
        abc.meta.Array
    ] = read(target)
    if source_meta is not target_meta:
        write(target, source_meta)
    # ... and recursively do the same for member data
    if isinstance(source, abc.model.Object):
        for property_name in source_meta.properties.keys():
            source_property_value = getattr(source, property_name)
            target_property_value = getattr(target, property_name)
            if target_property_value and isinstance(
                source_property_value,
                (abc.model.Object, abc.model.Dictionary, abc.model.Array)
            ):
                copy_to(source_property_value, target_property_value)
    elif isinstance(source, abc.model.Array):
        for index, value in enumerate(source):
            target_value: MarshallableTypes = target[index]
            if target_value and isinstance(
                value,
                (abc.model.Object, abc.model.Dictionary, abc.model.Array)
            ):
                copy_to(value, target_value)
    elif isinstance(source, abc.model.Dictionary):
        for key, value in source.items():
            target_value: MarshallableTypes = target[key]
            if target_value and isinstance(
                value,
                (abc.model.Object, abc.model.Dictionary, abc.model.Array)
            ):
                copy_to(value, target_value)
