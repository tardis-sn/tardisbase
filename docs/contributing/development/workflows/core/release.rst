.. _workflow_release:

***********
release.yml
***********

Source: https://github.com/tardis-sn/tardis/blob/master/.github/workflows/release.yml

Publishes a new release of TARDIS every Sunday at 00:00 UTC.

Release
=======

Creates a new release on GitHub after the pre-release PR is merged.

1. Check out the TARDIS repository with 0 fetch depth.
2. Set up Python.
3. Install ``setuptools_scm`` and ``git-cliff``.
4. Get the current TARDIS version using ``setuptools_scm`` via a helper script.
5. Get the next TARDIS version using ``setuptools_scm``.
6. Create a GitHub release that uses the new version as the tag.
7. Wait for Zenodo to update the new release of TARDIS (2 min sleep).
8. Fetch the new DOI from Zenodo using the Zenodo API, and create a badge.
9. Generate the changelog using ``git-cliff``.
10. Update the release description with the changelog and the Zenodo badge.
    Include the environment lock files in the release assets.
