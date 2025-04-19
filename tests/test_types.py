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


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vv"])
