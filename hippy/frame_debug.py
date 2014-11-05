"""
Tooling to help understand the contents of the frame
"""

from hippy.builtin import wrap
from hippy.objects.reference import W_Reference
from rpython.rlib.objectmodel import compute_unique_id
from rpython.rlib import jit

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
        if isinstance(content, W_Reference):
            val = content.deref_temp()
            #unique_str = " (unique)" if content._unique else ""
            ident = the_id(val)
            #print("%s: Ref%s -> %s @ %s" %
            #        (name, unique_str, val, ident))
        else:
            ident = the_id(content)
            #print("%s: %s @ %s" % (name, content, ident))
