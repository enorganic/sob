import doctest

from sob.utilities import (
    inspect, io, string, types
)


def test_strings():
    doctest.testmod(string)


def test_inspect():
    doctest.testmod(inspect)


def test_io():
    doctest.testmod(io)


def test_types():
    doctest.testmod(types)


if __name__ == '__main__':
    test_strings()
    test_inspect()
    test_io()
    test_strings()
    test_types()
