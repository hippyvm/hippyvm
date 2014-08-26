from rpython.rlib.rstring import StringBuilder
from rpython.rlib.rfile import create_popen_file

from hippy.objects.nullobject import w_Null
from hippy.builtin import wrap, Optional, ExitFunctionWithError


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


@wrap(['interp', str, Optional('reference'), Optional('reference')],
      error=False, name='exec')
def exec_(interp, cmd, r_output=None, r_return_var=None):
    space = interp.space
    if not cmd:
        raise ExitFunctionWithError('Cannot execute a blank command')
    if r_output is not None:
        if not space.is_array(r_output.deref_temp()):
            r_output.store(space.new_array_from_list([]))
        w_output = r_output.deref_unique()
    else:
        w_output = None
    try:
        pfile = create_popen_file(cmd, 'r')
    except OSError:
        raise ExitFunctionWithError('Unable to fork [%s]' % cmd, w_Null)
    last_line = ''
    while True:
        line = pfile.readline()
        if not line:
            break
        last_line = line.rstrip()
        if w_output:
            w_output.appenditem_inplace(space, space.newstr(last_line))
    exitcode = pfile.close()
    if r_return_var is not None:
        r_return_var.store(space.wrap(exitcode))
    return space.newstr(last_line)


@wrap(['interp', str, Optional('reference')], error=False)
def passthru(interp, cmd, r_return_var=None):
    space = interp.space
    if not cmd:
        raise ExitFunctionWithError('Cannot execute a blank command')
    try:
        pfile = create_popen_file(cmd, 'r')
    except OSError:
        raise ExitFunctionWithError('Unable to fork [%s]' % cmd, w_Null)
    last_line = ''
    while True:
        line = pfile.read()
        if not line:
            break
        interp.writestr(line, buffer=False)
    exitcode = pfile.close()
    if r_return_var is not None:
        r_return_var.store(space.wrap(exitcode))
    return space.newstr(last_line)


@wrap(['interp', str, Optional('reference')], error=False)
def system(interp, cmd, r_return_var=None):
    space = interp.space
    if not cmd:
        raise ExitFunctionWithError('Cannot execute a blank command')
    try:
        pfile = create_popen_file(cmd, 'r')
    except OSError:
        raise ExitFunctionWithError('Unable to fork [%s]' % cmd, w_Null)
    last_line = ''
    while True:
        line = pfile.readline()
        if not line:
            break
        interp.writestr(line, buffer=True)
        last_line = line
    exitcode = pfile.close()
    if r_return_var is not None:
        r_return_var.store(space.wrap(exitcode))
    return space.newstr(last_line.rstrip())


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
