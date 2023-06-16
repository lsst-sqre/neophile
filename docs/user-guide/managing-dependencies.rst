.. _managing-dependencies:

#####################
Managing dependencies
#####################

As documented in :sqr:`042`, none of Dependabot, Mend Renovate, or neophile can handle all types of dependencies with the desired feature set.
All three should therefore be used in different situations.
Below is documentation for when to use each service and how to configure it.

.. note::

   These instructions are specific to SQuaRE services for Vera C. Rubin Observatory.
   They may be helpful to other projects, but they should not be taken as general guidance and will require modifications in other contexts.

Dependabot
==========

Dependabot is preferred for those dependencies that it supports well.
Use it for:

#. GitHub Actions
#. Docker base images
#. Python library (not application) dependencies.
   These are dependencies expressed in ``pyproject.toml``, but not dependencies frozen with ``pip-compile``.

See `GitHub's help on dependency updates <https://docs.github.com/en/code-security/dependabot/dependabot-version-updates>`__ for documentation.

Configuration should be stored in ``.github/dependabot.yml``.
Here is the configuration to use for GitHub Actions (which nearly every project will have):

.. code-block:: yaml

   version: 2
   updates:
     - package-ecosystem: "github-actions"
       directory: "/"
       schedule:
         interval: "weekly"

For repositories that build a Docker image, add the following to the ``updates`` key:

.. code-block:: yaml

   - package-ecosystem: "docker"
     directory: "/"
     schedule:
       interval: "weekly"

For Python library packages, add the following to the ``updates`` key:

.. code-block:: yaml

   - package-ecosystem: "pip"
     directory: "/"
     schedule:
       interval: "weekly"

No further repository configuration is required.

Mend Renovate
=============

Renovate is the most flexible of the available options but requires a bit more configuration and setup work.
Use it for:

#. Helm chart repositories with Docker image references.
#. Argo CD deployment repositories with Helm chart references.
#. Packages that use ``docker-compose`` to stand up a test environment.
   (Although consider using the ``latest`` tag of any test dependencies if you don't expect their behavior to change significantly, such as Redis and PostgreSQL images used only for testing.)

Renovate is capable of doing all of the updates that Dependabot can do, but since Dependabot is a first-party GitHub application that is almost certain not to go away, we prefer to use it when it does a good enough job.

Renovate generates a lot of spam and pull requests if enabled for an entire organization, so we selectively enable it only for the repositories where we want to use it.
To enable it for a repository, go to the GitHub page for the organization that owns that repository (`lsst-sqre <https://github.com/lsst-sqre>`__, for example).
Then go to :guilabel:`Settings`, and then :guilabel:`Installed GitHub Apps`.
Select :guilabel:`Configure` for Renovate.
Scroll down to the bottom, and add the additional repository that you want it to scan.

Renovate will then perform an initial scan of that repository and generate a pull request containing a trivial ``renovate.json`` file.
Included in that PR will be a preview of the issues that Renovate would create PRs for.
Create a local branch based on the PR branch created by Renovate so that you can make some modifications to the configuration.

For Argo CD repositories, change the configuration to:

.. code-block:: json
   :caption: renovate.json

   {
     "extends": [
       "config:base"
     ],
     "configMigration": true,
     "schedule": [
       "before 6am on Monday"
     ],
     "timezone": "America/Los_Angeles"
   }

This runs Renovate weekly so that its PRs will be ready for merging on Monday mornings, and lets it create up to five PRs at a time.

If the Argo CD repository uses the commit queue, also add ``"rebaseWhen": "conflicted"`` to tell Renovate to not rebase branches on every commit.
The commit queue will rebase and retest the PR, so those extra rebases add to testing load and notification noise without accomplishing anything that useful.

For Helm chart repositories, instead use:

.. code-block:: json
   :caption: renovate.json
   :emphasize-lines: 5

   {
     "extends": [
       "config:base"
     ],
     "bumpVersion": "patch",
     "configMigration": true,
     "schedule": [
       "before 6am on Monday"
     ],
     "timezone": "America/Los_Angeles"
   }

This tells Renovate to increase the version of the Helm chart each time it changes the versions of its dependencies, which is necessary for published Helm charts.
(For Argo CD repositories, we don't maintain versioning for Helm charts and leave the version at ``1.0.0``.)

For repositories that construct a test environment using ``docker-compose`` and use pinned versions for those dependencies, change the configuration to:

.. code-block:: json

   {
     "enabledManagers": [
       "docker-compose"
     ],
     "extends": [
       "config:base",
       "schedule:weekly"
     ],
     "packageRules": [
       {
         "groupName": "test dependencies",
         "paths": [
           "docker-compose.yaml"
         ]
       }
     ]
   }

This groups updates to the ``docker-compose`` configuration into a single pull request.

Once you have updated the configuration, push the modified configuration to the same PR branch that Renovate used originally.
Renovate will then regenerate its preview of PRs that it will create.
When you're happy with the results, merge the PR, and Renovate will start scanning the repository.

neophile
========

neophile is a locally-written service to fill gaps left by Dependabot and Renovate.
Use it for:

#. Python frozen dependencies
#. pre-commit hooks

Any Python package using pre-commit should use neophile, but is particularly useful for Python applications using dependencies frozen with ``pip-compile``.

To enable neophile for a repository, see :doc:`github-actions`.
