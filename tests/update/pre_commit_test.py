"""Tests for the PreCommitUpdate class."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from neophile.exceptions import DependencyNotFoundError
from neophile.update.pre_commit import PreCommitUpdate


def test_update(tmp_path: Path) -> None:
    source_path = (
        Path(__file__).parent.parent
        / "data"
        / "python"
        / ".pre-commit-config.yaml"
    )
    config_path = tmp_path / ".pre-commit-config.yaml"
    shutil.copy(str(source_path), str(config_path))

    update = PreCommitUpdate(
        repository="https://github.com/pre-commit/pre-commit-hooks",
        current="v3.1.0",
        latest="v3.1.1",
        path=str(config_path),
    )
    update.apply()

    description = (
        "Update pre-commit/pre-commit-hooks pre-commit hook from v3.1.0 to"
        " v3.1.1"
    )
    assert update.description() == description

    yaml = YAML()
    expected = yaml.load(source_path)
    expected["repos"][0]["rev"] = "v3.1.1"
    assert yaml.load(config_path) == expected


def test_update_not_found() -> None:
    source_path = (
        Path(__file__).parent.parent
        / "data"
        / "python"
        / ".pre-commit-config.yaml"
    )

    update = PreCommitUpdate(
        repository="https://github.com/foo/bar",
        current="1.0.0",
        latest="1.2.0",
        path=str(source_path),
    )
    with pytest.raises(DependencyNotFoundError):
        update.apply()
