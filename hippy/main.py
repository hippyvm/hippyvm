#!/usr/bin/env python
""" Hippy VM. Execute by typing

hippy [--gcdump dumpfile] [--cgi] [--server port] [--jit jit_param] [<file.php>] [php program options]

and enjoy
"""

import sys
import os

if __name__ == '__main__': # untranslated
    sys.path.insert(0, os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
    from hippy.hippyoption import enable_all_optional_extensions
    enable_all_optional_extensions()

from hippy.phpcompiler import compile_php
from hippy.interpreter import Interpreter
from hippy.objspace import getspace
from hippy.error import ExplicitExitException, InterpreterError, SignalReceived
from hippy.config import load_ini
from hippy.sourceparser import ParseError
from hippy.lexer import LexerError
from rpython.rlib.rgc import dump_rpy_heap
from rpython.rlib.objectmodel import we_are_translated
from hippy import rpath

# Needs to be a separate func so flowspace doesn't say import cannot succeed
# when there is no fastcgi module source around.
def _run_fastcgi_server(server_port):
    from ext_module.fastcgi.fcgi import run_fcgi_server
    print "Running fcgi server on port %d" % (server_port,)
    return run_fcgi_server(port=server_port)

def mk_entry_point(py_space=None):
  # XXX 2 space indent to make merging with master less painful XXX

  # equivalent to the hack in app_main.py of PyPy, albiet interp-level.
  w_sys = py_space.sys
  w_modnames = w_sys.get("builtin_module_names")
  w_in = py_space.contains(w_modnames, py_space.wrap("__pypy__"))
  if not py_space.is_true(w_in):
    rl = py_space.sys.get("setrecursionlimit")
    py_space.call(rl, py_space.newlist([py_space.wrap(5000)]))

  def entry_point(argv):
    i = 1
    fname = None
    gcdump = None
    cgi = False
    fastcgi = False
    bench_mode = False
    bench_no = 0
    debugger_pipes = (-1, -1)
    server_port = 9000
    jit_param = None
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
            elif arg == '--server':
                if i == len(argv) - 1:
                    print "--server requires an int"
                    return 1
                server_port = int(argv[i + 1])
                i += 1
                fastcgi = True
            elif arg == '--bench':
                bench_mode = True
                if i == len(argv) - 1:
                    print "--bench requires an int"
                    return 1
                bench_no = int(argv[i + 1])
                i += 1
            elif arg == '--debugger_pipes':
                assert i + 2 < len(argv)
                debugger_pipes = (int(argv[i + 1]), int(argv[i + 2]))
                i += 2
            elif arg == '--jit':
                if i == len(argv) - 1:
                    print "--jit requires an argument"
                    return 1
                i += 1
                jit_param = argv[i]
            else:
                print __doc__
                print "Unknown parameter %s" % arg
                return 1
        else:
            fname = arg
            break
        i += 1
    if jit_param:
        from rpython.rlib.jit import set_user_param
        set_user_param(None, jit_param)
    if fastcgi:
        if bench_mode:
            print "can't specify --bench and --server"
            return 1
        from hippy.hippyoption import is_optional_extension_enabled
        if not is_optional_extension_enabled("fastcgi"):
            print("No fastcgi support compiled in")
            return 1
        else:
            return _run_fastcgi_server(server_port)
    rest_of_args = []
    for k in range(i + 1, len(argv)):
        s = argv[k]
        assert s is not None
        rest_of_args.append(s)
    return main(fname, rest_of_args, cgi, gcdump, debugger_pipes,
                bench_mode, bench_no, py_space=py_space)
  return entry_point

def main(filename, rest_of_args, cgi, gcdump, debugger_pipes=(-1, -1),
         bench_mode=False, bench_no=-1, py_space=None):
    space = getspace()
    if py_space is not None:
        py_space.startup() # must be called once prior to use

    interp = Interpreter(space, py_space=py_space)

    try:
        ini_data = open('hippy.ini').read(-1)
    except (OSError, IOError):
        ini_data = None

    if ini_data is not None:
        try:
            load_ini(interp, ini_data)
        except:
            os.write(2, "error reading `hippy.ini`")

    try:
        bc = space.bytecode_cache.compile_file(filename, space)
    except ParseError as e:
        print 'Parse error:  %s' % e
        return 2
    except LexerError as e:
        print 'Parse error:  %s on line %d' % (e.message, e.source_pos + 1)
        return 2
    except IOError as e:
        print 'Could not open input file: %s' % filename
        return 2
    except Exception as e:
        print 'Got exception: %s' % e
        return 2
    #
    if bench_mode:
        no = bench_no
    else:
        no = 1

    exitcode = 0
    space.ec.init_signals()
    for i in range(no):
        # load the ini file situated in the current wc
        interp.setup(cgi, argv=[filename] + rest_of_args)
        if bc is None:
            return 1
        # The script originally called is considered an "included file,"
        # so it will be listed together with the files
        # referenced by include and family.
        interp.cached_files[filename] = bc
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
        except SignalReceived:
            exitcode = 130
        if exitcode:
            return exitcode
        if i < no - 1:
            interp = Interpreter(space, py_space=py_space)
            if ini_data is not None:
                try:
                    load_ini(interp, ini_data)
                except:
                    os.write(2, "error reading `hippy.ini`")
    if gcdump is not None:
        f = os.open(gcdump, os.O_CREAT | os.O_WRONLY, 0777)
        dump_rpy_heap(f)
        os.close(f)
    return exitcode

if __name__ == '__main__':
    from pypy.config.pypyoption import get_pypy_config
    pypy_config = get_pypy_config(translating=False)


    # Enabling all modules takes a while.
    # It also maxes out the recursion limit on OpenBSD, even with a massive
    # recursion limit and stack size set. XXX fix!
    #from pypy.config.pypyoption import enable_allworkingmodules
    #enable_allworkingmodules(pypy_config)

    from pypy.config.pypyoption import enable_translationmodules
    enable_translationmodules(pypy_config)

    from pypy.objspace.std import StdObjSpace as PyStdObjSpace
    py_space = PyStdObjSpace(pypy_config)

    entry_point = mk_entry_point(py_space)
    sys.exit(entry_point(sys.argv))
