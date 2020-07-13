"""Process a set of repositories for updates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from neophile.repository import Repository

if TYPE_CHECKING:
    from neophile.config import Configuration
    from neophile.factory import Factory
    from neophile.update.base import Update
    from pathlib import Path
    from typing import Dict, List

__all__ = ["Processor"]


class Processor:
    """Process a set of repositories for updates.

    Parameters
    ----------
    config : `neophile.config.Configuration`
        The neophile configuration.
    factory : `neophile.factory.Factory`
        Used to create additional components where necessary.
    """

    def __init__(self, config: Configuration, factory: Factory) -> None:
        self._config = config
        self._factory = factory

    async def analyze_checkout(self, path: Path) -> Dict[str, List[Update]]:
        """Analyze a cloned repository without applying updates.

        Parameters
        ----------
        path : `pathlib.Path`
            The path to the cloned repository.

        Returns
        -------
        updates : Dict[`str`, List[`neophile.update.base.Update`]]
            Any updates found, sorted by the analyzer that found the update.
        """
        analyzers = self._factory.create_all_analyzers(path, use_venv=True)
        return {a.name(): await a.analyze() for a in analyzers}

    async def process(self) -> None:
        """Process all configured repositories for updates."""
        for github_repo in self._config.repositories:
            url = f"https://github.com/{github_repo.owner}/{github_repo.repo}"
            path = self._config.work_area / github_repo.repo
            repo = Repository.clone_or_update(path, url)
            await self._process_one_repository(repo, path)

    async def process_checkout(self, path: Path) -> None:
        """Check a cloned repository for updates.

        Creates pull requests as necessary if any needed updates are found.

        Parameters
        ----------
        path : `pathlib.Path`
            The path to the cloned repository.
        """
        repo = Repository(path)
        await self._process_one_repository(repo, path)

    async def update_checkout(self, path: Path) -> List[Update]:
        """Update a cloned repository.

        This does not switch branches.  Updates are written to the current
        working tree.

        Parameters
        ----------
        path : `pathlib.Path`
            The path to the cloned repository.

        Returns
        -------
        updates : List[`neophile.update.base.Update`]
            All the updates that were applied.
        """
        analyzers = self._factory.create_all_analyzers(path, use_venv=True)

        all_updates = []
        for analyzer in analyzers:
            updates = await analyzer.update()
            all_updates.extend(updates)

        return all_updates

    async def _process_one_repository(
        self, repo: Repository, path: Path
    ) -> None:
        """Check a single repository for updates.

        Creates pull requests as necessary if any needed updates are found.

        Parameters
        ----------
        repo : `neophile.repository.Repository`
            The cloned repository to check.
        path : `pathlib.Path`
            The path to the cloned repository.
        """
        repo.switch_branch()
        updates = await self.update_checkout(path)
        if updates:
            pull_requester = self._factory.create_pull_requester(path)
            await pull_requester.make_pull_request(updates)
        repo.restore_branch()
