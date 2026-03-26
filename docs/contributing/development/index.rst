.. _unpinning_lockfiles:

**********************************
Unpinning Environment Lockfiles
**********************************

TARDIS packages use lockfiles for dependency management, which are unpinned annually. This document provides a methodology to follow or take inspiration from when performing this process.

Generating Lockfiles
====================

To generate conda lockfiles, you need the ``conda-lock`` package: `conda-lock on GitHub <https://github.com/conda/conda-lock>`_. Instructions for installing ``conda-lock`` are available in the repository README.

.. code-block:: bash

   # Step 1: Generate conda-lock.yml from an environment file
   conda-lock -f <env-file>.yml -p <platform>

   # Step 2: Render a platform-specific explicit lockfile
   conda-lock render -p <platform>

   # Step 3: Create an environment from the lockfile
   conda create --name <env-name> --file conda-<platform>.lock

**Example:**

.. code-block:: bash

   conda-lock -f env.yml -p linux-64
   conda-lock render -p linux-64
   conda create --name my-env --file conda-linux-64.lock

.. note::

   Supported platforms are ``linux-64`` and ``osx-arm64``. We do not maintain lockfiles for ``osx-64`` since it is not tested in CI.

Debugging CI Failures
=====================

The new unpinned lockfiles will most certainly cause CI failures. The CI workflows to test are: **build docs**, **tests**, and **benchmarks**.

.. note::

   Benchmarks maintain a separate set of pinned ``env.yml`` files, which are exported dependencies from the lockfile environment. Instructions for updating them can be found in the benchmarks documentation.

We recommend experimenting with changes to ``env.yml`` rather than editing the lockfiles directly, since lockfiles are more comprehensive and include internal dependencies as well.

Testing Locally
---------------

Some dependencies in the default ``env.yml`` are pinned because they caused issues in the past. Since this is a fresh unpin, we recommend unpinning them all.

Start by creating an environment from the ``env.yml``:

.. code-block:: bash

   mamba env create -f env.yml -n <env-name>

Then run the test suite. There will likely be some test failures.

Testing in CI
-------------

The test workflow uses the ``setup-env`` action from the `tardis-actions repository <https://github.com/tardis-sn/tardis-actions/blob/main/setup-env/action.yml>`_, which is responsible for setting up the environment and caching dependencies for faster installations.

To test new lockfiles, push them in a new branch and provide the URL to the ``setup-env`` action:

.. code-block:: yaml

   # Using a custom URL (lockfile or env.yml hosted somewhere)
   - uses: tardis-sn/tardis-actions/setup-env@main
     with:
       lock-file-url-prefix: "https://raw.githubusercontent.com/your-org/your-repo/branch"
       os-label: "linux-64"  # or "osx-arm64"
       cache-environment: "false"
       cache-downloads: "false"

.. code-block:: yaml

   # Using a local file path (lockfile or env.yml checked into the repo)
   - uses: tardis-sn/tardis-actions/setup-env@main
     with:
       lockfile-path: "path/to/env.yml"
       cache-environment: "false"
       cache-downloads: "false"

Narrowing Down Buggy Dependencies
==================================

Once you have a test failure log (it is recommended to have one for both Linux and macOS—use the same ``env.yml``, create conda environments, and compare against regression data on both platforms), you can begin narrowing down the cause.

Common Culprits
---------------

The most common culprits that have caused issues in the past are **NumPy**, **pandas**, **Numba**, and sometimes plotting libraries, since TARDIS relies on these heavily. However, errors can stem from any dependency.

Once you have a test log, group all the errors. Based on the type of errors, you may get a hint about which dependencies are causing the issues.

Common Dependency Issues
------------------------

1. **HDF issues**: If the underlying errors originate from PyTables or pandas, try pinning pandas to a previous version.

2. **Assertion errors during regression data comparison**: Depending on where they originate, these could be caused by either Numba or NumPy. Numba depends on NumPy, so these are often intertwined and hard to isolate. Downgrading either NumPy or Numba may result in an automatic downgrade of the other.

Local Debugging
---------------

Once you have a list of all issues, pick an error to start with. We suggest starting with tests that are mostly standalone, since they are easier to track down.

To make it easier, run the test of your choice in two different environments with the ``--pdb`` flag enabled:

.. code-block:: bash

   pytest path/to/test_module --tardis-regression-data=path/to/regression-data -vvv --pdb

The ``-x`` flag can be useful for ending the test suite early to focus on one error at a time. The ``-vvv`` flag provides extra verbosity and more detail during the run.

Once the test suite fails, use the debugger to navigate to the location in TARDIS where the failure occurs. You can then set breakpoints and observe how the code performs in both environments to narrow down the dependency.

Once you suspect a dependency is causing the issue, try pinning it to a previous version and run the test suite again. Check the list of failures to validate your hypothesis.

Since dependencies are interrelated, pinning one may cause another to be pinned as well. Review the changelogs of both dependencies, associated issues, and pull requests to further investigate which dependency is the root cause.

Resolving Discovered Issues
============================

Once buggy dependencies have been identified, there are three directions to take:

1. **Keep the dependency pinned** to a known working version.
2. **Update the regression data** if the old regression data no longer works with the new dependency versions.
3. **Modify the code** to handle the changes if the old regression data still works.

Updating Regression Data
-------------------------

If the regression data needs to be updated, the regression data comparison workflow can be useful:
`compare-regdata.yml <https://github.com/tardis-sn/tardis/blob/master/.github/workflows/compare-regdata.yml>`_.

This workflow also uses the same ``setup-env`` action, so you can provide the lockfile path to configure it.

.. note::

   If you open a pull request with changes, the workflow will give incorrect results by default because it uses the ``pull_request_target`` event, which means changes in the PR will not be picked up. To work around this, either run the workflow from a fork or push the branch to the upstream remote. In either case, modify the trigger from ``pull_request_target`` to ``pull_request`` on the upstream branch. Once this is done, the workflow will run correctly and post a comment with graphs displaying the spectrum change and differences in regression data.

An example of such a comment can be found at: `tardis-sn/tardis#3391 (comment) <https://github.com/tardis-sn/tardis/pull/3391#issuecomment-3784883251>`_.
