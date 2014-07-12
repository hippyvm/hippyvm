
""" Tests for hippy JIT without compiling the whole JIT to C
"""

import sys, os
from rpython.rtyper.lltypesystem import lltype
from rpython.jit.codewriter.policy import JitPolicy
from rpython.rtyper.annlowlevel import llhelper, llstr, hlstr
from rpython.rtyper.lltypesystem.rstr import STR
from rpython import conftest

from hippy.objspace import getspace
from hippy.phpcompiler import compile_php
from hippy.interpreter import Interpreter
from hippy.error import ExplicitExitException
from hippy.bytecode import unserialize

filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'jithip.php')

def read_code():
    source = open(filename).read()
    space = getspace()
    bc = compile_php('<input>', source, space)
    return llstr(bc.serialize(space))

FPTR = lltype.Ptr(lltype.FuncType([], lltype.Ptr(STR)))
read_code_ptr = llhelper(FPTR, read_code)

def run():
    space = getspace()
    interp = Interpreter(space)
    bc = unserialize(hlstr(read_code_ptr()), space)
    interp.setup(False, {})
    try:
        interp.run_main(space, bc)
    except ExplicitExitException, e:
        print "EXITED WITH %d" % e.code
        return
    except Exception, e:
        print "Exception encountered"
        print e

import pdb

def run_child(glob, loc):
    interp = loc['interp']
    graph = loc['graph']
    interp.malloc_check = False

    def returns_null(T, *args, **kwds):
        return lltype.nullptr(T)
    interp.heap.malloc_nonmovable = returns_null     # XXX

    from rpython.jit.backend.llgraph.runner import LLGraphCPU
    #LLtypeCPU.supports_floats = False     # for now
    apply_jit(interp, graph, LLGraphCPU)


def apply_jit(interp, graph, CPUClass):
    from rpython.jit.metainterp import warmspot

    print 'warmspot.jittify_and_run() started...'
    policy = JitPolicy()
    warmspot.jittify_and_run(interp, graph, [], policy=policy,
                             listops=True, CPUClass=CPUClass,
                             backendopt=True, inline=True)

def test_run_translation():
    from rpython.rtyper.test.test_llinterp import get_interpreter
    from rpython.translator.goal import unixcheckpoint
    from rpython.config.translationoption import get_combined_translation_config
    from rpython.config.translationoption import set_opt_level

    config = get_combined_translation_config(translating=True)
    config.translation.gc = 'boehm'
    set_opt_level(config, level='jit')
    config.translation.backendopt.inline_threshold = 0.1

    try:
        interp, graph = get_interpreter(run, [], backendopt=False,
                                        config=config)
    except Exception, e:
        print '%s: %s' % (e.__class__, e)
        pdb.post_mortem(sys.exc_info()[2])
        raise
    class Option:
        view = True

    conftest.option = Option

    unixcheckpoint.restartable_point(auto='run')

    from rpython.jit.codewriter.codewriter import CodeWriter
    CodeWriter.debug = True
    run_child(globals(), locals())

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        # debugging: run the code directly
        run()
    else:
        test_run_translation()
