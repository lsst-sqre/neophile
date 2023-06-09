#####
Usage
#####

neophile can be used as a command-line tool or as a Kubernetes ``CronJob``.
It is not currently uploaded to PyPI.
Install it as documented in :ref:`dev-environment`.

Once installed, run ``neophile --help`` for a usage summary.

neophile's processing is divided into five steps:

#. **scan**: Find all the declared dependencies in a directory.
#. **inventory**: Find the available versions of each dependency.
#. **analyze**: Compare the two and report on out-of-date dependencies.
#. **update**: Apply the changes found by analyze.
#. **pull request**: Create a GitHub pull request.

The primary command for command-line use is ``neophile analyze``, which will analyze the current working directory for out-of-date dependencies and produce either a report (the default), update those dependencies (``--update``), or create a GitHub pull request (``--pr``).
Other commands are provided to run only one of the above steps.

The primary command when run as a cron job is ``neophile process``.
This checks out each configured repository, looks for available updates, and creates one pull request per repository that has pending updates.
It is normally used with a configuration file, specified with the ``--config-path`` option.
See :ref:`configuration` for details about the contents of that file and how to specify its path.

.. _configuration:

Configuration
=============

neophile can be configured through a YAML file, environment variables, or both.

Configuration files
-------------------

By default, neophile will look for a configuration file in ``$XDG_CONFIG_HOME/neophile.yaml`` (which normally expands to ``~/.config/neophile.yaml``) and load it if it is present.
To use a different configuration file path, pass the ``--config-path`` option to neophile before the subcommand.
For example:

.. code-block:: sh

   neophile --config-path /path/to/config.yaml process

Alternately, set the environment variable ``NEOPHILE_CONFIG`` to the path to the configuration file.

.. _settings:

Settings
--------

All configuration settings except ``repositories`` may be set via environment variables or via the YAML configuration file.
To set a boolean configuration setting via the environment, set the environment variable to ``0`` (false) or ``1`` (true).
However, the ``repositories`` setting is best set via a configuration file.
Here are all of the configuration settings and the corresponding environment variable.
At least ``github_user`` and ``github_token`` must be set.

``github_email`` (env: ``NEOPHILE_GITHUB_EMAIL``)
    The email address to use for commits when pushing to GitHub.
    If not set, the default is the public email address of the configured GitHub user.

``github_token`` (env: ``NEOPHILE_GITHUB_TOKEN``)
    A GitHub token.
    This must at least have ``public_repo`` access scope.
    neophile has only been tested with a `personal access token`_.
    It should also work with a GitHub App token, but that has not yet been tested.

``github_user`` (env: ``NEOPHILE_GITHUB_USER``)
    The GitHub user to use for pull requests and for other queries, such as looking up the tags on a repository.
    Must be the user corresponding to the token set in ``github_token``.

``repositories``
    The list of GitHub repositories to process with ``neophile process``.
    Each member of the list is a dict with the following keys:

    ``owner``
        The owner of the GitHub repository.

    ``repo``
        The name of the GitHub repository.

``work_area``
    A directory in which ``neophile process`` should do its work.
    Clones of the repositories being checked will be kept here.
    If this storage is persistent, neophile will take advantage of existing clones and update them to the latest upstream ``main`` branch, avoiding re-downloading the rest of the repository.
    Defaults to the current directory.

.. _personal access token: https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token

Example configuration file
--------------------------

Here is an example configuration file suitable for use inside a Docker container with a writable ``/data`` file system.

.. code-block:: yaml

   github_user: some-github-user
   github_token: some-github-token
   repositories:
     - owner: example
       repo: foo
     - owner: example
       repo: bar
     - owner: other-example
       repo: charts
   work_area: /data
