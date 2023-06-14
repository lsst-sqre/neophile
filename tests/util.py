"""Utility functions for tests."""

from __future__ import annotations

import shutil
from collections.abc import Mapping
from io import StringIO
from pathlib import Path
from typing import Any

from git.repo import Repo
from git.util import Actor
from ruamel.yaml import YAML

__all__ = [
    "dict_to_yaml",
    "setup_python_repo",
]


def dict_to_yaml(data: Mapping[str, Any]) -> str:
    """Convert any mapping to YAML serialized as a string.

    Parameters
    ----------
    data
        Data to convert.

    Returns
    -------
    str
        Data serialized as YAML.
    """
    yaml = YAML()
    output = StringIO()
    yaml.dump(data, output)
    return output.getvalue()


def setup_python_repo(tmp_path: Path) -> Repo:
    """Set up a test repository with the Python test files.

    Parameters
    ----------
    tmp_path
        The directory in which to create the repository.

    Returns
    -------
    Repo
        Repository object.
    """
    data_path = Path(__file__).parent / "data" / "python"
    shutil.copytree(str(data_path), str(tmp_path), dirs_exist_ok=True)
    repo = Repo.init(str(tmp_path), initial_branch="main")
    repo.index.add(
        [
            str(tmp_path / ".pre-commit-config.yaml"),
            str(tmp_path / "Makefile"),
            str(tmp_path / "requirements"),
        ]
    )
    actor = Actor("Someone", "someone@example.com")
    repo.index.commit("Initial commit", author=actor, committer=actor)
    return repo
