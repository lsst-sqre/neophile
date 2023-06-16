################
Running neophile
################

neophile is a command-line tool.
Although it is normally run via GitHub Actions (see :doc:`github-actions`), it can be installed and run directly on a repository working tree.

Installation
============

Install neophile from PyPI:

.. code-block:: shell

   pip install neophile

Once installed, run ``neophile --help`` for a usage summary.

Commands
========

neophile's processing is divided into five steps:

#. **scan**: Find all the declared dependencies in a directory.
#. **inventory**: Find the available versions of each dependency.
#. **analyze**: Compare the two and report on out-of-date dependencies.
#. **update**: Apply the changes found by analyze.
#. **pull request**: Create a GitHub pull request.

Normally at least the first three steps are run, but all of these steps can be run independently if you wish.

The most frequently used command outside of GitHub Actions is ``neophile update``, which will analyze the current working directory for out-of-date dependencies and update them if needed.
Those modifications will be left in the current working tree and won't be committed.
(Do not use the ``--pr`` flag to ``neophile update`` when running it this way.
That flag is intended for use by GitHub Actions.)

``neophile check`` checks whether dependencies are up-to-date and exits with a non-zero status if they are not.

Other commands are provided to run only one of the above steps.
See :doc:`cli` for a complete listing of available commands.
