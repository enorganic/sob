# !/usr/bin/python3
import os
from subprocess import getstatusoutput
from tempfile import gettempdir

from setuptools_setup_versions import install_requires

# Update `setup.py` to require currently installed versions of all packages
install_requires.update_versions(operator='>=')


def run(command: str) -> str:
    status, output = getstatusoutput(command)
    # Create an error if a non-zero exit status is encountered
    if status:
        raise OSError(output)
    else:
        print(output)
    return output


try:
    # Build
    run(
        'py -3.7 setup.py sdist bdist_wheel upload clean --all'
        if os.name == 'nt' else
        'python3.7 setup.py sdist bdist_wheel upload clean --all'
    )
finally:
    exec(
        open('./clean.py').read(),
        {'__file__': os.path.abspath('./clean.py')}
    )

