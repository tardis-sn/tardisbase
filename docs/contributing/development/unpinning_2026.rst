.. _unpinning_2026_bugs:

**********************************
Unpinning 2026
**********************************

This documentation provides details of the bugs that were discovered during lockfile unpinning in 2026.
For ways to understand how to unpin lockfiles, look at the :ref:`unpinning_lockfiles` documentation.

Dependencies which resulted in issues are ``Pandas``, ``pytest`` and ``Numba``.
``NumPy`` is dependent on ``Numba`` and varies according to the ``Numba`` version.

Pandas
======

``Pandas`` upgrade is the cause of the majority of failures since ``Pandas`` is used in regression data, which is used in almost all of the tests.
This script below replicates the root causes.

``test_cow_to_numpy_copy`` passes and all others fail in ``Pandas`` 3. All tests pass in ``Pandas`` 2.

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

pytest
======

``pytest`` reordered fixtures which also cause similar issues. `pytest-dev/pytest#13774 <https://github.com/pytest-dev/pytest/pull/13774>`_ is a related PR.
Below is a simple reproducer script which fails in ``pytest`` 9 but passes in ``pytest`` 8.

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

Running TARDIS with tracking enabled produces different tracker dataframes in ``Numba`` ``0.61.2`` and ``Numba`` ``0.63.1``. This is seen in line interactions, originating from ``line_scatter_event`` in ``interaction_event_callers.py``.

The root cause is order of operations which changes between LLVM 15 and LLVM 20. ``Numba`` ``0.61.2`` uses ``llvmlite`` ``0.44.0`` (LLVM 15), while ``Numba`` ``0.63.1`` uses ``llvmlite`` ``0.46.0`` (LLVM 20).

This is also a ``fastmath`` issue, disabling ``fastmath`` makes it go away.

Tracing the tracker dataframe leads to `line_scatter_event <https://github.com/tardis-sn/tardis/blob/master/tardis/transport/montecarlo/interaction_event_callers.py#L179>`_ as the root cause. `line_scatter_event <https://github.com/tardis-sn/tardis/blob/master/tardis/transport/montecarlo/interaction_event_callers.py#L179>`_ calls `get_doppler_factor <https://github.com/tardis-sn/tardis/blob/master/tardis/transport/frame_transformations.py#L12>`_, and the combination of equations produced do not match between LLVM 15 and LLVM 20. The bug only appears in ``line_scatter_event`` and not in ``get_doppler_factor``, since ``get_doppler_factor`` standalone is a smaller equation and does not require LLVM reorganisation.

For more information, please see :doc:`numba_0.61.2_llvm15` and :doc:`numba_0.63.1_llvm20`.

