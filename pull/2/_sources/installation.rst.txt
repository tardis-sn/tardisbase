Installation
-----------

.. note::
    - tardisbase is only supported on macOS and GNU/Linux.
    - TARDIS dependencies are distributed only through the `conda <https://docs.conda.io/en/latest/>`_ 
      package management system, therefore installation requires `Anaconda <https://docs.anaconda.com/anaconda/install/index.html>`_ 
      or `Miniconda <https://conda.io/projects/conda/en/latest/user-guide/install/index.html>`_
      to be installed on your system.

Conda lockfiles are platform-specific dependency files that produce repeatable environments.
These files are generated on every new release. We strongly recommend installing TARDIS ecosystem
packages using this method by following the steps described below.

1. Download the lockfile for your platform:

   .. code-block:: bash

       wget -q https://github.com/tardis-sn/tardisbase/master/conda-{platform}-64.lock

   Replace ``{platform}`` with ``linux-64`` or ``osx-arm64`` based on your operating system.

2. Create the environment:

   .. code-block:: bash

       conda create --name tardis --file conda-{platform}.lock

3. Activate the environment:

   .. code-block:: bash

       conda activate tardis

4. a. Developers should `fork the repository <https://github.com/tardis-sn/{package}/fork>`_, configure
      GitHub to `work with SSH keys <https://docs.github.com/en/authentication/connecting-to-github-with-ssh>`_,
      set up the `upstream remote <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/configuring-a-remote-for-a-fork>`_,
      and install the package in development mode.

      .. code-block:: bash

        $ git clone git@github.com:<username>/{package}.git
        $ cd {package}
        $ git remote add upstream git@github.com:tardis-sn/{package}.git
        $ git fetch upstream
        $ git checkout upstream/master
        $ pip install -e .

      Replace ``{package}`` with tardis, stardis, carsus, or tardisbase.
        
   b. Non-developers can install from specific releases using pip:

      .. code-block:: bash

        $ pip install git+https://github.com/tardis-sn/{package}.git@{tag}

      For example, to install the latest release:

      .. code-block:: bash
      
        $ pip install git+https://github.com/tardis-sn/{package}.git@release-latest

      or to install the most recent, unreleased changes from upstream:

      .. code-block:: bash

        $ pip install git+https://github.com/tardis-sn/{package}.git@master

.. note::
   This environment works for all TARDIS ecosystem packages. No additional environments are required.

To update the environment:

.. code-block:: bash

    conda update --name tardis --file conda-{platform}.lock
