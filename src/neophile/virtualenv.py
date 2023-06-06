"""Virtual environment handling."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Sequence
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any
from venv import EnvBuilder

__all__ = ["VirtualEnv"]


class VirtualEnv:
    """Manage virtual environments.

    Python dependency updates using ``make update`` have to be done inside a
    virtual environment because they may attempt to install packages with
    ``pip``. This class manages creation and execution of commands inside a
    virtual environment.

    Parameters
    ----------
    path
        Path to where to create the virtual environment. If that directory
        already exists, it will be used as an existing virtual environment
        instead of creating a new one.
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    def create(self) -> None:
        """Create the virtualenv if it does not already exist.

        Raises
        ------
        subprocess.CalledProcessError
            Raised on failure to install the wheel package.
        """
        if self._path.is_dir():
            return
        EnvBuilder(with_pip=True).create(str(self._path))
        env = self._build_env()
        subprocess.run(
            ["pip", "install", "wheel"],
            env=env,
            cwd=str(self._path),
            check=True,
            capture_output=True,
        )

    def run(self, command: Sequence[str], **kwargs: Any) -> CompletedProcess:
        """Run a command inside the virtualenv.

        Sets up the virtualenv if necessary and then runs the command given.

        Parameters
        ----------
        command
            The command to run.
        **kwargs
            The arguments, which except for the ``env`` parameter if any will
            be passed as-is to `subprocess.run`.

        Returns
        -------
        subprocess.CompletedProcess
            Return value of `subprocess.run`.

        Raises
        ------
        subprocess.CalledProcessError
            Raised on failure to install the wheel package or failure of the
            provided command.
        """
        self.create()

        env = self._build_env(kwargs.get("env"))
        kwargs["env"] = env
        return subprocess.run(command, **kwargs)

    def _build_env(self, env: dict[str, str] | None = None) -> dict[str, str]:
        """Construct the environment for running commands in the virtualenv.

        Parameters
        ----------
        env
            The existing environment on which to base the new environment.
            If none is given, will use `os.environ` instead.

        Returns
        -------
        dict of str to str
            Environment to use when running commands in the virtualenv.
        """
        env = dict(env) if env else dict(os.environ)
        env["PATH"] = str(self._path / "bin") + ":" + os.environ["PATH"]
        env["VIRTUAL_ENV"] = str(self._path)
        return env
