"""Base class for an analysis step."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neophile.update.base import Update
    from typing import List

__all__ = ["BaseAnalyzer"]


class BaseAnalyzer(ABC):
    """Base class for an analysis step."""

    @abstractmethod
    async def analyze(self) -> List[Update]:
        """Analyze a tree and return a list of needed changes.

        Returns
        -------
        results : List[`neophile.update.base.Update`]
            A list of updates.
        """

    @abstractmethod
    def name(self) -> str:
        """The name of the analyzer type.

        Returns
        -------
        name : `str`
            A string representing the type of analyzer this is.  Used for
            reporting results accumulated from a bunch of analyzers.
        """
