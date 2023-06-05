# Change log

All notable changes to mobu will be documented in this file.

Versioning follows [semver](https://semver.org/).

Dependencies are updated to the latest available version during each release. Those changes are not noted here explicitly.

This project uses [scriv](https://scriv.readthedocs.io/) to maintain the change log.
Changes for the upcoming release can be found in [changelog.d](https://github.com/lsst-sqre/mobu/tree/main/changelog.d/).

<!-- scriv-insert-here -->

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
