from hippy.objects.base import W_Root
from hippy.objects.reference import W_Reference
from hippy import consts
from rpython.rlib import jit


class ArgDesc(object):
    def __init__(self, name, typehint=None, isref=False, default=None):
        self.name = name
        self.typehint = typehint
        self.isref = isref
        self.default = default

    def str(self):
        hint = (self.typehint + ' ') if self.typehint is not None else ''
        ref = '&' if self.isref else ''
        default = (' = ' + self.default.repr()) if self.default is not None else ''
        return '%s%s$%s%s' % (hint, ref, self.name, default)

    def matches(self, other):
        assert isinstance(other, ArgDesc)
        return (self.typehint == other.typehint and self.isref == other.isref)


class ClosureArgDesc(object):
    def __init__(self, name, isref):
        self.name = name
        self.isref = isref


class Signature(object):
    def __init__(self, args):
        self.args = args

    def matches(self, other):
        """ A signature ``self`` matches ``other`` iff every call matching
        ``other`` also matches ``self``. """
        if other is None:
            return True
        assert isinstance(other, Signature)
        self_len = len(self.args)
        other_len = len(other.args)
        if self_len < other_len:
            return False
        for i in range(other_len):
            if not self.args[i].matches(other.args[i]):
                return False
        for i in range(other_len, self_len):
            if self.args[i].default is None:
                return False
        return True

    def str(self):
        args = [arg.str() for arg in self.args]
        return '(%s)' % ', '.join(args)


class W_Constant(W_Root):
    def __init__(self, name):
        self.name = name

    def eval_static(self, space):
        return space.ec.interpreter.locate_constant(self.name)

    def repr(self):
        return self.name


class AbstractFunction(W_Root):
    name = "??"

    _immutable_fields_ = ['name']
    _attrs_ = ('name',)

    def needs_value(self, i):
        return not self.needs_ref(i)

    def needs_ref(self, i):
        raise NotImplementedError("abstract base class")

    def call_args(self, interp, args_w, w_this=None, thisclass=None,
                  closureargs=None):
        raise NotImplementedError("abstract base class")


class Function(AbstractFunction):
    _immutable_fields_ = ['tp[*]', 'names[*]',
                          'defaults_w[*]', 'typehints[*]', 'bytecode',
                          'types[*]']

    def __init__(self, args, closuredecls, typehints, bytecode, static=False):
        self.types      = [tp    for tp, name, w_def in args]
        self.names      = [name  for tp, name, w_def in args]
        self.defaults_w = [w_def for tp, name, w_def in args]
        self.typehints = typehints
        self.bytecode   = bytecode
        self.closuredecls = closuredecls
        self.name = bytecode.name
        self.identifier = bytecode.name.lower()

    def get_names(self):
        return self.names

    def get_identifier(self):
        return self.identifier

    def get_fullname(self):
        w_cls = self.bytecode.method_of_class
        if w_cls is None:
            return self.name
        else:
            return "%s::%s" % (w_cls.name, self.name)

    def get_typehints(self):
        typehints = [None] * len(self.names)
        for i, typehint, _ in self.typehints:
            typehints[i] = typehint
        return typehints

    def get_signature(self):
        args = []
        typehints = self.get_typehints()
        for i in range(len(self.names)):
            name = self.names[i]
            w_default = self.defaults_w[i]
            isref = self.needs_ref(i)
            typehint = typehints[i]
            args.append(ArgDesc(name, typehint, isref, w_default))
        return Signature(args)

    def signature_repr(self):
        return self.get_fullname() + self.get_signature().str()

    def needs_ref(self, i):
        assert i >= 0
        return i < len(self.types) and self.types[i] == consts.ARG_REFERENCE

    @jit.unroll_safe
    def call_args(self, interp, args_w, w_this=None, thisclass=None,
                  closureargs=None):
        from hippy.interpreter import Frame
        from hippy.objects.instanceobject import W_InstanceObject
        # XXX warn if too many arguments and this function does not call
        # func_get_arg() & friends
        if w_this is not None:
            assert isinstance(w_this, W_InstanceObject)
        newframe = Frame(interp, self.bytecode, self, thisclass, w_this)
        newframe.args_w = args_w  # save it for later, for func_get_args
        nb_args = len(args_w)
        for i in range(len(self.types)):
            if i < nb_args:
                # this argument was provided
                w_argument = args_w[i]
                if self.needs_value(i) and isinstance(w_argument, W_Reference):
                    w_argument = w_argument.deref()
            else:
                arg = self.defaults_w[i]
                if arg is None:
                    interp.warn("Missing argument %d for %s()" %
                                  (i + 1, self.get_fullname()))
                    interp.notice("Undefined variable: %s" %
                                    (self.names[i]))
                    w_argument = interp.space.w_Null
                else:
                    w_argument = arg.eval_static(interp.space)
            newframe.vars_w[i] = w_argument
        if closureargs is not None:
            assert len(closureargs) == len(self.closuredecls)
            cl_start = len(self.types)
            if self.bytecode.this_var_num >= 0:
                cl_start += 1
            for i, decl in enumerate(self.closuredecls):
                r_var = closureargs[i]
                if not isinstance(r_var, W_Reference):
                    r_var = W_Reference(r_var)
                newframe.vars_w[cl_start + i] = r_var
        w_res = interp.interpret(newframe)
        assert w_res is not None
        return w_res
