"""Tests for the command-line interface."""

from __future__ import annotations

import shutil
from io import StringIO
from pathlib import Path

from aioresponses import aioresponses
from click.testing import CliRunner
from ruamel.yaml import YAML

from neophile.cli import main


def test_help() -> None:
    runner = CliRunner()

    result = runner.invoke(main, ["-h"])
    assert result.exit_code == 0
    assert "Commands:" in result.output

    result = runner.invoke(main, ["help"])
    assert result.exit_code == 0
    assert "Commands:" in result.output

    result = runner.invoke(main, ["help", "scan"])
    assert result.exit_code == 0
    assert "Commands:" not in result.output
    assert "Options:" in result.output

    result = runner.invoke(main, ["help", "unknown-command"])
    assert result.exit_code != 0
    assert "Unknown help topic unknown-command" in result.output


def test_analyze() -> None:
    runner = CliRunner()

    yaml = YAML()
    output = StringIO()
    yaml.dump({"entries": {"gafaelfawr": [{"version": "1.4.0"}]}}, output)
    sqre = output.getvalue()
    root = Path(__file__).parent / "data" / "helm" / "gafaelfawr"
    with aioresponses() as mock:
        mock.get("https://lsst-sqre.github.io/charts/index.yaml", body=sqre)
        result = runner.invoke(main, ["analyze", "--path", str(root)])

    assert result.exit_code == 0
    data = yaml.load(result.output)
    assert data[0]["name"] == "gafaelfawr"
    assert data[0]["current"] == "1.3.1"
    assert data[0]["latest"] == "1.4.0"


def test_analyze_update(tmp_path: Path) -> None:
    runner = CliRunner()
    src = Path(__file__).parent / "data" / "helm" / "gafaelfawr" / "Chart.yaml"
    dst = tmp_path / "Chart.yaml"
    shutil.copy(src, dst)
    yaml = YAML()
    output = StringIO()
    yaml.dump({"entries": {"gafaelfawr": [{"version": "1.4.0"}]}}, output)
    sqre = output.getvalue()

    with aioresponses() as mock:
        mock.get("https://lsst-sqre.github.io/charts/index.yaml", body=sqre)
        result = runner.invoke(
            main, ["analyze", "--path", str(tmp_path), "--update"]
        )

    assert result.exit_code == 0
    data = yaml.load(dst)
    assert data["dependencies"][0]["version"] == "1.4.0"


def test_inventory() -> None:
    runner = CliRunner()

    index_path = Path(__file__).parent / "data" / "helm" / "sample-index.yaml"
    index_data = index_path.read_bytes()
    with aioresponses() as mock:
        mock.get("https://example.com/index.yaml", body=index_data)
        result = runner.invoke(main, ["inventory", "https://example.com/"])
    assert result.exit_code == 0
    yaml = YAML()
    data = yaml.load(result.output)
    assert data["gafaelfawr"] == "1.3.1"


def test_scan() -> None:
    runner = CliRunner()

    path = Path(__file__).parent / "data" / "helm"
    result = runner.invoke(main, ["scan", "--path", str(path)])
    assert result.exit_code == 0
    yaml = YAML()
    data = yaml.load(result.output)
    assert sorted(data, key=lambda r: r["name"])[0]["name"] == "elasticsearch"
