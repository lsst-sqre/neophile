"""Process a set of repositories for updates."""

from __future__ import annotations

from pathlib import Path

from .analysis.base import BaseAnalyzer
from .config import Config
from .pr import PullRequester
from .repository import Repository
from .update.base import Update

__all__ = ["Processor"]


class Processor:
    """Process a set of repositories for updates.

    Parameters
    ----------
    config
        neophile configuration.
    analyzers
        Analyzers to run on the repositories.
    pull_requester
        Used to create pull requests.
    """

    def __init__(
        self,
        config: Config,
        analyzers: list[BaseAnalyzer],
        pull_requester: PullRequester,
    ) -> None:
        self._config = config
        self._analyzers = analyzers
        self._pull_requester = pull_requester

    async def analyze_checkout(self, path: Path) -> dict[str, list[Update]]:
        """Analyze a cloned repository without applying updates.

        Parameters
        ----------
        path
            Path to the cloned repository.

        Returns
        -------
        dict of Update
            Any updates found, organized by the analyzer that found the
            update.
        """
        results = {}
        for analyzer in self._analyzers:
            analysis = await analyzer.analyze(path)
            if analysis:
                results[analyzer.name] = analysis
        return results

    async def process_checkout(self, path: Path) -> None:
        """Check a cloned repository for updates.

        Creates pull requests as necessary if any needed updates are found.

        Parameters
        ----------
        path
            Path to the cloned repository.
        """
        repo = Repository(path)
        await self._process_one_repository(repo, path)

    async def update_checkout(self, path: Path) -> list[Update]:
        """Update a cloned repository.

        This does not switch branches. Updates are written to the current
        working tree.

        Parameters
        ----------
        path
            Path to the cloned repository.

        Returns
        -------
        list of Update
            All the updates that were applied.
        """
        all_updates = []
        for analyzer in self._analyzers:
            updates = await analyzer.update(path)
            all_updates.extend(updates)
        return all_updates

    async def _process_one_repository(
        self, repo: Repository, path: Path
    ) -> None:
        """Check a single repository for updates.

        Creates pull requests as necessary if any needed updates are found.

        Parameters
        ----------
        repo
            Cloned repository to check.
        path
            Path to the cloned repository.
        """
        repo.switch_branch()
        updates = await self.update_checkout(path)
        if updates:
            await self._pull_requester.make_pull_request(path, updates)
        repo.restore_branch()
