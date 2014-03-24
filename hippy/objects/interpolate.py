from hippy.objects.base import W_Object
from rpython.rlib import jit


class W_StrInterpolation(W_Object):
    _immutable_fields_ = ['strings[*]']

    def __init__(self, strings):
        self.strings = strings

    @jit.unroll_safe
    def interpolate(self, space, frame, bytecode, n):
        r = []
        c = 0
        for s in self.strings:
            if s is None:
                s = space.str_w(space.as_string(
                        frame.peek_nth(n - c - 1)))
                c += 1
            r.append(s)
        frame.pop_n(c)
        return space.newstr(''.join(r))
