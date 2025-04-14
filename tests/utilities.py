from __future__ import annotations

import json as _json
from typing import TYPE_CHECKING, Any
from warnings import warn

from sob import abc, meta
from sob._types import NoneType
from sob.errors import ObjectDiscrepancyError
from sob.model import serialize, validate
from sob.utilities import get_qualified_name

if TYPE_CHECKING:
    from collections.abc import Sequence


def _get_object_property_names(object_: abc.Object) -> set[str]:
    meta_: abc.Meta | None = meta.read_model_meta(object_)
    if not isinstance(meta_, (abc.ObjectMeta, NoneType)):
        raise TypeError(meta_)
    return set(
        meta_.properties.keys()
        if ((meta_ is not None) and (meta_.properties is not None))
        else ()
    )


def _object_discrepancies(
    object_a: abc.Object, object_b: abc.Object
) -> dict[
    str,
    tuple[abc.MarshallableTypes | None, abc.MarshallableTypes | None],
]:
    discrepancies: dict[
        str,
        tuple[abc.MarshallableTypes | None, abc.MarshallableTypes | None],
    ] = {}
    for property_ in sorted(
        (
            _get_object_property_names(object_a)
            | _get_object_property_names(object_b)
        ),
        key=lambda item: item[0],
    ):
        a_value: abc.MarshallableTypes | None
        b_value: abc.MarshallableTypes | None
        try:
            a_value = getattr(object_a, property_)
        except AttributeError:
            a_value = None
        try:
            b_value = getattr(object_b, property_)
        except AttributeError:
            b_value = None
        if a_value != b_value:
            discrepancies[property_] = (a_value, b_value)
    return discrepancies


def _get_value_discrepancies_error_message(
    class_name: str,
    property_name: str,
    property_value_a: Any,
    property_value_b: Any,
) -> str:
    a_serialized = serialize(property_value_a)
    b_serialized = serialize(property_value_b)
    a_representation = repr(property_value_a)
    b_representation = repr(property_value_b)
    a_representation = "".join(
        line.strip() for line in a_representation.split("\n")
    )
    b_representation = "".join(
        line.strip() for line in b_representation.split("\n")
    )
    message: list[str] = []
    if a_serialized != b_serialized or (a_representation != b_representation):
        message.append(
            "\n    {}().{}:\n        {}        \n        {}\n     "
            "   {}".format(
                class_name,
                property_name,
                a_serialized,
                "==" if a_serialized == b_serialized else "!=",
                b_serialized,
            )
        )
    if a_representation != b_representation:
        message.append(
            f"\n        {a_representation}\n        !=\n        "
            f"{b_representation}"
        )
    return "\n".join(message)


def _get_object_discrepancies_error_message(
    object_a: abc.Object, object_b: abc.Object
) -> str:
    a_serialized: str = serialize(object_a)
    b_serialized: str = serialize(object_b)
    a_representation: str = "".join(
        line.strip() for line in repr(object_a).split("\n")
    )
    b_representation = "".join(
        line.strip() for line in repr(object_b).split("\n")
    )
    class_name: str = get_qualified_name(type(object_a))
    message = [
        "Discrepancies were found between the instance of "
        f"`{class_name}` provided and "
        "a serialized/deserialized clone:"
    ]
    if a_serialized != b_serialized or (a_representation != b_representation):
        message.append(
            "        {}\n        {}\n        {}".format(
                a_serialized,
                "==" if a_serialized == b_serialized else "!=",
                b_serialized,
            )
        )
    if a_representation != b_representation:
        message.append(
            f"\n        {a_representation}\n        !=\n        "
            f"{b_representation}"
        )
    property_name: str
    property_values: tuple[
        abc.MarshallableTypes | None, abc.MarshallableTypes | None
    ]
    for property_name, property_values in _object_discrepancies(
        object_a, object_b
    ).items():
        property_value_a: abc.MarshallableTypes | None
        property_value_b: abc.MarshallableTypes | None
        property_value_a, property_value_b = property_values
        message.append(
            _get_value_discrepancies_error_message(
                class_name, property_name, property_value_a, property_value_b
            )
        )
    return "\n".join(message)


def _get_object_discrepancies_error(
    object_instance: abc.Object, reloaded_object_instance: abc.Object
) -> ObjectDiscrepancyError:
    message: str = _get_object_discrepancies_error_message(
        object_instance, reloaded_object_instance
    )
    return ObjectDiscrepancyError(message)


def _remarshal_object(string_object: str, object_instance: abc.Object) -> None:
    reloaded_marshalled_data = _json.loads(
        string_object,
        object_hook=dict,
        object_pairs_hook=dict,
    )
    keys: set[str] = set()
    instance_meta: abc.Meta | None = meta.read_model_meta(object_instance)
    if not isinstance(instance_meta, (abc.ObjectMeta, NoneType)):
        raise TypeError(instance_meta)
    if (instance_meta is not None) and (instance_meta.properties is not None):
        for property_name, property_ in instance_meta.properties.items():
            keys.add(property_.name or property_name)
        for key in reloaded_marshalled_data:
            if key not in keys:
                message: str = (
                    f'"{key}" not found in serialized/re-deserialized data: '
                    f"{string_object}"
                )
                raise KeyError(message)


def _reload_object(object_instance: abc.Object) -> None:
    object_type: type = type(object_instance)
    string_object: str = str(object_instance)
    if string_object == "":
        raise ValueError(string_object)
    reloaded_object_instance = object_type(string_object)
    meta._copy_model_meta_to(  # noqa: SLF001
        object_instance, reloaded_object_instance
    )
    if object_instance != reloaded_object_instance:
        raise _get_object_discrepancies_error(
            object_instance, reloaded_object_instance
        )
    reloaded_string = str(reloaded_object_instance)
    if string_object != reloaded_string:
        msg = f"\n{string_object}\n!=\n{reloaded_string}"
        raise ObjectDiscrepancyError(msg)
    _remarshal_object(string_object, object_instance)


def _serial_validate_object(
    object_instance: abc.Object,
    *,
    raise_validation_errors: bool = True,
) -> None:
    errors: Sequence[str] = validate(
        object_instance, raise_errors=raise_validation_errors
    )
    if errors:
        warn("\n" + "\n".join(errors), stacklevel=2)
    _reload_object(object_instance)
    instance_meta: abc.Meta | None = meta.read_model_meta(object_instance)
    if not isinstance(instance_meta, (abc.ObjectMeta, NoneType)):
        raise TypeError(instance_meta)
    if (instance_meta is not None) and (instance_meta.properties is not None):
        # Recursively test property values
        property_name: str
        for property_name in instance_meta.properties:
            property_value: Any = getattr(object_instance, property_name)
            if isinstance(property_value, abc.Model):
                validate_serialization_is_replicable(
                    property_value,
                    raise_validation_errors=raise_validation_errors,
                )


def validate_serialization_is_replicable(
    model_instance: abc.Model,
    *,
    raise_validation_errors: bool = True,
) -> None:
    """
    Validates an instance of a `sob.model.Model` sub-class and verifies that
    the object can be serialized, then subsequently de-serialized,
    without introducing discrepancies.

    Please note that this validation will only succeed for models which
    have no extraneous properties (all properties have metadata).

    Parameters:
        model_instance: An instance of a `sob.model.Model` sub-class.
        raise_validation_errors:
            The function `sob.model.validate` verifies that all required
            attributes are present, as well as any additional validations
            implemented using the model's validation hooks `after_validate`
            and/or `before_validate`. If `True`, errors resulting from
            `sob.model.validate` are raised. If `False`, errors resulting
            from `sob.model.validate` are expressed only as warnings.
    """
    if not isinstance(model_instance, abc.Model):
        raise TypeError(model_instance)
    if isinstance(model_instance, abc.Object):
        _serial_validate_object(
            model_instance, raise_validation_errors=raise_validation_errors
        )
    elif isinstance(model_instance, abc.Array):
        validate(model_instance)
        for item in model_instance:
            if isinstance(item, abc.Model):
                validate_serialization_is_replicable(
                    item,
                    raise_validation_errors=raise_validation_errors,
                )
    elif isinstance(model_instance, abc.Dictionary):
        validate(model_instance)
        key: str
        value: abc.MarshallableTypes
        for value in model_instance.values():
            if isinstance(value, abc.Model):
                validate_serialization_is_replicable(
                    value,
                    raise_validation_errors=raise_validation_errors,
                )
