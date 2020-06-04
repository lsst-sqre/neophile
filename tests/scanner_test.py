"""Tests for the Scanner class."""

from __future__ import annotations

from pathlib import Path

from neophile.scanner import Scanner


def test_scanner() -> None:
    datapath = Path(__file__).parent / "data" / "helm"
    scanner = Scanner(root=str(datapath))
    results = scanner.scan()

    assert sorted(results, key=lambda r: r["name"]) == [
        {
            "name": "elasticsearch",
            "type": "helm",
            "version": "1.26.2",
            "repository": "https://kubernetes-charts.storage.googleapis.com/",
            "path": str(datapath / "logging" / "requirements.yaml"),
        },
        {
            "name": "fluentd-elasticsearch",
            "type": "helm",
            "version": ">=3.0.0",
            "repository": "https://kiwigrid.github.io",
            "path": str(datapath / "logging" / "requirements.yaml"),
        },
        {
            "name": "gafaelfawr",
            "type": "helm",
            "version": "1.3.1",
            "repository": "https://lsst-sqre.github.io/charts/",
            "path": str(datapath / "gafaelfawr" / "Chart.yaml"),
        },
        {
            "name": "kibana",
            "type": "helm",
            "version": ">=3.0.0",
            "repository": "https://kubernetes-charts.storage.googleapis.com/",
            "path": str(datapath / "logging" / "requirements.yaml"),
        },
    ]
