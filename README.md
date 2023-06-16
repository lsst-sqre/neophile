# neophile

neophile is a dependency scanner.
It looks through a repository for declared dependencies, attempts to determine if those dependencies are out of date, and optionally updates them, either directly in the working tree or by creating a GitHub pull request.

neophile was written to fill gaps betwen [GitHub Dependabot](https://docs.github.com/en/code-security/dependabot) and [Mend Renovate](https://www.mend.io/renovate/).
It currently supports updating pre-commit hooks and frozen Python dependencies that use `make update-deps`.

For full documentation, see [the manual](https://neophile.lsst.io/).

See [SQR-042](https://sqr-042.lsst.io/) for more details about the problem statement and the gap that neophile fills.
