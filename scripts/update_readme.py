import os

import readme_md_docstrings

if __name__ == '__main__':
    # `cd` into the repository's root directory
    os.chdir(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))
    ))
    # Update `setup.py` to require currently installed versions of all packages
    readme_md_docstrings.update()
