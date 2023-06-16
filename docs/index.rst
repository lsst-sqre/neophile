########
neophile
########

neophile is a dependency scanner.
It looks through a repository for declared dependencies, attempts to determine if those dependencies are out of date, and optionally updates them, either directly in the working tree or by creating a GitHub pull request.
neophile was written to fill gaps betwen GitHub Dependabot and Mend Renovate.

neophile currently supports pre-commit hooks and frozen Python dependencies that use ``make update-deps``.
It is normally run via GitHub Actions.

neophile only checks whether a dependency is out of date.
It doesn't attempt to determine whether the newer version has security fixes, is a major or minor change, is part of a different line of development, or other practical complexities.
Its results should always be confirmed by a test suite or examined by a human, rather than applied blindly.

neophile is intended for use in conjunction with Dependabot and Mend Renovate to cover all types of dependencies.
See :sqr:`042` for more details about the problem statement and the gap that neophile fills, and see :ref:`managing-dependencies` for configuration recommendations.

neophile is developed on `GitHub <https://github.com/lsst-sqre/neophile>`__.

.. warning::

   neophile is a highly opinionated implementation of dependency updates that is primarily intended for use by the SQuaRE team inside Rubin Observatory.
   It will work for others, but only if you follow the same conventions as SQuaRE.
   See :ref:`package-layout` for more information.

.. toctree::
   :maxdepth: 2

   user-guide/index

.. toctree::
   :hidden:

   changelog

.. toctree::
   :maxdepth: 2

   dev/index
