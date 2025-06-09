Installation
-----------

.. note::
    - tardisbase and TARDIS ecosystem packages are only supported on macOS and GNU/Linux. Windows users can run TARDIS ecosystem packages 
      from our official Docker image (*coming soon*), `WSL <https://docs.microsoft.com/en-us/windows/wsl/>`_ 
      or a Virtual Machine.
    - TARDIS ecosystem package dependencies are distributed only through the `conda <https://docs.conda.io/en/latest/>`_ 
      package management system, therefore installation requires `Anaconda <https://docs.anaconda.com/anaconda/install/index.html>`_ 
      or `Miniconda <https://conda.io/projects/conda/en/latest/user-guide/install/index.html>`_
      to be installed on your system.

Conda lockfiles are platform-specific dependency files that produce reproducible environments. 
We strongly recommend installing TARDIS ecosystem packages using this method by following the steps below.

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

4. To install TARDIS ecosystem packages, first execute these commands:

   .. note::
      Replace {package} with the name of the TARDIS package you wish to install.

   .. code-block:: bash

      $ git clone git@github.com:tardis-sn/{package}.git
      $ cd {package}
      $ git remote add upstream git@github.com:tardis-sn/{package}.git
      $ git fetch upstream
      $ git checkout upstream/master
    
   The installation process differs for developers and non-developers:

   a. Developers should `fork the repository <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo>`_ of the package to be installed, configure
      GitHub to `work with SSH keys <https://docs.github.com/en/authentication/connecting-to-github-with-ssh>`_,
      set up the `upstream remote <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/configuring-a-remote-for-a-fork>`_,
      and install the package in development mode.

      .. code-block:: bash

        $ pip install -e .

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
      Running specific modules or tests for some packages might require additional optional dependencies. 
      The tardisbase package can also be installed as an optional dependency.
      These optional dependencies can be installed by running:
      
      .. code-block:: bash
      
        $ pip install -e ".[optional_dependencies]"
        # for example:
        # pip install -e ".[tardisbase]" # installs the package with tardisbase optional dependency group
        # for multiple optional dependencies
        # $ pip install -e ".[dependency1,dependency2,dependency3]"

      To update optional dependencies, use:

      .. code-block:: bash
      
          $ pip install -e ".[optional_dependency]" --upgrade --force-reinstall
          # for example:
          $ pip install -e ".[tardisbase]" --upgrade --force-reinstall # forces reinstall of tardisbase dependencies group
      
      Please refer to the package documentation for more details.

.. note::
   This environment works for all TARDIS ecosystem packages. No additional environments are required.

To update the environment:

.. code-block:: bash

    conda update --name tardis --file conda-{platform}.lock
