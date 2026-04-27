.. _workflow_lfs_cache:

**************
lfs-cache.yml
**************

Source: https://github.com/tardis-sn/tardis/blob/master/.github/workflows/lfs-cache.yml

Reusable workflow responsible for **caching** the regression data. For the action that retrieves regression data see :doc:`setup-lfs <../actions/setup-lfs>`.

Works with both atom data and the complete regression data suite.

Inputs
======

This workflow can be called both via `workflow_call <https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_call>`_ and `workflow_dispatch <https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_dispatch>`_. See the `source file <https://github.com/tardis-sn/tardis/blob/master/.github/workflows/lfs-cache.yml>`_ for the full list of inputs.

.. note::

   The ``allow-lfs-pull`` input controls whether the workflow performs a ``git lfs pull`` and caches the regression data. When ``allow-lfs-pull`` is ``false`` the workflow only checks whether the cache is present and up to date — this mode is used by :doc:`tests <../core/tests>` to fail fast before tests actually run.

What it does
============

1. Checkout the `regression data repo <https://github.com/tardis-sn/tardis-regression-data>`_ without `LFS <https://git-lfs.com/>`_.
2. Build an LFS file list, used to derive the cache key.
3. Validate the cache key with `actions/cache/restore <https://github.com/actions/cache/tree/main/restore>`_ in lookup-only mode.
4. Branch on ``allow-lfs-pull``:

   - ``false`` — fail if the cache is missing.
   - ``true`` — run ``git lfs pull`` and save the LFS cache.

See also
========

- :doc:`tests <../core/tests>`
- :doc:`compare-regdata <../core/compare-regdata>`
- :doc:`setup-lfs <../actions/setup-lfs>`
