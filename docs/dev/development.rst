#################
Development guide
#################

This page provides procedures and guidelines for developing and contributing to neophile.

Scope of contributions
======================

neophile is an open source package, meaning that you can contribute to neophile itself, or fork neophile for your own purposes.

Since neophile is intended for internal use by Rubin Observatory, community contributions can only be accepted if they align with Rubin Observatory's aims.
For that reason, it's a good idea to propose changes with a new `GitHub issue`_ before investing time in making a pull request.

neophile is developed by the Rubin Observatory SQuaRE team.

.. _GitHub issue: https://github.com/lsst-sqre/neophile/issues/new

.. _dev-environment:

Setting up a local development environment
==========================================

To develop neophile, create a virtual environment with your method of choice (like virtualenvwrapper) and then clone or fork, and install:

.. code-block:: sh

   git clone https://github.com/lsst-sqre/neophile.git
   cd neophile
   make init

This init step does three things:

1. Installs neophile in an editable mode with its "dev" extra that includes test and documentation dependencies.
2. Installs pre-commit and tox.
3. Installs the pre-commit hooks.

.. _pre-commit-hooks:

Pre-commit hooks
================

The pre-commit hooks, which are automatically installed by running the :command:`make init` command on :ref:`set up <dev-environment>`, ensure that files are valid and properly formatted.
Some pre-commit hooks automatically reformat code:

``ruff``
    Lint Python code and attempt to automatically fix some problems.

``black``
    Automatically formats Python code.

``blacken-docs``
    Automatically formats Python code in reStructuredText documentation and docstrings.

When these hooks fail, your Git commit will be aborted.
To proceed, stage the new modifications and proceed with your Git commit.

.. _dev-run-tests:

Running tests
=============

To test nephile, run tox_, which tests it the same way that the CI workflow does:

.. code-block:: sh

   tox run

To run the tests with coverage analysis and generate a report, run:

.. code-block:: sh

   tox run -e py,coverage-report

To see a listing of test environments, run:

.. code-block:: sh

   tox list

To run a specific test or list of tests, you can add test file names (and any other pytest_ options) after ``--`` when executing the ``py`` tox environment.
For example:

.. code-block:: sh

   tox run -e py -- tests/handlers/api_tokens_test.py

.. _dev-build-docs:

Building documentation
======================

Documentation is built with Sphinx_:

.. _Sphinx: https://www.sphinx-doc.org/en/master/

.. code-block:: sh

   tox run -e docs

The build documentation is located in the :file:`docs/_build/html` directory.

To check the documentation for broken links, run:

.. code-block:: sh

   tox run -e docs-linkcheck

.. _dev-change-log:

Updating the change log
=======================

neophile uses scriv_ to maintain its change log.

When preparing a pull request, run :command:`scriv create`.
This will create a change log fragment in :file:`changelog.d`.
Edit that fragment, removing the sections that do not apply and adding entries fo this pull request.
You can pass the ``--edit`` flag to :command:`scriv create` to open the created fragment automatically in an editor.

Change log entries use the following sections:

- **Backward-incompatible changes**
- **New features**
- **Bug fixes**
- **Other changes** (for minor, patch-level changes that are not bug fixes, such as logging formatting changes or updates to the documentation)

These entries will eventually be cut and pasted into the release description for the next release, so the Markdown for the change descriptions must be compatible with GitHub's Markdown conventions for the release description.
Specifically:

- Each bullet point should be entirely on one line, even if it contains multiple sentences.
  This is an exception to the normal documentation convention of a newline after each sentence.
  Unfortunately, GitHub interprets those newlines as hard line breaks, so they would result in an ugly release description.
- Avoid using too much complex markup, such as nested bullet lists, since the formatting in the GitHub release description may not be what you expect and manually editing it is tedious.

.. _style-guide:

Style guide
===========

Code
----

- neophile mostly follows the :sqr:`072` Python style guide, although the code layout does not match that document.

- The code style follows :pep:`8`, though in practice lean on Black and isort to format the code for you.

- Use :pep:`484` type annotations.
  The ``tox run -e typing`` test environment, which runs mypy_, ensures that the project's types are consistent.

- neophile uses the Ruff_ linter with most checks enabled.
  Try to avoid ``noqa`` markers except for issues that need to be fixed in the future.
  Tests that generate false positives should normally be disabled, but if the lint error can be avoided with minor rewriting that doesn't make the code harder to read, prefer the rewriting.

- Write tests for Pytest_.

Documentation
-------------

- Follow the `LSST DM User Documentation Style Guide`_, which is primarily based on the `Google Developer Style Guide`_.

- Document the Python API with numpydoc-formatted docstrings.
  See the `LSST DM Docstring Style Guide`_.

- Follow the `LSST DM ReStructuredTextStyle Guide`_.
  In particular, ensure that prose is written **one-sentence-per-line** for better Git diffs.

.. _`LSST DM User Documentation Style Guide`: https://developer.lsst.io/user-docs/index.html
.. _`Google Developer Style Guide`: https://developers.google.com/style/
.. _`LSST DM Docstring Style Guide`: https://developer.lsst.io/python/style.html
.. _`LSST DM ReStructuredTextStyle Guide`: https://developer.lsst.io/restructuredtext/style.html
