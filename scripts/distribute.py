# !/usr/bin/python3
import os
import sys
from subprocess import getstatusoutput

REPOSITORY_DIRECTORY = os.path.dirname(
    os.path.dirname(
        __file__
    )
)
PACKAGE_NAME = REPOSITORY_DIRECTORY.split('/')[-1].split('\\')[-1]


def run(command: str) -> str:
    print(command)
    status, output = getstatusoutput(command)
    # Create an error if a non-zero exit status is encountered
    if status:
        raise OSError(output)
    else:
        print(output)
    return output


if __name__ == '__main__':
    os.chdir(
        REPOSITORY_DIRECTORY
    )
    try:
        # Build
        run(f'{sys.executable} setup.py sdist bdist_wheel')
        run(f'{sys.executable} -m twine upload dist/*')
    finally:
        run(f'{sys.executable} setup.py clean --all')
        exec(
            open(REPOSITORY_DIRECTORY + '/scripts/clean.py').read(),
            {
                '__file__': os.path.abspath(
                    REPOSITORY_DIRECTORY + '/scripts/clean.py'
                )
            }
        )
