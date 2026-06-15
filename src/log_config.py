"""
PictoMusic Logging Configuration
Single entrypoint for logging setup — import this before using logging in any module.
"""

import logging
import sys


def setup_logging(level=logging.INFO):
    """Configure the root logger once. Subsequent calls are no-ops."""
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    ))
    root.setLevel(level)
    root.addHandler(handler)
