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

* :doc:`actions/setup-env` — creates the conda environment from the lockfile and caches it for faster subsequent runs.
* :doc:`actions/setup-lfs` — restores the cached regression data / atom data LFS objects for use in a job.

Reusable Workflows
==================

Workflows that are not triggered directly but are called by other workflows.

* :doc:`reusable/lfs-cache` — checks whether regression data LFS objects are cached, and pulls + saves them if not.

Core Workflows
==============

End-to-end workflows triggered by pushes, pull requests, schedules, or manual
dispatch.

Testing
-------

* :doc:`core/tests` — runs the TARDIS test suite on Linux and macOS for every push / PR to ``master``.
* :doc:`core/full-tests` — runs the full test suite on a self-hosted runner (PR label-gated).
* :doc:`core/compare-regdata` — regenerates regression data on a PR and posts a comparison report.
* :doc:`core/stardis-tests` — pulls STARDIS and runs its tests against the current TARDIS commit.

Documentation
-------------

* :doc:`core/build-docs` — builds the Sphinx docs and deploys them to GitHub Pages.
* :doc:`core/clean-docs` — removes preview doc folders when PRs/branches are closed or deleted.
* :doc:`core/docstr-cov` — tracks docstring coverage and updates a shields.io badge.

Release
-------

* :doc:`core/pre-release` — weekly cron that prepares a release PR with updated Zenodo metadata.
* :doc:`core/release` — creates the GitHub Release, attaches lockfiles, and injects the DOI and changelog.
* :doc:`core/post-release` — updates ``CHANGELOG.md``, ``CITATION.cff``, and credits after a release.

Benchmarks
----------

* :doc:`core/benchmarks` — runs airspeed velocity benchmarks and publishes results to ``tardis-benchmarks``.

Code Quality
------------

* :doc:`core/codestyle` — runs ``ruff`` and posts a summary comment on PRs.
* :doc:`core/codespell` — runs ``codespell`` on the ``docs/`` tree.
* :doc:`core/mailmap` — ensures PR authors have an entry in ``.mailmap``.

Utility
-------

* :doc:`core/util` — PR housekeeping: LFS label warnings, GSoC label, first-time contributor welcome, ORCID check.
* :doc:`core/tardis-research-papers` — monthly cron that refreshes the list of papers using TARDIS.

Archived
--------

* :doc:`core/archived` — legacy workflows kept under ``.github/workflows/archive/`` for reference.


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
   core/archived
