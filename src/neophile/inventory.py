"""Inventory of available versions."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import urljoin

import yaml
from semver import VersionInfo

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from typing import Dict

__all__ = ["HelmInventory"]


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
        index = yaml.safe_load(await r.text())

        results = {}
        for name, data in index.get("entries", {}).items():
            versions = []
            for release in data:
                if "version" in release:
                    if not VersionInfo.isvalid(release["version"]):
                        continue
                    version = VersionInfo.parse(release["version"])
                    versions.append(version)
            if versions:
                results[name] = str(max(versions))

        return results
