"""Tests for the Analyzer class."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING

import aiohttp
import pytest
from aioresponses import aioresponses
from ruamel.yaml import YAML

from neophile.analysis import Analyzer
from neophile.update import HelmUpdate

if TYPE_CHECKING:
    from typing import Any, Dict


def yaml_to_string(data: Dict[str, Any]) -> str:
    yaml = YAML()
    output = StringIO()
    yaml.dump(data, output)
    return output.getvalue()


@pytest.mark.asyncio
async def test_analyzer() -> None:
    datapath = Path(__file__).parent / "data" / "helm"
    googleapis = yaml_to_string(
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
    kiwigrid = yaml_to_string(
        {"entries": {"fluentd-elasticsearch": [{"version": "3.0.0"}]}}
    )
    sqre = yaml_to_string({"entries": {"gafaelfawr": [{"version": "1.4.0"}]}})

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

    assert sorted(results, key=lambda r: r.name) == [
        HelmUpdate(
            name="fluentd-elasticsearch",
            current=">=3.0.0",
            latest="3.0.0",
            path=str(datapath / "logging" / "requirements.yaml"),
        ),
        HelmUpdate(
            name="gafaelfawr",
            current="1.3.1",
            latest="1.4.0",
            path=str(datapath / "gafaelfawr" / "Chart.yaml"),
        ),
        HelmUpdate(
            name="kibana",
            current=">=3.0.0",
            latest="3.0.1",
            path=str(datapath / "logging" / "requirements.yaml"),
        ),
    ]

    assert sorted(results_expressions, key=lambda r: r.name) == [
        HelmUpdate(
            name="gafaelfawr",
            current="1.3.1",
            latest="1.4.0",
            path=str(datapath / "gafaelfawr" / "Chart.yaml"),
        )
    ]
