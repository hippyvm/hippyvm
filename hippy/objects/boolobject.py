
from hippy.objects.base import W_Object


class W_BoolObject(W_Object):
    _immutable_fields_ = ['boolval']

    supports_arithmetics = True

    def __init__(self, boolval):
        self.boolval = boolval

    def is_true(self, space):
        return self.boolval

    def str(self, space, quiet=False):
        if self.boolval:
            return '1'
        return ''

    def repr(self):
        return 'true' if self.boolval else 'false'

    def as_number(self, space):
        return space.newint(int(self.boolval))

    def int_w(self, space):
        return int(self.boolval)

    def __repr__(self):
        return 'W_BoolObject(%s)' % self.boolval

    def var_dump(self, space, indent, recursion):
        if self.boolval:
            s = '%sbool(true)\n' % indent
        else:
            s = '%sbool(false)\n' % indent
        return s

    def var_export(self, space, indent, recursion, suffix):
        if self.boolval:
            s = '%strue%s' % (indent, suffix)
        else:
            s = '%sfalse%s' % (indent, suffix)
        return s

    def is_empty_value(self):
        return not self.boolval

    def overflow_convert(self, space):
        return self

    def eval_static(self, space):
        return self

    def serialize(self, space, builder, memo):
        builder.append(["b:0;", "b:1;"][self.boolval])
        return True

    def to_py(self, interp):
        return interp.py_space.wrap(interp.space.is_true(self))

    def uplusplus(self, space):
        return self

w_True = W_BoolObject(True)
w_False = W_BoolObject(False)
