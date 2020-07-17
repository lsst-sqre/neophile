"""Virtual environment handling."""

from __future__ import annotations

import os
import subprocess
from typing import TYPE_CHECKING
from venv import EnvBuilder

if TYPE_CHECKING:
    from pathlib import Path
    from subprocess import CompletedProcess
    from typing import Any, Dict, Optional, Sequence

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
        """Create the virtualenv if it does not already exist.

        Raises
        ------
        subprocess.CalledProcessError
            On failure to install the wheel package or if the command given
            sets the ``check`` argument.
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
        command : Sequence[`str`]
            The command to run.
        **kwargs: `typing.Any`
            The arguments, which except for the ``env`` parameter if any will
            be passed as-is to :py:func:`subprocess.run`.

        Returns
        -------
        result : `subprocess.CompletedProcess`
            The return value of :py:func:`subprocess.run`.

        Raises
        ------
        subprocess.CalledProcessError
            On failure to install the wheel package or if the command given
            sets the ``check`` argument.
        """
        self.create()

        env = self._build_env(kwargs.get("env"))
        kwargs["env"] = env
        return subprocess.run(command, **kwargs)

    def _build_env(
        self, env: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Construct the environment for running commands in the virtualenv.

        Parameters
        ----------
        env : Dict[`str`, `str`], optional
            The existing environment on which to base the new environment.
            If none is given, will use `os.environ` instead.

        Returns
        -------
        env : Dict[`str`, `str`]
            The environment to use when running commands in the virtualenv.
        """
        if env:
            env = dict(env)
        else:
            env = dict(os.environ)
        env["PATH"] = str(self._path / "bin") + ":" + os.environ["PATH"]
        env["VIRTUAL_ENV"] = str(self._path)
        return env
