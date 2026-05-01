.. _workflow_codespell:

*************
codespell.yml
*************

Source: https://github.com/tardis-sn/tardis/blob/master/.github/workflows/codespell.yml

Runs `codespell <https://github.com/codespell-project/codespell>`_ over the `docs/ <https://github.com/tardis-sn/tardis/tree/master/docs>`_ tree to catch common spelling mistakes in the documentation. Triggered on pushes to ``master``, on pull requests targeting ``master``, and via `workflow_dispatch <https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_dispatch>`_.

Jobs
====

**codespell**

1. Checkout the repository (PR head SHA on ``pull_request_target``, otherwise the default ref).
2. :doc:`setup-env <../actions/setup-env>` with ``os-label: linux-64`` and the in-repo ``conda-linux-64.lock`` lockfile.
3. Run ``codespell docs/``.

See also
========

- :doc:`codestyle <codestyle>`
- :doc:`setup-env <../actions/setup-env>`
