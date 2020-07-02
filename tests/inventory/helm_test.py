"""Tests for the HelmInventory class."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from unittest.mock import ANY

import aiohttp
import pytest
from aioresponses import aioresponses
from ruamel.yaml import YAML

from neophile.inventory.helm import CachedHelmInventory, HelmInventory

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
async def test_inventory() -> None:
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
        async with aiohttp.ClientSession() as session:
            inventory = HelmInventory(session)
            results = await inventory.inventory("https://example.com/charts/")
            assert results == EXPECTED


@pytest.mark.asyncio
async def test_cached_inventory(cache_path: Path) -> None:
    url = "https://example.com/charts"
    index_path = (
        Path(__file__).parent.parent
        / "data"
        / "kubernetes"
        / "sample-index.yaml"
    )
    index = index_path.read_bytes()
    assert not cache_path.exists()

    with aioresponses() as mock:
        mock.get(url + "/index.yaml", body=index)
        async with aiohttp.ClientSession() as session:
            inventory = CachedHelmInventory(session)
            results = await inventory.inventory(url)
    assert results == EXPECTED

    # Check the cache contains the same data and a correct timestamp.
    yaml = YAML()
    with cache_path.open() as f:
        cache = yaml.load(f)
    assert cache == {url: {"timestamp": ANY, "versions": EXPECTED}}
    now = datetime.now(tz=timezone.utc)
    timestamp = cache[url]["timestamp"]
    assert (now - timedelta(seconds=5)).timestamp() < timestamp
    assert timestamp < now.timestamp()

    # Now, change the data provided to the inventory function.
    yaml = YAML()
    yaml_data = {"entries": {"gafaelfawr": [{"version": "1.4.0"}]}}
    index_output = BytesIO()
    yaml.dump(yaml_data, index_output)
    index = index_output.getvalue()

    # Doing another inventory will return the same results since it will be
    # retrieved from the cache.
    with aioresponses() as mock:
        mock.get(url + "/index.yaml", body=index)
        async with aiohttp.ClientSession() as session:
            inventory = CachedHelmInventory(session)
            results = await inventory.inventory(url)

    # Change the cache timestamp to be older than the cache age.
    cache_timestamp = now - timedelta(seconds=CachedHelmInventory._LIFETIME)
    cache[url]["timestamp"] = cache_timestamp.timestamp()
    with cache_path.open("w") as f:
        yaml.dump(cache, f)

    # Now the inventory will return entirely different results.
    with aioresponses() as mock:
        mock.get(url + "/index.yaml", body=index)
        async with aiohttp.ClientSession() as session:
            inventory = CachedHelmInventory(session)
            results = await inventory.inventory(url)
    assert results == {"gafaelfawr": "1.4.0"}
