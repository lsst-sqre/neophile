# neophile

neophile is a dependency scanner.
It looks through a repository for declared dependencies, attempts to determine if those dependencies are out of date, and generates a report.
It was written to fill gaps betwen [GitHub dependabot](https://docs.github.com/en/code-security/dependabot) and [Mend Renovate](https://www.mend.io/renovate/).
neophile can find outdated dependencies and optionally update them for Helm charts, references to Kustomize resources, pre-commit hooks, and frozen Python dependencies that use `make update-deps`.

For full documentation, see [the manual](https://neophile.lsst.io/).

See [SQR-042](https://sqr-042.lsst.io/) for more details about the problem statement and the gap that neophile fills.
