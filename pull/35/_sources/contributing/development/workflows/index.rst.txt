.. _tardis_workflows:

**********************************
TARDIS GitHub Actions Workflows
**********************************

This section documents the GitHub Actions **actions**, **reusable workflows**,
and **core workflows** maintained in the
`TARDIS repository <https://github.com/tardis-sn/tardis>`_ under
``.github/workflows/``. It also references related actions that live in the
`tardis-actions repository <https://github.com/tardis-sn/tardis-actions>`_.

Actions
=======

Small, reusable building blocks used across the core workflows.

* :doc:`setup-env.yml <actions/setup-env>` (`source <https://github.com/tardis-sn/tardis/blob/master/.github/actions/setup_env/action.yml>`__) — creates the conda environment from the lockfile and caches it for faster subsequent runs.
* :doc:`setup-lfs.yml <actions/setup-lfs>` (`source <https://github.com/tardis-sn/tardis/blob/master/.github/actions/setup_lfs/action.yml>`__) — restores the cached regression data / atom data LFS objects for use in a job.

Reusable Workflows
==================

Workflows that are not triggered directly but are called by other workflows.

* :doc:`lfs-cache.yml <reusable/lfs-cache>` (`source <https://github.com/tardis-sn/tardis/blob/master/.github/workflows/lfs-cache.yml>`__) — checks whether regression data LFS objects are cached, and pulls + saves them if not.

Core Workflows
==============

End-to-end workflows triggered by pushes, pull requests, schedules, or manual
dispatch.

Testing
-------

* :doc:`tests.yml <core/tests>` (`source <https://github.com/tardis-sn/tardis/blob/master/.github/workflows/tests.yml>`__) — runs the TARDIS test suite on Linux and macOS for every push / PR to ``master``.
* :doc:`full-tests.yml <core/full-tests>` (`source <https://github.com/tardis-sn/tardis/blob/master/.github/workflows/full-tests.yml>`__) — runs the full test suite on a self-hosted runner (PR label-gated).
* :doc:`compare-regdata.yml <core/compare-regdata>` (`source <https://github.com/tardis-sn/tardis/blob/master/.github/workflows/compare-regdata.yml>`__) — regenerates regression data on a PR and posts a comparison report.
* :doc:`stardis-tests.yml <core/stardis-tests>` (`source <https://github.com/tardis-sn/tardis/blob/master/.github/workflows/stardis-tests.yml>`__) — pulls STARDIS and runs its tests against the current TARDIS commit.

Documentation
-------------

* :doc:`build-docs.yml <core/build-docs>` (`source <https://github.com/tardis-sn/tardis/blob/master/.github/workflows/build-docs.yml>`__) — builds the Sphinx docs and deploys them to GitHub Pages.
* :doc:`clean-docs.yml <core/clean-docs>` (`source <https://github.com/tardis-sn/tardis/blob/master/.github/workflows/clean-docs.yml>`__) — removes preview doc folders when PRs/branches are closed or deleted.
* :doc:`docstr-cov.yml <core/docstr-cov>` (`source <https://github.com/tardis-sn/tardis/blob/master/.github/workflows/docstr-cov.yml>`__) — tracks docstring coverage and updates a shields.io badge.

Release
-------

* :doc:`pre-release.yml <core/pre-release>` (`source <https://github.com/tardis-sn/tardis/blob/master/.github/workflows/pre-release.yml>`__) — weekly cron that prepares a release PR with updated Zenodo metadata.
* :doc:`release.yml <core/release>` (`source <https://github.com/tardis-sn/tardis/blob/master/.github/workflows/release.yml>`__) — creates the GitHub Release, attaches lockfiles, and injects the DOI and changelog.
* :doc:`post-release.yml <core/post-release>` (`source <https://github.com/tardis-sn/tardis/blob/master/.github/workflows/post-release.yml>`__) — updates ``CHANGELOG.md``, ``CITATION.cff``, and credits after a release.

Benchmarks
----------

* :doc:`benchmarks.yml <core/benchmarks>` (`source <https://github.com/tardis-sn/tardis/blob/master/.github/workflows/benchmarks.yml>`__) — runs airspeed velocity benchmarks and publishes results to ``tardis-benchmarks``.

Code Quality
------------

* :doc:`codestyle.yml <core/codestyle>` (`source <https://github.com/tardis-sn/tardis/blob/master/.github/workflows/codestyle.yml>`__) — runs ``ruff`` and posts a summary comment on PRs.
* :doc:`codespell.yml <core/codespell>` (`source <https://github.com/tardis-sn/tardis/blob/master/.github/workflows/codespell.yml>`__) — runs ``codespell`` on the ``docs/`` tree.
* :doc:`mailmap.yml <core/mailmap>` (`source <https://github.com/tardis-sn/tardis/blob/master/.github/workflows/mailmap.yml>`__) — ensures PR authors have an entry in ``.mailmap``.

Utility
-------

* :doc:`util.yml <core/util>` (`source <https://github.com/tardis-sn/tardis/blob/master/.github/workflows/util.yml>`__) — PR housekeeping: LFS label warnings, GSoC label, first-time contributor welcome, ORCID check.
* :doc:`tardis-research-papers.yml <core/tardis-research-papers>` (`source <https://github.com/tardis-sn/tardis/blob/master/.github/workflows/tardis-research-papers.yml>`__) — monthly cron that refreshes the list of papers using TARDIS.


.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: Actions

   actions/setup-env
   actions/setup-lfs

.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: Reusable Workflows

   reusable/lfs-cache

.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: Core Workflows

   core/tests
   core/full-tests
   core/compare-regdata
   core/stardis-tests
   core/build-docs
   core/clean-docs
   core/docstr-cov
   core/pre-release
   core/release
   core/post-release
   core/benchmarks
   core/codestyle
   core/codespell
   core/mailmap
   core/util
   core/tardis-research-papers
