.. _workflow_mailmap:

***********
mailmap.yml
***********

Source: https://github.com/tardis-sn/tardis/blob/master/.github/workflows/mailmap.yml

Verifies that every PR commit author has an entry in `.mailmap <https://github.com/tardis-sn/tardis/blob/master/.mailmap>`_. If an author is missing, the bot fails the check and posts a comment asking the contributor to add their name and email.

Jobs
====

**check**

1. Checkout the PR head SHA with full history.
2. Run ``cat .mailmap | grep "$(git log $PR_BASE_SHA..HEAD --pretty='%aN <%aE>')"`` to confirm every PR-commit author appears in ``.mailmap``.
3. On failure, log the missing names/emails (``git log $PR_BASE_SHA..HEAD --pretty='%aN <%aE>'``) and post a bot comment instructing the contributor to add themselves to ``.mailmap``.

See also
========

- :doc:`util <util>`
