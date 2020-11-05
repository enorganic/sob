from setuptools import setup

setup(
    name='sob',
    version='0.6.3',
    description=(
        'A framework for serializing/deserializing JSON/YAML into python '
        'class instances and vice versa'
    ),
    url='https://github.com/davebelais/sob',
    author='David Belais',
    author_email='david@belais.me',
    license='MIT',
    include_package_data=True,
    zip_safe=False,
    python_requires='~=3.6',
    keywords='rest api serialization serialize',
    packages=[
        'sob',
        'sob.abc',
        'sob.utilities'
    ],
    package_data={
        "sob": ["py.typed"],
        "sob.abc": ["py.typed"],
        "sob.utilities": ["py.typed"],
    },
    install_requires=[
        "pyyaml>=3.10",
        "iso8601~=0.1",
        "more-itertools~=8.5"
    ],
    setup_requires=['setuptools'],
    extras_require={
        "test": [
            "mypy~=0.782",
            "tox~=3.19",
            "pytest~=5.4",
            "flake8~=3.8",
            "setuptools-setup-versions>=1.2.3,<2",
            "readme-md-docstrings>=0.1.0,<1"
        ],
        "dev": [
            "mypy~=0.782",
            "wheel~=0.34.2",
            "tox~=3.19",
            "pytest~=5.4",
            "flake8~=3.8",
            "setuptools-setup-versions>=1.2.3,<2",
            "readme-md-docstrings~=0.1.0,<2",
            "twine~=3.2"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers"
    ]
)
