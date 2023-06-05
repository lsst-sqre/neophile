"""Inventory of available Helm chart versions."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING
from urllib.parse import urljoin

from ruamel.yaml import YAML

from neophile.inventory.version import SemanticVersion

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any

    from aiohttp import ClientSession

__all__ = [
    "CachedHelmInventory",
    "HelmInventory",
]


class HelmInventory:
    """Inventory the versions available from a Helm repository.

    Parameters
    ----------
    session : `aiohttp.ClientSession`
        The aiohttp client session to use to make requests for Helm repository
        index files.
    """

    def __init__(self, session: ClientSession) -> None:
        self._session = session
        self._yaml = YAML()

    def canonicalize_url(self, url: str) -> str:
        """Canonicalize the URL for a Helm repository.

        Parameters
        ----------
        url : `str`
            The URL for a Helm repository.

        Returns
        -------
        canonical_url : `str`
            The canonical URL for the index.yaml file of the repository.
        """
        if url.endswith("/index.yaml"):
            return url
        if not url.endswith("/"):
            url += "/"
        return urljoin(url, "index.yaml")

    async def inventory(self, url: str) -> dict[str, str]:
        """Inventory the available versions of Helm charts.

        Retrieve the inventory from the given Helm repository.

        Parameters
        ----------
        url : `str`
            URL of the repository.

        Returns
        -------
        results : Dict[`str`, `str`]
            Returns a dict of Helm chart names to the latest available version
            of that Helm chart.

        Raises
        ------
        aiohttp.ClientError
            Failure to retrieve the index file from the Helm repository.
        yaml.YAMLError
            The index file for the repository doesn't parse as YAML.
        """
        url = self.canonicalize_url(url)
        logging.info("Inventorying %s", url)
        r = await self._session.get(url, raise_for_status=True)
        index = self._yaml.load(await r.text())

        results = {}
        for name, data in index.get("entries", {}).items():
            versions = []
            for release in data:
                if "version" in release:
                    version = release["version"]
                    if SemanticVersion.is_valid(version):
                        versions.append(SemanticVersion.from_str(version))
            if versions:
                results[name] = str(max(versions))

        return results


class CachedHelmInventory(HelmInventory):
    """Cache the inventory of versions from a Helm repository.

    Currently this does not protect against multiple versions of neophile
    runnign simultaneously.  This can be added later.

    Parameters
    ----------
    session : `aiohttp.ClientSession`
        The aiohttp client session to use to make requests for Helm repository
        index files.
    """

    _LIFETIME = 24 * 60 * 60
    """Lifetime of a version cache in seconds (one day)."""

    def __init__(self, session: ClientSession, cache_path: Path) -> None:
        super().__init__(session)
        self._cache: dict[str, dict[str, Any]] = {}
        self._cache_path = cache_path
        self._load_cache()

    async def inventory(self, url: str) -> dict[str, str]:
        """Inventory the available versions of Helm charts.

        Retrieve the inventory from the given Helm repository.

        Parameters
        ----------
        url : `str`
            URL of the repository.

        Returns
        -------
        results : Dict[`str`, `str`]
            Returns a dict of Helm chart names to the latest available version
            of that Helm chart.

        Raises
        ------
        aiohttp.ClientError
            Failure to retrieve the index file from the Helm repository.
        yaml.YAMLError
            The index file for the repository doesn't parse as YAML.

        Notes
        -----
        This makes a copy of the contents of the cache to prevent the caller
        from mutating the cache unexpectedly.
        """
        url = self.canonicalize_url(url)
        now = time.time()
        if url in self._cache:
            age = self._cache[url]["timestamp"]
            if age + self._LIFETIME > now:
                return self._cache[url]["versions"]

        result = await super().inventory(url)
        self._cache[url] = {"timestamp": now, "versions": result}
        self._save_cache()
        return result

    def _load_cache(self) -> None:
        """Load the version cache from disk."""
        if self._cache_path.is_file():
            self._cache = self._yaml.load(self._cache_path)

    def _save_cache(self) -> None:
        """Save the cache to disk."""
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._yaml.dump(self._cache, self._cache_path)
