.. _carsus_workflow_bridge:

**********
bridge.yml
**********

Source: https://github.com/tardis-sn/carsus/blob/master/.github/workflows/bridge.yml

The ``tardis-carsus-bridge`` generates TARDIS regression data from atomic files produced by `carsus <https://github.com/tardis-sn/carsus>`_ and compares them against the atomic data saved in the `tardis-regression-data <https://github.com/tardis-sn/tardis-regression-data>`_ repository. When run on a pull request, the workflow posts a bot comment with a `GitHub Pages <https://pages.github.com/>`_ link to the exported notebook with the comparison details (example: `tardis-sn/carsus#477 (comment) <https://github.com/tardis-sn/carsus/pull/477#issuecomment-4313720006>`_).

The workflow can also be invoked via ``workflow_dispatch`` from the GitHub Actions tab to run on ``master``.

It is also called by the :doc:`save_atomic_files <save-atomic-files>` workflow as a prerequisite before saving atomic files.

Triggered on pull requests requires the ``run-tardis-carsus-bridge`` label to be applied to run.

Jobs
====

**carsus-build** — builds the atomic data file from carsus:

1. Checkout `carsus <https://github.com/tardis-sn/carsus>`_ (the PR head SHA on ``pull_request_target``, otherwise the default ref).
2. Restore (or download and cache) the `Chianti database <https://download.chiantidatabase.org>`_.
3. Checkout the `carsus-data-cmfgen <https://github.com/tardis-sn/carsus-data-cmfgen>`_ data repo and symlink ``atomic/`` into ``/tmp/atomic``.
4. Set up the ``carsus`` conda environment from ``conda-lock.yml`` using `setup-micromamba <https://github.com/mamba-org/setup-micromamba>`_.
5. ``pip install -e carsus/``.
6. Execute ``carsus/docs/tardis_atomdata_ref.ipynb`` via `nbconvert <https://github.com/jupyter/nbconvert>`_ to produce ``kurucz_cd23_cmfgen_H_Si.h5``.
7. Upload the generated atom data as an artifact.

**tardis-build** — regenerates TARDIS regression data using the new atom data and compares it against the saved regression data:

1. Set up `tardis <https://github.com/tardis-sn/tardis>`_.
2. Set up the environment with tardis, `tardisbase <https://github.com/tardis-sn/tardisbase>`_, and `GitPython <https://github.com/gitpython-developers/GitPython>`_.
3. Set up regression data from `tardis-regression-data <https://github.com/tardis-sn/tardis-regression-data>`_.
4. Download the ``atom-data`` artifact and replace the atom data file in the regression data.
5. Generate regression data and check whether it differs from the saved data.
6. If it differs, snapshot the regenerated data as a CI commit and run the comparison notebook from `tardisbase <https://github.com/tardis-sn/tardisbase/blob/master/tardisbase/testing/regression_comparison/compare_regression_data.ipynb>`_ between ``HEAD~1`` and ``HEAD``.
7. Upload the rendered comparison HTML as an artifact.
8. On ``workflow_dispatch``, fail the workflow if the comparison failed (so the manual run surfaces the diff).

**deploy-comparison** — runs on ``pull_request_target``:

1. Download the comparison notebook artifact.
2. Push it to the `reg-data-comp <https://github.com/tardis-sn/reg-data-comp>`_ repo at ``carsus/pull/<PR#>/`` using `actions-gh-pages <https://github.com/peaceiris/actions-gh-pages>`_.
3. Find or create a bot comment on the PR linking to the deployed ``compare_regression_data.html``.

.. note::

   ``tardis-build`` uses ``continue-on-error`` on the regression-data equality check so that ``deploy-comparison`` can still run when the data differs. The job's ``step-ref-check-trig`` output is consumed by the :doc:`save_atomic_files <save-atomic-files>` workflow to gate atom-data saving on a successful comparison.

See also
========

- :doc:`save_atomic_files <save-atomic-files>`
- :doc:`compare-regdata <../core/compare-regdata>`
