.. _workflow_setup_env:

**************
setup-env.yml
**************

Source: https://github.com/tardis-sn/tardis-actions/blob/main/setup-env/action.yml

Composite action to create and cache the conda environment using `mamba-org/setup-micromamba <https://github.com/mamba-org/setup-micromamba>`_. Used by the `tardis <https://github.com/tardis-sn/tardis>`_, `carsus <https://github.com/tardis-sn/carsus>`_ and `stardis <https://github.com/tardis-sn/stardis>`_ repos to set up environments.

Inputs:

- ``os-label`` — lock file suffix, e.g. ``linux-64``, ``osx-64`` (default ``linux-64``).
- ``lockfile-path`` — use a local lock file instead of downloading one.
- ``lock-file-url-prefix`` — override the lock file source (default `tardis-base/master <https://github.com/tardis-sn/tardis-base/tree/master>`_).
- ``environment-name`` — conda env name (default ``tardis``).
- ``cache-environment`` / ``cache-downloads`` — toggle caching.

What it does
============

1. Get the lock file from ``lockfile-path`` or download it from ``lock-file-url-prefix``.
2. Generate a cache key of the form ``tardis-conda-env-<os-label>-<hash>-v1``, e.g.:

   - ``tardis-conda-env-linux-<hash>-v1`` — Linux conda environment
   - ``tardis-conda-env-macos-<hash>-v1`` — macOS conda environment

3. Call `mamba-org/setup-micromamba <https://github.com/mamba-org/setup-micromamba>`_ to create (or restore) the environment, passing the remaining inputs through.

.. warning::
   The version suffix (``-v1``) allows for future cache invalidation if needed.
