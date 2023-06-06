"""Tests for the VirtualEnv class."""

from __future__ import annotations

from pathlib import Path

from neophile.virtualenv import VirtualEnv


def test_provided_env(tmp_path: Path) -> None:
    """Test virtualenv execution with an env parameter."""
    venv_path = tmp_path / "venv"
    venv = VirtualEnv(venv_path)
    result = venv.run(
        ["/bin/sh", "-c", "echo $FOO"],
        capture_output=True,
        text=True,
        env={"FOO": "testing"},
    )
    assert result.stdout == "testing\n"
    assert (venv_path / "bin" / "activate").exists()


def test_preexisting(tmp_path: Path) -> None:
    """If the directory exists, create should silently do nothing."""
    venv_path = tmp_path / "venv"
    venv_path.mkdir()
    venv = VirtualEnv(venv_path)
    venv.create()
    assert not (venv_path / "bin" / "activate").exists()
