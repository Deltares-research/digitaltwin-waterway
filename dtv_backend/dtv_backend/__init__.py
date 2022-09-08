"""Top-level package for Digital Twin Waterway Backend."""

__author__ = """Fedor Baart"""
__email__ = "fedor.baart@deltares.nl"
__version__ = "0.1.0"

import pathlib


def get_src_path():
    """return the src_path"""
    src_path = pathlib.Path(__file__).parent.parent
    return src_path
