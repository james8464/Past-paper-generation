# Keep both command names bound to the same implementation and Python types.

from pastpapergen.cli import generate_package, main

__all__ = ["generate_package", "main"]
