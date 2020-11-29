import collections
import operator
import re

from decimal import Decimal
from itertools import chain
from typing import Any, Callable, List, Optional, Sequence, Tuple, Union

from . import abc
from .utilities.assertion import assert_is_instance
from .utilities.inspect import represent

_DOT_SYNTAX_RE = re.compile(r"^\d+(\.\d+)*$")


def _are_versions_compatible(
    version_a: Tuple[int, ...], version_b: Tuple[int, ...]
) -> bool:
    length_a: int = len(version_a)
    length_b: int = len(version_b)
    # If `version_a` is less precise than `version_b`--they must have the same
    # version number up to the precision held by `version_a`.
    if length_a < length_b:
        return version_a == tuple(version_b[:length_a])
    if length_b > 1:
        return (
            version_b
            <= version_a
            < (tuple(version_b[:-2]) + (version_b[-2] + 1, 0))
        )
    return version_a == version_b


def _are_versions_equal(
    version_a: Tuple[int, ...], version_b: Tuple[int, ...]
) -> bool:
    length_a: int = len(version_a)
    length_b: int = len(version_b)
    if length_a != length_b:
        length: int = min(length_a, length_b)
        version_a = tuple(version_a[:length])
        version_b = tuple(version_b[:length])
    return version_a == version_b


_VERSION_PROPERTIES_COMPARE_FUNCTIONS: Tuple[Tuple[str, Callable], ...] = (
    ("exactly_equals", operator.eq),
    ("equals", _are_versions_equal),
    ("not_equals", operator.ne),
    ("less_than", operator.lt),
    ("less_than_or_equal_to", operator.le),
    ("greater_than", operator.gt),
    ("greater_than_or_equal_to", operator.ge),
    ("compatible_with", _are_versions_compatible),
)
_REPR_OPERATORS_VERSION_PROPERTIES: Tuple[Tuple[str, str], ...] = (
    ("===", "exactly_equals"),
    ("<=", "less_than_or_equal_to"),
    (">=", "greater_than_or_equal_to"),
    ("!=", "not_equals"),
    ("==", "equals"),
    ("~=", "compatible_with"),
    ("<", "less_than"),
    (">", "greater_than"),
    ("=", "equals"),
)
_VERSION_PROPERTIES_REPR_OPERATORS: Tuple[Tuple[str, str], ...] = (
    ("exactly_equals", "==="),
    ("equals", "=="),
    ("compatible_with", "~="),
    ("not_equals", "!="),
    ("greater_than", ">"),
    ("greater_than_or_equal_to", ">="),
    ("less_than", "<"),
    ("less_than_or_equal_to", "<="),
)


def _version_string_as_tuple(version_string: str) -> Tuple[int, ...]:
    assert _DOT_SYNTAX_RE.match(version_string)
    return tuple(int(item) for item in version_string.split("."))


def _version_number_as_tuple(
    version_number: Union[float, int, Decimal]
) -> Tuple[int, ...]:
    return _version_string_as_tuple(str(version_number))


def _version_sequence_as_tuple(
    version_sequence: Sequence[Union[str, int, float, Decimal]]
) -> Tuple[int, ...]:
    return tuple(
        chain(
            *(
                (
                    _version_string_as_tuple(str(item))
                    if float(item) % 1
                    else [int(item)]
                )
                for item in version_sequence
            )
        )
    )


def _version_as_tuple(
    version_: Union[str, int, float, Decimal, Sequence[int]]
) -> Tuple[int, ...]:
    version_tuple: Tuple[int, ...]
    assert_is_instance(
        "version_",
        version_,
        (str, int, float, Decimal, collections.abc.Sequence),
    )
    if isinstance(version_, str):
        version_tuple = _version_string_as_tuple(version_)
    elif isinstance(version_, (int, float, Decimal)):
        version_tuple = _version_number_as_tuple(version_)
    else:
        version_tuple = _version_sequence_as_tuple(version_)
    return version_tuple


class Version(abc.Version):
    def __init__(
        self,
        version_string: Optional[str] = None,
        specification: str = "",
        compatible_with: Optional[
            Sequence[Union[str, int, float, Decimal]]
        ] = None,
        equals: Optional[Sequence[Union[str, int, float, Decimal]]] = None,
        exactly_equals: Optional[
            Sequence[Union[str, int, float, Decimal]]
        ] = None,
        not_equals: Optional[Sequence[Union[str, int, float, Decimal]]] = None,
        less_than: Optional[Sequence[Union[str, int, float, Decimal]]] = None,
        less_than_or_equal_to: Optional[
            Sequence[Union[str, int, float, Decimal]]
        ] = None,
        greater_than: Optional[
            Sequence[Union[str, int, float, Decimal]]
        ] = None,
        greater_than_or_equal_to: Optional[
            Sequence[Union[str, int, float, Decimal]]
        ] = None,
    ) -> None:
        self.specification = specification
        self.compatible_with = compatible_with
        self.exactly_equals = exactly_equals
        self.equals = equals
        self.not_equals = not_equals
        self.less_than = less_than
        self.less_than_or_equal_to = less_than_or_equal_to
        self.greater_than = greater_than
        self.greater_than_or_equal_to = greater_than_or_equal_to
        if version_string is not None:
            assert isinstance(version_string, str)
            self._update_version_parameters_from_string(version_string)

    def _update_version_parameters_from_string(self, version_: str) -> None:
        specification: str = ""
        for version_specifier in version_.split(","):
            spec: str
            operator_str: str
            variable_name: str
            for (
                operator_str,
                variable_name,
            ) in _REPR_OPERATORS_VERSION_PROPERTIES:
                if operator_str in version_specifier:
                    (
                        spec,
                        version_number_string,
                    ) = version_specifier.strip().split(operator_str)
                    if spec:
                        if self.specification:
                            if spec != self.specification:
                                raise ValueError(
                                    "Multiple specifications cannot be "
                                    "associated with one instance of "
                                    "`sob.meta.Version`:\n"
                                    f"- {represent(spec)}\n"
                                    f"- {represent(specification)}\n"
                                )
                        else:
                            self.specification = spec
                    setattr(self, variable_name, version_number_string)
                    break

    def __eq__(self, other: Any) -> bool:
        compare_property_name: str
        compare_function: Callable
        for (
            compare_property_name,
            compare_function,
        ) in _VERSION_PROPERTIES_COMPARE_FUNCTIONS:
            compare_value: Optional[
                Union[int, float, Decimal, str, Tuple[int, ...]]
            ] = getattr(self, compare_property_name)
            if compare_value is not None:
                if not compare_function(
                    _version_as_tuple(other), _version_as_tuple(compare_value)
                ):
                    return False
        return True

    def __str__(self) -> str:
        """
        Return the version represented in accordance with version
        identification described in
        [PEP-440](https://www.python.org/dev/peps/pep-0440).
        """
        version_specifiers: List[str] = []
        property_name: str
        repr_operator: str
        for property_name, repr_operator in _VERSION_PROPERTIES_REPR_OPERATORS:
            version_: Optional[
                Union[int, float, Decimal, str, Tuple[int, ...]]
            ] = getattr(self, property_name)
            if version_ is not None:
                version_specifiers.append(
                    repr_operator
                    + ".".join(
                        str(item) for item in _version_as_tuple(version_)
                    )
                )
        assert self.specification is not None
        return self.specification + ",".join(version_specifiers)

    def __repr__(self) -> str:
        return f"'{str(self)}'"
