"""Tests for the HelmUpdate class."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from neophile.exceptions import DependencyNotFoundError
from neophile.update.helm import HelmUpdate


def test_update(tmp_path: Path) -> None:
    helm_path = Path(__file__).parent.parent / "data" / "kubernetes"
    chart_path = helm_path / "gafaelfawr" / "Chart.yaml"
    update_path = tmp_path / "Chart.yaml"
    shutil.copy(str(chart_path), str(update_path))

    update = HelmUpdate(
        path=str(update_path),
        applied=False,
        name="gafaelfawr",
        current="1.0.0",
        latest="2.0.0",
    )
    update.apply()
    assert update.applied

    description = "Update gafaelfawr Helm chart from 1.0.0 to 2.0.0"
    assert update.description() == description

    yaml = YAML()
    expected = yaml.load(chart_path)
    expected["dependencies"][0]["version"] = "2.0.0"
    assert yaml.load(update_path) == expected


def test_update_not_found() -> None:
    helm_path = Path(__file__).parent.parent / "data" / "kubernetes"
    requirements_path = helm_path / "logging" / "requirements.yaml"

    update = HelmUpdate(
        path=str(requirements_path),
        applied=False,
        name="gafaelfawr",
        current="1.0.0",
        latest="2.0.0",
    )
    with pytest.raises(DependencyNotFoundError):
        update.apply()
    assert not update.applied

    # Test that if the update is already applied, we won't try again, by
    # running apply and showing that it doesn't thrown an exception.
    update.applied = True
    update.apply()
