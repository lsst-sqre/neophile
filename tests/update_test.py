"""Tests for the HelmUpdater class."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from neophile.exceptions import DependencyNotFoundError
from neophile.update import HelmUpdater


def test_update(tmp_path: Path) -> None:
    helm_path = Path(__file__).parent / "data" / "helm"
    chart_path = helm_path / "gafaelfawr" / "Chart.yaml"
    update_path = tmp_path / "Chart.yaml"
    shutil.copy(str(chart_path), str(update_path))

    updater = HelmUpdater()
    updater.update(str(update_path), "gafaelfawr", "2.0.0")

    yaml = YAML()
    expected = yaml.load(chart_path)
    expected["dependencies"][0]["version"] = "2.0.0"
    assert yaml.load(update_path) == expected


def test_update_not_found() -> None:
    helm_path = Path(__file__).parent / "data" / "helm"
    requirements_path = helm_path / "logging" / "requirements.yaml"

    updater = HelmUpdater()
    with pytest.raises(DependencyNotFoundError):
        updater.update(str(requirements_path), "gafaelfawr", "2.0.0")
