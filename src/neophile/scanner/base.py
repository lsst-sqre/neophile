"""Base class for dependency scanners."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from neophile.dependency.base import Dependency

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
        results : List[`neophile.dependency.base.Dependency`]
            A list of all discovered dependencies.
        """
