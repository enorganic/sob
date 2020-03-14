from setuptools import setup, find_packages

setup(
    name='sob',
    version="0.2.0",
    description=(
        'A framework for serializing/deserializing JSON/YAML into a python '
        'class instances and vice versa'
    ),
    url='https://github.com/davebelais/sob.git',
    author='David Belais',
    author_email='david@belais.me',
    license='MIT',
    python_requires='>=3.5, <4',
    keywords='rest api serialization serialize',
    packages=find_packages(),
    install_requires=[
        "future>=0.18.2",
        "pyyaml>=5.3",
        "iso8601>=0.1.12"
    ],
    extras_require={
        "test": [
            "setuptools_setup_versions>=0.0.30",
            "readme-md-docstrings>=0.0.8"
        ],
        "dev": [
            "setuptools_setup_versions>=0.0.30",
            "readme-md-docstrings>=0.0.8"
        ]
    }
)
