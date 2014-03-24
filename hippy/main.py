#!/usr/bin/env python
""" Hippy VM. Execute by typing

hippy [--gcdump dumpfile] [--cgi] <file.php> [php program options]

and enjoy
"""

import sys
import os

if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))

from hippy.phpcompiler import compile_php
from hippy.interpreter import Interpreter
from hippy.objspace import getspace
from hippy.error import ExplicitExitException, InterpreterError
from hippy.config import load_ini
from hippy.sourceparser import ParseError
from rpython.rlib.rgc import dump_rpy_heap
from rpython.rlib.objectmodel import we_are_translated


def entry_point(argv):
    if len(argv) < 2:
        print __doc__
        return 1

    i = 1
    fname = None
    gcdump = None
    cgi = False
    debugger_pipes = (-1, -1)
    while i < len(argv):
        arg = argv[i]
        if arg.startswith('-'):
            if arg == '--gcdump':
                if i == len(argv) - 1:
                    print "--gcdump requires an argument"
                    return 1
                i += 1
                gcdump = argv[i]
            elif arg == '--cgi':
                cgi = True
            elif arg == '--debugger_pipes':
                assert i + 2 < len(argv)
                debugger_pipes = (int(argv[i + 1]), int(argv[i + 2]))
                i += 2
            else:
                print __doc__
                print "Unknown parameter %s" % arg
                return 1
        else:
            fname = arg
            break
        i += 1
    if not fname:
        print "php filename required"
        return 1
    rest_of_args = argv[i + 1:]
    return main(fname, rest_of_args, cgi, gcdump, debugger_pipes)


def main(filename, rest_of_args, cgi, gcdump, debugger_pipes=(-1, -1)):
    try:
        f = open(filename)
        data = f.read()
        f.close()
    except:
        print "Error opening %s" % filename
        return 2
    #
    space = getspace()
    interp = Interpreter(space)
    # load the ini file situated in the current wc
    try:
        ini_data = open('hippy.ini').read()
    except (OSError, IOError):
        ini_data = None
    if ini_data is not None:
        try:
            load_ini(interp, ini_data)
        except:
            os.write(2, "error reading `hippy.ini`")
    interp.setup(cgi, argv=[filename] + rest_of_args)
    absname = os.path.abspath(filename)
    bc = interp.compile_bytecode(absname, data)
    if bc is None:
        return 1
    # The script originally called is considered an "included file,"
    # so it will be listed together with the files
    # referenced by include and family.
    interp.included_files.append(filename)
    #
    exitcode = 0
    try:
        try:
            if debugger_pipes != (-1, -1):
                interp.setup_debugger(debugger_pipes[0], debugger_pipes[1],
                                      start_paused=True)
            interp.run_main(space, bc, top_main=True)
        finally:
            interp.shutdown()
    except InterpreterError, e:
        tb = e.traceback
        if tb is not None:
            tb = tb[:]
            tb.reverse()
            for filename, funcname, line, source in tb:
                os.write(2, "function %s, file %s:%d\n" % (funcname, filename, line))
                os.write(2, source + "\n")
        if we_are_translated():
            os.write(2, "Fatal interpreter error %s\n" % e.msg)
        else:
            print >>sys.stderr, "%s: %s\n" % (e.__class__.__name__, e.msg)

    except ParseError as e:
        print e.__str__()
        return 1
    except ExplicitExitException, e:
        os.write(1, e.message)
        exitcode = e.code
    if gcdump is not None:
        f = os.open(gcdump, os.O_CREAT | os.O_WRONLY, 0777)
        dump_rpy_heap(f)
        os.close(f)
    return exitcode

if __name__ == '__main__':
    sys.exit(entry_point(sys.argv))
