"""PyInstaller entry point.

PyInstaller executes its Analysis script directly (not as `python -m
<package>`), so a script relying on relative imports (like
workday_tracker/__main__.py, used for `python -m workday_tracker`) fails at
runtime with "attempted relative import with no known parent package". This
standalone script uses an absolute import instead and is what the .spec
file points at.
"""

import sys

from workday_tracker.app import run

if __name__ == "__main__":
    sys.exit(run())
