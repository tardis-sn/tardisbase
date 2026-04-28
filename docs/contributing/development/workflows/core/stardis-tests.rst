.. _workflow_stardis_tests:

******************
stardis-tests.yml
******************

Source: https://github.com/tardis-sn/tardis/blob/master/.github/workflows/stardis-tests.yml

Runs the `STARDIS <https://github.com/tardis-sn/stardis>`_ test suite against the current TARDIS commit, so TARDIS changes that break STARDIS are caught early. Triggered on pushes and PRs to ``master`` and on ``workflow_dispatch``. Skipped on draft PRs.

Jobs
====

**build** — matrix over ``linux-64``:

1. Checkout the ``tardis-sn/stardis`` repo (not TARDIS).
2. Download the STARDIS conda lockfile from ``raw.githubusercontent.com/tardis-sn/stardis/main/conda-<label>.lock``.
3. Compute a cache key from the SHA-256 of the lockfile.
4. Set up the ``stardis`` conda environment with `mamba-org/setup-micromamba <https://github.com/mamba-org/setup-micromamba>`_, using the lockfile and the cache key for both env and downloads.
5. Install TARDIS at the triggering commit: ``pip install git+https://github.com/tardis-sn/tardis.git@${{ github.sha }}``.
6. Install STARDIS in editable mode with its ``test`` extra: ``pip install -e .[test]``.
7. Run ``pytest``.

See also
========

- :doc:`tests <tests>`
- :doc:`setup-env <../actions/setup-env>`
