"""Tests for the HelmInventory class."""

from __future__ import annotations

from pathlib import Path

import aiohttp
import pytest
from aioresponses import aioresponses

from neophile.inventory import HelmInventory


@pytest.mark.asyncio
async def test_helm_inventory() -> None:
    index_path = Path(__file__).parent / "data" / "helm" / "sample-index.yaml"
    index = index_path.read_bytes()

    with aioresponses() as mock:
        mock.get("https://example.com/charts/index.yaml", body=index)
        async with aiohttp.ClientSession() as session:
            inventory = HelmInventory(session)
            results = await inventory.inventory("https://example.com/charts/")

    assert results == {
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
