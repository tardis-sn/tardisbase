.. _workflow_tests:

*********
tests.yml
*********

The `testing pipeline`_ (CI) comprises 4 concurrent jobs that execute tests both with and without the continuum marker across Ubuntu and macOS platforms (2 platforms × 2 test types).
The pipeline includes both preparatory setup (environment installation and regression data configuration) and subsequent uploading of coverage reports upon test completion.

.. _testing pipeline: https://github.com/tardis-sn/tardis/blob/master/.github/workflows/tests.yml
