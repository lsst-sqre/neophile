"""Tests for the HelmInventory class."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import ANY

import pytest
from aioresponses import aioresponses
from ruamel.yaml import YAML

from neophile.inventory.helm import CachedHelmInventory, HelmInventory
from tests.util import dict_to_yaml

if TYPE_CHECKING:
    from aiohttp import ClientSession

EXPECTED = {
    "cadc-tap": "0.1.9",
    "cadc-tap-postgres": "0.1.1",
    "chronograf": "1.3.0",
    "fileserver": "0.2.1",
    "firefly": "0.1.2",
    "gafaelfawr": "1.3.1",
    "influxdb": "3.0.3",
    "kafka-connect-manager": "0.4.0",
    "kapacitor": "1.3.0",
    "landing-page": "0.2.2",
    "nublado": "0.8.5",
    "opendistro-es": "1.4.0",
    "postgres": "0.0.23",
}
"""Expected inventory from tests/data/helm/sample-index.yaml."""


@pytest.mark.asyncio
async def test_inventory(session: ClientSession) -> None:
    index_path = (
        Path(__file__).parent.parent
        / "data"
        / "kubernetes"
        / "sample-index.yaml"
    )
    index = index_path.read_bytes()

    with aioresponses() as mock:
        mock.get(
            "https://example.com/charts/index.yaml", body=index, repeat=True
        )
        inventory = HelmInventory(session)
        results = await inventory.inventory("https://example.com/charts/")
        assert results == EXPECTED


@pytest.mark.asyncio
async def test_cached_inventory(
    tmp_path: Path, session: ClientSession
) -> None:
    url = "https://example.com/charts"
    full_url = url + "/index.yaml"
    index_path = (
        Path(__file__).parent.parent
        / "data"
        / "kubernetes"
        / "sample-index.yaml"
    )
    index = index_path.read_text()
    cache_path = tmp_path / "helm.yaml"
    assert not cache_path.exists()

    with aioresponses() as mock:
        mock.get(full_url, body=index)
        inventory = CachedHelmInventory(session, cache_path)
        results = await inventory.inventory(url)
    assert results == EXPECTED

    # Check the cache contains the same data and a correct timestamp.
    yaml = YAML()
    cache = yaml.load(cache_path)
    assert cache == {full_url: {"timestamp": ANY, "versions": EXPECTED}}
    now = datetime.now(tz=timezone.utc)
    timestamp = cache[full_url]["timestamp"]
    assert (now - timedelta(seconds=5)).timestamp() < timestamp
    assert timestamp < now.timestamp()

    # Now, change the data provided to the inventory function.
    index = dict_to_yaml({"entries": {"gafaelfawr": [{"version": "1.4.0"}]}})

    # Doing another inventory will return the same results since it will be
    # retrieved from the cache.
    with aioresponses() as mock:
        mock.get(full_url, body=index)
        inventory = CachedHelmInventory(session, cache_path)
        results = await inventory.inventory(url)

    # Change the cache timestamp to be older than the cache age.
    cache_timestamp = now - timedelta(seconds=CachedHelmInventory._LIFETIME)
    cache[full_url]["timestamp"] = cache_timestamp.timestamp()
    yaml.dump(cache, cache_path)

    # Now the inventory will return entirely different results.
    with aioresponses() as mock:
        mock.get(full_url, body=index)
        inventory = CachedHelmInventory(session, cache_path)
        results = await inventory.inventory(url)
    assert results == {"gafaelfawr": "1.4.0"}
