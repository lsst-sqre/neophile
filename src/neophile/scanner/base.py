"""Base class for dependency scanners."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neophile.dependency.base import BaseDependency
    from typing import Sequence


class BaseScanner(ABC):
    """Base class for dependency scanners."""

    @abstractmethod
    def scan(self) -> Sequence[BaseDependency]:
        """Scan a source tree for dependencies.

        Returns
        -------
        results : List[`neophile.dependency.base.Dependency`]
            A list of all discovered dependencies.
        """
