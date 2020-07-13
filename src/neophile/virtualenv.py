"""Virtual environment handling."""

from __future__ import annotations

import os
import subprocess
from typing import TYPE_CHECKING
from venv import EnvBuilder

if TYPE_CHECKING:
    from pathlib import Path
    from subprocess import CompletedProcess
    from typing import Any, Dict, Sequence

__all__ = ["VirtualEnv"]


class VirtualEnv:
    """Manage virtual environments.

    Python dependency updates using ``make update`` have to be done inside a
    virtual environment because they may attempt to install packages with
    pip.  This class manages creation and execution of commands inside a
    virtual environment.

    Parameters
    ----------
    path : `pathlib.Path`
        Path to where to create the virtual environment.  If that directory
        already exists, it will be used as an existing virtual environment
        instead of creating a new one.
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    def create(self) -> None:
        """Create the virtualenv if it does not already exist."""
        if self._path.is_dir():
            return
        EnvBuilder(with_pip=True).create(str(self._path))

    def run(self, command: Sequence[str], **kwargs: Any) -> CompletedProcess:
        """Run a command inside the virtualenv.

        Parameters
        ----------
        command : Sequence[`str`]
            The command to run.
        **kwargs: `typing.Any`
            The arguments, which except for the ``env`` parameter if any will
            be passed as-is to :py:func:`subprocess.run`.

        Returns
        -------
        result : `subprocess.CompletedProcess`
            The return value of :py:func:`subprocess.run`.
        """
        self.create()
        if "env" in kwargs:
            env: Dict[str, str] = dict(kwargs["env"])
        else:
            env = dict(os.environ)
        env["PATH"] = str(self._path / "bin") + ":" + os.environ["PATH"]
        env["VIRTUAL_ENV"] = str(self._path)
        kwargs["env"] = env

        return subprocess.run(command, **kwargs)
