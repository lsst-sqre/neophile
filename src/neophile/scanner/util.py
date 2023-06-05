"""Utilities for dependency scanning."""

from __future__ import annotations

import os
from pathlib import Path

__all__ = ["find_files"]


def find_files(root: Path, wanted_names: set[str]) -> list[Path]:
    """Scan a tree of files for files of a given set of names.

    Files in a directory named "tests" under the root directory will be
    ignored.

    Parameters
    ----------
    root : `pathlib.Path`
        The root from which to begin the search.
    wanted_names : Set[`str`]
        The file names to search for.

    Returns
    -------
    results : List[`pathlib.Path`]
        A list of matching files.
    """
    tests_path = root / "tests"

    results = []
    for directory, _, filenames in os.walk(str(root)):
        dir_path = Path(directory)
        if dir_path == tests_path or tests_path in dir_path.parents:
            continue
        for name in filenames:
            if name not in wanted_names:
                continue
            results.append(dir_path / name)

    return results
