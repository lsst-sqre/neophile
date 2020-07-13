"""Tests for the PythonFrozenUpdate class."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from neophile.update.python import PythonFrozenUpdate
from neophile.virtualenv import VirtualEnv
from tests.util import setup_python_repo


def test_python_update(tmp_path: Path) -> None:
    data_path = Path(__file__).parent.parent / "data" / "python"
    main_path = tmp_path / "requirements" / "main.txt"
    shutil.copytree(str(data_path), str(tmp_path), dirs_exist_ok=True)

    with (data_path / "Makefile").open() as f:
        for line in f:
            match = re.match("NEW = (.*)", line)
            if match:
                new_hash = match.group(1)
    assert new_hash not in main_path.read_text()

    update = PythonFrozenUpdate(path=tmp_path / "requirements", applied=False)
    assert "Python" in update.description()
    update.apply()
    assert new_hash in main_path.read_text()


def test_python_update_applied(tmp_path: Path) -> None:
    data_path = Path(__file__).parent.parent / "data" / "python"
    main_path = tmp_path / "requirements" / "main.txt"
    shutil.copytree(str(data_path), str(tmp_path), dirs_exist_ok=True)
    main_data = main_path.read_text()

    update = PythonFrozenUpdate(path=tmp_path / "requirements", applied=True)
    update.apply()
    assert main_data == main_path.read_text()


def test_virtualenv(tmp_path: Path) -> None:
    setup_python_repo(tmp_path / "python", require_venv=True)
    requirements_path = tmp_path / "python" / "requirements"

    update = PythonFrozenUpdate(path=requirements_path, applied=False)
    with pytest.raises(subprocess.CalledProcessError):
        update.apply()
    update = PythonFrozenUpdate(
        path=requirements_path,
        applied=False,
        virtualenv=VirtualEnv(tmp_path / "venv"),
    )
    update.apply()

    with (tmp_path / "python" / "Makefile").open() as f:
        for line in f:
            match = re.match("NEW = (.*)", line)
            if match:
                new_hash = match.group(1)
    main_path = requirements_path / "main.txt"
    assert new_hash in main_path.read_text()
