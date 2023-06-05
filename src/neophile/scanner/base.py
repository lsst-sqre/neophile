"""Base class for dependency scanners."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from ..models.dependencies import Dependency

__all__ = ["BaseScanner"]


class BaseScanner(ABC):
    """Base class for dependency scanners."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the scanner type."""

    @abstractmethod
    def scan(self) -> Sequence[Dependency]:
        """Scan a source tree for dependencies.

        Returns
        -------
        list of Dependency
            A list of all discovered dependencies.
        """
