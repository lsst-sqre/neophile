"""Inventory of available GitHub tags."""

from __future__ import annotations

import logging

from aiohttp import ClientError, ClientSession
from gidgethub import BadRequest
from gidgethub.aiohttp import GitHubAPI

from ..config import Config
from .version import PackagingVersion, ParsedVersion, SemanticVersion

__all__ = [
    "GitHubInventory",
]


class GitHubInventory:
    """Inventory available tags of a GitHub repository.

    Parameters
    ----------
    config
        neophile configuration.
    session
        The aiohttp client session to use to make requests for GitHub tags.
    """

    def __init__(self, config: Config, session: ClientSession) -> None:
        self._github = GitHubAPI(
            session,
            config.github_user,
            oauth_token=config.github_token.get_secret_value(),
        )

    async def inventory(
        self, owner: str, repo: str, *, semantic: bool = False
    ) -> str | None:
        """Return the latest tag of a GitHub repository.

        Parameters
        ----------
        owner : `str`
            Owner of the repository.
        repo : `str`
            Name of the repository.
        semantic : `bool`, optional
            If set to true, only semantic versions will be considered and the
            latest version will be determined by semantic version sorting
            instead of `packaging.version.Version`.

        Returns
        -------
        result : `str` or `None`
            The latest tag in sorted order.  Tags that parse as valid versions
            sort before tags that do not, which should normally produce the
            correct results when version tags are mixed with other tags.  If
            no valid tags are found or the repository doesn't exist, returns
            `None`.
        """
        logging.info("Inventorying GitHub repo %s/%s", owner, repo)
        if semantic:
            cls: type[ParsedVersion] = SemanticVersion
        else:
            cls = PackagingVersion

        try:
            tags = self._github.getiter(
                "/repos{/owner}{/repo}/tags",
                url_vars={"owner": owner, "repo": repo},
            )
            versions = [
                cls.from_str(tag["name"])
                async for tag in tags
                if cls.is_valid(tag["name"])
            ]
        except (BadRequest, ClientError) as e:
            logging.warning(
                "Unable to inventory GitHub repo %s/%s: %s",
                owner,
                repo,
                str(e),
            )
            return None

        if versions:
            return str(max(versions))
        else:
            logging.warning(
                "No valid versions for GitHub repo %s/%s", owner, repo
            )
            return None
