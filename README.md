
HippyVM
=======

HippyVM is an implementation of the PHP language using
[RPython/PyPy](http://pypy.org "pypy website") technology.

HippyVM right now works only on 64bit linux on x86 platform (this limitation
is temporary though, the RPython toolchain supports 32 and 64 bit x86,
ARMv6 and ARMv7 on windows, os x and linux).

Building
========

You need a [full checkout](http://bitbucket.org/pypy/pypy) of the RPython
translation toolchain. Having [a snapshot](https://bitbucket.org/pypy/pypy/get/default.tar.bz2) of PyPy is the easiest way to get a large repository.
Building goes like this (in hippyvm main directory):

<path to pypy>/rpython/bin/rpython -Ojit targethippy.py

This will create a hippy-c binary that works mostly like a php cli without
readling support.

Running it
==========

You can run it with ./hippy-c <file.php>. Example of benchmarks are in bench/
subdirectory.
