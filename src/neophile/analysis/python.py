"""Analysis of a repository for needed Python updates."""

from __future__ import annotations

import os
import subprocess
from typing import TYPE_CHECKING

from git import Repo

from neophile.analysis.base import BaseAnalyzer
from neophile.exceptions import UncommittedChangesError
from neophile.update.python import PythonFrozenUpdate

if TYPE_CHECKING:
    from neophile.update.base import Update
    from typing import List

__all__ = ["PythonAnalyzer"]


class PythonAnalyzer(BaseAnalyzer):
    """Analyze a tree for needed Python frozen dependency updates.

    Parameters
    ----------
    root : `str`
        Root of the directory tree to analyze.
    """

    def __init__(self, root: str,) -> None:
        self._root = root

    async def analyze(self) -> List[Update]:
        """Analyze a tree and return needed Python frozen dependency updates.

        Returns
        -------
        results : List[`neophile.update.base.Update`]
            Will contain either no elements (no updates needed) or a single
            element (an update needed).

        Raises
        ------
        neophile.exceptions.UncommittedChangesError
            The repository being analyzed has uncommitted changes and
            therefore cannot be checked for updates.
        subprocess.CalledProcessError
            Running ``make update-deps`` failed.
        """
        for name in ("Makefile", "requirements/main.in"):
            if not os.path.exists(os.path.join(self._root, name)):
                return []
        repo = Repo(self._root)

        if repo.is_dirty():
            msg = "Working tree contains uncommitted changes"
            raise UncommittedChangesError(msg)

        subprocess.run(
            ["make", "update-deps"],
            cwd=self._root,
            check=True,
            capture_output=True,
        )

        if repo.is_dirty():
            repo.git.restore(".")
            return [
                PythonFrozenUpdate(
                    path=os.path.join(self._root, "requirements")
                )
            ]
        else:
            return []

    def name(self) -> str:
        return "python"
