"""Base class for an analysis step."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..update.base import Update

__all__ = ["BaseAnalyzer"]


class BaseAnalyzer(ABC):
    """Base class for an analysis step."""

    @abstractmethod
    async def analyze(self, *, update: bool = False) -> list[Update]:
        """Analyze a tree and return a list of needed changes.

        Parameters
        ----------
        update : `bool`, optional
            If set to `True`, leave the update applied if this is more
            efficient.  Used by analyzers like the Python frozen dependency
            analyzer that have to do work and apply the update to see if any
            update is necessary.  They can then mark the returned update as
            already applied and not have to run it twice.

        Returns
        -------
        results : List[`neophile.update.base.Update`]
            A list of updates.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the analyzer type.

        String representing the type of analyzer this is. Used for reporting
        results accumulated from a bunch of analyzers.
        """

    async def update(self) -> list[Update]:
        """Analyze a tree, apply updates, and return them as a list.

        Returns
        -------
        results : List[`neophile.update.base.Update`]
            A list of updates.
        """
        updates = await self.analyze(update=True)
        for update in updates:
            update.apply()
        return updates
