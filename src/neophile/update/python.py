"""Python frozen dependency update."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

from neophile.update.base import Update

__all__ = ["PythonFrozenUpdate"]


@dataclass
class PythonFrozenUpdate(Update):
    """An update to Python frozen dependencies."""

    def apply(self) -> None:
        """Apply an update to frozen Python dependencies.

        Raises
        ------
        subprocess.CalledProcessError
            Running ``make update-deps`` failed.
        """
        if self.applied:
            return
        rootdir = self.path.parent
        subprocess.run(
            ["make", "update-deps"],
            cwd=str(rootdir),
            check=True,
            capture_output=True,
        )
        self.applied = True

    def description(self) -> str:
        """Build a description of this update.

        Returns
        -------
        description : `str`
            Short text description of the update.
        """
        return "Update frozen Python dependencies"
