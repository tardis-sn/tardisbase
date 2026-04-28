.. _workflow_tardis_research_papers:

***************************
tardis-research-papers.yml
***************************

Source: https://github.com/tardis-sn/tardis/blob/master/.github/workflows/tardis-research-papers.yml

Monthly cron (``0 0 1 * *``) — also runnable via ``workflow_dispatch`` — that refreshes the list of papers using TARDIS. It runs the ADS notebook to regenerate ``research_papers.rst``, opens an auto-merged bot PR with the changes, and pings the website repo to pick up the new list.

Jobs
====

**research-using-tardis**

1. Checkout the repository.
2. Set up a ``fetch-env`` conda env with ``python=3.10`` and ``jupyter`` via `mamba-org/setup-micromamba <https://github.com/mamba-org/setup-micromamba>`_.
3. Convert ``docs/resources/research_done_using_TARDIS/ads.ipynb`` to a script with ``jupyter nbconvert`` and run it; the script queries `NASA ADS <https://ui.adsabs.harvard.edu/>`_ via ``NASA_ADS_TOKEN`` (repo secret).
4. Upload the resulting ``research_papers.rst`` as the ``research_papers`` artifact.

**pull_request** (needs ``research-using-tardis``)

1. Checkout the repository.
2. Download the ``research_papers`` artifact and copy it into ``docs/resources/research_done_using_TARDIS/``.
3. Open a PR from ``tardis-bot/tardis`` using `peter-evans/create-pull-request <https://github.com/peter-evans/create-pull-request>`_, branch ``TARDIS-research-papers-<DATE>``, with the ``automated`` and ``build-docs`` labels and ``tardis-infrastructure`` as team reviewer.
4. Sleep 30s, then approve the PR twice (``INFRASTRUCTURE_COORDINATOR_TOKEN`` and ``CORE_COORDINATOR_TOKEN``) and enable squash automerge.

**dispatch-to-tardis-website** (needs ``research-using-tardis``) — ``POST`` a ``repository_dispatch`` event (``event_type: fetch-papers``) to ``tardis-sn/tardis-org-data`` so the website repo can pull in the refreshed list.

See also
========

- :doc:`build-docs <build-docs>`
