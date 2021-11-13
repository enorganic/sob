import collections
from copy import deepcopy
from itertools import chain
from typing import (
    Any,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    List,
    Mapping,
    Optional,
    Reversible,
    Sequence,
    Tuple,
    Union,
    ValuesView,
)

from . import abc, errors
from .types import MutableTypes
from .utilities import (
    calling_function_qualified_name,
    indent,
    properties_values,
    qualified_name,
)
from .utilities.assertion import assert_is_instance
from .utilities.inspect import represent
from .utilities.types import NoneType, UNDEFINED, Undefined
from .abc import MarshallableTypes


def _is_dictionary(_dictionary: Any) -> bool:
    return isinstance(_dictionary, abc.Dictionary) or (
        isinstance(_dictionary, type)
        and issubclass(_dictionary, abc.Dictionary)
    )


def _is_array(_array: Any) -> bool:
    return isinstance(_array, abc.Array) or (
        isinstance(_array, type) and issubclass(_array, abc.Array)
    )


def _is_object(_object: Any) -> bool:
    return isinstance(_object, abc.Object) or (
        isinstance(_object, type) and issubclass(_object, abc.Object)
    )


def _is_model(_model: Any) -> bool:
    return _is_object(_model) or _is_array(_model) or _is_dictionary(_model)


class Meta(abc.Meta):
    """
    TODO
    """

    def __copy__(self) -> abc.Meta:
        new_instance: Meta = self.__class__()
        attribute_name: str
        value: Any
        for attribute_name in dir(self):
            if attribute_name[0] != "_":
                value = getattr(self, attribute_name)
                if not callable(value):
                    setattr(new_instance, attribute_name, value)
        assert isinstance(new_instance, abc.Meta)  # to appease `mypy`
        return new_instance

    def __deepcopy__(self, memo: dict = None) -> abc.Meta:
        new_instance: Meta = self.__class__()
        for a, v in properties_values(self):
            # noinspection PyArgumentList
            setattr(new_instance, a, deepcopy(v, memo=memo))
        assert isinstance(new_instance, abc.Meta)  # to appease mypy
        return new_instance

    def __bool__(self) -> bool:
        return True

    def __repr__(self) -> str:
        lines: List[str] = ["%s(" % qualified_name(type(self))]
        property_name: str
        value: Any
        for property_name, value in properties_values(self):
            if isinstance(value, type):
                value_representation = qualified_name(value)
            else:
                value_representation = repr(value)
            lines.append(
                "    %s=%s," % (property_name, indent(value_representation))
            )
        # Strip the trailing comma
        lines[-1] = lines[-1][:-1]
        lines.append(")")
        return "\n".join(lines)


# noinspection PyUnresolvedReferences


class Object(Meta, abc.ObjectMeta):
    """
    TODO
    """

    def __init__(
        self,
        properties: Union[
            Mapping[str, abc.Property],
            Iterable[Tuple[str, abc.Property]],
            abc.Properties,
            None,
        ] = None,
    ) -> None:
        self._properties: Optional[abc.Properties] = None
        self.properties = properties  # type: ignore

    @property
    def properties(self) -> Optional[abc.Properties]:
        return self._properties

    @properties.setter
    def properties(
        self,
        properties_: Union[
            Mapping[str, abc.Property],
            Iterable[Tuple[str, abc.Property]],
            abc.Properties,
            None,
        ],
    ) -> None:
        if isinstance(properties_, abc.Properties):
            new_properties = properties_
        else:
            new_properties = Properties(properties_)
        self._properties = new_properties


class Dictionary(Meta, abc.DictionaryMeta):
    """
    TODO
    """

    def __init__(
        self,
        value_types: Union[
            Iterable[Union[abc.Property, type]],
            abc.Types,
            None,
            abc.Property,
            type,
        ] = None,
    ) -> None:
        self._value_types: Optional[abc.Types] = None
        self.value_types = value_types  # type: ignore

    @property  # type: ignore
    def value_types(self) -> Optional[abc.Types]:
        return self._value_types

    @value_types.setter
    def value_types(
        self,
        value_types: Union[
            Iterable[Union[abc.Property, type]],
            abc.Types,
            None,
            abc.Property,
            type,
        ],
    ) -> None:
        if (value_types is not None) and not isinstance(
            value_types, abc.Types
        ):
            if isinstance(value_types, (type, abc.Property)):
                value_types = (value_types,)
            value_types = MutableTypes(value_types)
        self._value_types = value_types


class Array(Meta, abc.ArrayMeta):
    """
    TODO
    """

    def __init__(
        self,
        item_types: Union[
            Iterable[Union[abc.Property, type]],
            abc.Types,
            None,
            abc.Property,
            type,
        ] = None,
    ):
        self._item_types: Optional[abc.Types] = None
        self.item_types = item_types  # type: ignore

    @property  # type: ignore
    def item_types(self) -> Optional[abc.Types]:
        return self._item_types

    @item_types.setter  # type: ignore
    def item_types(
        self,
        item_types: Union[
            Iterable[Union[abc.Property, type]],
            abc.Types,
            None,
            abc.Property,
            type,
        ],
    ) -> None:
        if (item_types is not None) and not isinstance(item_types, abc.Types):
            if isinstance(item_types, (type, abc.Property)):
                item_types = (item_types,)
            item_types = MutableTypes(item_types)
        self._item_types = item_types


class Properties(abc.Properties):
    """
    TODO
    """

    def __init__(
        self,
        items: Union[
            Mapping[str, abc.Property],
            Iterable[Tuple[str, abc.Property]],
            abc.Properties,
            None,
        ] = None,
    ) -> None:
        self._dict: "abc.OrderedDict[str, abc.Property]" = (
            collections.OrderedDict()
        )
        if items is not None:
            self.update(items)

    def __setitem__(self, key: str, value: abc.Property) -> None:
        if not isinstance(value, abc.Property):
            raise ValueError(value)
        self._dict.__setitem__(key, value)

    def __copy__(self) -> abc.Properties:
        new_instance: abc.Properties = self.__class__(self)
        return new_instance

    # noinspection PyArgumentList
    def __deepcopy__(self, memo: dict = None) -> abc.Properties:
        key: str
        value: abc.Property
        new_instance: Properties = self.__class__(
            tuple(
                (key, deepcopy(value, memo=memo))
                for key, value in self.items()
            )
        )
        assert isinstance(new_instance, abc.Properties)  # for `mypy`
        return new_instance

    @staticmethod
    def _repr_item(key: str, value: Any) -> str:
        value_representation: str = (
            qualified_name(value) if isinstance(value, type) else repr(value)
        )
        value_representation_lines: List[str] = value_representation.split(
            "\n"
        )
        if len(value_representation_lines) > 1:
            indented_lines: List[str] = [value_representation_lines[0]]
            for line in value_representation_lines[1:]:
                indented_lines.append("        " + line)
            value_representation = "\n".join(indented_lines)
            representation = "\n".join(
                [
                    "    (",
                    "        %s," % repr(key),
                    "        %s" % value_representation,
                    "    ),",
                ]
            )
        else:
            representation = "    (%s, %s)," % (
                repr(key),
                value_representation,
            )
        return representation

    def __repr__(self) -> str:
        representation = [qualified_name(type(self)) + "("]
        items = tuple(self.items())
        if len(items) > 0:
            representation[0] += "["
            for key, value in items:
                representation.append(self._repr_item(key, value))
            representation[-1] = representation[-1].rstrip(",")
            representation.append("]")
        representation[-1] += ")"
        if len(representation) > 2:
            return "\n".join(representation)
        else:
            return "".join(representation)

    def keys(self) -> KeysView[str]:
        return self._dict.keys()

    def values(self) -> ValuesView[abc.Property]:
        return self._dict.values()

    def items(self) -> ItemsView[str, abc.Property]:
        return self._dict.items()

    def __getitem__(self, key: str) -> abc.Property:
        return self._dict.__getitem__(key)

    def __delitem__(self, key: str) -> None:
        self._dict.__delitem__(key)

    def __iter__(self) -> Iterator[str]:
        return self._dict.__iter__()

    def __contains__(self, key: str) -> bool:
        return self._dict.__contains__(key)

    def pop(self, key: str, default: Undefined = UNDEFINED) -> abc.Property:
        return self._dict.pop(key)

    def popitem(self) -> Tuple[str, abc.Property]:
        return self._dict.popitem()

    def clear(self) -> None:
        self._dict.clear()

    def update(
        self,
        *args: Union[
            Mapping[str, abc.Property],
            Iterable[Tuple[str, abc.Property]],
            abc.Properties,
        ],
        **kwargs: abc.Property,
    ) -> None:
        other: Union[
            abc.Properties,
            Mapping[str, abc.Property],
            Iterable[Tuple[str, abc.Property]],
        ]
        key: str
        value: abc.Property
        items: Iterable[Tuple[str, abc.Property]] = ()
        for other in args:
            if isinstance(other, (Mapping, abc.Properties)):
                if isinstance(other, (Reversible, abc.Properties)):
                    assert isinstance(other, (Mapping, abc.Properties))
                    items = chain(items, other.items())
                else:
                    items = chain(
                        items, sorted(other.items(), key=lambda item: item[0])
                    )
            else:
                items = chain(items, other)
        for key, value in chain(
            items, sorted(kwargs.items(), key=lambda item: item[0])
        ):
            self[key] = value

    def setdefault(
        self, key: str, default: Optional[abc.Property] = None
    ) -> Optional[abc.Property]:
        if not isinstance(default, (NoneType, abc.Property)):
            raise ValueError(default)
        return self._dict.setdefault(key, default)

    def get(
        self, key: str, default: Optional[abc.Property] = None
    ) -> Optional[abc.Property]:
        return self._dict.get(key, default)

    def __eq__(self, other: Any) -> bool:
        if type(self) is not type(other):
            return False
        return self._dict.__eq__(other)

    def __len__(self) -> int:
        return self._dict.__len__()


def read(model: Union[type, abc.Model]) -> Any:
    if isinstance(model, abc.Model):
        return getattr(model, "_meta") or read(type(model))
    elif isinstance(model, type):
        if issubclass(model, abc.Model):
            return getattr(model, "_meta")
        else:
            raise TypeError(
                "%s requires a parameter which is an instance or sub-class of "
                "`%s`, not `%s`"
                % (
                    calling_function_qualified_name(),
                    qualified_name(abc.Model),
                    qualified_name(model),
                )
            )
    else:
        repr_model: str = repr(model)
        raise TypeError(
            "%s requires a parameter which is an instance or sub-class of "
            "`%s`, not%s"
            % (
                calling_function_qualified_name(),
                qualified_name(abc.Model),
                (
                    ":\n" + repr_model
                    if "\n" in repr_model
                    else " `%s`" % repr_model
                ),
            )
        )


def object_read(model: Union[type, abc.Object]) -> Optional[abc.ObjectMeta]:
    return read(model)


def array_read(model: Union[type, abc.Array]) -> Optional[abc.ArrayMeta]:
    return read(model)


def dictionary_read(
    model: Union[type, abc.Dictionary]
) -> Optional[abc.DictionaryMeta]:
    return read(model)


def writable(model: Union[type, abc.Model]) -> Any:
    """
    This function returns an instance of [sob.meta.Meta](#Meta) which can
    be safely modified. If the class or model instance inherits its metadata
    from a class or base class, this function will create and return a
    duplicate of that metadata assigned directly to the class or instance
    represented by `model`.
    """
    assert _is_model(model)
    if isinstance(model, abc.Model):
        if getattr(model, "_meta") is None:
            model._meta = deepcopy(writable(type(model)))
    elif isinstance(model, type) and issubclass(
        model, (abc.Object, abc.Dictionary, abc.Array)
    ):
        model_meta: Union[
            abc.ObjectMeta, abc.DictionaryMeta, abc.ArrayMeta
        ] = getattr(model, "_meta")
        if model_meta is None:
            # If this model doesn't have any metadata yet--create an
            # appropriate metadata instance
            model._meta = (
                Object()
                if issubclass(model, abc.Object)
                else Array()
                if issubclass(model, abc.Array)
                else Dictionary()
            )
        else:
            # Ensure that the metadata is not being inherited from a base
            # class by copying the metadata if it has the same ID as any
            # base class
            for base in model.__bases__:
                base_meta: Optional[abc.Meta] = None
                try:
                    base_meta = getattr(base, "_meta")
                except AttributeError:
                    pass
                if base_meta is not None:
                    if model_meta is base_meta:
                        model._meta = deepcopy(model_meta)
                        break
    else:
        repr_model = represent(model)
        raise TypeError(
            "%s requires a parameter which is an instance or sub-class of "
            "`%s`, not%s"
            % (
                calling_function_qualified_name(),
                qualified_name(abc.Model),
                (
                    ":\n" + repr_model
                    if "\n" in repr_model
                    else " `%s`" % repr_model
                ),
            )
        )
    return getattr(model, "_meta")


def object_writable(model: Union[type, abc.Object]) -> abc.ObjectMeta:
    """
    This function returns an instance of [sob.meta.Object](#meta-Object) which
    can be safely modified. If the class or model instance inherits its
    metadata from a class or base class, this function will create and return a
    duplicate of that metadata assigned directly to the class or instance
    represented by `model`.
    """
    return writable(model)


def array_writable(model: Union[type, abc.Array]) -> abc.ArrayMeta:
    """
    This function returns an instance of [sob.meta.Array](#meta-Array) which
    can be safely modified. If the class or model instance inherits its
    metadata from a class or base class, this function will create and return a
    duplicate of that metadata assigned directly to the class or instance
    represented by `model`.
    """
    return writable(model)


def dictionary_writable(
    model: Union[type, abc.Dictionary]
) -> abc.DictionaryMeta:
    """
    This function returns an instance of
    [sob.meta.Dictionary](#meta-Dictionary) which can be safely modified. If
    the class or model instance inherits its metadata from a class or base
    class, this function will create and return a duplicate of that metadata
    assigned directly to the class or instance represented by `model`.
    """
    return writable(model)


def write(model: Union[type, abc.Model], meta: Optional[abc.Meta]) -> None:
    if meta is not None:
        model_type: type
        if isinstance(model, abc.Model):
            model_type = type(model)
        elif isinstance(model, type) and issubclass(model, abc.Model):
            model_type = model
        else:
            repr_model = repr(model)
            raise TypeError(
                "{} requires a value for the parameter `model` which is an "
                "instance or sub-class of `{}`, not{}".format(
                    calling_function_qualified_name(),
                    qualified_name(abc.Model),
                    (
                        ":\n" + repr_model
                        if "\n" in repr_model
                        else " `%s`" % repr_model
                    ),
                )
            )
        metadata_type: type = (
            Object
            if issubclass(model_type, abc.Object)
            else Array
            if issubclass(model_type, abc.Array)
            else Dictionary
            if issubclass(model_type, abc.Dictionary)
            else Meta
        )
        if not isinstance(meta, metadata_type):
            raise ValueError(
                "Metadata assigned to `%s` must be of type `%s`"
                % (qualified_name(model_type), qualified_name(metadata_type))
            )
    setattr(model, "_meta", meta)


def get_pointer(model: abc.Model) -> Optional[str]:
    return getattr(model, "_pointer")


def _read_object(model: Union[abc.Object, type]) -> abc.ObjectMeta:
    metadata: Optional[abc.Meta] = read(model)
    assert isinstance(metadata, abc.ObjectMeta)
    return metadata


def _read_object_properties(
    model: Union[abc.Object, type]
) -> Iterable[Tuple[str, abc.Property]]:
    metadata: abc.ObjectMeta = _read_object(model)
    return (metadata.properties or collections.OrderedDict()).items()


def _read_object_property_names(
    model: Union[abc.Object, type]
) -> Iterable[str]:
    metadata: abc.ObjectMeta = _read_object(model)
    return (metadata.properties or collections.OrderedDict()).keys()


def escape_reference_token(reference_token: str) -> str:
    return reference_token.replace("~", "~0").replace("/", "~1")


def set_pointer(model: abc.Model, pointer_: str) -> None:
    key: str
    value: Any
    assert_is_instance("pointer_", pointer_, str)
    model._pointer = pointer_
    if isinstance(model, abc.Dictionary):
        for key, value in model.items():
            if isinstance(
                value,
                (abc.Object, abc.Dictionary, abc.Array),
            ):
                pointer(
                    value,
                    "{}/{}".format(
                        pointer_,
                        (
                            escape_reference_token(key)
                            if isinstance(key, str)
                            else str(key)
                        ),
                    ),
                )
    elif isinstance(model, abc.Object):
        property_name: str
        property_: abc.Property
        for property_name, property_ in _read_object_properties(model):
            key = property_.name or property_name
            value = getattr(model, property_name)
            if isinstance(
                value,
                (abc.Object, abc.Dictionary, abc.Array),
            ):
                pointer(
                    value,
                    "{}/{}".format(
                        pointer_,
                        (
                            escape_reference_token(key)
                            if isinstance(key, str)
                            else str(key)
                        ),
                    ),
                )
    elif isinstance(model, abc.Array):
        index: int
        for index in range(len(model)):
            value = model[index]
            if isinstance(
                value,
                (abc.Object, abc.Dictionary, abc.Array),
            ):
                pointer(value, "%s/%s" % (pointer_, str(index)))


def pointer(model: abc.Model, pointer_: Optional[str] = None) -> Optional[str]:
    """
    Get or set a model's pointer
    """
    assert_is_instance(
        "model",
        model,
        (abc.Object, abc.Dictionary, abc.Array),
    )
    if pointer_ is not None:
        set_pointer(model, pointer_)
    return get_pointer(model)


def _traverse_models(
    model_instance: abc.Model,
) -> Iterable[abc.Model]:
    """
    Iterate over all child model instances
    """
    if isinstance(model_instance, abc.Dictionary):
        for value in model_instance.values():
            if isinstance(
                value,
                (abc.Object, abc.Dictionary, abc.Array),
            ):
                yield value
    elif isinstance(model_instance, abc.Object):
        property_name: str
        for property_name in _read_object_property_names(model_instance):
            value = getattr(model_instance, property_name)
            if isinstance(
                value,
                (abc.Object, abc.Dictionary, abc.Array),
            ):
                yield value
    elif isinstance(model_instance, abc.Array):
        for value in model_instance:
            if isinstance(
                value,
                (abc.Object, abc.Dictionary, abc.Array),
            ):
                yield value


# noinspection PyShadowingNames
def set_url(model_instance: abc.Model, source_url: Optional[str]) -> None:
    assert_is_instance(
        "model",
        model_instance,
        (abc.Object, abc.Dictionary, abc.Array),
    )
    if source_url is not None:
        assert_is_instance("url_", source_url, str)
    model_instance._url = source_url
    child_model: abc.Model
    for child_model in _traverse_models(model_instance):
        set_url(child_model, source_url)


def get_url(model: abc.Model) -> Optional[str]:
    return getattr(model, "_url")


def url(model: abc.Model, url_: Optional[str] = None) -> Optional[str]:
    if url_ is not None:
        set_url(model, url_)
    return get_url(model)


def set_format(
    model: abc.Model, serialization_format: Optional[str] = None
) -> None:
    assert_is_instance(
        "model",
        model,
        (abc.Object, abc.Dictionary, abc.Array),
    )
    assert_is_instance("serialization_format", serialization_format, str)
    model._format = serialization_format
    if isinstance(model, abc.Dictionary):
        for value in model.values():
            if isinstance(
                value,
                (abc.Object, abc.Dictionary, abc.Array),
            ):
                set_format(value, serialization_format)
    elif isinstance(model, abc.Object):
        for property_name in _read_object_property_names(model):
            value = getattr(model, property_name)
            if isinstance(
                value,
                (abc.Object, abc.Dictionary, abc.Array),
            ):
                set_format(value, serialization_format)
    elif isinstance(model, abc.Array):
        for value in model:
            if isinstance(
                value,
                (abc.Object, abc.Dictionary, abc.Array),
            ):
                set_format(value, serialization_format)


def get_format(model: abc.Model) -> Optional[str]:
    return getattr(model, "_format")


def format_(
    model: abc.Model, serialization_format: Optional[str] = None
) -> Optional[str]:
    if serialization_format is not None:
        set_format(model, serialization_format)
    return get_format(model)


def _version_match(
    property_: abc.Property,
    specification: str,
    version_number: Union[str, int, Sequence[int]],
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
    properties_: Union[abc.Types, Iterable[Union[abc.Property, type]]],
    specification: str,
    version_number: Union[str, int, Sequence[int]],
) -> Optional[Tuple[Union[abc.Property, type], ...]]:
    changed: bool = False
    new_properties: List[Union[abc.Property, type]] = []
    property_: Union[abc.Property, type]
    for property_ in properties_:
        if isinstance(property_, abc.Property):
            if _version_match(property_, specification, version_number):
                new_property = _version_property(
                    property_, specification, version_number
                )
                if new_property is not property_:
                    changed = True
                new_properties.append(new_property)
            else:
                # Exclude this property, as it's not a match
                changed = True
        else:
            new_properties.append(property_)
    if changed:
        return tuple(new_properties)
    else:
        return None


def _version_property(
    property_: abc.Property,
    specification: str,
    version_number: Union[str, int, Sequence[int]],
) -> abc.Property:
    changed: bool = False
    if isinstance(property_, abc.ArrayProperty) and (
        property_.item_types is not None
    ):
        item_type_items = _version_properties(
            property_.item_types, specification, version_number
        )
        if item_type_items is not None:
            if not changed:
                property_ = deepcopy(property_)
            item_types = MutableTypes(item_type_items)
            assert isinstance(item_types, abc.Types)
            property_.item_types = item_types  # type: ignore
            changed = True
    elif isinstance(property_, abc.DictionaryProperty) and (
        property_.value_types is not None
    ):
        value_types_items = _version_properties(
            property_.value_types, specification, version_number
        )
        if value_types_items is not None:
            if not changed:
                property_ = deepcopy(property_)
            value_types = MutableTypes(value_types_items)
            assert isinstance(value_types, abc.Types)
            property_.value_types = value_types  # type: ignore
            changed = True
    if property_.types is not None:
        types_items = _version_properties(
            property_.types, specification, version_number
        )
        if types_items is not None:
            if not changed:
                property_ = deepcopy(property_)
            types = MutableTypes(types_items)
            assert isinstance(types, abc.Types)
            property_.types = types  # type: ignore
    return property_


def _version_object(
    data: abc.Object,
    specification: str,
    version_number: Union[str, int, Sequence[int]],
) -> None:
    instance_meta: Optional[abc.Meta] = read(data)
    assert isinstance(instance_meta, abc.ObjectMeta)  # for `mypy`
    assert isinstance(instance_meta.properties, abc.Properties)  # for `mypy`
    if instance_meta.properties:
        class_meta = read(type(data))
        property_name: str
        property_: abc.Property
        for property_name, property_ in tuple(
            instance_meta.properties.items()
        ):
            if _version_match(property_, specification, version_number):
                new_property = _version_property(
                    property_, specification, version_number
                )
                if new_property is not property_:
                    if instance_meta is class_meta:
                        instance_meta = writable(data)
                    assert isinstance(
                        instance_meta, abc.ObjectMeta
                    )  # for `mypy`
                    assert isinstance(  # for `mypy`
                        instance_meta.properties, abc.Properties
                    )
                    instance_meta.properties[property_name] = new_property
            else:
                if instance_meta is class_meta:
                    instance_meta = writable(data)
                assert isinstance(instance_meta, abc.ObjectMeta)  # for `mypy`
                assert isinstance(  # for `mypy`
                    instance_meta.properties, abc.Properties
                )
                del instance_meta.properties[property_name]
                version_ = getattr(data, property_name)
                if version_ is not None:
                    raise errors.VersionError(
                        "%s - the property `%s` is not applicable in %s "
                        "version %s:\n%s"
                        % (
                            qualified_name(type(data)),
                            property_name,
                            specification,
                            version_number,
                            str(data),
                        )
                    )
            value = getattr(data, property_name)
            if isinstance(value, abc.Model):
                version(value, specification, version_number)


def _version_dictionary(
    data: abc.Dictionary,
    specification: str,
    version_number: Union[str, int, Sequence[int]],
) -> None:
    instance_meta: Optional[abc.Meta] = read(data)
    assert isinstance(instance_meta, abc.DictionaryMeta)  # for `mypy`
    class_meta = read(type(data))
    if instance_meta and instance_meta.value_types:
        new_value_types = _version_properties(
            instance_meta.value_types, specification, version_number
        )
        if new_value_types:
            if instance_meta is class_meta:
                instance_meta = writable(data)
            setattr(instance_meta, "value_types", new_value_types)
    for value in data.values():
        if isinstance(value, (abc.Object, abc.Dictionary, abc.Array)):
            version(value, specification, version_number)


def _version_array(
    data: abc.Array,
    specification: str,
    version_number: Union[str, int, Sequence[int]],
) -> None:
    instance_meta = read(data)
    class_meta = read(type(data))
    if isinstance(instance_meta, abc.ArrayMeta) and instance_meta.item_types:
        new_item_types = _version_properties(
            instance_meta.item_types, specification, version_number
        )
        if new_item_types:
            if instance_meta is class_meta:
                instance_meta = writable(data)
            setattr(instance_meta, "item_types", new_item_types)
    for item in data:
        if isinstance(item, abc.Model):
            version(item, specification, version_number)


def version(
    data: abc.Model,
    specification: str,
    version_number: Union[str, int, Sequence[int]],
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
    assert_is_instance("data", data, abc.Model)
    if isinstance(data, abc.Object):
        _version_object(data, specification, version_number)
    elif isinstance(data, abc.Dictionary):
        _version_dictionary(data, specification, version_number)
    elif isinstance(data, abc.Array):
        _version_array(data, specification, version_number)


def _copy_object_to(
    source: abc.Object,
    target: abc.Object,
) -> None:
    source_meta: Optional[abc.Meta] = read(source)
    assert isinstance(source_meta, (NoneType, abc.ObjectMeta))
    if (source_meta is not None) and (source_meta.properties is not None):
        for property_name in source_meta.properties.keys():
            source_property_value = getattr(source, property_name)
            target_property_value = getattr(target, property_name)
            if target_property_value and isinstance(
                source_property_value, abc.Model
            ):
                copy_to(source_property_value, target_property_value)


def _copy_array_to(source: abc.Array, target: abc.Array) -> None:
    for index, value in enumerate(source):
        target_value = target[index]
        if target_value and isinstance(value, abc.Model):
            assert isinstance(target_value, abc.Model)
            copy_to(value, target_value)


def _copy_dictionary_to(
    source: abc.Dictionary, target: abc.Dictionary
) -> None:
    key: str
    value: MarshallableTypes
    for key, value in source.items():
        target_value: Optional[MarshallableTypes] = target[key]
        if (
            target_value
            and isinstance(value, abc.Model)
            and isinstance(target_value, abc.Model)
        ):
            copy_to(value, target_value)


def copy_to(source: abc.Model, target: abc.Model) -> None:
    """
    This function copies metadata from one model instance to another
    """
    # Verify both arguments are models
    argument_name: str
    value: MarshallableTypes
    target_value: MarshallableTypes
    argument_value: abc.Model
    for argument_name, argument_value in (
        ("source", source),
        ("target", target),
    ):
        assert_is_instance(argument_name, argument_value, abc.Model)
    # Verify both arguments are of of the same `type`
    assert type(source) is type(target)
    # Copy the metadata
    source_meta: Optional[abc.Meta] = read(source)
    target_meta: Optional[abc.Meta] = read(target)
    if source_meta is not target_meta:
        write(target, source_meta)
    # ... and recursively do the same for member data
    if isinstance(source_meta, abc.ObjectMeta) and (
        source_meta.properties is not None
    ):
        assert isinstance(source, abc.Object)
        assert isinstance(target, abc.Object)
        _copy_object_to(source, target)
    elif isinstance(source, abc.Array):
        assert isinstance(target, abc.Array)
        _copy_array_to(source, target)
    elif isinstance(source, abc.Dictionary):
        assert isinstance(target, abc.Dictionary)
        _copy_dictionary_to(source, target)
