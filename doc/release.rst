Prototype PHP interpreter using the PyPy toolchain - Hippy VM
=============================================================

Hello everyone.

I'm proud to release the result of a Facebook-sponsored study on the feasibility of
using the RPython toolchain to produce a PHP interpreter. The rules were
simple: two months; one person; get as close to PHP as possible, implementing
enough warts and corner cases to be reasonably sure that it answers hard
problems in the PHP language. The outcome is called ``Hippy VM`` and implements
most of the PHP 1.0 language (functions, arrays, ints, floats and strings).
This should be considered an alpha release.

The resulting interpreter is obviously incomplete – it does not support all
modern PHP constructs (classes are completely unimplemented), builtin functions,
grammar productions, web server integration, builtin libraries
etc., etc.. It's **just** complete enough for me to reasonably be able to 
say that – given some engineering effort – it's possible to provide a rock-solid
and fast PHP VM using PyPy technologies.

The result is available in a `Bitbucket repo`_ and is released under the MIT
license.

.. _`Bitbucket repo`: https://bitbucket.org/fijal/hippyvm


Performance
-----------

The table below shows a few benchmarks comparing Hippy VM to `Zend`_ (a standard 
PHP interpreter available in Linux distributions) and `HipHop VM`_ (a PHP-to-C++ 
optimizing compiler developed by Facebook).  The versions used were Zend 5.3.2 
(Zend Engine v2.3.0) and HipHop VM heads/vm-0-ga4fbb08028493df0f5e44f2bf7c042e859e245ab 
(note that you need to check out the ``vm`` branch to get the newest version).

The run was performed on 64-bit Linux running on a Xeon W3580 with 8M of
L2 cache, which was otherwise unoccupied.

Unfortunately, I was not able to run it on the JITted version of HHVM, the new effort by Facebook,
but people involved with the project told me it's usually slower or comparable with the compiled HipHop.
Their JITted VM is still alpha software, so I'll update it as soon as I have the info.

.. _`Zend`: http://www.zend.com
.. _`HipHop VM`: https://github.com/facebook/hiphop-php

  +---------------+--------+-----------+-----------+--------------+----------------+
  | benchmark     | Zend   | HipHop VM | Hippy VM  | Hippy / Zend | Hippy / HipHop |
  +---------------+--------+-----------+-----------+--------------+----------------+
  | arr           | 2.771  | 0.508+-0% | 0.274+-0% | 10.1x        | 1.8x           |
  +---------------+--------+-----------+-----------+--------------+----------------+
  | fannkuch      | 21.239 | 7.248+-0% | 1.377+-0% | 15.4x        | 5.3x           |
  +---------------+--------+-----------+-----------+--------------+----------------+
  | heapsort      | 1.739  | 0.507+-0% | 0.192+-0% | 9.1x         | 2.6x           |
  +---------------+--------+-----------+-----------+--------------+----------------+
  | binary_trees  | 3.223  | 0.641+-0% | 0.460+-0% | 7.0x         | 1.4x           |
  +---------------+--------+-----------+-----------+--------------+----------------+
  | cache_get_scb | 3.350  | 0.614+-0% | 0.267+-2% | 12.6x        | 2.3x           |
  +---------------+--------+-----------+-----------+--------------+----------------+
  | fib           | 2.357  | 0.497+-0% | 0.021+-0% | 111.6x       | 23.5x          |
  +---------------+--------+-----------+-----------+--------------+----------------+
  | fasta         | 1.499  | 0.233+-4% | 0.177+-0% | 8.5x         | 1.3x           |
  +---------------+--------+-----------+-----------+--------------+----------------+

The PyPy compiler toolchain provides a way to implement a dynamic
language interpreter in a high-level language called RPython. This is
a language which is lower-level than Python, but still higher-level than
C or C++: for example, RPython is a garbage-collected language. The killer
feature is that the toolchain will generate a JIT for your interpreter which 
will be able to leverage most of the work that has been done on speeding up Python 
in the PyPy project.  The resulting JIT is generated for your interpreter, and is not Python-specific. 
This was one of the toolchain's original design decisions – in contrast to e.g. the JVM, 
which was initially only used to interpret Java and later adjusted to serve as a platform for
dynamic languages.

Another important difference is that there is no common bytecode to which you compile both your 
language and Python, so you don't inherit problems presented when implementing language X on top of, 
say, `Parrot VM`_ or the JVM.  The PyPy toolchain does not impose constraints on the semantics of 
your language, whereas the benefits of the JVM only apply to languages that map well onto Java concepts.

To read more about creating your own interpreters using the PyPy toolchain,
read `more`_ `blog posts`_ or an `excellent article`_ by Laurence Tratt.

.. _`more`: http://morepypy.blogspot.com/2011/04/tutorial-writing-interpreter-with-pypy.html
.. _`blog posts`: http://morepypy.blogspot.com/2011/04/tutorial-part-2-adding-jit.html
.. _`excellent article`: http://tratt.net/laurie/tech_articles/articles/fast_enough_vms_in_fast_enough_time
.. _`Parrot VM`: http://www.parrot.org/

PHP deviations
--------------

The project's biggest deviation from the PHP specification is probably 
that GC is no longer reference counting. That means that the object finalizer, when
implemented, will not be called directly at the moment of object death, but
at some later point. There are possible future developments to alleviate that
problem, by providing "refcounted" objects when leaving the current scope.
Research has to be done in order to achieve that.

Assessment
----------

The RPython toolchain seems to be a cost-effective choice for writing
dynamic language VMs.  It both provides a fast JIT and gives you
access to low-level primitives when you need them. A good example is
in the directory ``hippy/rpython`` which contains the implementation
of an ordered dictionary. An ordered dictionary is not a primitive
that RPython provides – it's not necessary for the goal of
implementing Python.  Now, implementing it on top of a normal dictionary
is possible, but inefficient. RPython provides a way to work
directly at a lower level, if you desire to do so.

Things that require improvements in RPython:

* Lack of mutable strings on the RPython level ended up being a problem.
  I ended up using lists of characters; which are efficient, but inconvenient,
  since they don't support any string methods.

* Frame handling is too conservative and too Python-specific, especially around
  the calls. It's possible to implement less general, but simpler and faster
  frame handling implementation in RPython.

Status of the implementation
----------------------------

Don't use it! It's a research prototype intended to assess the feasibility
of using RPython to create dynamic language VMs. The most notable
feature that's missing is reasonable error reporting. That said, I'm
confident it implements enough of the PHP language to prove that the full
implementation will present the same performance characteristics.

Benchmarks
----------

The benchmarks are a selection of computer language shootout benchmarks, as well
as ``cache_get_scb``, which is a part of old Facebook code. All benchmarks other 
than this one (which is not open source, but definitely the most interesting :( ) are
available in the ``bench`` directory. The Python program to run them is called
``runner.py`` and is in the same directory. It runs them 10 times, cutting off the first
3 runs (to ignore the JIT warm-up time) and averaging the rest. As you can see
the standard deviation is fairly minimal for all interpreters and runs; if 
it's omitted it means it's below 0.5%.

The benchmarks were not selected for their ease of optimization – the optimizations
in the interpreter were written specifically for this set of benchmarks. No special JIT 
optimizations were added, and barring what's mentioned below a vanilla PyPy 1.9 checkout 
was used for compilation.


So, how fast will my website run if this is completed?
------------------------------------------------------

The truth is that I lack the benchmarks to be able to answer that right now. The core
of the PHP language is implemented up to the point where I'm confident
that the performance will not change as we get more of the PHP going.

How do I run it?
----------------

Get a `PyPy checkout`_, apply the `diff`_ if you want to squeeze out the last
bits of performance and run ``pypy-checkout/bin/rpython targethippy.py`` to
get an executable that resembles a PHP interpreter. You can also directly run
``python targethippy.py file.php``, but this will be about 2000x slower.

RPython modifications
-----------------------

There was a modification that I did to the PyPy source code; the `diff`_
is available. It's trivial, and should simply be made optional in the
RPython JIT generator, but it was easier just to do it, given the very constrained time
frame.

* ``gen_store_back_in_virtualizable`` was disabled. This feature is
  necessary for Python frames but not for PHP frames. PHP frames
  do not have to be kept alive after we exit a function.

.. _`PyPy checkout`: https://bitbucket.org/pypy/pypy
.. _`diff`: https://gist.github.com/2923845

Future
------

Hippy is a cool prototype that presents a very interesting path towards a fast
PHP VM.  However, at the moment I have too many other open source commitments
to take on the task of completing it in my spare time.  I do think that this project
has a lot of potential, but I will not commit to any further development at
this time.  If you send pull requests I'll try to review them.  I'm also open
to having further development on this project funded, so if you're interested
in this project and the potential of a fast PHP interpreter, please get in
touch.

Cheers,
fijal
