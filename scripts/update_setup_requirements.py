#!/usr/bin/env python3
"""
This script updates installation requirements in ../setup.py
"""
import os
from setuptools_setup_versions import install_requires

if __name__ == '__main__':
    # `cd` into the repository's root directory
    os.chdir(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))
    ))
    # Update `setup.py` to require currently installed versions of all packages
    install_requires.update_versions(operator='~=')
