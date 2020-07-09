"""Process a set of repositories for updates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from neophile.repository import Repository

if TYPE_CHECKING:
    from neophile.config import Configuration, GitHubRepository
    from neophile.factory import Factory


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

    async def process(self) -> None:
        """Process all configured repositories for updates."""
        for github_repo in self._config.repositories:
            await self._process_one_repository(github_repo)

    async def _process_one_repository(
        self, github_repo: GitHubRepository
    ) -> None:
        """Check a single repository for updates.

        Creates pull requests as necessary if any needed updates are found.

        Parameters
        ----------
        github_repo : `neophile.config.GitHubRepository`
            The GitHub repository to check.
        """
        url = f"https://github.com/{github_repo.owner}/{github_repo.repo}"
        path = self._config.work_area / github_repo.repo
        repo = Repository.clone_or_update(path, url)
        analyzers = self._factory.create_all_analyzers(path)

        repo.switch_branch()
        all_updates = []
        for analyzer in analyzers:
            updates = await analyzer.update()
            all_updates.extend(updates)
        if all_updates:
            pull_requester = self._factory.create_pull_requester(path)
            await pull_requester.make_pull_request(all_updates)
        repo.restore_branch()
