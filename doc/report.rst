
Evaluation of a prototype PHP interpreter built on top of PyPy
==============================================================

Traditionally, high-level language interpreters are written in
low-level languages like C or C++. I would like to present a prototype
PHP interpreter written using the PyPy translation toolchain. This has
been done before [1], [2], and even for PHP [3], but I think the
performance results are interesting nonetheless. The interpreter
itself is implemented in RPython and available online [4]. It is
definitely a prototype and not production-ready. However, it addresses
most of the hard problems that real PHP VMs attempt to solve. Overall
it seems the approach of using PyPy can outperform a naive
implementation by a factor of about 10, with only minor changes to
strategies developed in PyPy for the Python programming language. Ther were
no changes to PHP semantics necessary so far.

.. [1] http://tratt.net/laurie/tech_articles/articles/fast_enough_vms_in_fast_enough_time
.. [2] http://wyvern.cs.uni-duesseldorf.de/svn/pypy/extradoc/talk/s3-2008/talk.pdf
.. [3] http://dl.acm.org/citation.cfm?id=2047854
.. [4] https://bitbucket.org/fijal/hippy

Brief description
-----------------

The interpreter itself is written in RPython. It uses the JIT generator that
is a part of the PyPy project. It's a very simple interpreter that has a couple
of stages:

* a parser that accepts a custom written grammar

* a compiler that compiles AST to bytecode

* a simple bytecode interpreter

* A JIT, which is generated mostly automatically from the
  interpreter. There are 14 hints in the interpreter source code that
  help the JIT generator to understand the interpreter. A few data
  structures are also marked as immutable.

The interpreter implements most of the core types of PHP 1.0: arrays,
strings, ints, floats, references and functions. Semantics are
preserved as far as possible without a formal set of tests or
specifications.

Benchmarks
----------

I decided to pick a few benchmarks from the computer language shootout
as well as one internal Facebook benchmark. To ensure that the VM was
sufficiently warmed up before performance was measured, I ran each
benchmark 10 times and discarded the first 3 iterations. The times of
the remaining 7 runs were averaged.

The Zend version used was ``PHP 5.3.2-1ubuntu4.15 with Suhosin-Patch
(cli)``. All tests were performed on an x86_64-architecture Xeon
W3580 processor with 8M of cache.  The machine was otherwise idle.

The benchmark choice was not arbitrary, but it was also not based on
"what we can make fast". These benchmarks were chosen because they are
interesting, but also because they do something -- they cannot be
optimized away as dead code.

.. table:: Benchmark numbers:

  +---------------+--------+-----------+-----------+--------------+----------------+
  | benchmark     | zend   | hiphop VM | hippy VM  | hippy / zend | hippy / hiphop |
  +---------------+--------+-----------+-----------+--------------+----------------+
  | arr           | 2.771  | 0.541+-0% | 0.274+-0% | 10.1x        | 2.0x           |
  +---------------+--------+-----------+-----------+--------------+----------------+
  | fannkuch      | 21.239 | 7.227+-0% | 1.377+-0% | 15.4x        | 5.2x           |
  +---------------+--------+-----------+-----------+--------------+----------------+
  | heapsort      | 1.739  | 0.574+-0% | 0.192+-0% | 9.1x         | 3.0x           |
  +---------------+--------+-----------+-----------+--------------+----------------+
  | binary_trees  | 3.223  | 0.658+-0% | 0.460+-0% | 7.0x         | 1.4x           |
  +---------------+--------+-----------+-----------+--------------+----------------+
  | cache_get_scb | 3.350  | 0.747+-0% | 0.267+-2% | 12.6x        | 2.8x           |
  +---------------+--------+-----------+-----------+--------------+----------------+
  | fib           | 2.357  | 0.487+-0% | 0.021+-0% | 111.6x       | 23.0x          |
  +---------------+--------+-----------+-----------+--------------+----------------+
  | fasta         | 1.499  | 0.226+-2% | 0.177+-0% | 8.5x         | 1.3x           |
  +---------------+--------+-----------+-----------+--------------+----------------+


The standard deviation for Zend PHP is negligible in all cases (below
0.5%). This is expected from a relatively simple interpreter. In the
case of hippy, the standard deviation is only small once the VM has
warmed up, hence the rejection of the first 3 runs.

Note that the VM was implemented specifically to perform well on these
benchmarks. This does not mean that any heuristics were tweaked, but
that only those optimizations that were interesting for these
benchmarks were performed. Because of the time constraints it was
impossible to optimize for all cases. Given enough work and a decent
benchmark set, it could be done.

Two tweaks were made to the default PyPy settings:

* ``gen_store_back_in_virtualizable`` was disabled. This feature is
  necessary for Python frames but not for PHP frames. PHP frames
  do not have to be kept alive after we exit a function.

* The default trace limit was raised from 6000 to 20000. This makes
  for longer warm-up times (which is less of a concern in PHP than in
  Python), but the resulting code is faster.

These two tweaks have to be done in the PyPy codebase. A diff is
`available`_.

.. _`available`: http://wyvern.cs.uni-duesseldorf.de/~fijal/pypy.diff

Object model
============

The object model is specified in ``objects/`` directory and in ``objspace.py``.
The implementations are relatively straightforward with few exceptions:

* an array can have one of several strategies; including hash tables, maps
  (for prebuilt hashes), lists and unwrapped lists. The case of sparse
  arrays which contain only or mostly ints is not currently optimized
  for.

* a string can also have one of several strategies, the most notable
  of which is the string concatenation strategy which makes string
  concatenation lazy.

The object model chosen for hippy includes immutable types. This
results in many layers of indirection (from references, to cells, to
values). A better implementation of the basic types might improve
performance.

Another problem is copy-on-write semantics. Right now an object keeps track
of its copies, and copies know how to remove themselves from the linked list
of copies. This could be greatly improved with more explicit or implicit
refcounting for mutable objects.

Assessment
==========

Overall, given very limited time constraints (8 weeks of work, including
writing this report), the performance improvements are pretty large.
Implementing a simple VM in RPython, which is a high level language, lets
the PyPy translation toolchain automatically generate a Just in Time compiler
for the language implemented. There are few missing things from RPython, that
can be implemented either in core PyPy or mostly separately. Those are:

* An ordered dict implementation. RPython comes with unordered dict. Costs
  of keeping list of keys together with a normal dict turned out to be high.
  I implemented a completely functional ordered dict implementation in
  ``hippy/rpython``.

* A mutable string implementation. Right now the mutable string type is
  implemented using a list of characters. Since this is a second class citizen
  in RPython, there are quite a few places where instead of just using a list
  of chars, it's converted into immutable string first. This is by far
  suboptimal.

* Handling of frames is too conservative for the case of PHP. Several
  "safe bets", that are necessary in corner cases of the python language
  are unnecessary. The goal would be to make those features optional, or
  come up with general abstraction that handles both cases well.

Future possibilities
====================

I believe this study proves enough that it's possible to implement a
performant PHP VM using PyPy technology with relatively little effort. This
approach should scale well to the entire language.

Due to time constraints, some parts were not implemented up to the production
quality. Most notably the refcounting semantics for copy-on-write might be
missing a thing here and there. A more systematic approach is necessary.

There are also vast improvements to be done in cases that were already
optimized. Important improvements would include:

* Smarter handling of integer keys in arrays that are dictionaries.

* Sparse arrays (but not too sparse), where keys are only integers.

* More prevalent usage of maps where key sets can be considered constant
  enough.

* Improvements in frame handling, that should remove a lot of overhead
  in uninlined calls.

* Unboxed storage for typewise constant arrays (constant keys and constant
  types of values), as an extension to maps

* Tons of smaller and bigger improvements, like assembler generation.

