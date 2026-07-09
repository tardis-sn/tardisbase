.. _workflow_tests:

*********
tests.yml
*********

Source: https://github.com/tardis-sn/tardis/blob/master/.github/workflows/tests.yml

The TARDIS testing pipeline. Comprises concurrent jobs that execute tests both with and without the continuum marker (currently set to non-continuum tests only) across Ubuntu and macOS platforms (2 platforms × 2 test types). The pipeline includes preparatory setup (environment installation and regression data configuration) and subsequent uploading of coverage reports upon test completion.

Jobs
====

**tests-cache** — calls the :doc:`lfs-cache <../reusable/lfs-cache>` reusable workflow to verify the regression data cache exists and is up to date; fails the workflow otherwise.

**tests** — matrix job over ``linux-64`` / ``osx-arm64``:

1. Checkout `TARDIS <https://github.com/tardis-sn/tardis>`_.
2. Free up disk space — `jlumbroso/free-disk-space <https://github.com/jlumbroso/free-disk-space>`_ on Ubuntu, manual cleanup on macOS.
3. :doc:`setup-lfs <../actions/setup-lfs>` to restore regression data.
4. Install TARDIS — either from git via `pip <https://pip.pypa.io/>`_, or in editable mode. The pip-from-git path is used to test that ``pyproject.toml`` lists all data files and that no modules are missing ``__init__`` files.
5. :doc:`setup-env <../actions/setup-env>` to create the conda environment from the TARDIS lock file (via ``lockfile-path``).
6. Install `tardisbase <https://github.com/tardis-sn/tardisbase>`_.
7. ``pip install`` `lineid_plot <https://github.com/phn/lineid_plot>`_ — only dependency installed via pip.
8. Run tests.
9. Run regression-generation tests when the corresponding label is present.
10. Upload coverage files.

**coverage-combine** — combines `coverage <https://coverage.readthedocs.io/>`_ reports from the matrix jobs. Originally written to combine continuum and non-continuum reports.

See also
========

- :doc:`pre-release <pre-release>`
- :doc:`lfs-cache <../reusable/lfs-cache>`
- :doc:`setup-lfs <../actions/setup-lfs>`
- :doc:`setup-env <../actions/setup-env>`
