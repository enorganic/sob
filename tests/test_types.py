import decimal
import pickle
from copy import copy

import pytest

import sob
import sob._types
import sob.types


def test_undefined() -> None:
    """
    Test the behavior of the `Undefined` type.
    """
    assert isinstance(sob.UNDEFINED, sob.Undefined)
    # Check to make sure only one instance of Undefined can be created
    error_raised: bool = False
    try:
        sob.Undefined()
    except sob.errors.DefinitionExistsError:
        error_raised = True
    assert error_raised
    # Make sure UNDEFINED evaluates as False
    assert not sob.UNDEFINED
    # Make sure UNDEFINED hashes to a constant value
    assert hash(sob.UNDEFINED) == 0
    # Make sure UNDEFINED copies correctly
    assert copy(sob.UNDEFINED) is sob.UNDEFINED
    # Make sure UNDEFINED pickles correctly
    assert pickle.loads(pickle.dumps(sob.UNDEFINED)) is sob.UNDEFINED


def test_none_type() -> None:
    """
    Test the behavior of the `NoneType` type.
    """
    assert isinstance(None, sob.NoneType)


def test_null() -> None:
    """
    Test the behavior of the `Null` type.
    """
    assert isinstance(sob.NULL, sob.Null)
    # Check to make sure only one instance of `Null` can be created
    error_raised: bool = False
    try:
        sob.Null()
    except sob.errors.DefinitionExistsError:
        error_raised = True
    assert error_raised
    # Make sure NULL evaluates as False
    assert not sob.NULL
    # Make sure NULL hashes to a constant value and stringifies as "null"
    assert hash(sob.NULL) == 0
    assert str(sob.NULL) == "null"
    assert sob.Null._marshal() is None  # noqa: SLF001
    # Make sure NULL copies correctly
    assert copy(sob.NULL) is sob.NULL
    # Make sure NULL pickles correctly
    assert pickle.loads(pickle.dumps(sob.NULL)) is sob.NULL


def test_types() -> None:
    sob.Types(
        [
            int,
            str,
            float,
            sob.Property(
                types=sob.Types(
                    [
                        str,
                    ]
                )
            ),
        ]
    )
    # Make sure only usable types are accepted
    error_raised: bool = False
    try:
        sob.Types([int, str, float, object])
    except TypeError:
        error_raised = True
    assert error_raised


def test_mutable_types() -> None:
    types: sob.abc.MutableTypes = sob.MutableTypes(
        [
            int,
            float,
            sob.Property(
                types=sob.Types(
                    [
                        str,
                    ]
                )
            ),
        ]
    )
    # Make sure that a MutableTypes instance can be modified
    types.append(str)
    types.pop(0)


def test_types_bare_type() -> None:
    """
    A bare type (not wrapped in a sequence) is accepted and wrapped.
    """
    types_ = sob.Types(str)
    assert list(types_) == [str]


def test_types_copy() -> None:
    types_ = sob.Types([int, str])
    copied = copy(types_)
    assert copied is not types_
    assert list(copied) == list(types_)


def test_mutable_types_protocol() -> None:
    """
    Exercise the full `MutableList`-like protocol of `MutableTypes`.
    """
    types_: sob.MutableTypes = sob.MutableTypes([int, str])
    types_[0] = float
    assert types_[0] is float
    types_.extend([bool])
    assert bool in types_
    del types_[0]
    assert float not in types_
    types_ += [bytes]
    assert bytes in types_
    new_types = types_ + [decimal.Decimal]
    assert decimal.Decimal in new_types
    assert decimal.Decimal not in types_


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vv"])
