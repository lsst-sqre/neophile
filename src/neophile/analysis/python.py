"""Analysis of a repository for needed Python updates."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from git.repo import Repo

from ..exceptions import UncommittedChangesError
from ..update.base import Update
from ..update.python import PythonFrozenUpdate
from .base import BaseAnalyzer

__all__ = ["PythonAnalyzer"]


class PythonAnalyzer(BaseAnalyzer):
    """Analyze a tree for needed Python frozen dependency updates.

    Parameters
    ----------
    root
        Root of the directory tree to analyze.
    virtualenv
        Virtual environment manager.
    """

    async def analyze(
        self, root: Path, *, update: bool = False
    ) -> list[Update]:
        """Analyze a tree and return needed Python frozen dependency updates.

        Parameters
        ----------
        root
            Root of the path to analyze.
        update
            If set to `True`, leave the update applied. This avoids having to
            run ``make update-deps`` twice, once to see if an update is needed
            and again to apply it properly.

        Returns
        -------
        list of Update
            Either an empty list (no updates needed) or a list with a single
            element (an update needed).

        Raises
        ------
        UncommittedChangesError
            Raised if the repository being analyzed has uncommitted changes
            and therefore cannot be checked for updates.
        subprocess.CalledProcessError
            Raised if running ``make update-deps`` failed.
        """
        for name in ("Makefile", "requirements/main.in"):
            if not (root / name).exists():
                return []
        repo = Repo(str(root))

        if repo.is_dirty():
            msg = "Working tree contains uncommitted changes"
            raise UncommittedChangesError(msg)

        try:
            subprocess.run(
                ["make", "update-deps"],
                cwd=str(root),
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            logging.exception(
                "make update-deps failed: %s%s", e.stdout, e.stderr
            )
            return []

        if not repo.is_dirty():
            return []

        if not update:
            repo.git.restore(".")
        return [PythonFrozenUpdate(path=root / "requirements", applied=update)]

    @property
    def name(self) -> str:
        return "python"
