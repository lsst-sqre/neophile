"""Factory for neophile components."""

from __future__ import annotations

from typing import TYPE_CHECKING

from neophile.pr import PullRequester

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from neophile.config import Configuration


class Factory:
    """Factory to create neophile components.

    Parameters
    ----------
    config : `neophile.config.Configuration`
        neophile configuration.
    session : `aiohttp.ClientSession`
        The client session to use for requests.
    """

    def __init__(self, config: Configuration, session: ClientSession) -> None:
        self._config = config
        self._session = session

    def create_pull_requester(self, path: str) -> PullRequester:
        """Create a new pull requester.

        Parameters
        ----------
        path : `str`
            Path to the Git repository.

        Returns
        -------
        pull_requester : `neophile.pr.PullRequester`
            New pull requester.
        """
        return PullRequester(path, self._config, self._session)
