from hippy.objects.base import W_Object


class W_NullObject(W_Object):
    supports_arithmetics = True

    def is_true(self, space):
        return False

    def as_number(self, space):
        return space.wrap(0)

    def str(self, space, quiet=False):
        return ""

    def repr(self):
        return 'NULL'

    def int_w(self, space):
        return 0

    def var_dump(self, space, indent, recursion):
        return "%sNULL\n" % indent

    def var_export(self, space, indent, recursion, suffix):
        return '%sNULL%s' % (indent, suffix)

    def uplusplus(self, space):
        return space.newint(1)

    def getitem(self, space, w_arg, give_notice=False):
        return space.w_Null

    def is_empty_value(self):
        return True

    def overflow_convert(self, space):
        return self

    def eval_static(self, space):
        return self

    def serialize(self, space, builder, memo):
        builder.append("N;")
        return True

    def to_py(self, interp, w_php_ref=None):
        return interp.py_space.w_None

w_Null = W_NullObject()
