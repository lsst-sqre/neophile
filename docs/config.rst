###########################################
Using neophile with Dependabot and Renovate
###########################################

As documented in `SQR-042 <https://sqr-042.lsst.io>`__, none of Dependabot, WhiteSource Renovate, or neophile can handle all types of dependencies with the desired feature set.
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
   These are dependencies expressed in ``pyproject.toml`` or ``setup.cfg``, but not dependencies frozen with ``pip-compile``.

Use the integrated GitHub Dependabot service, not the pre-acquisition Dependabot Preview GitHub App.
See `GitHub's help on dependency updates <https://docs.github.com/en/github/administering-a-repository/keeping-your-dependencies-updated-automatically>`__ for documentation.

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

neophile
========

neophile is a locally-written service to fill gaps left by Dependabot and Renovate.
Use it for:

#. Python frozen dependencies
#. pre-commit hooks
#. Kustomize references

It also scans Helm chart references, but we prefer WhiteSource Renovate for those because the feature support is better.
neophile should be configured for all Python packages using pre-commit, but is particularly useful for Python applications using dependencies frozen with ``pip-compile``.

To enable neophile scanning of a repository, the GitHub ``sqrbot`` user must be added as a collaborator on the repository with ``Write`` permissions.
This will already be done automatically if ``sqrbot`` created the repository.
Otherwise, it must be done by a repository or organization admin.
Do this in the GitHub web interface by going to the repository, going to **Settings**, and then going to **Manage access**.
Then use **Invite teams or people** to add ``sqrbot`` with the ``Write`` role.

Then, enable neophile by editing `its configuration in Roundtable <https://github.com/lsst-sqre/roundtable/blob/master/deployments/neophile/values.yaml>`__.
Add the repository to the ``repositories`` key.
A sample entry looks like:

.. code-block:: yaml

   - owner: "lsst-sqre"
     repo: "neophile"

for the ``lsst-sqre/neophile`` repository.

This is the only configuration that is necessary (or supported).
neophile will create a pull request weekly with any updates that it has detected to be needed.

WhiteSource Renovate
====================

Renovate is the most flexible of the available options but requires a bit more configuration and setup work.
Use it for:

#. Helm chart repositories with Docker image references.
#. Argo CD deployment repositories with Helm chart references.
#. Packages that use ``docker-compose`` to stand up a test environment.

Renovate generates a lot of spam and pull requests if enabled for an entire organization, so we selectively enable it only for the repositories where we want to use it.
To enable it for a repository, go to the GitHub page for the organization that owns that repository (`lsst-sqre <https://github.com/lsst-sqre>`__, for example).
Then go to **Settings**, and then **Installed GitHub Apps**.
Select **Configure** for Renovate.
Scroll down to the bottom, and add the additional repository that you want it to scan.

Renovate will then perform an initial scan of that repository and generate a pull request containing a trivial ``renovate.json`` file.
Included in that PR will be a preview of the issues that Renovate would create PRs for.
Create a local branch based on the PR branch created by Renovate so that you can make some modifications to the configuration.

For Argo CD and Helm chart repositories, change the configuration to:

.. code-block:: json

   {
     "extends": [
       "config:base"
     ],
     "versioning": "docker"
   }

This fixes the version comparison algorithm to not strip qualifiers from the end of the Docker image version.

For repositories that construct a test environment using ``docker-compose``, change the configuration to:

.. code-block:: json

   {
     "enabledManagers": [
       "docker-compose",
       "kustomize"
     ],
     "extends": [
       "config:base"
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
It also enables scanning of Kustomize dependencies.
Delete this if the package does not include Kustomize resources.

Once you have updated the configuration, push the modified configuration to the same PR branch that Renovate used originally.
Renovate will then regenerate its preview of PRs that it will create.
When you're happy with the results, merge the PR, and Renovate will start scanning the repository.
