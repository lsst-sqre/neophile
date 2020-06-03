"""Inventory of available versions."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING
from urllib.parse import urljoin

import yaml

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from typing import DefaultDict, Dict, List

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

    async def inventory(self, url: str) -> Dict[str, List[str]]:
        """Inventory the available versions of Helm charts.

        Retrieve the inventory from the given Helm repository.

        Parameters
        ----------
        url : `str`
            URL of the repository.

        Returns
        -------
        results : Dict[`str`, List[`str`]]
            Returns a dict of Helm chart names to a list of available versions
            of that Helm chart.

        Raises
        ------
        aiohttp.ClientError
            Failure to retrieve the index file from the Helm repository.
        yaml.YAMLError
            The index file for the repository doesn't parse as YAML.
        """
        index_url = urljoin(url, "index.yaml")
        r = await self._session.get(index_url, raise_for_status=True)
        index = yaml.safe_load(await r.text())

        results: DefaultDict[str, List[str]] = defaultdict(list)
        for name, data in index.get("entries", {}).items():
            for release in data:
                if "version" in release:
                    results[name].append(release["version"])

        return results
