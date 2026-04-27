.. _workflow_compare_regdata:

*******************
compare-regdata.yml
*******************

Source: https://github.com/tardis-sn/tardis/blob/master/.github/workflows/compare-regdata.yml

Compares the regression data generated from the pull request code against the regression data saved in the `regression data repository <https://github.com/tardis-sn/tardis-regression-data>`_. Comparison notebooks are committed to the `reg-data-comp repo <https://github.com/tardis-sn/reg-data-comp>`_ for easier lookup. The notebooks, along with comparison image plots, are linked from a bot comment on the PR.

Requires the ``run-regression-comparison`` label to be applied to run.

Example comment: https://github.com/tardis-sn/tardis/pull/3548#issuecomment-4223586937

Jobs
====

**tests-cache** — uses :doc:`lfs-cache <../reusable/lfs-cache>` to verify the regression data cache exists.

**tests** — matrix job over Ubuntu and macOS, for both continuum and non-continuum tests (currently set to non-continuum only):

1. Free up disk space (same as :doc:`tests <tests>`).
2. Checkout the pull request code.
3. Checkout the `tardisbase <https://github.com/tardis-sn/tardisbase>`_ repo.
4. :doc:`setup-lfs <../actions/setup-lfs>` to set up regression data.
5. Install `tardis <https://github.com/tardis-sn/tardis>`_ and `tardisbase <https://github.com/tardis-sn/tardisbase>`_ in editable mode.
6. ``pip install`` `gitpython <https://github.com/gitpython-developers/GitPython>`_ `lineid_plot <https://github.com/phn/lineid_plot>`_.
7. Commit the regenerated regression data — required because the regression data comparison defaults to comparing the last two commits.
8. Install comparison notebook requirements (`kaleido <https://github.com/plotly/Kaleido>`_ to save plots) — only required here to save plots for the bot comment.
9. Run and export the comparison notebook.

**deploy-comparison** — downloads the artifacts, pushes them to the `reg-data-comp <https://github.com/tardis-sn/reg-data-comp>`_ repo, deploys to `GitHub Pages <https://pages.github.com/>`_, and writes the bot comment.

.. note::

   The workflow exports images from the comparison notebook and embeds them in the bot comment. Unless there are key changes to any of the HDF files in the regression data, the bot shows two images — one for the spectrum change and one for relative changes in the keys. If there are key changes, a third image visualizing them is included.

See also
========

- :doc:`tests <tests>`
- :doc:`lfs-cache <../reusable/lfs-cache>`
- :doc:`setup-lfs <../actions/setup-lfs>`
- :doc:`setup-env <../actions/setup-env>`
