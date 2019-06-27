import doctest
from sob.utilities import compatibility, inspect, io, strings, types


def test_strings():
    doctest.testmod(strings)


def test_compatibility():
    doctest.testmod(compatibility)


def test_inspect():
    doctest.testmod(inspect)


def test_io():
    doctest.testmod(io)


def test_strings():
    doctest.testmod(strings)


def test_types():
    doctest.testmod(types)


if __name__ == '__main__':
    test_strings()
    test_compatibility()
    test_inspect()
    test_io()
    test_strings()
    test_types()

