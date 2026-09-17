"""Entry point: `python -m workday_tracker`."""

import sys

from .app import run

if __name__ == "__main__":
    sys.exit(run())
