.. _unpinning_2026_bugs:

**********************************
Unpinning 2026
**********************************

This documentation provides details of the bugs that were discovered during lockfile unpinning in 2026.
For ways to understand how to unpin lockfiles, look at the :ref:`unpinning_lockfiles` documentation.

Dependencies which resulted in issues are Pandas, ``pytest`` and ``numba``.

``numpy`` is dependent on ``numba`` and varies if ``numba`` is pinned.

Pandas
======

Pandas alone is the cause of a lot of failures. This script below can be used to understand the root causes.
``test_cow_to_numpy_copy`` passes and all others fail in Pandas 2:

.. code-block:: python

   import os
   import tempfile

   import pandas as pd
   import numpy as np


   def test_cow_series_values():
       df = pd.DataFrame({"a": [1.0, 2.0, 3.0]})
       arr = df["a"].values
       arr[0] = 99.0


   def test_cow_dataframe_values():
       df = pd.DataFrame({"a": [1.0, 2.0], "b": [3.0, 4.0]})
       arr = df.values
       arr[0, 0] = 99.0


   def test_cow_to_numpy():
       df = pd.DataFrame({"a": [1.0, 2.0, 3.0]})
       arr = df["a"].to_numpy()
       arr[0] = 99.0


   def test_cow_to_numpy_copy():
       df = pd.DataFrame({"a": [1.0, 2.0, 3.0]})
       arr = df["a"].to_numpy(copy=True)
       arr[0] = 99.0


   def test_hdf5_bytes_attr():
       import tables

       with tempfile.TemporaryDirectory() as tmpdir:
           path = os.path.join(tmpdir, "test.h5")
           df = pd.DataFrame({"x": [1.0, 2.0, 3.0]})
           df.to_hdf(path, key="mydata")

           with tables.open_file(path, "a") as f:
               node = f.root.mydata
               node._v_attrs.pandas_type = b"frame"

           df2 = pd.read_hdf(path, key="mydata")

``test_cow_to_numpy_copy`` passes and all others fail in Pandas 2.

pytest
======

``pytest`` reordered fixtures which also cause similar issues. Below is a simple reproducer script:

.. code-block:: python

   import pytest


   @pytest.fixture(params=["a0"])
   def fix_a(request):
       return request.param


   @pytest.fixture
   def fix_b(fix_a):
       return fix_a


   @pytest.fixture(params=["c0"])
   def fix_c(fix_a, request):
       return request.param


   @pytest.fixture
   def fix_group(fix_b, fix_c):
       return [fix_b, fix_c]


   def test_solve(fix_group, request):
       print(f"Got '{request.node.name}'")
       assert request.node.name == "test_solve[c0-a0]"

Numba
=====

Running TARDIS plainly with tracking enabled produces a different tracker dataframe. This is seen in line interactions, originating from ``line_scatter_event`` in ``interaction_event_callers.py``.

The root cause is order of operations which changes between LLVM 15 and LLVM 20, though the exact location in the code is still under investigation. The difference can be reproduced using `this script <https://gist.github.com/atharva-2001/9b511316f71f39d2bb77c4febd65553b>`_.

This is a fastmath issue — disabling fastmath makes it go away.

The errors start around:

.. code-block:: python

   @njit(**njit_dict_no_parallel)
   def line_scatter_event(
       r_packet,
       time_explosion,
       line_interaction_type,
       opacity_state,
       enable_full_relativity,
   ):

which calls:

.. code-block:: python

   @njit(**njit_dict_no_parallel)
   def get_doppler_factor(r, mu, time_explosion, enable_full_relativity):
       inv_c = 1 / C_SPEED_OF_LIGHT
       inv_t = 1 / time_explosion
       beta = r * inv_t * inv_c
       if not enable_full_relativity:
           return get_doppler_factor_partial_relativity(mu, beta)
       else:
           return get_doppler_factor_full_relativity(mu, beta)

The doppler factor computation along with the line scatter event together causes differences which cascade over time.

Pinning ``numba`` to ``0.61.2`` pins ``llvmlite`` to ``0.44.0``, ``numpy`` to ``2.2.6``, and uses LLVM 15. See ``llvm15.ipynb`` and ``llvm20.ipynb`` in the repository root for detailed analysis.
