import pkg_resources
from setuptools import setup, find_packages

try:
    pyserial_distribution = pkg_resources.get_distribution('pyserial')
    raise RuntimeError(
        'This package cannot be installed alongside `pyserial`, due to a module name conflict. ' +
        'To install `sob`, first uninstall `pyserial`: \n' +
        '>>> pip uninstall pyserial\n' +
        '>>> pip install sob\n' +
        '...or:\n'
        '>>> pip3 uninstall sob\n'
        '>>> pip3 install pyserial\n'
    )
except pkg_resources.DistributionNotFound:
    pass

setup(
    name='sob',
    version="0.1.0",
    description='A framework for serializing/deserializing JSON/YAML into python class instances and vice versa',
    url='https://bitbucket.com/davebelais/sob.git',
    author='David Belais',
    author_email='david@belais.me',
    license='MIT',
    classifiers=[
        # 'Development Status :: 1 - Planning',
        'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='rest api serialization serialize',
    packages=find_packages(),
    install_requires=[
        "future>=0.17.1",
        "pyyaml>=3.13",
        "iso8601>=0.1.12"
    ],
)
