.. _workflow_tests:

*********
tests.yml
*********

Source: https://github.com/tardis-sn/tardis/blob/master/.github/workflows/tests.yml

The `testing pipeline`_ (CI) comprises 4 concurrent jobs that execute tests both with and without the continuum marker across Ubuntu and macOS platforms (2 platforms × 2 test types).
The pipeline includes both preparatory setup (environment installation and regression data configuration) and subsequent uploading of coverage reports upon test completion.

.. _testing pipeline: https://github.com/tardis-sn/tardis/blob/master/.github/workflows/tests.yml

Jobs
====

**test-cache** — calls the :doc:`lfs-cache.yml <../reusable/lfs-cache>` reusable workflow to ensure the regression data LFS cache exists.

**tests** — matrix job over ``linux-64`` / ``osx-arm64``:

* free up disk space on the runner
* :doc:`setup-lfs <../actions/setup-lfs>` to restore the cached regression data
* :doc:`setup-env <../actions/setup-env>` to create the conda environment from the lockfile
* ``pip install -e ".[tardisbase]"`` (or install ``tardis`` from git if ``pip_git`` is true)
* ``pytest tardis`` against the regression data
* optionally regenerate regression data when triggered from ``master`` or a PR with the ``run-generation-tests`` label
* upload coverage artifact

**combine_coverage_reports** — runs after ``tests``:

* :doc:`setup-env <../actions/setup-env>`
* download all coverage artifacts
* ``coverage combine`` and ``coverage xml`` / ``coverage html``
* upload to Codecov

.. note::

   :doc:`pre-release.yml <pre-release>` also runs this workflow via ``workflow_call`` with ``pip_git: true``.
