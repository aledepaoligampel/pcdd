#!/usr/bin/env python3
"""Checkout launcher: runs the PCDD CLI from src/ without installing it."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from pcdd_toolkit.cli import main  # noqa: E402

if __name__ == '__main__':
    main()
