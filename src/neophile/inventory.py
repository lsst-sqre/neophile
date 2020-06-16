"""Inventory of available versions."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from urllib.parse import urljoin

from ruamel.yaml import YAML
from semver import VersionInfo
from xdg import XDG_CACHE_HOME

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from typing import Any, Dict

__all__ = [
    "CachedHelmInventory",
    "HelmInventory",
]


@dataclass(frozen=True, order=True)
class Version:
    """Represents a version string."""

    parsed_version: VersionInfo
    """The parsed version of it, for sorting.

    Notes
    -----
    This field must be first because it's the field we want to sort on and
    dataclass ordering is done as if the dataclass were a tuple, via ordering
    on each element of the tuple in sequence.
    """

    version: str
    """The raw version string, which may start with a v."""

    def __str__(self) -> str:
        return self.version


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

    async def inventory(self, url: str) -> Dict[str, str]:
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
        logging.info("Inventorying %s", url)
        if not url.endswith("/"):
            url += "/"
        index_url = urljoin(url, "index.yaml")
        r = await self._session.get(index_url, raise_for_status=True)
        index = self._yaml.load(await r.text())

        results = {}
        for name, data in index.get("entries", {}).items():
            versions = []
            for release in data:
                if "version" in release:
                    if release["version"].startswith("v"):
                        version = release["version"][1:]
                    else:
                        version = release["version"]
                    if not VersionInfo.isvalid(version):
                        continue
                    versions.append(
                        Version(
                            version=release["version"],
                            parsed_version=VersionInfo.parse(version),
                        )
                    )
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

    _CACHE_PATH = XDG_CACHE_HOME / "neophile" / "helm.yaml"
    """Path to the cache file."""

    _LIFETIME = 24 * 60 * 60
    """Lifetime of a version cache in seconds (one day)."""

    def __init__(self, session: ClientSession) -> None:
        super().__init__(session)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load_cache()

    async def inventory(self, url: str) -> Dict[str, str]:
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
        now = datetime.now(tz=timezone.utc).timestamp()
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
        if self._CACHE_PATH.is_file():
            with self._CACHE_PATH.open() as f:
                self._cache = self._yaml.load(f)

    def _save_cache(self) -> None:
        """Save the cache to disk."""
        self._CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with self._CACHE_PATH.open("w") as f:
            self._yaml.dump(self._cache, f)
