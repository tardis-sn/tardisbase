.. _workflow_clean_docs:

**************
clean-docs.yml
**************

Source: https://github.com/tardis-sn/tardis/blob/master/.github/workflows/clean-docs.yml

Runs when pull requests are closed or when a branch/tag is deleted. Performs a surgical clean of the `gh-pages branch <https://github.com/tardis-sn/tardis/tree/gh-pages>`_ — unlike the "clean branch" path in :doc:`build-docs <build-docs>` (triggered by `workflow_dispatch <https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_dispatch>`_), this only deletes specific folders such as ``pull/<pr>``.

Jobs
====

**clean**

1. Checkout the repo.
2. Derive the folder name from the trigger (PR number, branch, or tag).
3. Delete the folder and commit the change back to ``gh-pages``.

See also
========

- :doc:`build-docs <build-docs>`
