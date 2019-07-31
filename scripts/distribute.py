# !/usr/bin/python3.7
import os
from subprocess import getstatusoutput
from setuptools_setup_versions import install_requires

# Update `setup.py` to require currently installed versions of all packages
install_requires.update_versions('../', operator='>=')
# Build
status, output = getstatusoutput(
    'py -3.7 ../setup.py sdist bdist_wheel upload clean --all'
    if os.name == 'nt' else
    'python3.7 ../setup.py sdist bdist_wheel upload clean --all'
)
# Create an error if a non-zero exit status is encountered
error = None
if status:
    error = OSError(output)
else:
    print(output)
exec(
    open('./scripts/clean.py').read(),
    {'__file__': os.path.abspath('./scripts/clean.py')}
)
# Raise the previously created error, if there was one
if error:
    raise error
