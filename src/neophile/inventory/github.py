"""Inventory of available GitHub tags."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aiohttp import ClientError
from gidgethub.aiohttp import GitHubAPI

from neophile.inventory.version import PackagingVersion, SemanticVersion

if TYPE_CHECKING:
    from typing import Optional

    from aiohttp import ClientSession

    from neophile.config import Configuration

__all__ = [
    "GitHubInventory",
]


class GitHubInventory:
    """Inventory available tags of a GitHub repository.

    Parameters
    ----------
    config : `neophile.config.Configuration`
        neophile configuration.
    session : `aiohttp.ClientSession`
        The aiohttp client session to use to make requests for GitHub tags.
    """

    def __init__(self, config: Configuration, session: ClientSession) -> None:
        self._github = GitHubAPI(
            session,
            config.github_user,
            oauth_token=config.github_token.get_secret_value(),
        )

    async def inventory(
        self, owner: str, repo: str, semantic: bool = False
    ) -> Optional[str]:
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
        cls = SemanticVersion if semantic else PackagingVersion

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
        except ClientError as e:
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
