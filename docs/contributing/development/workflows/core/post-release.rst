.. _workflow_post_release:

****************
post-release.yml
****************

Source: https://github.com/tardis-sn/tardis/blob/master/.github/workflows/post-release.yml

The post-release action updates the changelog, citation and credits in the main
repository.

Changelog job
=============

1. Check out the TARDIS repository with 0 fetch depth.
2. Get the current release tag
3. Generate a changelog with ``git-cliff``
4. Upload a CHANGELOG.md file as an artifact.

Citation job
============

1. Check out the TARDIS repository.
2. Wait for the Zenodo webhook to be available (3 min sleep).
3. Set up Python.
4. Install ``doi2cff``.
5. Convert the latest TARDIS release DOI to a CITATION.cff file. Try 10 times with a 60 second sleep between attempts.
6. Upload the CITATION.cff file as an artifact.

Credits job
===========

1. Check out the TARDIS repository.
2. Wait for the Zenodo webhook to be available (3 min sleep).
3. Set up Python.
4. Install ``requests``.
5. Run a helper script to update ``README.rst`` and ``docs/resources/credits.rst``.
6. Upload README.rst and credits.rst as artifacts.
7. Dispatch the updates to the TARDIS website.

Post-release pull request job
=============================

1. Checks out the TARDIS repository.
2. Downloads the artifacts from the previous steps.
3. Copy the ``CHANGELOG.md``, ``CITATION.cff``, ``README.rst`` and ``credits.rst`` files to the repository.
4. Get the current date.
5. Create a pull request.
6. Wait for the PR to be created (30 second sleep).
7. Automatically approve the PR using tokens from the infrastructure and core coordinator members.
8. Enable auto-merge.
