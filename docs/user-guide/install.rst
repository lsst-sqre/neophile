#######################
Kubernetes installation
#######################

neophile can be used as a command-line tool, but it is possibly most useful running as a cron job to monitor a set of repositories.
This guide documents how to use its official Helm chart to install neophile as a Kubernetes ``CronJob``.

Prerequisites
=============

The neophile Helm chart requires using Vault_ to store secrets and `Vault Secrets Operator`_ to materialize those secrets as Kubernetes secrets.

.. _Vault: https://vaultproject.io/
.. _Vault Secrets Operator: https://github.com/ricoberger/vault-secrets-operator

As documented in :ref:`settings`, neophile requires a GitHub token.
This should be stored in Vault as the value of the ``github_token`` key of a secret.
The path to that secret in Vault will be needed when configuring the Helm chart.

Helm deployment
===============

The is Helm chart for neophile is available from the `Rubin Observatory charts repository <https://lsst-sqre.github.io/charts/>`__.
To use that chart, you will need to set the following parameters (either on the Helm command line or in a ``values.yaml`` file):

``neophile.config.githubEmail``
    The email address to use for commit messages.
    If not set, the public email address of the configured GitHub user will be used.

``neophile.config.githubUser``
    The user corresponding to the GitHub token in the secret.

``neophile.config.repositories``
    A list of repositories.
    This has the same format as the corresponding setting.
    See :ref:`settings` for more information.

``neophile.image`` (optional)
    Controls the Docker image to use via the following keys.
    The default is the current release of neophile from its official repository.

    ``repository`` (optional)
        The Docker Hub repository.

    ``tag`` (optional)
        The tag of the image.

    ``pullPolicy`` (optional)
        The Kubernetes pull policy.
        Defaults to ``IfNotPresent``.

``neophile.persistence.volumeClaim`` (optional)
    The name of a ``PersistentVolumeClaim`` to use as the working directory.
    This makes neophile more efficient by allowing it to update existing checkouts of repositories rather than redownload each monitored repository on each run.
    If not set, neophile will use ``emptyDir``, which will not preserve the working directory between runs.

``neophile.schedule`` (optional)
    The schedule on which to run neophile as a cron expression.
    Defaults to ``0 4 * * 1`` (4am each Monday).

``neophile.vaultSecretsPath``
    The path in Vault to the secret containing the GitHub token.
