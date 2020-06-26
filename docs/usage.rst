#####
Usage
#####

neophile is currently only a command-line tool.
It is not currently uploaded to PyPI.
Install it as documented in :ref:`dev-environment`.

neophile's processing is divided into four steps:

#. **scan**: Find all the declared dependencies in a directory.
#. **inventory**: Find the available versions of each dependency.
#. **analyze**: Compare the two and report on out-of-date dependencies.
#. **update**: Apply the changes found by analyze.

The primary command is ``neophile analyze``, which will analyze the current working directory for out-of-date dependencies and produce either a report (the default), update those dependencies (``--update``), or create a GitHub pull request (``--pr``).
Other commands are provided to run only one of the above steps.

Once installed, run ``neophile --help`` for a usage summary.

Configuration
=============

neophile requires a GitHub token, both for creating pull requests and for retrieving available version information from GitHub tags.
It should be provided to neophile by setting the following environment variables:

NEOPHILE_GITHUB_TOKEN
    The GitHub token.

NEOPHILE_GITHUB_USER
    The name of the user associated with the GitHub token.

neophile has currently been tested with a `personal access token`_.
It should also work with a GitHub App token, but that has not yet been tested.

.. _personal access token: https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token
