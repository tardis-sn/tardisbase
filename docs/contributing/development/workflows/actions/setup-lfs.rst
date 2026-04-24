.. _workflow_setup_lfs:

**************
setup-lfs.yml
**************

Source: https://github.com/tardis-sn/tardis/blob/master/.github/actions/setup_lfs/action.yml

If you need access to regression or atomic data, incorporate the `setup_lfs` action to ensure proper handling of large file storage.

The `setup-lfs` action is used to restore the cached objects. It fails if the cache is not available.

Cache Keys
==========

**Regression Data Cache Keys**

- Format: ``tardis-regression-<data-type>-<hash>-v1``
- Examples:

  - ``tardis-regression-atom-data-sparse-<hash>-v1`` - For atomic data cache
  - ``tardis-regression-full-data-<hash>-v1`` - For full TARDIS regression data cache
- Used in: ``setup_lfs`` action

.. warning::
   The version suffix (-v1) allows for future cache invalidation if needed.
