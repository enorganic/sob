from __future__ import annotations

import operator
import re
from collections.abc import Sequence
from decimal import Decimal
from itertools import chain
from typing import TYPE_CHECKING, Callable

from sob import abc
from sob.utilities import represent

_DOT_SYNTAX_RE = re.compile(r"^\d+(\.\d+)*$")


def _are_versions_compatible(
    version_a: tuple[int, ...], version_b: tuple[int, ...]
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
            < ((*tuple(version_b[:-2]), version_b[-2] + 1, 0))
        )
    return version_a == version_b


def _are_versions_equal(
    version_a: tuple[int, ...], version_b: tuple[int, ...]
) -> bool:
    length_a: int = len(version_a)
    length_b: int = len(version_b)
    if length_a != length_b:
        length: int = min(length_a, length_b)
        version_a = tuple(version_a[:length])
        version_b = tuple(version_b[:length])
    return version_a == version_b


_VERSION_PROPERTIES_COMPARE_FUNCTIONS: tuple[tuple[str, Callable], ...] = (
    ("exactly_equals", operator.eq),
    ("equals", _are_versions_equal),
    ("not_equals", operator.ne),
    ("less_than", operator.lt),
    ("less_than_or_equal_to", operator.le),
    ("greater_than", operator.gt),
    ("greater_than_or_equal_to", operator.ge),
    ("compatible_with", _are_versions_compatible),
)
_REPR_OPERATORS_VERSION_PROPERTIES: tuple[tuple[str, str], ...] = (
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
_VERSION_PROPERTIES_REPR_OPERATORS: tuple[tuple[str, str], ...] = (
    ("exactly_equals", "==="),
    ("equals", "=="),
    ("compatible_with", "~="),
    ("not_equals", "!="),
    ("greater_than", ">"),
    ("greater_than_or_equal_to", ">="),
    ("less_than", "<"),
    ("less_than_or_equal_to", "<="),
)


def _version_string_as_tuple(version_string: str) -> tuple[int, ...]:
    if not _DOT_SYNTAX_RE.match(version_string):
        raise ValueError(version_string)
    return tuple(int(item) for item in version_string.split("."))


def _version_number_as_tuple(
    version_number: float | Decimal,
) -> tuple[int, ...]:
    return _version_string_as_tuple(str(version_number))


def _version_sequence_as_tuple(
    version_sequence: Sequence[str | int | float | Decimal],
) -> tuple[int, ...]:
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
    version_: str | float | Decimal | Sequence[int],
) -> tuple[int, ...]:
    version_tuple: tuple[int, ...]
    if not isinstance(version_, (str, int, float, Decimal, Sequence)):
        raise TypeError(version_)
    if isinstance(version_, str):
        version_tuple = _version_string_as_tuple(version_)
    elif isinstance(version_, (int, float, Decimal)):
        version_tuple = _version_number_as_tuple(version_)
    else:
        version_tuple = _version_sequence_as_tuple(version_)
    return version_tuple


class Version(abc.Version):
    """
    Instances of this class represent specification version compatibility.

    An instance of `sob.Version` can be initialized from a version string
    formatted similarly to python package dependency specifiers as
    documented in [PEP-440](https://www.python.org/dev/peps/pep-0440), but
    instead of representing package version compatibility, it represents
    compatibility with a specification version.

    Attributes:
        specification: A specification name/identifier. This can be any string,
            so long as the same string is used when representing versions
            in property metadata as when applying the version using
            `sob.version_model`.
        compatible_with: A sequence of version numbers for which comparisons
            should be evaluated as described for `~=` in
            [PEP-440](https://www.python.org/dev/peps/pep-0440).
        equals: A sequence of version numbers for which comparisons
            should be evaluated as described for `==` in
            [PEP-440](https://www.python.org/dev/peps/pep-0440).
        exactly_equals: A sequence of version numbers for which comparisons
            should be evaluated as described for `===` in
            [PEP-440](https://www.python.org/dev/peps/pep-0440).
        not_equals: A sequence of version numbers for which comparisons
            should be evaluated as described for `!=` in
            [PEP-440](https://www.python.org/dev/peps/pep-0440).
        less_than: A sequence of version numbers for which comparisons
            should be evaluated as described for `<` in
            [PEP-440](https://www.python.org/dev/peps/pep-0440).
        less_than_or_equal_to: A sequence of version numbers for which
            comparisons should be evaluated as described for `<=` in
            [PEP-440](https://www.python.org/dev/peps/pep-0440).
        greater_than: A sequence of version numbers for which
            comparisons should be evaluated as described for `>` in
            [PEP-440](https://www.python.org/dev/peps/pep-0440).
        greater_than_or_equal_to:  A sequence of version numbers for which
            comparisons should be evaluated as described for `>=` in
            [PEP-440](https://www.python.org/dev/peps/pep-0440).
    """

    __module__: str = "sob"

    def __init__(
        self,
        version_string: str | None = None,
        specification: str = "",
        compatible_with: Sequence[str | int | float | Decimal] | None = None,
        equals: Sequence[str | int | float | Decimal] | None = None,
        exactly_equals: Sequence[str | int | float | Decimal] | None = None,
        not_equals: Sequence[str | int | float | Decimal] | None = None,
        less_than: Sequence[str | int | float | Decimal] | None = None,
        less_than_or_equal_to: Sequence[str | int | float | Decimal]
        | None = None,
        greater_than: Sequence[str | int | float | Decimal] | None = None,
        greater_than_or_equal_to: Sequence[str | int | float | Decimal]
        | None = None,
    ) -> None:
        """
        Parameters:
            version_string: A version string formatted similarly to python
                package dependency specifiers as documented in
                [PEP-440](https://www.python.org/dev/peps/pep-0440).
            specification: A specification name/identifier. This can be any
                string, so long as the same string is used when representing
                versions in property metadata as when applying the version
                using `sob.version_model`.
            compatible_with: A sequence of version numbers for which
                comparisons should be evaluated as described for `~=` in
                [PEP-440](https://www.python.org/dev/peps/pep-0440).
            equals: A sequence of version numbers for which comparisons
                should be evaluated as described for `==` in
                [PEP-440](https://www.python.org/dev/peps/pep-0440).
            exactly_equals: A sequence of version numbers for which comparisons
                should be evaluated as described for `===` in
                [PEP-440](https://www.python.org/dev/peps/pep-0440).
            not_equals: A sequence of version numbers for which comparisons
                should be evaluated as described for `!=` in
                [PEP-440](https://www.python.org/dev/peps/pep-0440).
            less_than: A sequence of version numbers for which comparisons
                should be evaluated as described for `<` in
                [PEP-440](https://www.python.org/dev/peps/pep-0440).
            less_than_or_equal_to: A sequence of version numbers for which
                comparisons should be evaluated as described for `<=` in
                [PEP-440](https://www.python.org/dev/peps/pep-0440).
            greater_than: A sequence of version numbers for which
                comparisons should be evaluated as described for `>` in
                [PEP-440](https://www.python.org/dev/peps/pep-0440).
            greater_than_or_equal_to:  A sequence of version numbers for which
                comparisons should be evaluated as described for `>=` in
                [PEP-440](https://www.python.org/dev/peps/pep-0440).
        """
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
            if not isinstance(version_string, str):
                raise TypeError(version_string)
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
                                msg = (
                                    "Multiple specifications cannot be "
                                    "associated with one instance of "
                                    "`sob.meta.Version`:\n"
                                    f"- {represent(spec)}\n"
                                    f"- {represent(specification)}\n"
                                )
                                raise ValueError(msg)
                        else:
                            self.specification = spec
                    setattr(self, variable_name, version_number_string)
                    break

    def __eq__(self, other: object) -> bool:
        compare_property_name: str
        compare_function: Callable
        for (
            compare_property_name,
            compare_function,
        ) in _VERSION_PROPERTIES_COMPARE_FUNCTIONS:
            compare_value: (
                int | float | Decimal | str | tuple[int, ...] | None
            ) = getattr(self, compare_property_name)
            if TYPE_CHECKING:
                assert isinstance(other, (Decimal, str, float, Sequence))
            if compare_value is not None and not compare_function(
                _version_as_tuple(other),
                _version_as_tuple(compare_value),
            ):
                return False
        return True

    def __str__(self) -> str:
        # Return the version represented in accordance with version
        # identification described in
        # [PEP-440](https://www.python.org/dev/peps/pep-0440).
        version_specifiers: list[str] = []
        property_name: str
        repr_operator: str
        for property_name, repr_operator in _VERSION_PROPERTIES_REPR_OPERATORS:
            version_: int | float | Decimal | str | tuple[int, ...] | None = (
                getattr(self, property_name)
            )
            if version_ is not None:
                version_specifiers.append(
                    repr_operator
                    + ".".join(
                        str(item) for item in _version_as_tuple(version_)
                    )
                )
        if self.specification is None:
            message: str = "No specification identified"
            raise RuntimeError(message)
        return self.specification + ",".join(version_specifiers)

    def __repr__(self) -> str:
        return f"'{self!s}'"
