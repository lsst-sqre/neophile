########
neophile
########

neophile is a dependency scanner.
It looks through a repository for declared dependencies, attempts to determine if those dependencies are out of date, and generates a report.
It was written to fill gaps betwen GitHub dependabot and WhiteSource Renovate.
neophile can find outdated dependencies and optionally update them for Helm charts, references to Kustomize resources, pre-commit hooks, and frozen Python dependencies that use ``make update-deps``.

neophile only checks whether a dependency is out of date.
It doesn't attempt to determine whether the newer version has security fixes, is a major or minor change, is part of a different line of development, or other practical complexities.
Its results should always be examined by a human rather than applied blindly.

See `SQR-042 <https://sqr-042.lsst.io/>`__ for more details about the problem statement and the gap that neophile fills.

neophile is developed on `GitHub <https://github.com/lsst-sqre/neophile>`__.

User guide
==========

.. toctree::
   :maxdepth: 1

   usage
   config
   install
   changelog

Development guide
=================

.. toctree::
   :maxdepth: 1

   dev/development
   dev/release

API
===

.. toctree::
   :maxdepth: 2

   api

Indices
=======

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
