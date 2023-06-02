"""Version representation for inventories.

Notes
-----
This is a bit more complicated than it should have to be to work around
https://github.com/python/mypy/issues/5374.  The mixins avoid the conflict
between an abstract base class and a dataclass in mypy's understanding of the
Python type system.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass

from packaging import version
from semver.version import Version

__all__ = [
    "PackagingVersion",
    "ParsedVersion",
    "SemanticVersion",
]


@dataclass(frozen=True, order=True)
class ParsedVersion(metaclass=ABCMeta):
    """Abstract base class for versions.

    We use two separate version implementations, one based on
    `packaging.version.Version` and one based on `semver.VersionInfo`.  This
    class defines the common interface.
    """

    @classmethod
    @abstractmethod
    def from_str(cls, string: str) -> ParsedVersion:
        """Parse a string into a version.

        Parameters
        ----------
        string : `str`
            The version as a string.

        Returns
        -------
        version : `ParsedVersion`
            The parsed version.
        """

    @staticmethod
    @abstractmethod
    def is_valid(string: str) -> bool:
        """Return whether a version string is a valid version.

        Parameters
        ----------
        string : `str`
            The version as a string.

        Returns
        -------
        result : `bool`
            Whether it is valid.
        """

    @abstractmethod
    def __str__(self) -> str:
        """Return the original form of the version."""


@dataclass(frozen=True, order=True)
class PackagingVersion(ParsedVersion):
    """Represents a version string using `packaging.version.Version`."""

    parsed_version: version.Version
    """The canonicalized, parsed version, for sorting.

    Notes
    -----
    This field must be first because it's the field we want to sort on and
    dataclass ordering is done as if the dataclass were a tuple, via ordering
    on each element of the tuple in sequence.
    """

    version: str
    """The raw version string."""

    @classmethod
    def from_str(cls, string: str) -> PackagingVersion:
        """Parse a string into a `~packaging.version.Version`.

        Parameters
        ----------
        string : `str`
            The version as a string.

        Returns
        -------
        version : `PackagingVersion`
            The parsed version.
        """
        parsed_version = version.parse(string)
        return cls(parsed_version=parsed_version, version=string)

    @staticmethod
    def is_valid(string: str) -> bool:
        """Return whether a version is valid.

        Parameters
        ----------
        string : `str`
            The version as a string.

        Returns
        -------
        result : `True`
            All versions are valid for this implementation (some will parse to
            a legacy version).
        """
        try:
            version.parse(string)
            return True
        except version.InvalidVersion:
            return False

    def __str__(self) -> str:
        return self.version


@dataclass(frozen=True, order=True)
class SemanticVersion(ParsedVersion):
    """Represents a semantic version string."""

    parsed_version: Version
    """The parsed version of it, for sorting.

    Notes
    -----
    This field must be first because it's the field we want to sort on and
    dataclass ordering is done as if the dataclass were a tuple, via ordering
    on each element of the tuple in sequence.
    """

    version: str
    """The raw version string, which may start with a v."""

    @classmethod
    def from_str(cls, string: str) -> SemanticVersion:
        """Parse a string into a `semver.VersionInfo`.

        Parameters
        ----------
        string : `str`
            The version as a string.

        Returns
        -------
        version : `SemanticVersion`
            The parsed version.
        """
        version = string[1:] if string.startswith("v") else string
        return cls(version=string, parsed_version=Version.parse(version))

    @staticmethod
    def is_valid(string: str) -> bool:
        """Return whether a version is valid.

        Parameters
        ----------
        string : `str`
            The version as a string.

        Returns
        -------
        result : `bool`
            Whether the version is valid.
        """
        version = string[1:] if string.startswith("v") else string
        return Version.is_valid(version)

    def __str__(self) -> str:
        return self.version
