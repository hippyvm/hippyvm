import sys, struct
from rpython.rlib import jit
from rpython.rlib.rarithmetic import ovfcheck, intmask
from hippy.objects.base import W_Object
from hippy.objects.support import _new_binop
from hippy.consts import BINOP_LIST, BINOP_COMPARISON_LIST

SYS_MAXINT_PLUS_1 = float(sys.maxint+1)
SYS_MININT_MINUS_1 = float(-sys.maxint-2)


@jit.elidable
def hash_int(v, l=[0]*20):
    """The algorithm behind compute_hash() for a string or a unicode."""
    i = 0
    while v:
        l[i] = (v % 10) + ord('0')
        v /= 10
        i += 1
    x = l[i - 1] << 7
    for k in range(i - 1, -1, -1):
        x = intmask((1000003*x) ^ l[k])
    x ^= i
    return intmask(x)


class W_IntObject(W_Object):
    _immutable_fields_ = ['intval']

    supports_arithmetics = True

    def __init__(self, intval):
        assert isinstance(intval, int)   # and not 'long'!
        self.intval = intval

    def __eq__(self, other):
        """ For testing """
        return isinstance(other, W_IntObject) and self.intval == other.intval

    def int_w(self, space):
        return self.intval

    def float_w(self, space):
        return float(self.intval)

    def as_number(self, space):
        return self

    def as_stringoffset(self, space, give_notice):
        return self.intval

    def str(self, space, quiet=False):
        return str(self.intval)

    def repr(self):
        return str(self.intval)

    def div(self, space, w_other):
        assert isinstance(w_other, W_IntObject)
        x = self.intval
        y = w_other.intval
        if y == 0:
            space.ec.warn("Division by zero")
            return space.w_False
        try:
            z = ovfcheck(x % y)
        except OverflowError:
            z = 1
        if z == 0:
            try:
                return space.newint(ovfcheck(x // y))
            except OverflowError:
                return space.newfloat(float(x) / float(y))
        else:
            return space.newfloat(float(x) / float(y))

    def is_true(self, space):
        return self.intval != 0

    def uplus(self, space):
        return self

    def uminus(self, space):
        try:
            return space.newint(ovfcheck(-self.intval))
        except OverflowError:
            return space.newfloat(-float(self.intval))

    def uplusplus(self, space):
        try:
            v = ovfcheck(self.intval + 1)
        except OverflowError:
            return space.newfloat(SYS_MAXINT_PLUS_1)
        return space.newint(v)

    def uminusminus(self, space):
        try:
            v = ovfcheck(self.intval - 1)
        except OverflowError:
            return space.newfloat(SYS_MININT_MINUS_1)
        return space.newint(v)

    def bitwise_not(self, space):
        return space.newint(~self.intval)

    def hash(self, space):
        return hash_int(self.intval)

    def __repr__(self):
        return 'W_IntObject(%s)' % self.intval

    def var_dump(self, space, indent, recursion):
        return '%sint(%d)\n' % (indent, self.intval)

    def var_export(self, space, indent, recursion, suffix):
        return '%s%d%s' % (indent, self.intval, suffix)

    def abs(self, space):
        if self.intval < 0:
            return self.uminus(space)
        else:
            return self

    def add(self, space, w_other):
        assert isinstance(w_other, W_IntObject)
        x = self.intval
        y = w_other.intval
        try:
            z = ovfcheck(x + y)
        except OverflowError:
            return space.newfloat(float(x) + float(y))
        return W_IntObject(z)

    def sub(self, space, w_other):
        assert isinstance(w_other, W_IntObject)
        x = self.intval
        y = w_other.intval
        try:
            z = ovfcheck(x - y)
        except OverflowError:
            return space.newfloat(float(x) - float(y))
        return W_IntObject(z)

    def mul(self, space, w_other):
        assert isinstance(w_other, W_IntObject)
        x = self.intval
        y = w_other.intval
        try:
            z = ovfcheck(x * y)
        except OverflowError:
            return space.newfloat(float(x) * float(y))
        return W_IntObject(z)

    def overflow_convert(self, space):
        return self

    def serialize(self, space, builder, memo):
        builder.append("i:%d;" % self.intval)
        return True

    def ll_serialize(self, builder):
        builder.append("i")
        builder.append(struct.pack("l", self.intval))

    def eval_static(self, space):
        return self


for _name in BINOP_LIST:
    if hasattr(W_IntObject, _name):
        continue
    setattr(W_IntObject, _name, _new_binop(W_IntObject, _name,
                                           'intval',
                                           _name in BINOP_COMPARISON_LIST))
