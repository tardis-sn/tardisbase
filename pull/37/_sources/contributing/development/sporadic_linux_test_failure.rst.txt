.. _sporadic_linux_test_failure:

******************************************
Sporadic Linux Test Failure
******************************************

This page documents differences in platform architecture between two pre-release runs, in which one passed and one failed.

As for the difference, only the ``archspec`` was found different.

Passed Run
==========

.. code-block:: text

   libmamba version : 2.3.3
   micromamba version : 2.3.3
   curl version : libcurl/8.14.1 OpenSSL/3.5.4 zlib/1.3.1 zstd/1.5.7 libssh2/1.11.1 nghttp2/1.67.0
   libarchive version : libarchive 3.8.2 zlib/1.3.1 bz2lib/1.0.8 libzstd/1.5.7 libb2/bundled
   envs directories : /home/runner/micromamba/envs
   package cache : /home/runner/micromamba/pkgs
                   /home/runner/.mamba/pkgs
   environment : tardis
   env location : /home/runner/micromamba/envs/tardis
   user config files : /home/runner/.mambarc
   populated config files : /home/runner/work/_temp/setup-micromamba/.condarc
   virtual packages : __unix=0=0
                      __linux=6.11.0=0
                      __glibc=2.39=0
                      __archspec=1=x86_64_v3
   channels : https://conda.anaconda.org/conda-forge/linux-64
              https://conda.anaconda.org/conda-forge/noarch
   base environment : /home/runner/micromamba
   platform : linux-64

Failed Run
==========

.. code-block:: text

   libmamba version : 2.3.3
   micromamba version : 2.3.3
   curl version : libcurl/8.14.1 OpenSSL/3.5.4 zlib/1.3.1 zstd/1.5.7 libssh2/1.11.1 nghttp2/1.67.0
   libarchive version : libarchive 3.8.2 zlib/1.3.1 bz2lib/1.0.8 libzstd/1.5.7 libb2/bundled
   envs directories : /home/runner/micromamba/envs
   package cache : /home/runner/micromamba/pkgs
                   /home/runner/.mamba/pkgs
   environment : tardis
   env location : /home/runner/micromamba/envs/tardis
   user config files : /home/runner/.mambarc
   populated config files : /home/runner/work/_temp/setup-micromamba/.condarc
   virtual packages : __unix=0=0
                      __linux=6.11.0=0
                      __glibc=2.39=0
                      __archspec=1=x86_64_v4
   channels : https://conda.anaconda.org/conda-forge/linux-64
              https://conda.anaconda.org/conda-forge/noarch
   base environment : /home/runner/micromamba
   platform : linux-64

If we look closely:

.. code-block:: text

   2.log (FAILED) - Line 2073:
     virtual packages : __unix=0=0
                        __linux=6.11.0=0
                        __glibc=2.39=0
                        __archspec=1=x86_64_v4    ← Intel Xeon with AVX-512

     3.log (PASSED) - Line 2060:
     virtual packages : __unix=0=0
                        __linux=6.11.0=0
                        __glibc=2.39=0
                        __archspec=1=x86_64_v3    ← AMD EPYC with AVX2

What This Means
===============

**x86_64_v4 vs x86_64_v3:**

* v4 supports **AVX-512** instructions (Intel Skylake-X and newer)
* v3 supports **AVX2** instructions (Intel Haswell and newer)

When GitHub assigns a v4 runner, NumPy/SciPy detect AVX-512 support at runtime and use different SIMD code paths. This causes tiny numerical differences (~1e-13 relative error) that exceed our tolerance levels.
