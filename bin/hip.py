#!/usr/bin/env python
"""
Main read-eval-print loop for untranslated Hippy.
"""

import sys, os, pdb

if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hippy.sourceparser import parse
from hippy.astcompiler import compile_ast
from hippy.interpreter import Interpreter
from hippy.phpcompiler import compile_php
from hippy.objspace import getspace
from hippy.error import ExplicitExitException


def run(args):
    assert len(args) == 1, "XXX only supports one argument, a php file"
    filename = args[0]
    f = open(filename, 'r')
    source = f.read(-1)
    f.close()
    space = getspace()
    bc = compile_php(filename, source, space)
    print '-=- %s -=-' % (filename,)
    interp = Interpreter(space)
    interp.setup(False, args)
    try:
        interp.run_main(space, bc)
        interp.shutdown()
    except ExplicitExitException, e:
        sys.exit(e.code)
    except Exception, e:
        print e
        pdb.post_mortem(sys.exc_info()[2])


def repl():
    space = getspace()
    interp = Interpreter(space)
    print
    print '-=- Hippy -=-'
    print
    while True:
        try:
            line = raw_input("<? ")
        except EOFError:
            print
            break
        if not line.lstrip() or line.lstrip().startswith('//'):
            continue
        try:
            pc = parse(space, line, 0)
            bc = compile_ast("<input>", line, pc, space, print_exprs=True)
        except Exception, e:
            print >> sys.stderr, '%s: %s' % (e.__class__.__name__, e)
            continue
        try:
            interp.run_main(space, bc)
        except ExplicitExitException, e:
            os.write(1, e.message)
            sys.exit(e.code)
        except Exception, e:
            print e
            pdb.post_mortem(sys.exc_info()[2])

if __name__ == '__main__':
    if len(sys.argv) > 1:
        run(sys.argv[1:])
    else:
        repl()
