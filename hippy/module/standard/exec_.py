
from hippy.builtin import wrap
from rpython.rlib.rstring import StringBuilder


@wrap(['interp', str])
def escapeshellarg(interp, arg):
    s = StringBuilder(len(arg) + 2)
    s.append("'")
    for c in arg:
        if c == "'":
            s.append("'")
            s.append("\\")
            s.append("'")
            s.append("'")
        else:
            s.append(c)
    s.append("'")
    return interp.space.wrap(s.build())


@wrap(['interp', str])
def passthru(interp, cmd):
    interp.warn("passthru not implemented")
    return interp.space.w_False
