"""Tests for the command-line interface."""

from __future__ import annotations

from pathlib import Path

import yaml
from aioresponses import aioresponses
from click.testing import CliRunner

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

    result = runner.invoke(main, ["help", "unknown-command"])
    assert result.exit_code != 0
    assert "Unknown help topic unknown-command" in result.output


def test_analyze() -> None:
    runner = CliRunner()

    sqre = yaml.dump({"entries": {"gafaelfawr": [{"version": "1.4.0"}]}})
    root = Path(__file__).parent / "data" / "helm" / "gafaelfawr"
    with aioresponses() as mock:
        mock.get("https://lsst-sqre.github.io/charts/index.yaml", body=sqre)
        result = runner.invoke(main, ["analyze", "--path", str(root)])

    print(result)
    print(result.output)
    assert result.exit_code == 0
    data = yaml.safe_load(result.output)
    assert data[0]["name"] == "gafaelfawr"
    assert data[0]["current"] == "1.3.1"
    assert data[0]["latest"] == "1.4.0"


def test_inventory() -> None:
    runner = CliRunner()

    index_path = Path(__file__).parent / "data" / "helm" / "sample-index.yaml"
    index_data = index_path.read_bytes()
    with aioresponses() as mock:
        mock.get("https://example.com/index.yaml", body=index_data)
        result = runner.invoke(main, ["inventory", "https://example.com/"])
    assert result.exit_code == 0
    data = yaml.safe_load(result.output)
    assert data["gafaelfawr"] == "1.3.1"


def test_scan() -> None:
    runner = CliRunner()

    path = Path(__file__).parent / "data" / "helm"
    result = runner.invoke(main, ["scan", "--path", str(path)])
    assert result.exit_code == 0
    data = yaml.safe_load(result.output)
    assert sorted(data, key=lambda r: r["name"])[0]["name"] == "elasticsearch"
