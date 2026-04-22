.. _workflow_lfs_cache:

**************
lfs-cache.yml
**************

The `LFS-cache` workflow caches the regression data and atomic data and can be triggered either manually or when there is a push to the main branch of the regression data repository. This is mainly responsible for doing LFS pulls when necessary and caching objects while the `setup-lfs` action is used to restore the cached objects. Both fail if the cache is not available.

The `lfs-cache` workflow is used to cache the regression data and atomic data and to check if the cache is available.

.. warning::
   - The `lfs-cache` workflow will fail if the cache is not available and will not pull LFS data by default.
   - However, if the `allow_lfs_pull` label is added to the PR, the workflow will pull LFS data. Please note that this is to be used sparingly and only with caution.
