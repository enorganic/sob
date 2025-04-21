# sob

[![test](https://github.com/enorganic/sob/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/enorganic/sob/actions/workflows/test.yml)
[![PyPI version](https://badge.fury.io/py/sob.svg?icon=si%3Apython)](https://badge.fury.io/py/sob)

`sob` is an object serialization/deserialization library intended to facilitate
automated authoring of models for JSON web APIs which are readable and
introspective, and to expedite data validation and integration testing.

- [Documentation](https://sob.enorganic.org)
- [Contributing](https://sob.enorganic.org/contributing)

## Installation

You can install `sob` with pip:

```shell
pip3 install sob
```

## Background Information

This library is developed in concert with, and in support of, the
[oapi](https://enorganic.github.io/oapi/) library, which facilitates
generating client libraries ("SDKs") based on an
[Open API](https://www.openapis.org/) specification. For very niche use cases,
`sob` remains a separate library, but the development roadmap and all feature
requests should be viewed in the context of supporting the definition and
validation of data as described by an [Open API](https://www.openapis.org/)
specification.

When authoring server-side code for your web API, I recommend
[pydantic](https://docs.pydantic.dev/latest/). The `sob` library is designed
primarily to support API *client* data models, and for automated model module
creation based on metadata generated either using
[sob.thesaurus](https://sob.enorganic.org/api/thesaurus) or
[oapi](https://oapi.enorganic.org/).

The name "sob" is not a profane acronym (in this case), it is a portmanteau
of "serial" and "object". Originally, this library was named "serial",
but was renamed with version 1 due to a namespace conflict with
[pyserial](https://pyserial.readthedocs.io/en/latest/).
