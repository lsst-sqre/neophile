"""Tests for the HelmUpdater class."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from neophile.exceptions import DependencyNotFoundError
from neophile.update import HelmUpdate, PythonFrozenUpdate


def test_helm_update(tmp_path: Path) -> None:
    helm_path = Path(__file__).parent / "data" / "helm"
    chart_path = helm_path / "gafaelfawr" / "Chart.yaml"
    update_path = tmp_path / "Chart.yaml"
    shutil.copy(str(chart_path), str(update_path))

    update = HelmUpdate(
        name="gafaelfawr",
        current="1.0.0",
        latest="2.0.0",
        path=str(update_path),
    )
    update.apply()

    description = "Update gafaelfawr Helm chart from 1.0.0 to 2.0.0"
    assert update.description() == description

    yaml = YAML()
    expected = yaml.load(chart_path)
    expected["dependencies"][0]["version"] = "2.0.0"
    assert yaml.load(update_path) == expected


def test_helm_update_not_found() -> None:
    helm_path = Path(__file__).parent / "data" / "helm"
    requirements_path = helm_path / "logging" / "requirements.yaml"

    update = HelmUpdate(
        name="gafaelfawr",
        current="1.0.0",
        latest="2.0.0",
        path=str(requirements_path),
    )
    with pytest.raises(DependencyNotFoundError):
        update.apply()


def test_python_update(tmp_path: Path) -> None:
    data_path = Path(__file__).parent / "data" / "python"
    main_path = tmp_path / "requirements" / "main.txt"
    shutil.copytree(str(data_path), str(tmp_path), dirs_exist_ok=True)

    with (data_path / "Makefile").open() as f:
        for line in f:
            match = re.match("NEW = (.*)", line)
            if match:
                new_hash = match.group(1)
    assert new_hash not in main_path.read_text()

    update = PythonFrozenUpdate(
        name="python-deps", path=str(tmp_path / "requirements")
    )
    assert "Python" in update.description()
    update.apply()
    assert new_hash in main_path.read_text()
