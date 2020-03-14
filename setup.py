from setuptools import setup, find_packages

setup(
    name='sob',
    version="0.1.49",
    description=(
        'A framework for serializing/deserializing JSON/YAML into a python '
        'class instances and vice versa'
    ),
    url='https://github.com/davebelais/sob.git',
    author='David Belais',
    author_email='david@belais.me',
    license='MIT',
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, <4',
    keywords='rest api serialization serialize',
    packages=find_packages(),
    install_requires=[
        "future>=0.18.2",
        "pyyaml>=5.1.1",
        "iso8601>=0.1.12"
    ],
    extras_require={
        "test": [
            "setuptools_setup_versions>=0.0.29"
        ],
        "dev": [
            "setuptools_setup_versions>=0.0.29"
        ]
    }
)