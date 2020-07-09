"""Tests for scanner utilities."""

from __future__ import annotations

from pathlib import Path

from neophile.scanner.util import find_files


def test_find_files() -> None:
    data_path = Path(__file__).parent.parent / "data" / "kubernetes"
    files = find_files(data_path, {"Chart.yaml", "kustomization.yaml"})

    assert data_path / "gafaelfawr" / "Chart.yaml" in files
    assert data_path / "sqrbot-jr" / "kustomization.yaml" in files
    assert data_path / "tests" / "Chart.yaml" not in files
    assert data_path / "tests" / "kustomization.yaml" not in files
