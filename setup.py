from setuptools import setup, find_packages

setup(
    name='sob',
    version="0.1.21",
    description=(
        'A framework for serializing/deserializing JSON/YAML into python class'
        'instances and vice versa'
    ),
    url='https://github.com/davebelais/sob.git',
    author='David Belais',
    author_email='david@belais.me',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
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
        "pyyaml>=5.1.1",
        "iso8601>=0.1.12"
    ],
    extras_require={
        'testing': [
            'setuptools_setup_versions'
        ]
    }
)