"""
Tools for interactive translation

Relies implicitly on PyPy's dotviewer and thus requires pygame.

Example session
---------------

>>> from hippy.debug import *
>>> space = make_space()
>>> strncmp = builtin_impl('strncmp')
>>> t = Translation(lambda s1, s2, n: strncmp(space, s1, s2, n), [str, str, int])
[flowgraph:start] (__main__:1)<lambda>
[flowgraph:done] <lambda>
>>> t.backendopt()
[translation:info] Annotating&simplifying...
...
>>> t.view()

"""
from rpython.translator.interactive import Translation
from hippy.objspace import ObjSpace
from hippy.interpreter import Interpreter
from hippy.builtin import BUILTIN_FUNCTIONS

def make_space():
    """Create a working ObjSpace, that can be used as a prebuilt constant
    for translation."""
    space = ObjSpace()
    Interpreter(space)  # XXX: seriously?
    return space

def builtin_impl(name):
    """Fetch the RPython implementation of the builtin `name`"""
    wrapped = dict(BUILTIN_FUNCTIONS)[name]
    return wrapped.runner.ll_func
