"""Inventory of available GitHub tags."""

from __future__ import annotations

import logging

from gidgethub import GitHubException
from gidgethub.httpx import GitHubAPI
from httpx import AsyncClient, HTTPError

from .version import PackagingVersion, ParsedVersion, SemanticVersion

__all__ = ["GitHubInventory"]


class GitHubInventory:
    """Inventory available tags of a GitHub repository.

    Parameters
    ----------
    http_client
        HTTP client to use for requests.
    """

    def __init__(self, http_client: AsyncClient) -> None:
        self._github = GitHubAPI(http_client, "lsst-sqre/neophile")

    async def inventory(
        self, owner: str, repo: str, *, semantic: bool = False
    ) -> str | None:
        """Return the latest tag of a GitHub repository.

        Parameters
        ----------
        owner
            Owner of the repository.
        repo
            Name of the repository.
        semantic
            If set to true, only semantic versions will be considered and the
            latest version will be determined by semantic version sorting
            instead of `packaging.version.Version`.

        Returns
        -------
        str or None
            The latest tag in sorted order. Tags that parse as valid versions
            sort before tags that do not, which should normally produce the
            correct results when version tags are mixed with other tags. If no
            valid tags are found or the repository doesn't exist, returns
            `None`.
        """
        logging.info(f"Inventorying GitHub repo {owner}/{repo}")
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
        except (GitHubException, HTTPError) as e:
            error = type(e).__name__
            if str(e):
                error += f": {e!s}"
            msg = f"Unable to inventory GitHub repo {owner}/{repo}: {error}"
            logging.exception(msg)
            return None

        if versions:
            return str(max(versions))
        else:
            msg = f"No valid versions for GitHub repo {owner}/{repo}"
            logging.warning(msg)
            return None
