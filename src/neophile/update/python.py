"""Python frozen dependency update."""

from __future__ import annotations

import logging
import subprocess
from dataclasses import InitVar, dataclass
from pathlib import Path  # noqa: F401
from typing import TYPE_CHECKING

from neophile.update.base import Update

if TYPE_CHECKING:
    from neophile.virtualenv import VirtualEnv

__all__ = ["PythonFrozenUpdate"]


@dataclass
class PythonFrozenUpdate(Update):
    """An update to Python frozen dependencies."""

    virtualenv: InitVar[VirtualEnv | None] = None
    """Virtual environment to use for updates."""

    def __post_init__(self, virtualenv: VirtualEnv | None) -> None:
        self._virtualenv = virtualenv

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

        try:
            if self._virtualenv:
                self._virtualenv.run(
                    ["make", "update-deps"],
                    cwd=str(rootdir),
                    check=True,
                    capture_output=True,
                )
            else:
                subprocess.run(
                    ["make", "update-deps"],
                    cwd=str(rootdir),
                    check=True,
                    capture_output=True,
                )
        except subprocess.CalledProcessError as e:
            logging.exception(
                "make update-deps failed: %s%s", e.stdout, e.stderr
            )
            return

        self.applied = True

    def description(self) -> str:
        """Build a description of this update.

        Returns
        -------
        description : `str`
            Short text description of the update.
        """
        return "Update frozen Python dependencies"
