"""Base class for dependency scanners."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path

from ..models.dependencies import Dependency

__all__ = ["BaseScanner"]


class BaseScanner(ABC):
    """Base class for dependency scanners."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the scanner type."""

    @abstractmethod
    def scan(self, root: Path) -> Sequence[Dependency]:
        """Scan a source tree for dependencies.

        Parameters
        ----------
        root
            Root of the source tree.

        Returns
        -------
        list of Dependency
            A list of all discovered dependencies.
        """
