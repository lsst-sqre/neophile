##################################
Using neophile from GitHub Actions
##################################

The standard way to use neophile is via GitHub Actions.
Most packages will use neophile in three GitHub Action workflows:

#. Non-blocking pull request test for whether Python dependencies are up-to-date.
#. Periodic workflow to create a pull request to update pre-commit dependencies.
#. Periodic workflow to update Python dependencies and then run tests to see if they still pass.

Each is discussed separately below.

Checking if Python dependencies are up-to-date
==============================================

Packages that use frozen Python dependencies can use neophile to check whether those dependencies are up-to-date on each pull request.

For packages using the `fastapi_safir_app template <https://github.com/lsst/templates/tree/main/project_templates/fastapi_safir_app>`__ (see `the Safir documentation <https://safir.lsst.io/user-guide/set-up-from-template.html>`__ for more details), this workflow job should be added to the list of jobs in the :file:`.github/workflows/ci.yaml` workflow:

.. code-block:: yaml
   :caption: ci.yaml (partial)

   dependencies:
     runs-on: ubuntu-latest
     timeout-minutes: 10

     steps:
       - uses: actions/checkout@v3

       - name: Set up Python
         uses: actions/setup-python@v4
         with:
           python-version: "3.11"

       - name: Install neophile
         run: pip install neophile

       - name: Run neophile
         run: neophile check python

The Python version should be set to the minimum supported Python version for that package.
This test will fail if the Python dependencies are not up-to-date.

Normally, this should be a non-blocking test (in other words, a passing test should not be required to merge), since there are situations where updating the dependencies is incorrect.
(If, for example, one is preparing a bug-fix-only point release.)
The person preparing the pull request will see the test failure and can decide whether to also update dependencies.

This job should only be used for Python applications with pinned dependencies, not for library packages that use floating dependencies.
It intentionally doesn't check if pre-commit hooks are up-to-date, since those will be automatically updated using the next workflow.

Updating pre-commit dependencies
================================

Any package that uses pre-commit may wish to add the following workflow file, conventionally at :file:`.github/workflows/dependencies.yaml`.

.. code-block:: yaml
   :caption: dependencies.yaml

   name: Dependency Update

   "on":
     schedule:
       - cron: "0 12 * * 1"
     workflow_dispatch: {}

   jobs:
     update:
       runs-on: ubuntu-latest
       timeout-minutes: 10

       steps:
         - uses: actions/checkout@v3

         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: "3.11"

         - name: Install neophile
           run: pip install neophile

         - name: Run neophile
           run: neophile update --pr pre-commit
           env:
             NEOPHILE_COMMIT_EMAIL: "24442459+sqrbot@users.noreply.github.com"
             NEOPHILE_GITHUB_APP_ID: ${{ secrets.NEOPHILE_APP_ID }}
             NEOPHILE_GITHUB_PRIVATE_KEY: ${{ secrets.NEOPHILE_PRIVATE_KEY }}

         - name: Report status
           if: always()
           uses: ravsamhq/notify-slack-action@v1
           with:
             status: ${{ job.status }}
             notify_when: "failure"
             notification_title: "Periodic dependency update for {repo} failed"
           env:
             SLACK_WEBHOOK_URL: ${{ secrets.SLACK_ALERT_WEBHOOK }}

This workflow will run at midnight UTC on Monday, and whenever requested by manually running the action, and create a PR to update pre-commit hook dependencies.
If the repository configuration allows, that PR will be set to automerge if tests pass.

The Python version should be set to whatever Python version is used to run lint tests for this package.

neophile configuration
----------------------

``NEOPHILE_GITHUB_APP_ID`` and ``NEOPHILE_GITHUB_PRIVATE_KEY`` must be set to the secrets containing the GitHub App credentials for neophile.
See :ref:`actions-setup` for more information.
Two more environment variables may be set to customize neophile's behavior:

``NEOPHILE_COMMIT_NAME`` (optional)
    The name portion of the author and committer for the Git commit updating the dependencies.
    If not set, defaults to ``neophile``.

``NEOPHILE_COMMIT_EMAIL`` (required)
    The email address to use for the author and committer of the Git commit updating these dependencies.
    The value shown in the example above is the GitHub email for the ``sqrbot`` user used by SQuaRE, and is an appropriate setting for SQuaRE-maintained packages.
    For non-SQuaRE packages, set it to some appropriate value for your organization.

.. _slack-alerts:

Slack alerts
------------

The final step of this action reports any failures to Slack.
This is optional and can be omitted, with the caveat that notifications for failed periodic GitHub Actions tend to be sent somewhat randomly to the committer of the last Git commit merged to the main branch, and therefore are easy to miss.

If you keep the Slack alerting step, set ``SLACK_WEBHOOK_URL`` to the secret containing the Slack webhook used to post messages.
See :ref:`actions-setup` for more information.

Testing with updated dependencies
=================================

When application Python dependencies are not regularly updated (between rounds of development, for example), it is still useful to periodically check if updated dependencies would break the application.
These problems can then be caught more quickly, when it's easy to understand what has changed and there are a smaller number of issues to fix.
Addressing upgrade issues regularly avoids having to do a massive round of upgrades as part of the next release, involving possibly confusing and interacting issues from multiple dependency changes.

The recommended approach for doing this is a weekly GitHub Actions workflow that uses neophile to update dependencies and then runs the test suite.

.. code-block:: yaml

   # This is a separate run of the Python test suite that doesn't cache
   # the tox environment and runs from a schedule.  The purpose is to test
   # compatibility with the latest versions of all modules neophile
   # depends on, since neophile (being a PyPI application) does not pin
   # its dependencies.

   name: Periodic CI

   "on":
     schedule:
       - cron: "0 12 * * 1"
     workflow_dispatch: {}

   jobs:
     test:
       runs-on: ubuntu-latest
       timeout-minutes: 10

       strategy:
         matrix:
           python:
             - "3.11"

       steps:
         - uses: actions/checkout@v3

         # Use the oldest supported version of Python to update dependencies,
         # not the matrixed Python version, since this accurately reflects
         # how dependencies should later be updated.
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: "3.11"

         - name: Install neophile
           run: pip install neophile

         - name: Run neophile
           run: neophile update

         - name: Run tox
           uses: lsst-sqre/run-tox@v1
           with:
             python-version: ${{ matrix.python }}
             tox-envs: "lint,typing,py"

         - name: Report status
           if: always()
           uses: ravsamhq/notify-slack-action@v1
           with:
             status: ${{ job.status }}
             notify_when: "failure"
             notification_title: "Periodic test for {repo} failed"
           env:
             SLACK_WEBHOOK_URL: ${{ secrets.SLACK_ALERT_WEBHOOK }}

This should use the oldest supported Python version to run neophile, but then run the normal package tests using a matrix of all supported Python versions.
Extend the list of tox environments as appropriate for the application.

The Slack status reporting step is optional.
See :ref:`slack-alerts` for more information about it.
