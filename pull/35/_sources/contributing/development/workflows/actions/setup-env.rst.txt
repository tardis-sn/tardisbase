.. _workflow_setup_env:

**************
setup-env.yml
**************

To configure your environment effectively, utilize the `setup_env` action. This will help establish the necessary variables and settings for your pipeline.

Cache Keys
==========

**Environment Cache Keys**

- Format: ``tardis-conda-env-<os-label>-<hash>-v1``
- Examples:

  - ``tardis-conda-env-linux-<hash>-v1`` - For Linux conda environment
  - ``tardis-conda-env-macos-<hash>-v1`` - For macOS conda environment
- Used in: ``setup_env`` action

.. warning::
   The version suffix (-v1) allows for future cache invalidation if needed.
