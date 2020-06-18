"""Tests for the KustomizeUpdate class."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from neophile.exceptions import DependencyNotFoundError
from neophile.update.kustomize import KustomizeUpdate


def test_update(tmp_path: Path) -> None:
    kustomization_path = (
        Path(__file__).parent.parent
        / "data"
        / "kubernetes"
        / "sqrbot-jr"
        / "kustomization.yaml"
    )
    update_path = tmp_path / "kustomization.yaml"
    shutil.copy(str(kustomization_path), str(update_path))

    current = "github.com/lsst-sqre/sqrbot-jr.git//manifests/base?ref=0.6.0"
    new = "github.com/lsst-sqre/sqrbot-jr.git//manifests/base?ref=1.0.0"
    update = KustomizeUpdate(
        path=str(update_path), url=current, current="0.6.0", latest="1.0.0",
    )
    update.apply()

    description = (
        "Update lsst-sqre/sqrbot-jr Kustomize resource from 0.6.0 to 1.0.0"
    )
    assert update.description() == description

    yaml = YAML()
    kustomization = yaml.load(kustomization_path)
    for index, resource in enumerate(kustomization["resources"]):
        if resource == current:
            break
    kustomization["resources"][index] = new
    assert yaml.load(update_path) == kustomization


def test_update_not_found() -> None:
    kustomization_path = (
        Path(__file__).parent.parent
        / "data"
        / "kubernetes"
        / "sqrbot-jr"
        / "kustomization.yaml"
    )

    update = KustomizeUpdate(
        path=str(kustomization_path),
        url="github.com/lsst-sqre/sqrbot//manifests/base?ref=0.7.1",
        current="0.7.0",
        latest="0.8.0",
    )
    with pytest.raises(DependencyNotFoundError):
        update.apply()
