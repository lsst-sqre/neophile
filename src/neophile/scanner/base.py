"""Base class for dependency scanners."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neophile.dependency.base import Dependency
    from typing import Sequence

__all__ = ["BaseScanner"]


class BaseScanner(ABC):
    """Base class for dependency scanners."""

    @abstractmethod
    def name(self) -> str:
        """The name of the scanner type.

        Returns
        -------
        name : `str`
            A string representing the type of scanner this is.  Used for
            reporting results accumulated from a bunch of scanners.
        """

    @abstractmethod
    def scan(self) -> Sequence[Dependency]:
        """Scan a source tree for dependencies.

        Returns
        -------
        results : List[`neophile.dependency.base.Dependency`]
            A list of all discovered dependencies.
        """
