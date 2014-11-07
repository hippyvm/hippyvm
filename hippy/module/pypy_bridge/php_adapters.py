"""
The data structures defined here are Python objects which in some way
wrap PHP objects for use within Python programs.
"""

from pypy.interpreter.baseobjspace import W_Root
from pypy.interpreter.typedef import TypeDef
from pypy.interpreter.gateway import interp2app, unwrap_spec
from pypy.interpreter.function import Function as Py_Function
from pypy.interpreter.argument import Arguments
from pypy.interpreter.error import OperationError

from hippy.objects.reference import W_Reference
from hippy.klass import def_class
from hippy.builtin import wrap_method
from hippy.error import Throw, VisibilityError
from hippy.module.pypy_bridge.util import _raise_py_bridgeerror

from rpython.rlib import jit, rerased

class W_PHPGenericAdapter(W_Root):
    """Generic adapter for PHP objects in Python.
    Used when no more specific adapter is available."""

    _immutable_fields_ = ["interp", "w_php_ref"]

    def __init__(self, interp, w_php_ref):
        self.w_php_ref = w_php_ref
        self.interp = interp

    def get_wrapped_php_obj(self):
        return self.w_php_ref

    def get_php_interp(self):
        return self.interp

    def to_php(self, php_interp):
        return self.w_php_ref.deref()

    def is_w(self, space, other):
        if isinstance(other, W_PHPGenericAdapter):
            return self.w_php_ref is other.w_php_ref
        return False

    @unwrap_spec(name=str)
    def descr_get(self, name):
        """Python is asking for an attribute of a proxied PHP object"""
        interp = self.interp
        php_space = interp.space
        py_space = interp.py_space

        w_php_val = self.w_php_ref.deref_temp()
        w_php_target = w_php_val.getattr(interp, name, None, fail_with_none=True)

        if w_php_target is None:
            try:
                w_php_target = w_php_val.getmeth(php_space, name, None)
            except VisibilityError:
                w_php_target = None

            if w_php_target is None:
                _raise_py_bridgeerror(py_space,
                        "Wrapped PHP instance has no attribute '%s'" % name)
        return w_php_target.to_py(interp)

    @unwrap_spec(name=str)
    def descr_set(self, name, w_obj):
        interp = self.interp
        php_space = self.interp.space
        py_space = self.interp.py_space

        w_php_val = self.w_php_ref.deref_temp()
        w_php_val.setattr(interp, name, w_obj.to_php(interp), None)

        return py_space.w_None

    @jit.unroll_safe
    def descr_call(self, __args__):
        w_py_args, w_py_kwargs = __args__.unpack()

        if w_py_kwargs:
            _raise_py_bridgeerror(self.interp.py_space,
                    "Cannot use kwargs with callable PHP instances")

        w_php_callable = self.w_php_ref.deref_temp().get_callable()
        if w_php_callable is None: # not callable
            _raise_py_bridgeerror(self.interp.py_space,
                    "Wrapped PHP instance is not callable")

        w_php_args_elems = [ x.to_php(self.interp) for x in w_py_args ]
        w_php_rv = w_php_callable.call_args(self.interp, w_php_args_elems)
        return w_php_rv.to_py(self.interp)

    def _descr_generic_unop(self, space, name):
        interp = self.interp
        php_space = interp.space
        w_php_val = self.w_php_ref.deref_temp()
        try:
            w_php_target = \
                    w_php_val.getmeth(php_space, name, None)
        except VisibilityError:
            _raise_py_bridgeerror(interp.py_space,
                    "Wrapped PHP instance has no %s method" % name)
        else:
            return w_php_target.call_args(interp, []).to_py(interp)

    def descr_str(self, space):
        return self._descr_generic_unop(space, "__toString")

    def _descr_generic_binop(self, space, w_other, name):
        interp = self.interp
        php_space = interp.space
        w_php_val = self.w_php_ref.deref_temp()
        try:
            w_php_target = w_php_val.getmeth(php_space, name, None)
        except VisibilityError:
            _raise_py_bridgeerror(interp.py_space,
                    "Wrapped PHP instance has no %s method" % name)
        else:
            return w_php_target.call_args(interp, [w_other.to_php(interp)]).to_py(interp)

    def descr_add(self, space, w_other):
        return self._descr_generic_binop(space, w_other, "__add__")

    def descr_sub(self, space, w_other):
        return self._descr_generic_binop(space, w_other, "__sub__")

    def descr_mul(self, space, w_other):
        return self._descr_generic_binop(space, w_other, "__mul__")

    def descr_floordiv(self, space, w_other):
        return self._descr_generic_binop(space, w_other, "__floordiv__")

    def descr_mod(self, space, w_other):
        return self._descr_generic_binop(space, w_other, "__mod__")

    def descr_divmod(self, space, w_other):
        return self._descr_generic_binop(space, w_other, "__divmod__")

    def descr_pow(self, space, w_other):
        return self._descr_generic_binop(space, w_other, "__pow__")

    def descr_lshift(self, space, w_other):
        return self._descr_generic_binop(space, w_other, "__lshift__")

    def descr_rshift(self, space, w_other):
        return self._descr_generic_binop(space, w_other, "__rshift__")

    def descr_and(self, space, w_other):
        return self._descr_generic_binop(space, w_other, "__and__")

    def descr_xor(self, space, w_other):
        return self._descr_generic_binop(space, w_other, "__xor__")

    def descr_or(self, space, w_other):
        return self._descr_generic_binop(space, w_other, "__or__")

    def descr_eq(self, space, w_other):
        if isinstance(w_other, W_PHPGenericAdapter):
            php_interp = self.interp
            php_space = php_interp.space
            if php_space.eq_w(self.w_php_ref, w_other.w_php_ref):
                return space.w_True
        return space.w_False

    def descr_ne(self, space, w_other):
        return space.not_(self.descr_eq(space, w_other))

W_PHPGenericAdapter.typedef = TypeDef("PHPGenericAdapter",
    __call__ = interp2app(W_PHPGenericAdapter.descr_call),
    __getattr__ = interp2app(W_PHPGenericAdapter.descr_get),
    __setattr__ = interp2app(W_PHPGenericAdapter.descr_set),
    __str__ = interp2app(W_PHPGenericAdapter.descr_str),
    __add__ = interp2app(W_PHPGenericAdapter.descr_add),
    __sub__ = interp2app(W_PHPGenericAdapter.descr_sub),
    __mul__ = interp2app(W_PHPGenericAdapter.descr_mul),
    __floordiv__ = interp2app(W_PHPGenericAdapter.descr_floordiv),
    __mod__ = interp2app(W_PHPGenericAdapter.descr_mod),
    __divmod__ = interp2app(W_PHPGenericAdapter.descr_divmod),
    __pow__ = interp2app(W_PHPGenericAdapter.descr_pow),
    __lshift__ = interp2app(W_PHPGenericAdapter.descr_lshift),
    __rshift__ = interp2app(W_PHPGenericAdapter.descr_rshift),
    __and__ = interp2app(W_PHPGenericAdapter.descr_and),
    __xor__ = interp2app(W_PHPGenericAdapter.descr_xor),
    __or__ = interp2app(W_PHPGenericAdapter.descr_or),
    __eq__ = interp2app(W_PHPGenericAdapter.descr_eq),
    __ne__ = interp2app(W_PHPGenericAdapter.descr_ne),
)

class W_PHPClassAdapter(W_Root):
    _immutable_fields_ = ["interp", "w_php_cls"]

    def __init__(self, interp, w_php_cls):
        """Note this does NOT wrap a reference.
        The reason for this is that classes are not first class in PHP and
        building a reference to a one upsets HippyVM"""
        self.w_php_cls = w_php_cls
        self.interp = interp

    def get_wrapped_php_obj(self):
        return self.w_php_cls

    def get_php_interp(self):
        return self.interp

    def to_php(self, php_interp):
        # Classes are not first class in PHP, so this would make no sense.
        assert(False)

    def is_w(self, space, other):
        if isinstance(other, W_PHPClassAdapter):
            return self.w_php_cls is other.w_php_cls
        return False

    @jit.unroll_safe
    def descr_call(self, __args__):
        w_py_args, w_py_kwargs = __args__.unpack()

        if w_py_kwargs:
            _raise_py_bridgeerror(self.interp.py_space,
                    "Cannot use kwargs with callable PHP instances")

        w_php_args_elems = [ x.to_php(self.interp) for x in w_py_args ]
        w_php_rv = self.w_php_cls.call_args(self.interp, w_php_args_elems)
        return w_php_rv.to_py(self.interp)

W_PHPClassAdapter.typedef = TypeDef("PHPClassAdapter",
    __call__ = interp2app(W_PHPClassAdapter.descr_call),
)

class W_PHPFuncAdapter(W_Root):
    """A Python callable that actually executes a PHP function"""

    _immutable_fields_ = ["space", "w_php_func"]

    def __init__(self, space, w_php_func):
        """Note this does NOT wrap a reference.
        The reason for this is that functions are not first class in PHP and
        building a reference to a one upsets HippyVM"""
        self.space = space
        self.w_php_func = w_php_func
        self.w_phpexception = space.builtin.get("PHPException")

    def get_wrapped_php_obj(self):
        return self.w_php_func

    def get_php_interp(self):
        return self.space.get_php_interp()

    def is_w(self, space, other):
        if isinstance(other, W_PHPFuncAdapter):
            return self.w_php_func is other.w_php_func
        return False

    @property
    def name(self):
        return self.w_php_func.name

    @jit.unroll_safe
    def descr_call(self, __args__):
        (args, kwargs) = __args__.unpack()

        # PHP has no equivalent to keyword arguments.
        if kwargs:
            _raise_py_bridgeerror(self.space,
                    "Cannot use kwargs when calling PHP functions")

        py_space = self.space
        php_interp = self.space.get_php_interp()
        php_space = php_interp.space

        w_php_args_elems = []
        for arg_no in xrange(len(args)):
            w_py_arg = args[arg_no]

            if self.w_php_func.needs_ref(arg_no):
                # if you try to pass a reference argument by value, fail.
                if not isinstance(w_py_arg, W_PHPRefAdapter):
                    err_str = "Arg %d of PHP func '%s' is pass by reference" % \
                            (arg_no + 1, self.w_php_func.name)
                    _raise_py_bridgeerror(py_space, err_str)

                w_php_args_elems.append(w_py_arg.w_php_ref)
            else:
                # if you pass a value argument by reference, fail.
                if isinstance(w_py_arg, W_PHPRefAdapter):
                    err_str = "Arg %d of PHP func '%s' is pass by value" % \
                            (arg_no + 1, self.w_php_func.name)
                    _raise_py_bridgeerror(py_space, err_str)

                w_php_args_elems.append(w_py_arg.to_php(php_interp))

        try:
            res = self.w_php_func.call_args(php_interp, w_php_args_elems)
        except Throw as w_php_throw:
            w_php_exn = w_php_throw.w_exc
            raise OperationError(
                    self.w_phpexception, w_php_exn.to_py(php_interp))

        return res.to_py(php_interp)

W_PHPFuncAdapter.typedef = TypeDef("PHPFunc",
    __call__ = interp2app(W_PHPFuncAdapter.descr_call),
)

class W_PHPRefAdapter(W_Root):
    """Represents a PHP reference (for call by reference Py->PHP only) """

    def __init__(self, space, w_php_ref):
        # XXX make it accept interp XXX
        assert isinstance(w_php_ref, W_Reference)
        self.w_php_ref = w_php_ref
        self.py_space = space
        self.interp = space.get_php_interp() # XXX

    def deref(self):
        return self.w_php_ref.deref().to_py(self.py_space.get_php_interp())

    @staticmethod
    def descr_new(space, w_type, w_py_val):
        w_php_val = w_py_val.to_php(space.get_php_interp())
        if isinstance(w_php_val, W_Reference):
            w_php_ref = w_php_val # already a reference
        else:
            w_php_ref = W_Reference(w_php_val)

        w_py_obj = space.allocate_instance(W_PHPRefAdapter, w_type)
        w_py_obj.__init__(space, w_php_ref)
        return w_py_obj

    #@unwrap_spec(name=str)
    def descr_get(self, w_py_name):
        interp = self.interp
        php_space = interp.space
        py_space = self.py_space

        w_php_ref = self.w_php_ref
        w_py_new_val = w_php_ref.to_py(interp)

        # We have to wrap in a generic fashion even for strings, so that
        # reference can observe any mutations (e.g. strings).
        from hippy.module.pypy_bridge.py_adapters import (
                W_PyGenericAdapter, k_PyGenericAdapter)
        w_php_val = W_PyGenericAdapter(k_PyGenericAdapter, [])
        w_php_val.setup_instance(interp, w_py_new_val)

        w_php_ref.store(w_php_val)
        return py_space.getattr(w_py_new_val, w_py_name)

    def descr_setitem(self, w_py_key, w_py_val):
        interp = self.interp
        self.w_php_ref.setitem_ref(interp.space,
                w_py_key.to_php(interp), w_py_val.to_php(interp))

    def descr_as_list(self, space):
        from hippy.objects.arrayobject import W_ArrayObject
        w_php_ref = self.w_php_ref
        assert isinstance(w_php_ref.deref_temp(), W_ArrayObject) # XXX exception
        w_py_val = w_php_ref.to_py(self.interp)
        w_py_as_list = space.getattr(w_py_val, space.wrap("as_list"))
        from pypy.interpreter.argument import Arguments
        return space.call_args(w_py_as_list, Arguments(space, []))

W_PHPRefAdapter.typedef = TypeDef("PHPRef",
    __new__ = interp2app(W_PHPRefAdapter.descr_new),
    __getattr__ = interp2app(W_PHPRefAdapter.descr_get),
    __setitem__ = interp2app(W_PHPRefAdapter.descr_setitem),
    as_list = interp2app(W_PHPRefAdapter.descr_as_list),
    deref = interp2app(W_PHPRefAdapter.deref),
)

