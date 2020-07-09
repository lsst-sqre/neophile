"""Tests for the HelmScanner class."""

from __future__ import annotations

from pathlib import Path

from neophile.scanner.helm import HelmDependency, HelmScanner


def test_scanner() -> None:
    data_path = Path(__file__).parent.parent / "data" / "kubernetes"
    scanner = HelmScanner(data_path)
    results = scanner.scan()

    assert sorted(results, key=lambda r: r.name) == [
        HelmDependency(
            name="elasticsearch",
            version="1.26.2",
            path=data_path / "logging" / "requirements.yaml",
            repository="https://kubernetes-charts.storage.googleapis.com/",
        ),
        HelmDependency(
            name="fluentd-elasticsearch",
            version=">=3.0.0",
            path=data_path / "logging" / "requirements.yaml",
            repository="https://kiwigrid.github.io",
        ),
        HelmDependency(
            name="gafaelfawr",
            version="1.3.1",
            path=data_path / "gafaelfawr" / "Chart.yaml",
            repository="https://lsst-sqre.github.io/charts/",
        ),
        HelmDependency(
            name="kibana",
            version=">=3.0.0",
            path=data_path / "logging" / "requirements.yaml",
            repository="https://kubernetes-charts.storage.googleapis.com/",
        ),
        HelmDependency(
            name="unknown",
            version="1.5.0",
            path=data_path / "logging" / "requirements.yaml",
            repository="https://kiwigrid.github.io",
        ),
    ]
