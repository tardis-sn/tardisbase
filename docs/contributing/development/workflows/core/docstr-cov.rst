.. _workflow_docstr_cov:

**************
docstr-cov.yml
**************

Source: https://github.com/tardis-sn/tardis/blob/master/.github/workflows/docstr-cov.yml

Uses `interrogate <https://interrogate.readthedocs.io/>`_ to track docstring coverage. On pull requests it fails if coverage drops vs. the base commit; on pushes to ``master`` it publishes an updated `shields.io <https://shields.io/>`_ badge backed by `jsonbin.org <https://jsonbin.org>`_.

Environment
===========

- ``THRESHOLD`` — ``0.05`` (allowed slack vs. base coverage).
- ``RANGE`` — ``50..75`` (drives badge color: red below 50, orange in-between, green at/above 75).
- ``ENDPOINT`` — ``https://jsonbin.org/tardis-bot/<repo>`` where the badge JSON is stored.
- ``TOKEN`` — ``JSONBIN_APIKEY`` repo secret used to write to jsonbin.

Jobs
====

**check**

1. Checkout the repo with full history.
2. Set up Python 3.x and ``pip install interrogate==1.7.0 parse==1.21.0 setuptools==82.0.0``.
3. Resolve ``BASE`` and ``HEAD`` SHAs:

   - ``push``: ``HEAD^`` and ``HEAD`` (last two commits).
   - ``pull_request``: the PR's base and head SHAs.

4. Check out ``BASE`` and compute its coverage with ``interrogate tardis -c pyproject.toml | python .ci-helpers/get_min_docstr_cov.py`` → ``BASE_COV``.
5. Check out ``HEAD`` and run ``interrogate tardis -c pyproject.toml --fail-under=$BASE_COV -v`` to fail the job if coverage regressed.
6. On failure, blame the diff: run ``interrogate`` per changed ``.py`` file with ``--fail-under=100`` to surface the offending file(s).
7. On pushes to ``master``, compute the new coverage (``NEW_COV``), pick a badge color from ``RANGE``, ``POST`` the badge JSON to the jsonbin endpoint, mark the endpoint public, and print the resulting `shields.io <https://shields.io/>`_ URL.

See also
========

- :doc:`build-docs <build-docs>`
