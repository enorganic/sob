from __future__ import (
    nested_scopes, generators, division, absolute_import, with_statement,
    print_function, unicode_literals
)
from .utilities import (
    compatibility, qualified_name, calling_function_qualified_name
)
from future.utils import native_str
from warnings import warn
import collections
import json as _json
from itertools import chain
import yaml as _yaml
from . import meta, abc, model as model_

compatibility.backport()


Dict = compatibility.typing.Dict


def _object_discrepancies(a, b):
    # type: (model_.Object, model_.Object) -> Dict
    discrepancies = {}
    a_properties = set(meta.read(a).properties.keys())
    b_properties = set(meta.read(b).properties.keys())
    for property_ in a_properties | b_properties:
        try:
            a_value = getattr(a, property_)
        except AttributeError:
            a_value = None
        try:
            b_value = getattr(b, property_)
        except AttributeError:
            b_value = None
        if a_value != b_value:
            discrepancies[property_] = (a_value, b_value)
    return discrepancies


def json(
    model_instance,  # type: abc.model.Model
    raise_validation_errors=True,  # type: bool
):
    # type: (...) -> None
    model(
        model_instance=model_instance,
        format_='json',
        raise_validation_errors=raise_validation_errors
    )


def yaml(
    model_instance,  # type: abc.model.Model
    raise_validation_errors=True,  # type: bool
):
    # type: (...) -> None
    model(
        model_instance=model_instance,
        format_='yaml',
        raise_validation_errors=raise_validation_errors
    )


def model(
    model_instance,  # type: abc.model.Model
    format_,  # type: str
    raise_validation_errors=True,  # type: bool
):
    # type: (...) -> None
    """
    Tests an instance of a `sob.model.Model` sub-class.

    Parameters:

        - model_instance (sob.model.Model):

            An instance of a `sob.model.Model` sub-class.

        - format_ (str):

            The serialization format being tested: 'json' or 'yaml'.

        - raise_validation_errors (bool):

            The function `sob.model.validate` verifies that all required
            attributes are present, as well as any additional validations
            implemented using the model's validation hooks `after_validate`
            and/or `before_validate`.

                - If `True`, errors resulting from `sob.model.validate` are
                  raised.

                - If `False`, errors resulting from `sob.model.validate` are
                  expressed only as warnings.
    """
    if not isinstance(model_instance, abc.model.Model):
        value_representation = repr(model_instance)
        raise TypeError(
            '`%s` requires an instance of `%s` for the parameter `model_instan'
            'ce`, not%s' % (
                calling_function_qualified_name(),
                qualified_name(model_.Model),
                (
                    (':\n%s' if '\n' in value_representation else ' `%s`') %
                    value_representation
                )
            )
        )
    meta.format_(model_instance, format_)
    if isinstance(model_instance, abc.model.Object):
        errors = model_.validate(
            model_instance, raise_errors=raise_validation_errors
        )
        if errors:
            warn('\n' + '\n'.join(errors))
        model_type = type(model_instance)
        string = str(model_instance)
        assert string != ''
        reloaded_model_instance = model_type(string)
        meta.copy_to(
            model_instance,
            reloaded_model_instance
        )
        qualified_model_name = qualified_name(type(model_instance))
        try:
            assert model_instance == reloaded_model_instance
        except AssertionError as e:
            a_serialized = model_.serialize(model_instance)
            b_serialized = model_.serialize(reloaded_model_instance)
            a_representation = repr(model_instance)
            b_representation = repr(reloaded_model_instance)
            a_representation_flattened = (
                ''.join(l.strip() for l in a_representation.split('\n'))
            )
            b_representation_flattened = ''.join(
                l.strip() for l in b_representation.split('\n')
            )
            message = [
                'Discrepancies were found between the instance of `%s` '
                'provided and ' % qualified_model_name +
                'a serialized/deserialized clone:'
            ]
            if a_serialized != b_serialized or (
                a_representation_flattened != b_representation_flattened
            ):
                message.append(
                    '        %s\n        %s\n        %s' % (
                        a_serialized,
                        '==' if a_serialized == b_serialized else '!=',
                        b_serialized
                    )
                )
            if a_representation_flattened != b_representation_flattened:
                message.append(
                    '\n        %s\n        !=\n        %s' % (
                        a_representation_flattened,
                        b_representation_flattened
                    )
                )
            for k, a_b in _object_discrepancies(
                model_instance,
                reloaded_model_instance
            ).items():
                a, b = a_b
                assert a != b
                a_serialized = model_.serialize(a)
                b_serialized = model_.serialize(b)
                a_representation = repr(a)
                b_representation = repr(b)
                a_representation_flattened = ''.join(
                    l.strip()
                    for l in a_representation.split('\n')
                )
                b_representation_flattened = ''.join(
                    l.strip()
                    for l in b_representation.split('\n')
                )
                if a_serialized != b_serialized or (
                    a_representation_flattened != b_representation_flattened
                ):
                    message.append(
                        '\n    %s().%s:\n        %s        \n        %s\n     '
                        '   %s' % (
                            qualified_model_name,
                            k,
                            a_serialized,
                            '==' if a_serialized == b_serialized else '!=',
                            b_serialized
                        )
                    )
                if a_representation_flattened != b_representation_flattened:
                    message.append(
                        '\n        %s\n        !=\n        %s' % (
                            a_representation_flattened,
                            b_representation_flattened
                        )
                    )

            e.args = tuple(
                chain(
                    (
                        (
                            e.args[0] + '\n' + '\n'.join(message)
                            if e.args else
                            '\n'.join(message)
                        ),
                    ),
                    e.args[1:] if e.args else tuple()
                )
            )

            raise e

        reloaded_string = str(reloaded_model_instance)

        try:
            assert string == reloaded_string
        except AssertionError as e:
            m = '\n%s\n!=\n%s' % (string, reloaded_string)
            if e.args:
                e.args = tuple(chain(
                    (e.args[0] + '\n' + m,),
                    e.args[1:]
                ))
            else:
                e.args = (m,)
            raise e

        if format_ == 'json':
            reloaded_marshalled_data = _json.loads(
                string,
                object_hook=collections.OrderedDict,
                object_pairs_hook=collections.OrderedDict
            )
        elif format_ == 'yaml':
            reloaded_marshalled_data = _yaml.load(string)
        else:
            format_representation = repr(format_)
            raise ValueError(
                'Valid serialization types for parameter `format_` are "json" '
                'or "yaml", not' + (
                    (
                        ':\n%s' if '\n' in format_representation else ' %s.'
                    ) % format_representation
                )
            )
        keys = set()
        for property_name, property in meta.read(
            model_instance
        ).properties.items():
            keys.add(property.name or property_name)
            property_value = getattr(model_instance, property_name)
            if isinstance(property_value, abc.model.Model):
                model(
                    property_value,
                    format_=format_,
                    raise_validation_errors=raise_validation_errors
                )
        for k in reloaded_marshalled_data.keys():

            if k not in keys:
                raise KeyError(
                    '"%s" not found in serialized/re-deserialized data: %s' % (
                        k,
                        string
                    )
                )
    elif isinstance(model_instance, abc.model.Array):
        model_.validate(model_instance)
        for item in model_instance:
            if isinstance(item, abc.model.Model) or (
                hasattr(item, '__iter__') and
                (not isinstance(item, (str, native_str, bytes)))
            ):
                model(
                    item,
                    format_=format_,
                    raise_validation_errors=raise_validation_errors
                )
    elif isinstance(model_instance, abc.model.Dictionary):
        model_.validate(model_instance)
        for key, value in model_instance.items():
            if isinstance(value, abc.model.Model) or (
                hasattr(value, '__iter__') and
                (not isinstance(value, (str, native_str, bytes)))
            ):
                model(
                    value,
                    format_=format_,
                    raise_validation_errors=raise_validation_errors
                )
