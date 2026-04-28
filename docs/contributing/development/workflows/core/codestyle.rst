.. _workflow_codestyle:

*************
codestyle.yml
*************

Source: https://github.com/tardis-sn/tardis/blob/master/.github/workflows/codestyle.yml

Runs `ruff <https://docs.astral.sh/ruff/>`_ on the repository and posts a summary comment on pull requests. Triggered on pushes to any single-segment branch name and on pull requests targeting ``master`` (via ``pull_request_target``).

Jobs
====

**ruff**

1. Checkout the repository — full history (``fetch-depth: 0``); for ``pull_request_target`` the PR head SHA is checked out.
2. :doc:`setup-env <../actions/setup-env>` with ``os-label: linux-64`` and the in-repo ``conda-linux-64.lock`` lockfile.
3. Run ``ruff`` twice on the relevant Python files:

   - On pull requests, run against the diff vs. ``origin/master`` — once with ``--statistics --show-fixes`` (``ruff_stats.txt``) and once with ``--output-format=concise`` (``ruff_full.txt``).
   - On pushes, run against the entire tree.

4. Truncate the full output to the first 200 lines (``ruff_truncated.txt``) so the PR comment stays under GitHub's size limits.
5. On pull requests, find any existing ``I ran ruff on the latest commit`` comment and replace it with the new statistics + truncated output, including a link to the run's artifacts.
6. Upload ``ruff_full.txt`` and ``ruff_stats.txt`` as the ``ruff-results`` artifact.

See also
========

- :doc:`codespell <codespell>`
- :doc:`setup-env <../actions/setup-env>`
