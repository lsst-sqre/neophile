"""Base class for an analysis step."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..update.base import Update

__all__ = ["BaseAnalyzer"]


class BaseAnalyzer(ABC):
    """Base class for an analysis step."""

    @abstractmethod
    async def analyze(
        self, root: Path, *, update: bool = False
    ) -> list[Update]:
        """Analyze a tree and return a list of needed changes.

        Parameters
        ----------
        root
            Root of the path to analyze.
        update
            If set to `True`, leave the update applied if this is more
            efficient. Used by analyzers like the Python frozen dependency
            analyzer that have to do work and apply the update to see if any
            update is necessary. They can then mark the returned update as
            already applied and not have to run it twice.

        Returns
        -------
        list of Update
            List of updates found.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the analyzer type.

        String representing the type of analyzer this is. Used for reporting
        results accumulated from a bunch of analyzers.
        """

    async def update(self, root: Path) -> list[Update]:
        """Analyze a tree and apply updates.

        Returns
        -------
        list of Update
            List of updates applied.
        """
        updates = await self.analyze(root, update=True)
        for update in updates:
            update.apply()
        return updates
