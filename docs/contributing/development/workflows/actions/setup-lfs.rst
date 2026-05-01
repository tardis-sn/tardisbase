.. _workflow_setup_lfs:

**************
setup-lfs.yml
**************

Source: https://github.com/tardis-sn/tardis/blob/master/.github/actions/setup_lfs/action.yml

Composite action to **restore** atomic and TARDIS regression data. This action is only used for retrieval, not for storing — for storing, see the :doc:`lfs-cache <../reusable/lfs-cache>` reusable workflow.

Inputs:

- ``regression-data-repo`` — regression data repository name (default `tardis-sn/tardis-regression-data <https://github.com/tardis-sn/tardis-regression-data>`_).
- ``atom-data-sparse`` — if true, retrieve only the atom data instead of the full regression data suite.

What it does
============

1. Clone the `regression data repository <https://github.com/tardis-sn/tardis-regression-data>`_ (without LFS).
2. Build an `LFS <https://git-lfs.com/>`_ file list, used to derive the cache key. If the LFS regression data is updated the cache key is automatically invalidated, and `GitHub automatically removes stale caches <https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows#usage-limits-and-eviction-policy>`_.
3. Restore the cache, then run ``git lfs checkout``.

Cache Keys
==========

**Regression Data Cache Keys**

- Format: ``tardis-regression-<data-type>-<hash>-v1``
- Examples:

  - ``tardis-regression-atom-data-sparse-<hash>-v1`` — atomic data cache
  - ``tardis-regression-full-data-<hash>-v1`` — full TARDIS regression data cache

.. warning::
   The version suffix (``-v1``) allows for future cache invalidation if needed.

See also
========

- :doc:`lfs-cache <../reusable/lfs-cache>`
- :doc:`tests <../core/tests>`
- :doc:`compare-regdata <../core/compare-regdata>`
