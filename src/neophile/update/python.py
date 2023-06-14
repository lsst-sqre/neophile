"""Python frozen dependency update."""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path  # noqa: F401

from .base import Update

__all__ = ["PythonFrozenUpdate"]


@dataclass
class PythonFrozenUpdate(Update):
    """An update to Python frozen dependencies."""

    def apply(self) -> None:
        """Apply an update to frozen Python dependencies.

        Raises
        ------
        subprocess.CalledProcessError
            Raised if running ``make update-deps`` failed.
        """
        if self.applied:
            return
        rootdir = self.path.parent

        try:
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
        return "Update frozen Python dependencies"
