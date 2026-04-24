.. _workflow_pre_release:

***************
pre-release.yml
***************

Source: https://github.com/tardis-sn/tardis/blob/master/.github/workflows/pre-release.yml

The pre-release action clones the ``tardis-sn/tardis_zenodo`` repository, runs the notebook to
generate a new ``.zenodo.json`` file, and pushes it to the root of the tardis repository.
This file is used to create a new version of TARDIS on Zenodo with all committers as authors.
A pull request is created and automatically merged if all required checks pass.

Zenodo job
==========

1. Checkout the ``tardis-sn/tardis_zenodo`` repository.
2. Wait for the Zenodo webhook to be available (3 min sleep).
3. Set up the Python environment stored in ``tardis-sn/tardis_zenodo``.
4. Store the secret key for the Zenodo API in an environment variable.
5. Run the notebook to generate a new ``.zenodo.json`` file. Re-run if there are
   errors and ignore any errors.
6. Upload the ``.zenodo.json`` as an artifact.

pip tests job
=============

Runs the TARDIS test suite after installing TARDIS using pip from master(using git) instead of editable install. This flags cases when a new modules was introduced recently without an ``__init__.py`` file or data files not included in ``[tool.setuptools.package-data]`` inside ``pyproject.toml``.

Pre-release pull request job
============================

Relies on Zenodo and pip test steps completing.

1. Checks out the TARDIS repository.
2. Downloads the artifacts from the previous steps.
3. Checks for ``.zenodo.json`` and uses it if it was generated.
4. Get the current date.
5. Create a bot pull request on the tardis-bot fork using a branch named ``pre-release-<date>`` with the new ``.zenodo.json`` file.
6. Wait for the PR to be created (1 min sleep).
7. Automatically approve the PR using tokens from the infrastructure and core coordinator members.
8. Enable auto-merge.
