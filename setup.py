import sys
from typing import Any, Set

import setuptools  # type: ignore

_INSTALL_REQUIRES: str = "install_requires"


def setup(**kwargs: Any) -> None:
    """
    This `setup` script intercepts arguments to be passed to
    `setuptools.setup` in order to dynamically alter setup requirements
    while retaining a function call which can be easily parsed and altered
    by `setuptools-setup-versions`.
    """
    # Require the package "dataclasses" for python 3.6, but not later
    # python versions (since it's part of the standard library after 3.6)
    if sys.version_info[:2] == (3, 6):
        if _INSTALL_REQUIRES not in kwargs:
            kwargs[_INSTALL_REQUIRES] = []
        kwargs[_INSTALL_REQUIRES].append("dataclasses")
    # Add an "all" extra which includes all extra requirements
    if "extras_require" in kwargs and "all" not in kwargs["extras_require"]:
        all_extras_require: Set[str] = set()
        kwargs["extras_require"]["all"] = []
        for extra_name, requirements in kwargs["extras_require"].items():
            if extra_name != "all":
                for requirement in requirements:
                    if requirement not in all_extras_require:
                        all_extras_require.add(requirement)
                        kwargs["extras_require"]["all"].append(requirement)
    # Pass the modified keyword arguments to `setuptools.setup`
    setuptools.setup(**kwargs)


setup(
    name="sob",
    version="1.7.0",
    description=(
        "A framework for serializing/deserializing JSON/YAML into python "
        "class instances and vice versa"
    ),
    url="https://github.com/davebelais/sob",
    author="David Belais",
    author_email="david@belais.me",
    license="MIT",
    include_package_data=True,
    zip_safe=False,
    python_requires="~=3.6",
    keywords="rest api serialization serialize",
    packages=["sob", "sob.utilities"],
    package_data={"sob": ["py.typed"], "sob.utilities": ["py.typed"]},
    install_requires=[
        "pyyaml>=3.10",
        "iso8601~=0.1",
        "more-itertools~=8.6"
    ],
    setup_requires=["setuptools"],
    extras_require={
        "test": [
            "mypy~=0.790",
            "tox~=3.20",
            "pytest~=5.4",
            "flake8~=3.8",
            "setuptools-setup-versions>=1.6.0,<2",
            "readme-md-docstrings>=0.1.0,<1"
        ],
        "dev": [
            "mypy~=0.790",
            "wheel~=0.35.1",
            "tox~=3.20",
            "pytest~=5.4",
            "flake8~=3.8",
            "setuptools-setup-versions>=1.6.0,<2",
            "readme-md-docstrings~=0.1.0,<2",
            "twine~=3.2",
            "daves-dev-tools~=0.1"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
    ],
)
