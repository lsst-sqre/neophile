########
neophile
########

|Build|

neophile is a dependency scanner.
It looks through a repository for declared dependencies, attempts to determine if those dependencies are out of date, and generates a report.
It was written to fill gaps betwen GitHub dependabot and WhiteSource Renovate.
neophile can find outdated dependencies and optionally update them for Helm charts, references to Kustomize resources, pre-commit hooks, and frozen Python dependencies that use ``make update-deps``.

For full documentation, see `neophile.lsst.io <https://neophile.lsst.io/>`__.

See `SQR-042 <https://sqr-042.lsst.io/>`__ for more details about the problem statement and the gap that neophile fills.

.. |Build| image:: https://github.com/lsst-sqre/neophile/workflows/CI/badge.svg
   :alt: GitHub Actions
   :scale: 100%
   :target: https://github.com/lsst-sqre/neophile/actions
