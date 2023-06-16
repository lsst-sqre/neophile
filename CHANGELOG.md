# Change log

All notable changes to mobu will be documented in this file.

Versioning follows [semver](https://semver.org/).

Dependencies are updated to the latest available version during each release. Those changes are not noted here explicitly.

This project uses [scriv](https://scriv.readthedocs.io/en/latest/) to maintain the change log.
Changes for the upcoming release can be found in [changelog.d](https://github.com/lsst-sqre/neophile/tree/main/changelog.d/).

<!-- scriv-insert-here -->

<a id='changelog-1.0.0'></a>
## 1.0.0 (2023-06-16)

### Backwards-incompatible changes

- neophile is now intended to be run either via GitHub Actions or on a local checkout, and never as a Kubernetes service. The `neophile process` command, the configuration specific to that command (work area, lists of repositories), and support for running inside a virtualenv have been removed.
- When creating PRs, neophile now must be configured as a GitHub App with a suitable application ID and private key in environment variables.
- neophile no longer provides Docker images and instead is now a conventional Python package installable from PyPI.
- Support for Helm and Kustomize dependency checking and updating has been removed, along with the configuration options for Helm chart caching and version patterns in Helm charts. Mend Renovate and Dependabot support Helm and Kustomize dependency checking with more features, and we haven't used this support in several years.
- Add a new `neophile update` command that updates known dependencies in the provided tree and (if the `--pr` flag is given) creates a GitHub pull request. This replaces the `--update` and `--pr` flags to `neophile analyze`.
- When creating PRs, neophile no longer embeds the GitHub username and token in the remote URL. It instead uses the existing `origin` remote and assumes Git operations are already authenticated.
- Name and email address are now used only for Git commits, so the names of the environment variables to set them have changed accordingly to `NEOPHILE_COMMIT_NAME` and `NEOPHILE_COMMIT_EMAIL`.

### New features

- Add a new `neophile check` command that checks to see if all dependencies are up-to-date and exits with a non-zero status and messages to standard error if they are not. This is intended for use as a GitHub Actions check.
- The types of dependencies to analyze may now be specified as command-line arguments to `neophile analyze` (and the new `neophile check` and `neophile update` commands). The default continues to be to analyze all known dependencies.

### Bug fixes

- `neophile analyze` now prints nothing if no pending updates were found, and omits dependency types with no pending updates from its output.

### Other changes

- neophile now uses the [Ruff](https://beta.ruff.rs/docs/) linter instead of flake8 and isort.
- The neophile change log is now maintained using [scriv](https://scriv.readthedocs.io/en/latest/).
- neophile no longer creates a separate remote for pusing PRs and instead uses the `origin` remote directly.

## 0.4.0 (2023-05-03)

### Backwards-incompatible changes

- Drop support for Python 3.10.
- `packaging.version` has dropped support for arbitrary legacy version numbers, so neophile also no longer supports them.

## 0.3.3 (2022-02-28)

### Backwards-incompatible changes

- Drop support for Python 3.9.

### Bug fixes

- Fix type of ``pullRequestId`` when enabling auto-merge.

## 0.3.2 (2021-11-08)

### Bug fixes

- Fix enabling of auto-merge after creating a new PR.

## 0.3.1 (2021-11-01)

### Bug fixes

- Warn of errors if auto-merge could not be enabled but do not fail.

## 0.3.0 (2021-10-25)

### New features

- Attempt to set auto-merge on pull requests after they're created. Failure to do so is silently ignored.

### Bug fixes

- Catch `BadRequest` errors from a GitHub repository inventory request.
- Support updating pull requests for the `main` branch instead of `master` if it is present.

## 0.2.2 (2021-03-22)

### New features

- Use the repository default branch to construct and query for PRs. This works properly with newer or converted GitHub repositories that use `main` instead of `master` as the default branch.

## 0.2.1 (2021-03-02)

### Other changes

- Update pinned dependencies.

## 0.2.0 (2021-01-25)

### Backwards-incompatible changes

- Require Python 3.9.

### New features

- Add support for full GitHub URLs in Kustomize external references.
- Add libpq-dev to the Docker image so that dependency updates work properly with packages using psycopg2.

## 0.1.0 (2020-07-17)

The initial release of neophile. Supports ``analyze`` to run on a single repository and ``process`` to process multiple configured repositories. This release supports frozen Python dependencies, pre-commit hooks, Helm charts, and Kustomize external references. Only GitHub is supported for pre-commit hooks and Kustomize external references.
