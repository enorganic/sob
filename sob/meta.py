from __future__ import (
    nested_scopes, generators, division, absolute_import, with_statement,
    print_function, unicode_literals
)
from .utilities import compatibility
from future.utils import native_str
import numbers
import operator
import re
import collections
from collections import OrderedDict
from copy import deepcopy
from copy import copy
from itertools import chain
from numbers import Number
from . import abc, errors
from .utilities import (
    qualified_name, properties_values, calling_function_qualified_name
)
from .properties.types import Types

compatibility.backport()

Optional = compatibility.typing.Optional
Dict = compatibility.typing.Dict
Sequence = compatibility.typing.Sequence
Tuple = compatibility.typing.Tuple
Mapping = compatibility.typing.Mapping
Union = compatibility.typing.Union
Any = compatibility.typing.Any
List = compatibility.typing.List
collections_abc = compatibility.collections_abc

_DOT_SYNTAX_RE = re.compile(
    r'^\d+(\.\d+)*$'
)


class Meta(object):

    def __copy__(self):
        new_instance = self.__class__()
        for a in dir(self):
            if a[0] != '_':
                v = getattr(self, a)
                if not isinstance(v, collections.Callable):
                    setattr(new_instance, a, v)
        return new_instance

    def __deepcopy__(self, memo=None):
        # type: (Optional[dict]) -> Meta
        new_instance = self.__class__()
        for a, v in properties_values(self):
            setattr(new_instance, a, deepcopy(v, memo=memo))
        return new_instance

    def __bool__(self):
        return True

    def __repr__(self):
        lines = ['%s(' % qualified_name(type(self))]
        for property_name, value in properties_values(self):
            if isinstance(value, type):
                value_representation = qualified_name(value)
            else:
                value_representation = repr(value)
            lines.append('    %s=%s,' % (property_name, value_representation))
        # Stript the trailing comma
        lines[-1] = lines[-1][:-1]
        lines.append(')')
        return '\n'.join(lines)


class Version(Meta):

    def __init__(
        self,
        version_number=None,  # type: Optional[str]
        specification=None,  # type: Optional[Sequence[str]]
        equals=None,  # type: Optional[Sequence[Union[str, Number]]]
        not_equals=None,  # type: Optional[Sequence[Union[str, Number]]]
        less_than=None,  # type: Optional[Sequence[Union[str, Number]]]
        less_than_or_equal_to=None,  # type: Optional[Sequence[Union[str, Number]]]
        greater_than=None,  # type: Optional[Sequence[Union[str, Number]]]
        greater_than_or_equal_to=None,  # type: Optional[Sequence[Union[str, Number]]]
    ):
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
                            'Multiple specifications cannot be associated with an instance of ' +
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

    def __eq__(self, other):
        # type: (Any) -> bool

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
            isinstance(other, (collections_abc.Sequence, int))
        ):
            if isinstance(other, (native_str, bytes, numbers.Number)):
                other = str(other)
            if isinstance(other, str):

                other = other.rstrip('.0')
                if other == '':
                    other_components = (0,)
                else:
                    other_components = tuple(int(other_component) for other_component in other.split('.'))
            else:
                other_components = tuple(other)
            for compare_property, compare_function in compare_properties_functions:
                compare_value = getattr(self, compare_property)
                if compare_value is not None:
                    compare_values = tuple(int(n) for n in compare_value.split('.'))
                    other_values = copy(other_components)
                    ld = len(other_values) - len(compare_values)
                    if ld < 0:
                        other_values = tuple(chain(other_values, [0] * (-ld)))
                    elif ld > 0:
                        compare_values = tuple(chain(compare_values, [0] * ld))
                    if not compare_function(other_values, compare_values):
                        return False
        else:
            for compare_property, compare_function in compare_properties_functions:
                compare_value = getattr(self, compare_property)
                if (compare_value is not None) and not compare_function(other, compare_value):
                    return False
        return True

    def __str__(self):
        representation = []
        for property, operator in (
            ('equals', '=='),
            ('not_equals', '!='),
            ('greater_than', '>'),
            ('greater_than_or_equal_to', '>='),
            ('less_than', '<'),
            ('less_than_or_equal_to', '<='),
        ):
            v = getattr(self, property)
            if v is not None:
                representation.append(
                    self.specification + operator + v
                )
        return '&'.join(representation)


class Object(Meta):

    def __init__(
        self,
        properties=None,  # type: Optional[Properties]
    ):
        self._properties = None  # type: Optional[Properties]
        self.properties = properties

    @property
    def properties(self):
        # type: () -> Optional[Properties]
        return self._properties

    @properties.setter
    def properties(
        self,
        properties_
        # type: Optional[Union[Dict[str, abc.properties.Property], Sequence[Tuple[str, Property]]]]
    ):
        # type: (...) -> None
        self._properties = Properties(properties_)


class Dictionary(Meta):

    def __init__(
        self,
        value_types=None,  # type: Optional[Sequence[Property, type]]
    ):
        self._value_types = None  # type: Optional[Tuple]
        self.value_types = value_types

    @property
    def value_types(self):
        return self._value_types

    @value_types.setter
    def value_types(self, value_types):
        # type: (Optional[Sequence[Union[type, abc.properties.Property, abc.model.Object]]]) -> None

        if value_types is not None:

            if isinstance(value_types, (type, abc.properties.Property)):
                value_types = (value_types,)

            if native_str is not str:
                if callable(value_types):
                    _types = value_types

                    def value_types(data):
                        # type: (Any) -> Any
                        return Types(_types(data))

            if not callable(value_types):
                value_types = Types(value_types)

        self._value_types = value_types


class Array(Meta):

    def __init__(
        self,
        item_types=None,  # type: Optional[Sequence[Property, type]]
    ):
        self._item_types = None  # type: Optional[Tuple]
        self.item_types = item_types

    @property
    def item_types(self):
        return self._item_types

    @item_types.setter
    def item_types(self, item_types):
        # type: (Optional[Sequence[Union[type, abc.properties.Property, abc.model.Object]]]) -> None

        if item_types is not None:

            if isinstance(item_types, (type, abc.properties.Property)):
                item_types = (item_types,)

            if native_str is not str:
                if callable(item_types):
                    _types = item_types

                    def item_types(data):
                        # type: (Any) -> Any
                        return Types(_types(data))

            if not callable(item_types):
                item_types = Types(item_types)

        self._item_types = item_types


class Properties(OrderedDict):

    def __init__(
        self,
        items=(
            None
        )  # type: Optional[Union[Dict[str, abc.properties.Property], List[Tuple[str, abc.properties.Property]]]]
    ):
        if items is None:
            super().__init__()
        else:
            if isinstance(items, OrderedDict):
                items = items.items()
            elif isinstance(items, dict):
                items = sorted(items.items())
            super().__init__(items)

    def __setitem__(self, key, value):
        # type: (str, Property) -> None
        if not isinstance(value, abc.properties.Property):
            raise ValueError(value)
        super().__setitem__(key, value)

    def __copy__(self):
        # type: () -> Properties
        return self.__class__(self)

    def __deepcopy__(self, memo=None):
        # type: (dict) -> Properties
        return self.__class__(
            tuple(
                (k, deepcopy(v, memo=memo))
                for k, v in self.items()
            )
        )

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
                indented_lines.append('        ' + line)
            value_representation = '\n'.join(indented_lines)
            representation = '\n'.join([
                '    (',
                '        %s,' % repr(key),
                '        %s' % value_representation,
                '    ),'
            ])
        else:
            representation = '    (%s, %s),' % (repr(key), value_representation)
        return representation

    def __repr__(self):
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
    model  # type: Union[type, abc.model.Model]
):
    # type: (...) -> Optional[Meta]
    if isinstance(
        model,
        abc.model.Model
    ):
        return model._meta or read(type(model))
    elif isinstance(model, type) and issubclass(model, abc.model.Model):
        return model._meta
    else:
        try:
            repr_model = repr(model)
        except:
            repr_model = object.__repr__(model)
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
    model  # type: Union[type, abc.model.Model]
):
    # type: (...) -> Optional[Meta]
    if isinstance(model, abc.model.Model):
        if model._meta is None:
            model._meta = deepcopy(writable(type(model)))
    elif isinstance(model, type) and issubclass(model, abc.model.Model):
        if model._meta is None:
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
            for b in model.__bases__:
                if hasattr(b, '_meta') and (model._meta is b._meta):
                    model._meta = deepcopy(model._meta)
                    break
    else:
        repr_model = repr(model)
        raise TypeError(
            '%s requires a parameter which is an instance or sub-class of `%s`, not%s' % (
                calling_function_qualified_name(),
                qualified_name(abc.model.Model),
                (
                    ':\n' + repr_model
                    if '\n' in repr_model else
                    ' `%s`' % repr_model
                )
            )
        )
    return model._meta


def write(
    model,  # type: Union[type, abc.model.Object]
    meta  # type: Meta
):
    # type: (...) -> None
    if isinstance(model, abc.model.Model):
        model_type = type(model)
    elif isinstance(model, type) and issubclass(model, abc.model.Model):
        model_type = model
    else:
        repr_model = repr(model)
        raise TypeError(
            '%s requires a value for the parameter `model` which is an instance or sub-class of `%s`, not%s' % (
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


_UNIDENTIFIED = None


def xpath(model, xpath_=_UNIDENTIFIED):
    # type: (abc.model.Model, Optional[str]) -> Optional[str]
    """
    Return the xpath at which the element represented by this object was found, relative to the root document. If
    the parameter `xpath_` is provided--set the value
    """

    if not isinstance(model, abc.model.Model):

        raise TypeError(
            '`model` must be an instance of `%s`, not %s.' % (qualified_name(abc.model.Model), repr(model))
        )

    if xpath_ is not _UNIDENTIFIED:

        if not isinstance(xpath_, str):

            if isinstance(xpath_, native_str):
                xpath_ = str(xpath_)
            else:
                raise TypeError(
                    '`xpath_` must be a `str`, not %s.' % repr(xpath_)
                )

        model._xpath = xpath_

        if isinstance(model, abc.model.Dictionary):
            for k, v in model.items():
                if isinstance(v, abc.model.Model):
                    xpath(v, '%s/%s' % (xpath_, k))
        elif isinstance(model, abc.model.Object):
            for pn, p in read(model).properties.items():
                k = p.name or pn
                v = getattr(model, pn)
                if isinstance(v, abc.model.Model):
                    xpath(v, '%s/%s' % (xpath_, k))
        elif isinstance(model, abc.model.Array):
            for i in range(len(model)):
                v = model[i]
                if isinstance(v, abc.model.Model):
                    xpath(v, '%s[%s]' % (xpath_, str(i)))
    return model._xpath


def pointer(model, pointer_=_UNIDENTIFIED):
    # type: (abc.model.Model, Optional[str]) -> Optional[str]

    if not isinstance(model, abc.model.Model):
        raise TypeError(
            '`model` must be an instance of `%s`, not %s.' % (qualified_name(abc.model.Model), repr(model))
        )

    if pointer_ is not _UNIDENTIFIED:

        if not isinstance(pointer_, (str, native_str)):
            raise TypeError(
                '`pointer_` must be a `str`, not %s (of type `%s`).' % (repr(pointer_), type(pointer_).__name__)
            )

        model._pointer = pointer_

        if isinstance(model, abc.model.Dictionary):

            for k, v in model.items():
                if isinstance(v, abc.model.Model):
                    pointer(v, '%s/%s' % (pointer_, k.replace('~', '~0').replace('/', '~1')))

        elif isinstance(model, abc.model.Object):

            for pn, property in read(model).properties.items():

                k = property.name or pn
                v = getattr(model, pn)

                if isinstance(v, abc.model.Model):
                    pointer(v, '%s/%s' % (pointer_, k.replace('~', '~0').replace('/', '~1')))

        elif isinstance(model, abc.model.Array):

            for i in range(len(model)):

                v = model[i]

                if isinstance(v, abc.model.Model):
                    pointer(v, '%s[%s]' % (pointer_, str(i)))

    return model._pointer


def url(model, url_=_UNIDENTIFIED):
    # type: (abc.model.Model, Optional[str]) -> Optional[str]
    if not isinstance(model, abc.model.Model):
        raise TypeError(
            '`model` must be an instance of `%s`, not %s.' % (qualified_name(abc.model.Model), repr(model))
        )
    if url_ is not _UNIDENTIFIED:
        if not isinstance(url_, str):
            raise TypeError(
                '`url_` must be a `str`, not %s.' % repr(url_)
            )
        model._url = url_
        if isinstance(model, abc.model.Dictionary):
            for v in model.values():
                if isinstance(v, abc.model.Model):
                    url(v, url_)
        elif isinstance(model, abc.model.Object):
            for pn in read(model).properties.keys():
                v = getattr(model, pn)
                if isinstance(v, abc.model.Model):
                    url(v, url_)
        elif isinstance(model, abc.model.Array):
            for v in model:
                if isinstance(v, abc.model.Model):
                    url(v, url_)
    return model._url


def format_(model, serialization_format=_UNIDENTIFIED):

    # type: (abc.model.Model, Optional[str]) -> Optional[str]
    if not isinstance(model, abc.model.Model):

        raise TypeError(
            '`model` must be an instance of `%s`, not %s.' % (qualified_name(abc.model.Model), repr(model))
        )

    if serialization_format is not _UNIDENTIFIED:

        if not isinstance(serialization_format, str):

            if isinstance(serialization_format, native_str):
                serialization_format = str(serialization_format)
            else:
                raise TypeError(
                    '`serialization_format` must be a `str`, not %s.' % repr(serialization_format)
                )

        model._format = serialization_format

        if isinstance(model, abc.model.Dictionary):
            for v in model.values():
                if isinstance(v, abc.model.Model):
                    format_(v, serialization_format)
        elif isinstance(model, abc.model.Object):
            for pn in read(model).properties.keys():
                v = getattr(model, pn)
                if isinstance(v, abc.model.Model):
                    format_(v, serialization_format)
        elif isinstance(model, abc.model.Array):
            for v in model:
                if isinstance(v, abc.model.Model):
                    format_(v, serialization_format)

    return model._format


def version(data, specification, version_number):
    # type: (abc.model.Model, str, Union[str, int, Sequence[int]]) -> None
    """
    Recursively alters model class or instance metadata based on version number metadata associated with an
    object's properties. This allows one data model to represent multiple versions of a specification and dynamically
    change based on the version of a specification represented.

    Arguments:

        - data (sob.abc.model.Model)

        - specification (str):

            The specification to which the `version_number` argument applies.

        - version_number (str|int|[int]):

            A version number represented as text (in the form of integers separated by periods), an integer, or a
            sequence of integers.
    """
    if not isinstance(data, abc.model.Model):
        raise TypeError(
            'The data provided is not an instance of sob.abc.model.Model: ' + repr(data)
        )

    def version_match(property_):
        # type: (abc.properties.Property) -> bool
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

    def version_properties(properties_):
        # type: (Sequence[abc.properties.Property]) -> Optional[Sequence[Meta]]
        changed = False
        nps = []

        for property in properties_:

            if isinstance(property, abc.properties.Property):
                if version_match(property):
                    np = version_property(property)
                    if np is not property:
                        changed = True
                    nps.append(np)
                else:
                    changed = True
            else:
                nps.append(property)
        if changed:
            return tuple(nps)
        else:
            return None

    def version_property(property):
        # type: (abc.properties.Property) -> Meta
        changed = False
        if isinstance(property, abc.properties.Array) and (property.item_types is not None):
            item_types = version_properties(property.item_types)
            if item_types is not None:
                if not changed:
                    property = deepcopy(property)
                property.item_types = item_types
                changed = True
        elif isinstance(property, abc.properties.Dictionary) and (property.value_types is not None):
            value_types = version_properties(property.value_types)
            if value_types is not None:
                if not changed:
                    property = deepcopy(property)
                property.value_types = value_types
                changed = True
        if property.types is not None:
            types = version_properties(property.types)
            if types is not None:
                if not changed:
                    property = deepcopy(property)
                property.types = types
        return property

    instance_meta = read(data)
    class_meta = read(type(data))

    if isinstance(data, abc.model.Object):
        for property_name in tuple(instance_meta.properties.keys()):
            property = instance_meta.properties[property_name]
            if version_match(property):
                np = version_property(property)
                if np is not property:
                    if instance_meta is class_meta:
                        instance_meta = writable(data)
                    instance_meta.properties[property_name] = np
            else:
                if instance_meta is class_meta:
                    instance_meta = writable(data)
                del instance_meta.properties[property_name]
                version_ = getattr(data, property_name)
                if version_ is not None:
                    raise errors.VersionError(
                        '%s - the property `%s` is not applicable in %s version %s:\n%s' % (
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
            new_value_types = version_properties(instance_meta.value_types)
            if new_value_types:
                if instance_meta is class_meta:
                    instance_meta = writable(data)
                instance_meta.value_types = new_value_types
        for value in data.values():
            if isinstance(value, abc.model.Model):
                version(value, specification, version_number)

    elif isinstance(data, abc.model.Array):
        if instance_meta and instance_meta.item_types:
            new_item_types = version_properties(instance_meta.item_types)
            if new_item_types:
                if instance_meta is class_meta:
                    instance_meta = writable(data)
                instance_meta.item_types = new_item_types
        for item in data:
            if isinstance(item, abc.model.Model):
                version(item, specification, version_number)


def copy_to(source, target):
    # type: (abc.model.Model, abc.model.Model) -> None
    if source != target:
        if not isinstance(source, abc.model.Model):
            raise TypeError(
                'The source and target must be instances of `%s`' % qualified_name(abc.model.Model)
            )
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
        # if isinstance(source, abc.model.Object):
        #     for property in source_meta.properties
