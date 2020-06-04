"""Tests for the Analyzer class."""

from __future__ import annotations

from pathlib import Path

import aiohttp
import pytest
import yaml
from aioresponses import aioresponses

from neophile.analysis import Analyzer


@pytest.mark.asyncio
async def test_analyzer() -> None:
    datapath = Path(__file__).parent / "data" / "helm"
    googleapis = yaml.dump(
        {
            "entries": {
                "elasticsearch": [
                    {"version": "1.24.0"},
                    {"version": "1.26.2"},
                    {"version": "1.25.3"},
                ],
                "kibana": [{"version": "3.0.0"}, {"version": "3.0.1"}],
            }
        }
    )
    kiwigrid = yaml.dump(
        {"entries": {"fluentd-elasticsearch": [{"version": "3.0.0"}]}}
    )
    sqre = yaml.dump({"entries": {"gafaelfawr": [{"version": "1.4.0"}]}})

    with aioresponses() as mock:
        mock.get(
            "https://kubernetes-charts.storage.googleapis.com/index.yaml",
            body=googleapis,
            repeat=True,
        )
        mock.get(
            "https://kiwigrid.github.io/index.yaml", body=kiwigrid, repeat=True
        )
        mock.get(
            "https://lsst-sqre.github.io/charts/index.yaml",
            body=sqre,
            repeat=True,
        )
        async with aiohttp.ClientSession() as session:
            analyzer = Analyzer(str(datapath), session)
            results = await analyzer.analyze()
            analyzer = Analyzer(str(datapath), session, allow_expressions=True)
            results_expressions = await analyzer.analyze()

    assert sorted(results, key=lambda r: r["name"]) == [
        {
            "path": str(datapath / "logging" / "requirements.yaml"),
            "name": "fluentd-elasticsearch",
            "type": "helm",
            "current": ">=3.0.0",
            "latest": "3.0.0",
        },
        {
            "path": str(datapath / "gafaelfawr" / "Chart.yaml"),
            "name": "gafaelfawr",
            "type": "helm",
            "current": "1.3.1",
            "latest": "1.4.0",
        },
        {
            "path": str(datapath / "logging" / "requirements.yaml"),
            "name": "kibana",
            "type": "helm",
            "current": ">=3.0.0",
            "latest": "3.0.1",
        },
    ]

    assert sorted(results_expressions, key=lambda r: r["name"]) == [
        {
            "path": str(datapath / "gafaelfawr" / "Chart.yaml"),
            "name": "gafaelfawr",
            "type": "helm",
            "current": "1.3.1",
            "latest": "1.4.0",
        }
    ]
