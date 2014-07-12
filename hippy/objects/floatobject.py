import sys
from hippy.objects.base import W_Object
from hippy.objects.support import _new_binop
from hippy.consts import BINOP_LIST, BINOP_COMPARISON_LIST
from rpython.rlib.rarithmetic import intmask, ovfcheck
from rpython.rlib.rfloat import isnan, isinf, double_to_string, DTSF_CUT_EXP_0


MAX_PRECISION = 500


class W_FloatObject(W_Object):
    _immutable_fields_ = ['floatval']

    supports_arithmetics = True

    def __init__(self, floatval):
        assert isinstance(floatval, float)
        self.floatval = floatval

    def __eq__(self, other):
        """ For testing """
        return (isinstance(other, W_FloatObject) and
                self.floatval == other.floatval)

    def _truncate(self, space):
        try:
            intval = ovfcheck(int(self.floatval))
        except OverflowError:
            intval = 0
        return space.newint(intval)

    def as_number(self, space):
        return self

    def str(self, space, quiet=False):
        prec = space.ec.interpreter.config.get_precision() or 10
        # Zend does that:
        if prec > MAX_PRECISION:
            prec = MAX_PRECISION
        return self._repr(prec)

    def repr(self):
        return self._repr()

    def _repr(self, prec=14):
        _str, _ = double_to_string(self.floatval, "G", prec, DTSF_CUT_EXP_0)
        if 'E' in _str and '.' not in _str:
            a, b = _str.split('E')
            return a + '.0E' + b
        return _str

    def dump(self):
        return str(self.floatval)

    def int_w(self, space):
        if isnan(self.floatval):
            result = -sys.maxint - 1
            space.ec.hippy_warn("cast float to integer: NaN"
                                " is returned as %d" % result)
            return result
        try:
            result = intmask(int(self.floatval))
        except OverflowError:
            result = 0    # +/- infinity
        if abs(result - self.floatval) > 1.0:
            space.ec.hippy_warn("cast float to integer: value %s overflows"
                                " and is returned as %d"
                                % (self.str(space), result))
        return result

    def float_w(self, space):
        return self.floatval

    def is_true(self, space):
        return self.floatval != 0.0

    def uplus(self, space):
        return self

    def uminus(self, space):
        return space.newfloat(-self.floatval)

    def uplusplus(self, space):
        return space.newfloat(self.floatval + 1)

    def uminusminus(self, space):
        return space.newfloat(self.floatval - 1)

    def bitwise_not(self, space):
        return space.newint(~self.int_w(space))

    def div(self, space, w_other):
        assert isinstance(w_other, W_FloatObject)
        x = self.floatval
        y = w_other.floatval
        if y == 0.:
            space.ec.warn("Division by zero")
            return space.w_False
        return W_FloatObject(x / y)

    def __repr__(self):
        return 'W_FloatObject(%r)' % self.floatval

    def var_dump(self, space, indent, recursion):
        if isinf(self.floatval):
            inf = "%s" % self.floatval
            return "%sfloat(%s)\n" % (indent, inf.upper())
        if isnan(self.floatval):
            return "%sfloat(NAN)\n" % (indent,)
        return "%sfloat(%s)\n" % (indent, self.str(space))

    def var_export(self, space, indent, recursion, suffix):
        if isinf(self.floatval):
            inf = "%s" % self.floatval
            return "%s" % inf.upper()
        if isnan(self.floatval):
            return "NAN"
        out = "%s%s%s" % (indent, self.str(space), suffix)
        return out

    def abs(self, space):
        return W_FloatObject(abs(self.floatval))

    def overflow_convert(self, space):
        return space.wrap(self.float_w(space))

    def eval_static(self, space):
        return self

    def serialize(self, space, builder, memo):
        prec = memo.serialize_precision
        if prec == 0:
            prec = (space.int_w(
                space.ec.interpreter.config.get_ini_w('serialize_precision'))
                or 17)
            memo.serialize_precision = prec
        builder.append("d:")
        builder.append(self._repr(prec=prec))
        builder.append(";")
        return True


for _name in BINOP_LIST:
    if hasattr(W_FloatObject, _name):
        continue
    setattr(W_FloatObject, _name, _new_binop(W_FloatObject, _name,
                                             'floatval',
                                             _name in BINOP_COMPARISON_LIST))
