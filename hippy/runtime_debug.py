"""
Tooling to help understand the contents of the frame
"""

from hippy.builtin import wrap
from hippy.objects.reference import W_Reference
from rpython.rlib.objectmodel import compute_unique_id
from rpython.rlib import jit

@wrap(['interp'])
def bc_dump(interp):
    bc = interp.topframeref().bytecode

    print("\nBYTECODE DUMP IN FUNCTION: %s" % bc.name)
    print(72 * "=")
    print("")
    bc.show()

@jit.dont_look_inside
def the_id(x): return compute_unique_id(x)

@wrap(['interp'])
def frame_dump(interp):
    frame = interp.topframeref()
    bc = frame.bytecode

    print("\nFRAME DUMP IN FUNCTION: %s" % bc.name)
    print(72 * "=")
    print("")

    print("Variables")
    print("---------")
    for name in bc.varnames:
        idx = bc.var_to_pos[name]
        content = frame.vars_w[idx]
        print("%s: %s" % (name, content))
