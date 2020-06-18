"""Tests for the KustomizeScanner class."""

from __future__ import annotations

from pathlib import Path

from neophile.scanner.kustomize import KustomizeDependency, KustomizeScanner


def test_scanner() -> None:
    data_path = Path(__file__).parent.parent / "data" / "kubernetes"
    scanner = KustomizeScanner(root=str(data_path))
    results = scanner.scan()

    assert sorted(results) == [
        KustomizeDependency(
            url="github.com/lsst-sqre/sqrbot-jr.git//manifests/base?ref=0.6.0",
            owner="lsst-sqre",
            repo="sqrbot-jr",
            version="0.6.0",
            path=str(data_path / "sqrbot-jr" / "kustomization.yaml"),
        ),
        KustomizeDependency(
            url="github.com/lsst-sqre/sqrbot//manifests/base?ref=0.7.0",
            owner="lsst-sqre",
            repo="sqrbot",
            version="0.7.0",
            path=str(data_path / "sqrbot-jr" / "kustomization.yaml"),
        ),
    ]
