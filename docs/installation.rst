Installation
-----------

.. note::
    - tardisbase and TARDIS ecosystem packages are only supported on macOS and GNU/Linux. Windows users can run TARDIS ecosystem packages using `WSL <https://docs.microsoft.com/en-us/windows/wsl/>`_  or on a Virtual Machine.
    - TARDIS ecosystem package dependencies are distributed only through the `conda <https://docs.conda.io/en/latest/>`_ 
      package management system, therefore installation requires `Anaconda <https://docs.anaconda.com/anaconda/install/index.html>`_ 
      or `Miniconda <https://conda.io/projects/conda/en/latest/user-guide/install/index.html>`_
      to be installed on your system.

Conda lockfiles are platform-specific dependency files that produce reproducible environments. 
We strongly recommend installing `tardisbase` using this method by following the steps below.

.. note::
    You need not install the environment if you have installed it already beforehand when installing a different TARDIS ecosystem package.

1. Download the lockfile for your platform:

   .. tabs:: 

      .. group-tab:: OSX (Arm CPU)

        .. code-block:: bash

            wget -q https://github.com/tardis-sn/tardisbase/master/conda-osx-arm64.lock
        
      
      .. group-tab:: Linux

        .. code-block:: bash

            wget -q https://github.com/tardis-sn/tardisbase/master/conda-linux-64.lock
      
      .. group-tab:: OSX (Intel CPU)

        .. code-block:: bash

            wget -q https://github.com/tardis-sn/tardisbase/master/conda-osx-64.lock
        
        .. warning::
            Use at your own risk. This lockfile is not tested, so we recommend running the tests before using any of the TARDIS ecosystem packages with this environment.

2. Create the environment:

   .. tabs:: 

      .. group-tab:: OSX (Arm CPU)

        .. code-block:: bash

            conda create --name tardis --file conda-osx-arm64.lock
        
      
      .. group-tab:: Linux

        .. code-block:: bash

            conda create --name tardis --file conda-linux-64.lock
      
      .. group-tab:: OSX (Intel CPU)

        .. code-block:: bash

            conda create --name tardis --file conda-osx-64.lock
   

3. Activate the environment:

   .. code-block:: bash

       conda activate tardis
   
   .. note::
   This environment works for all TARDIS ecosystem packages. No additional environments are required.


4. To install `tardisbase` first execute these commands:

   .. code-block:: bash

      $ git clone git@github.com:tardis-sn/tardisbase.git
      $ cd tardisbase
      $ git remote add upstream git@github.com:tardis-sn/tardisbase.git
      $ git fetch upstream
      $ git checkout upstream/master
    
   The installation process differs for developers and non-developers:

   a. Developers should `fork the repository <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo>`_ , configure
      GitHub to `work with SSH keys <https://docs.github.com/en/authentication/connecting-to-github-with-ssh>`_,
      set up the `upstream remote <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/configuring-a-remote-for-a-fork>`_ and `origin` (pointing to your fork),
      and install `tardisbase` in development mode.

      .. code-block:: bash

        $ pip install -e .

   b. Non-developers can install from specific releases using pip:

      .. code-block:: bash

        $ pip install git+https://github.com/tardis-sn/tardisbase.git@{tag}

      For example, to install the latest release:

      .. code-block:: bash
      
        $ pip install git+https://github.com/tardis-sn/tardisbase.git@release-latest

      or to install the most recent, unreleased changes from upstream:

      .. code-block:: bash

        $ pip install git+https://github.com/tardis-sn/tardisbase.git@master

Environment update
==================

To update the environment, download the latest lockfile and run ``conda update``.

.. code-block:: bash

    $ wget -q https://github.com/tardis-sn/tardisbase/master/conda-{platform}-64.lock
    $ conda update --name tardis --file conda-{platform}.lock

.. note::

  If you have installed `tardisbase` in development mode, you should *ideally* update your environment whenever you pull latest code because the new code added might be using updated (or new) dependencies. If you don't do that and your installation seems broken, you can check if your environment requires update by comparing it against the latest environment file:

  .. code-block:: bash

      $ conda compare --name tardis env.yml
   
  We also recommend updating optional dependencies whenever you pull latest code.


**Recommended approach:**

We highly recommend deleting your existing environment and creating a new one using the latest lockfile whenever you need to update your environment.

Use the following ``conda`` command to remove your current ``tardis`` environment:

.. code-block:: bash

    $ conda remove --name tardis --all


