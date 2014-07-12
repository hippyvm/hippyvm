#!/usr/bin/env python2.7
#
# Dumps the bytecode for the given script.

import sys, os

try:
    import rpython
except ImportError:
    print("Cannot import rpython. Put PyPy source tree in PYTHONPATH.")
    sys.exit(1)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def dump_bytecode(bc):

    def dump_idx_list(label, ls):
        print("  %s:" % label)
        for i in range(len(ls)):
            print("    %d: %s" % (i, repr(ls[i])))
        print("")

    def dump_code(bc):
        print("  code:")
        bc.show()
        print("")

    print("\n>>>>> Function: <main>\n")
    dump_idx_list("names", bc.names)
    dump_idx_list("consts", bc.consts)
    dump_idx_list("varnames", bc.varnames)
    dump_code(bc)

    for f in bc.functions:
        print(">>>>> Function: %s\n" % f.name)
        dump_idx_list("names", f.bytecode.names)
        dump_idx_list("consts", f.bytecode.consts)
        dump_idx_list("varnames", f.bytecode.varnames)
        dump_code(f.bytecode)

    for c in bc.classes:
        for meth_name, meth in c.method_decl.items():
            print(">>>>> Method: %s::%s\n" % (c.name, meth_name))
            dump_idx_list("names", meth.func.bytecode.names)
            dump_idx_list("consts", meth.func.bytecode.consts)
            dump_idx_list("varnames", meth.func.bytecode.varnames)
            dump_code(meth.func.bytecode)

def main(filename):
    from hippy.objspace import getspace
    from hippy.interpreter import Interpreter

    space = getspace()
    interp = Interpreter(space)

    absname = os.path.abspath(filename)

    try:
        bc = space.bytecode_cache.compile_file(absname, space)
    except:
        print "Error opening %s" % filename
        sys.exit(1)

    dump_bytecode(bc)

if __name__ == '__main__':
    try:
        fname = sys.argv[1]
    except:
        print("usage: dis.py <script>")
        sys.exit(1)

    main(fname)
