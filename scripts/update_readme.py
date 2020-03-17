import os

import readme_md_docstrings

if __name__ == '__main__':
    # `cd` into the repository's root directory
    os.chdir(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))
    ))
    readme_md_docstrings.update()
