from setuptools import setup  # type: ignore

setup(
    name='sob',
    version="0.5.0",
    description=(
        'A framework for serializing/deserializing JSON/YAML into python '
        'class instances and vice versa'
    ),
    url='https://github.com/davebelais/sob.git',
    author='David Belais',
    author_email='david@belais.me',
    license='MIT',
    python_requires='~=3.6',
    keywords='rest api serialization serialize',
    packages=[
        'sob',
        'sob.abc',
        'sob.utilities'
    ],
    install_requires=[
        "pyyaml>=3",
        "iso8601~=0.1",
        "more-itertools~=8.2"
    ],
    extras_require={
        "test": [
            "mypy~=0.770",
            "tox~=3.14",
            "pytest~=5.4",
            "flake8~=3.7",
            "setuptools-setup-versions>=1.1.0,<2",
            "readme-md-docstrings>=0.1.0,<1"
        ],
        "dev": [
            "mypy~=0.770",
            "wheel~=0.34.2",
            "tox~=3.14.6",
            "pytest~=5.4.1",
            "flake8~=3.7.9",
            "setuptools-setup-versions>=1.1.0,<2",
            "readme-md-docstrings~=0.1.0,<2"
        ]
    }
)
