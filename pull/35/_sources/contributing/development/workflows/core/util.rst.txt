.. _workflow_util:

********
util.yml
********

Source: https://github.com/tardis-sn/tardis/blob/master/.github/workflows/util.yml

Pull-request housekeeping. Runs on ``pull_request_target`` against ``master`` and bundles four independent jobs.

Jobs
====

**git-lfs-pull-label** — when a PR carries the ``git-lfs-pull`` label, posts a bot comment warning that the label triggers workflows that consume LFS bandwidth. (The comment text says the label is removed automatically after checks run; that removal is handled outside this workflow.)

**add-gsoc-label** — if the PR title contains ``GSoC``, automatically adds the ``GSoC :sun_with_face:`` label via `actions/github-script <https://github.com/actions/github-script>`_.

**check-first-time-committer** — uses `actions/first-interaction <https://github.com/actions/first-interaction>`_ to post a welcome message on a contributor's first PR, with links to the GSoC `AI Usage Policy <https://tardis-sn.github.io/summer_of_code/ai_usage_policy/>`_ and `PR checklist <https://tardis-sn.github.io/summer_of_code/pr_checklist/>`_.

**check-orcid** — verifies that every PR-commit author email appears in `.orcid.csv <https://github.com/tardis-sn/tardis/blob/master/.orcid.csv>`_:

1. Checkout the PR head SHA with full history.
2. ``grep`` the unique author emails from ``git log $PR_BASE_SHA..HEAD --pretty='%aE' | sort -u`` against ``.orcid.csv`` (``continue-on-error: true``).
3. If the grep failed, find any existing ``Please add your email and ORCID ID`` comment and replace it with a fresh request to add the author's email and `ORCID <https://orcid.org/>`_ ID to ``.orcid.csv``.

See also
========

- :doc:`mailmap <mailmap>`
- :doc:`lfs-cache <../reusable/lfs-cache>`
