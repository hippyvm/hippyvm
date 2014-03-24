
""" ctype module - various locale dependant things
"""

from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.rtyper.lltypesystem import rffi

from hippy.builtin import wrap

eci = ExternalCompilationInfo(includes=['ctype.h'])

def external(name, args, result):
    return rffi.llexternal(name, args, result, compilation_info=eci)

def new_func(name):
    c_func = external('is' + name, [rffi.INT], rffi.INT)

    def func(space, s):
        if len(s) == 0:
            return space.w_False
        for c in s:
            if not c_func(ord(c)):
                return space.w_False
        return space.w_True
    func.__name__ = 'ctype_' + name
    return wrap(['space', 'char'], error=None)(func)

for name in ['digit', 'lower', 'upper', 'alpha', 'alnum', 'cntrl',
             'graph', 'print', 'punct', 'space', 'xdigit']:
    globals()['ctype_' + name] = new_func(name)
