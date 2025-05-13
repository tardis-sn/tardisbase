Installation
-----------

.. note::
    - tardisbase is only supported on macOS and GNU/Linux.
    - TARDIS dependencies are distributed only through the `conda <https://docs.conda.io/en/latest/>`_ 
      package management system, therefore installation requires `Anaconda <https://docs.anaconda.com/anaconda/install/index.html>`_ 
      or `Miniconda <https://conda.io/projects/conda/en/latest/user-guide/install/index.html>`_
      to be installed on your system.

Follow these steps to install the environment for the TARDIS ecosystem:

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

4. Clone the package you want to work with:

   .. code-block:: bash

       git clone git@github.com:tardis-sn/{package}.git
       cd {package}
       pip install -e .

   Replace ``{package}`` with tardis, stardis, carsus, or tardisbase.

.. note::
   This environment works for all TARDIS ecosystem packages. No additional environments are required.

To update the environment:

.. code-block:: bash

    conda update --name tardis --file conda-{platform}.lock
