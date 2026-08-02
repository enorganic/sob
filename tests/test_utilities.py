from __future__ import annotations

import doctest
from typing import Any

import pytest

import sob
from sob import _io, _types, _utilities, utilities
from sob._utilities import get_readable_url


def test_doctest() -> None:
    """
    Run docstring tests
    """
    results: doctest.TestResults = doctest.testmod(utilities)
    assert results.failed == 0, results


def test_utilities() -> None:
    assert sob.utilities.get_calling_function_qualified_name() == (
        "tests.test_utilities.test_utilities"
    )

    class TestCallingFunctionQualifiedNameA:
        __module__ = "tests.utilities"

        def __init__(self) -> None:
            assert sob.utilities.get_calling_function_qualified_name() == (
                "tests.utilities.test_utilities."
                "TestCallingFunctionQualifiedNameA.__init__"
            )

    TestCallingFunctionQualifiedNameA()

    class TestCallingFunctionQualifiedNameB:
        def __init__(self) -> None:
            assert sob.utilities.get_calling_function_qualified_name() == (
                "tests.test_utilities.test_utilities.TestCallingFunctionQualif"
                "iedNameB.__init__"
            )

    TestCallingFunctionQualifiedNameB()

    class TestCallingFunctionQualifiedNameC:
        class TestCallingFunctionQualifiedNameD:
            def __init__(self) -> None:
                assert sob.utilities.get_calling_function_qualified_name() == (
                    "tests.test_utilities.test_utilities.TestCallingFunctionQu"
                    "alifiedNameC.TestCallingFunctionQualifiedNameD.__init__"
                )

    TestCallingFunctionQualifiedNameC.TestCallingFunctionQualifiedNameD()
    assert utilities.get_qualified_name(
        TestCallingFunctionQualifiedNameC(
            # -
        ).TestCallingFunctionQualifiedNameD
    ) == (
        "tests.test_utilities.test_utilities.TestCallingFunctionQualifiedNameC"
        ".TestCallingFunctionQualifiedNameD"
    )
    assert sob.utilities.get_qualified_name(sob.Object) == "sob.Object"


def test_inspect() -> None:
    def my_function() -> Any:
        class MyClass:
            """
            TODO
            """

            def __call__(self) -> str | None:
                return self.get_method_name()

            @staticmethod
            def get_static_method_name() -> str | None:
                return sob.utilities.get_calling_function_qualified_name()

            def get_method_name(self) -> str | None:
                return sob.utilities.get_calling_function_qualified_name()

            def get_module_name(self) -> str:
                return sob.utilities.get_calling_module_name()

        return MyClass()

    assert my_function().get_method_name() == (
        "tests.test_utilities.test_inspect.my_function.MyClass.get_method_name"
    )
    assert my_function()() == (
        "tests.test_utilities.test_inspect.my_function.MyClass.get_method_name"
    )
    # Static methods are defined at the module level...
    assert my_function().get_static_method_name() == (
        "tests.test_utilities.get_static_method_name"
    )
    assert my_function().get_module_name() == "tests.test_utilities"


def test_get_calling_function_qualified_name() -> None:
    assert sob.utilities.get_calling_function_qualified_name() == (
        "tests.test_utilities.test_get_calling_function_qualified_name"
    )


def test_io() -> None:
    results: doctest.TestResults = doctest.testmod(_io)
    assert results.failed == 0, results


def test_types() -> None:
    results: doctest.TestResults = doctest.testmod(_types)
    assert results.failed == 0, results


class HTTPResponseProxy1:
    def geturl(self) -> str:
        return "https://example.com"


class HTTPResponseProxy2:
    url = "https://example.com"


class WindowsFileProxy:
    name = r"C:\a\b\c"


class UnixFileProxy:
    name = "/a/b/c"


class URLNonStringProxy:
    url = 123


class NoAttributesProxy:
    pass


def test_get_readable_url() -> None:
    assert get_readable_url(HTTPResponseProxy1()) == "https://example.com"
    assert get_readable_url(HTTPResponseProxy2()) == "https://example.com"
    assert get_readable_url(WindowsFileProxy()) == "file:///C:/a/b/c"
    assert get_readable_url(UnixFileProxy()) == "file:///a/b/c"


def test_get_readable_url_type_error() -> None:
    error_caught: bool = False
    try:
        get_readable_url(URLNonStringProxy())
    except TypeError:
        error_caught = True
    assert error_caught


def test_get_readable_url_none() -> None:
    assert get_readable_url(NoAttributesProxy()) is None


def test_deserialize_error() -> None:
    error = sob.errors.DeserializeError(data="bad-data", message="oops")
    assert error.data == "bad-data"
    assert error.message == "oops"
    assert repr(error) == "oops\nCould not parse:\nbad-data"
    assert str(error) == repr(error)


def test_append_exception_text_strerror() -> None:
    error = OSError(1, "boom")
    sob.errors.append_exception_text(error, " (more info)")
    assert error.strerror is not None
    assert error.strerror.endswith(" (more info)")


def test_append_exception_text_no_string_arg() -> None:
    error = Exception()
    sob.errors.append_exception_text(error, "appended")
    assert error.args == ("appended",)


def test_deprecated() -> None:
    @_utilities.deprecated("this is deprecated")
    def old_function(value: int) -> int:
        return value * 2

    with pytest.warns(DeprecationWarning, match="this is deprecated"):
        result: int = old_function(21)
    assert result == 42


def test_get_class_name_leading_digit() -> None:
    assert utilities.get_class_name("123 abc").startswith("_")


def test_indent_negative_stop() -> None:
    # A negative `stop` excludes lines counting back from the end, similar
    # to slice notation.
    assert utilities.indent("a\nb\nc\nd", stop=-1) == ("a\n    b\n    c\nd")


def test_url_directory_and_file_name_value_error() -> None:
    error_caught: bool = False
    try:
        utilities._url_directory_and_file_name("no-slash-here")
    except ValueError:
        error_caught = True
    assert error_caught


def test_get_url_relative_to_no_shared_prefix() -> None:
    assert (
        utilities.get_url_relative_to("https://a.com/x/y", "https://a.com/x/z")
        == "y"
    )
    assert (
        utilities.get_url_relative_to("https://a.com/x/y", "https://b.com/p/q")
        == "../../a.com/x/y"
    )


def test_align_indent_no_leading_whitespace() -> None:
    assert utilities._align_indent("no-leading-space") == "no-leading-space"


def test_align_indent_with_leading_whitespace() -> None:
    # 6 leading spaces, tab_width=4 -> strip 6 % 4 == 2 spaces
    assert utilities._align_indent("      indented", tab_width=4) == (
        "    indented"
    )


def test_split_long_comment_line_short() -> None:
    assert (
        utilities._split_long_comment_line("# a short line")
        == "# a short line"
    )


def test_split_long_docstring_lines_tab_and_blank_line() -> None:
    docstring: str = (
        "\tLine one.\n\n\tLine two, which continues on the next line."
    )
    result: str = utilities.split_long_docstring_lines(docstring)
    assert "\t" not in result
    assert "\n\n" in result


def test_split_long_docstring_lines_no_leading_indent() -> None:
    docstring: str = (
        "Summary line with no leading indent and quite a few words in "
        "it so that it wraps onto more than one output line here.\n"
        "    Detail line."
    )
    result: str = utilities.split_long_docstring_lines(docstring)
    assert result.startswith("    Summary line")


def test_suffix_long_lines_multiline_string_literal() -> None:
    text: str = '"""\n' + ("word " * 20) + '\n"""'
    result: str = utilities.suffix_long_lines(text)
    lines: list[str] = result.split("\n")
    assert lines[-1] == '"""  # noqa: E501'


def test_get_qualified_name_type_error() -> None:
    error_caught: bool = False
    try:
        utilities.get_qualified_name(123)  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


def test_get_qualified_name_module() -> None:
    assert utilities.get_qualified_name(utilities) == "sob.utilities"


class GenericAliasProxy:
    __origin__ = list

    def __call__(self) -> None:
        pass


def test_get_qualified_name_generic_alias_repr_fallback() -> None:
    name: str = utilities.get_qualified_name(GenericAliasProxy())  # type: ignore
    assert "GenericAliasProxy object at" in name


class NoNameCallableProxy:
    def __call__(self) -> None:
        pass


def test_get_qualified_name_unresolvable() -> None:
    error_caught: bool = False
    try:
        utilities.get_qualified_name(NoNameCallableProxy())  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


def test_get_calling_module_name_out_of_range() -> None:
    assert utilities.get_calling_module_name(depth=99999) == "__main__"


def test_get_calling_function_qualified_name_type_error() -> None:
    error_caught: bool = False
    try:
        utilities.get_calling_function_qualified_name(depth="not-an-int")  # type: ignore
    except TypeError:
        error_caught = True
    assert error_caught


def test_get_calling_function_qualified_name_out_of_range() -> None:
    assert utilities.get_calling_function_qualified_name(depth=99999) is None


def test_get_source_fallback() -> None:
    source: str = utilities.get_source(utilities.get_qualified_name)
    assert "def get_qualified_name" in source


def test_repr_empty_collections() -> None:
    assert utilities.represent([]) == "[]"
    assert utilities.represent([1, "a"]) != "[]"
    assert utilities.represent(set()) == "set()"
    assert utilities.represent({}) == "{}"


class NonCallableAttributeProxy:
    value = 123


def test_get_method_missing_no_default() -> None:
    error_caught: bool = False
    try:
        utilities.get_method(object(), "nonexistent_method")
    except AttributeError:
        error_caught = True
    assert error_caught


def test_get_method_not_callable() -> None:
    error_caught: bool = False
    try:
        utilities.get_method(NonCallableAttributeProxy(), "value")
    except AttributeError:
        error_caught = True
    assert error_caught
    # When a `default` is provided, the non-callable attribute value itself
    # is returned rather than raising.
    assert (
        utilities.get_method(NonCallableAttributeProxy(), "value", None) == 123
    )


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-vv"])
