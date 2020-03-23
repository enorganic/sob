from setuptools import setup, find_packages

setup(
    name='sob',
    version="0.2.6",
    description=(
        'A framework for serializing/deserializing JSON/YAML into python '
        'class instances and vice versa'
    ),
    url='https://github.com/davebelais/sob.git',
    author='David Belais',
    author_email='david@belais.me',
    license='MIT',
    python_requires='>=3.6, <4',
    keywords='rest api serialization serialize',
    packages=find_packages(),
    install_requires=[
        "pyyaml>=5.3",
        "iso8601>=0.1.12",
        "more-itertools>=8.2.0"
    ],
    extras_require={
        "test": [
            "tox>=3.14.5",
            "pytest>=5.4.1",
            "flake8>=3.7.9",
            "setuptools-setup-versions>=0.0.30",
            "readme-md-docstrings>=0.0.8"
        ],
        "dev": [
            "wheel>=0.34.2",
            "tox>=3.14.5",
            "pytest>=5.4.1",
            "flake8>=3.7.9",
            "setuptools-setup-versions>=0.0.30",
            "readme-md-docstrings>=0.0.8"
        ]
    }
)
