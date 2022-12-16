##########
Change log
##########

0.4.0 (unreleased)
==================

- `packaging.version` has dropped support for arbitrary legacy version numbers, so neophile also no longer supports them.

0.3.3 (2022-02-28)
==================

- Fix type of ``pullRequestId`` when enabling auto-merge.
- Drop support for Python 3.9.
- Update pinned dependencies.

0.3.2 (2021-11-08)
==================

- Fix enabling of auto-merge after creating a new PR.
- Update pinned dependencies.

0.3.1 (2021-11-01)
==================

- Warn of errors if auto-merge could not be enabled but do not fail.
- Update pinned dependencies.

0.3.0 (2021-10-25)
==================

- Attempt to set auto-merge on pull requests after they're created.
  Failure to do so is silently ignored.
- Support updating pull requests for the ``main`` branch instead of ``master`` if it is present.
- Catch ``BadRequest`` errors from a GitHub repository inventory request.
- Update pinned dependencies.

0.2.2 (2021-03-22)
==================

- Use the repository default branch to construct and query for PRs.
  This works properly with newer or converted GitHub repositories that use ``main`` instead of ``master`` as the default branch.
- Update pinned dependencies.

0.2.1 (2021-03-02)
==================

- Update pinned dependencies.

0.2.0 (2021-01-25)
==================

- Require Python 3.9.
- Add support for full GitHub URLs in Kustomize external references.
- Add libpq-dev to the Docker image so that dependency updates work properly with packages using psycopg2.
- Update pinned dependencies.

0.1.0 (2020-07-17)
==================

The initial release of neophile.
Supports ``analyze`` to run on a single repository and ``process`` to process multiple configured repositories.
This release supports frozen Python dependencies, pre-commit hooks, Helm charts, and Kustomize external references.
Only GitHub is supported for pre-commit hooks and Kustomize external references.
