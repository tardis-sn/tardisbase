.. _carsus_workflow_save_atomic_files:

*********************
save_atomic_files.yml
*********************

Source: https://github.com/tardis-sn/carsus/blob/master/.github/workflows/save_atomic_files.yml

The ``save_atomic_files`` workflow generates the atom data file if the :doc:`bridge <bridge>` comparison passes, zips it together with the comparison notebook (if produced), and uploads the archive to Moria. Manually triggered via ``workflow_dispatch``.

Jobs
====

**create-artifacts** — calls the :doc:`bridge <bridge>` workflow.

**zip_artifacts** — zips ``kurucz_cd23_cmfgen_H_Si.h5`` (and the comparison notebook, if present) and SCPs the archive to Moria via `appleboy/scp-action@v1 <https://github.com/appleboy/scp-action>`_.

**bridge-ref-check** — fails the workflow if the bridge's regression data comparison reported a diff.

See also
========

- :doc:`bridge <bridge>`
