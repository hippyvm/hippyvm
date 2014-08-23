from rpython.rlib.rstring import StringBuilder
from rpython.rlib.rfile import create_popen_file

from hippy.objects.nullobject import w_Null
from hippy.builtin import wrap


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

@wrap(['interp', str])
def shell_exec(interp, cmd):
    try:
        r_pfile = create_popen_file(cmd, 'r')
    except OSError:
        interp.warn("Unable to execute '%s'" % cmd)
        return w_Null
    res = r_pfile.read(-1)
    if res:
        return interp.space.wrap(res)
    else:
        return w_Null
