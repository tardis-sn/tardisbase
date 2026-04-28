.. _workflow_benchmarks:

**************
benchmarks.yml
**************

Source: https://github.com/tardis-sn/tardis/blob/master/.github/workflows/benchmarks.yml

Runs `airspeed velocity (asv) <https://asv.readthedocs.io/>`_ benchmarks and publishes results to the `tardis-benchmarks <https://github.com/tardis-sn/tardis-benchmarks>`_ repo (deploys go to its ``main`` branch, served as `GitHub Pages <https://pages.github.com/>`_).

Triggered on pushes to ``master``, on ``pull_request_target`` to ``master``, and on ``workflow_dispatch``. The ``build`` job runs on any non-draft PR; draft PRs are skipped. The ``benchmarks`` label is listed in the trigger ``types`` so applying it on a draft re-runs the workflow, but it is not a gate on non-draft PRs.

See also the developer-facing `Benchmarks <https://tardis-sn.github.io/tardis/contributing/development/benchmarks.html>`_ page for ``asv`` setup and writing new benchmarks.

Jobs
====

**test-cache** — calls the :doc:`lfs-cache <../reusable/lfs-cache>` reusable workflow against ``tardis-sn/tardis-regression-data``. ``allow_lfs_pull`` is true on ``master`` or when the PR also carries the ``git-lfs-pull`` label.

**build**

1. Checkout the repo (PR head SHA on ``pull_request_target``); on PRs also fetch ``master`` and capture the head commit message for the deploy log.
2. :doc:`setup-lfs <../actions/setup-lfs>` with ``atom-data-sparse: true``.
3. Set up a ``benchmark`` env with `mamba-org/setup-micromamba <https://github.com/mamba-org/setup-micromamba>`_ pinning ``asv=0.6.4``, ``mamba``, ``libmambapy<2.0``, ``conda-build``, ``conda=24.11.0``.
4. ``asv machine --yes`` to accept defaults.
5. Download the benchmark environment file from ``tardisbase`` (``env-benchmark-linux.yml``).
6. Run benchmarks:

   - **Push / dispatch** — collect the last 4 commits into ``tag_commits.txt`` and run ``asv run -a rounds=1 HASHFILE:tag_commits.txt``. Fail the job if ``asv-output.log`` contains ``failed``.
   - **PR** — write the PR head and ``master`` SHAs into ``commit_hashes.txt`` and run ``asv run -a rounds=1 HASHFILE:commit_hashes.txt``.

7. On push/dispatch only: ``asv publish``, drop ``.asv/env``, and deploy ``.asv/html`` to ``tardis-sn/tardis-benchmarks`` (root) using `peaceiris/actions-gh-pages <https://github.com/peaceiris/actions-gh-pages>`_.
8. On PRs:

   - ``asv compare origin/master HEAD --factor 1.1 --split --sort ratio`` (full and ``--only-changed`` variants), tee'd into log files.
   - ``asv publish``, drop ``.asv/env``.
   - Set ``DEST_DIR=pull/<pr>`` and deploy ``.asv/html`` to that subdirectory of ``tardis-benchmarks``.
   - Find any existing ``I ran benchmarks as you asked`` comment and replace it with the changed and full ``asv compare`` outputs, plus links to the artifacts and the deployed pages URL.

9. Upload ``.asv/results`` and the compare logs as the ``asv-benchmark-results-<runner>`` artifact.

See also
========

- :doc:`tests <tests>`
- :doc:`lfs-cache <../reusable/lfs-cache>`
- :doc:`setup-lfs <../actions/setup-lfs>`
