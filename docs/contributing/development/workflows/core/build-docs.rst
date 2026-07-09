.. _workflow_build_docs:

**************
build-docs.yml
**************

Source: https://github.com/tardis-sn/tardis/blob/master/.github/workflows/build-docs.yml

Generates TARDIS documentation on ``master`` and pull requests, and deploys it to `GitHub Pages <https://pages.github.com/>`_ via the `gh-pages branch <https://github.com/tardis-sn/tardis/tree/gh-pages>`_.

Jobs
====

**tests-cache** — uses :doc:`lfs-cache <../reusable/lfs-cache>` to verify the regression data cache exists.

**check-for-changes** — the ``build-docs`` job only runs on pull requests if:

1. there are changes inside `/docs <https://github.com/tardis-sn/tardis/tree/master/docs>`_, or
2. the ``build-docs`` label is applied.

It always runs on ``master`` and on `workflow_dispatch <https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_dispatch>`_.

**build-docs**

1. Checkout code (PR or ``master``).
2. :doc:`setup-env <../actions/setup-env>`.
3. :doc:`setup-lfs <../actions/setup-lfs>` — atom data only.
4. Install `tardisbase <https://github.com/tardis-sn/tardisbase>`_ and pip packages.
5. Install `tardis <https://github.com/tardis-sn/tardis>`_ in editable mode.
6. Build the documentation with `Sphinx <https://www.sphinx-doc.org/>`_.
7. Set destination directory for ``gh-pages``: pushes to the ``/pull`` folder for pull requests, or updates the root for ``master``.
8. Clean branch on ``workflow_dispatch`` — this is a nuclear option that wipes the entire ``gh-pages`` branch and starts fresh. See :doc:`clean-docs <clean-docs>`.
9. Deploy to `GitHub Pages <https://pages.github.com/>`_.
10. Post a comment with success/failure of the job.

See also
========

- :doc:`clean-docs <clean-docs>`
- :doc:`docstr-cov <docstr-cov>`
- :doc:`setup-lfs <../actions/setup-lfs>`
- :doc:`setup-env <../actions/setup-env>`
- :doc:`lfs-cache <../reusable/lfs-cache>`
