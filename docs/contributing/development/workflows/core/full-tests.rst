.. _workflow_full_tests:

**************
full-tests.yml
**************

Source: https://github.com/tardis-sn/tardis/blob/master/.github/workflows/full-tests.yml

Runs the TARDIS test suite on a self-hosted runner. Label-gated: both jobs require the ``full-tests`` label on the PR. The trigger list also includes pushes to ``master``, but a push event has no PR labels attached, so the label check is false and neither job runs on push.

Jobs
====

**test-cache** — calls the :doc:`lfs-cache <../reusable/lfs-cache>` reusable workflow against ``tardis-sn/tardis-regression-data``. ``allow_lfs_pull`` is true on ``master`` or when the PR also carries the ``git-lfs-pull`` label.

**run-tests** — runs on ``self-hosted`` with a 60-minute timeout:

1. Checkout the PR head SHA (or the push SHA on ``master``).
2. :doc:`setup-lfs <../actions/setup-lfs>` to restore regression data.
3. Set up the conda environment directly with `mamba-org/setup-micromamba <https://github.com/mamba-org/setup-micromamba>`_ from ``conda-linux-64.lock`` (no caching — this runs on a self-hosted runner).
4. Install `tardis <https://github.com/tardis-sn/tardis>`_ in editable mode with the ``[tardisbase]`` extra: ``pip install -e ".[tardisbase]"``.
5. ``pip install --no-deps`` `lineid_plot <https://github.com/phn/lineid_plot>`_.
6. Run ``pytest tardis`` with regression-data, coverage, and ``--cov-append`` flags.

.. note::

   Triggered by applying the ``full-tests`` label to a pull request.

See also
========

- :doc:`tests <tests>`
- :doc:`lfs-cache <../reusable/lfs-cache>`
- :doc:`setup-lfs <../actions/setup-lfs>`
