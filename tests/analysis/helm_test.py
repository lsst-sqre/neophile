"""Tests for the HelmAnalyzer class."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import ClientSession
from aioresponses import aioresponses

from neophile.analysis.helm import HelmAnalyzer
from neophile.inventory.helm import HelmInventory
from neophile.scanner.helm import HelmScanner
from neophile.update.helm import HelmUpdate

from ..util import dict_to_yaml

MOCK_REPOSITORIES = {
    "https://kubernetes-charts.storage.googleapis.com/index.yaml": {
        "entries": {
            "elasticsearch": [
                {"version": "1.24.0"},
                {"version": "1.26.2"},
                {"version": "1.25.3"},
            ],
            "kibana": [{"version": "3.0.0"}, {"version": "3.0.1"}],
        }
    },
    "https://kiwigrid.github.io/index.yaml": {
        "entries": {"fluentd-elasticsearch": [{"version": "3.0.0"}]}
    },
    "https://lsst-sqre.github.io/charts/index.yaml": {
        "entries": {"gafaelfawr": [{"version": "v1.4.0"}]}
    },
}
"""Indexes for mock repositories with some chart versions."""


@pytest.mark.asyncio
async def test_analyzer(session: ClientSession) -> None:
    data_path = Path(__file__).parent.parent / "data" / "kubernetes"

    # Do not use Factory here because it will use a CachedHelmInventory, which
    # may use an existing cache from the person running the test without
    # further mocking that's not done in this test.
    with aioresponses() as mock:
        for url, index in MOCK_REPOSITORIES.items():
            mock.get(url, body=dict_to_yaml(index), repeat=True)
        scanner = HelmScanner()
        inventory = HelmInventory(session)
        analyzer = HelmAnalyzer(scanner, inventory)
        results = await analyzer.analyze(data_path)
        analyzer = HelmAnalyzer(scanner, inventory, allow_expressions=True)
        results_expressions = await analyzer.analyze(data_path)

    assert sorted(results) == [
        HelmUpdate(
            path=data_path / "gafaelfawr" / "Chart.yaml",
            applied=False,
            name="gafaelfawr",
            current="1.3.1",
            latest="v1.4.0",
        ),
        HelmUpdate(
            path=data_path / "logging" / "requirements.yaml",
            applied=False,
            name="fluentd-elasticsearch",
            current=">=3.0.0",
            latest="3.0.0",
        ),
        HelmUpdate(
            path=data_path / "logging" / "requirements.yaml",
            applied=False,
            name="kibana",
            current=">=3.0.0",
            latest="3.0.1",
        ),
    ]
    assert results_expressions == [
        HelmUpdate(
            path=data_path / "gafaelfawr" / "Chart.yaml",
            applied=False,
            name="gafaelfawr",
            current="1.3.1",
            latest="v1.4.0",
        ),
    ]
