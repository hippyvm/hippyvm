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

from rpython.rlib import jit, rerased, unroll


class W_PHPGenericAdapter(W_Root):
    """Generic adapter for PHP objects in Python.
    Used when no more specific adapter is available."""

    _immutable_fields_ = ["interp", "w_php_obj"]

    def __init__(self, interp, w_php_obj):
        assert not isinstance(w_php_obj, W_Reference)
        self.w_php_obj = w_php_obj
        self.interp = interp

    def get_wrapped_php_obj(self):
        return self.w_php_obj

    def get_php_interp(self):
        return self.interp

    def to_php(self, php_interp):
        return self.w_php_obj

    def is_w(self, space, other):
        if isinstance(other, W_PHPGenericAdapter):
            return self.w_php_obj is other.w_php_obj
        return False

    @unwrap_spec(name=str)
    def descr_get(self, name):
        """Python is asking for an attribute of a proxied PHP object"""
        interp = self.interp
        php_space = interp.space
        py_space = interp.py_space

        w_php_val = self.w_php_obj
        # PHP access modifiers are ignored when attributes are
        # accessed from Python.
        w_contextclass = w_php_val.getclass()

        # When we're looking up an attribute, we're in a sticky situation if we
        # look up an array and then mutate it. Calling getattr() would
        # (conceptually) create a copy of the array, so Python's mutations
        # wouldn't show up in PHP. We thus call getattr_ref() which returns a
        # reference to a thingy rather than the thingy itself. Mutation then
        # happens on the reference, and everything looks sensible to both Python
        # and PHP. However, getting a reference to any PHP thingy is slow and,
        # pointless, since most items are immutable (i.e. there's no point
        # getting a reference to a PHP int, because we can't mutate the int). So
        # we add a knob to getattr_ref called only_ref_arrays which only adds a
        # new reference if the attribute we're looking for happens to be an
        # array.
        w_php_target = w_php_val.getattr_ref(interp, name, w_contextclass,
                                         fail_with_none=True, ref_only_arrays=True)
        if w_php_target is None:
            try:
                w_php_target = w_php_val.getmeth(php_space, name, w_contextclass)
            except VisibilityError:
                w_php_target = None

            if w_php_target is None:
                _raise_py_bridgeerror(py_space,
                        "Wrapped PHP instance has no attribute '%s'" % name)

        return w_php_target.to_py(interp)

    @unwrap_spec(name=str)
    def descr_set(self, name, w_obj):
        interp = self.interp
        py_space = self.interp.py_space

        w_php_val = self.w_php_obj
        # PHP access modifiers are ignored when attributes are
        # accessed from Python.
        w_contextclass = w_php_val.getclass()
        w_php_val.setattr(interp, name, w_obj.to_php(interp), w_contextclass)

        return py_space.w_None

    @jit.unroll_safe
    def descr_call(self, __args__):
        if __args__.keywords:
            # PHP has no equivalent to keyword arguments.
            _raise_py_bridgeerror(self.interp.py_space,
                    "Cannot use kwargs with callable PHP instances")
        w_py_args = __args__.arguments_w

        w_php_callable = self.w_php_obj.get_callable()
        if w_php_callable is None: # not callable
            _raise_py_bridgeerror(self.interp.py_space,
                    "Wrapped PHP instance is not callable")

        w_php_args_elems = [ x.to_php(self.interp) for x in w_py_args ]
        w_php_rv = w_php_callable.call_args(self.interp, w_php_args_elems)
        return w_php_rv.to_py(self.interp)

    def _descr_generic_unop(self, name):
        interp = self.interp
        php_space = interp.space
        w_php_val = self.w_php_obj
        try:
            w_php_target = \
                    w_php_val.getmeth(php_space, name, None)
        except VisibilityError:
            _raise_py_bridgeerror(interp.py_space,
                    "Wrapped PHP instance has no %s method" % name)
        else:
            return w_php_target.call_args(interp, []).to_py(interp)

    def descr_str(self, space):
        return self._descr_generic_unop("__toString")

    # equality/disequality
    def descr_eq(self, space, w_other):
        if isinstance(w_other, W_PHPGenericAdapter):
            php_interp = self.interp
            php_space = php_interp.space
            if php_space.eq_w(self.w_php_obj, w_other.w_php_obj):
                return space.w_True
        return space.w_False

    def descr_ne(self, space, w_other):
        return space.not_(self.descr_eq(space, w_other))

W_PHPGenericAdapter.typedef = TypeDef("PHPGenericAdapter",
    __call__ = interp2app(W_PHPGenericAdapter.descr_call),
    __getattr__ = interp2app(W_PHPGenericAdapter.descr_get),
    __setattr__ = interp2app(W_PHPGenericAdapter.descr_set),
    __eq__ = interp2app(W_PHPGenericAdapter.descr_eq),
    __ne__ = interp2app(W_PHPGenericAdapter.descr_ne),
    __str__ = interp2app(W_PHPGenericAdapter.descr_str),
)

class W_PHPClassAdapter(W_Root):
    _immutable_fields_ = ["interp", "w_php_cls"]

    def __init__(self, interp, w_php_cls):
        """Note this does NOT wrap a reference.
        The reason for this is that classes are not first class in PHP and
        building a reference to one upsets HippyVM"""
        self.w_php_cls = w_php_cls
        self.interp = interp

    def get_wrapped_php_obj(self):
        return self.w_php_cls

    def get_php_interp(self):
        return self.interp

    def to_php(self, php_interp):
        # Classes are not first class in PHP, so this would make no sense.
        from hippy.module.pypy_bridge.bridge import _raise_php_bridgeexception
        _raise_php_bridgeexception(self.interp,
               "Cannot convert wrapped PHP class to PHP. Classes are not first class")

    def is_w(self, space, other):
        if isinstance(other, W_PHPClassAdapter):
            return self.w_php_cls is other.w_php_cls
        return False

    @jit.unroll_safe
    def fast_call(self, args):
        w_php_args_elems = [x.to_php(self.interp) for x in args]
        w_php_rv = self.w_php_cls.call_args(self.interp, w_php_args_elems)
        return w_php_rv.to_py(self.interp)

    def descr_call(self, __args__):
        if __args__.keywords:
            # PHP has no equivalent to keyword arguments.
            _raise_py_bridgeerror(self.interp.py_space,
                    "Cannot use kwargs with callable PHP instances")
        return self.fast_call(__args__.arguments_w)

    def descr_getattr(self, w_name):
        py_space = self.interp.py_space
        name = py_space.str_w(w_name)
        w_staticmember = self.w_php_cls.lookup_staticmember(name, None, False)
        if w_staticmember:
            return w_staticmember.value.to_py(self.interp)
        else:
            w_php_const = self.w_php_cls.lookup_w_constant(self.interp.space,
                                                           py_space.str_w(w_name))
            if w_php_const is not None:
                return w_php_const.to_py(self.interp)
            else:
                try:
                    w_php_method = self.w_php_cls.locate_method(name, None)
                    return w_php_method.to_py(self.interp)
                except VisibilityError:
                    _raise_py_bridgeerror(py_space,
                        "Wrapped PHP class has not attribute '%s'" % name)

    def descr_setattr(self, w_name, w_value):
        py_space = self.interp.py_space
        name = py_space.str_w(w_name)
        w_staticmember = self.w_php_cls.lookup_staticmember(name, None, False)
        if w_staticmember:
            w_staticmember.value = w_value.to_php(self.interp)
        else:
            _raise_py_bridgeerror(py_space,
                "Wrapped PHP class has no assignable attribute '%s'" % name)

W_PHPClassAdapter.typedef = TypeDef("PHPClassAdapter",
    __call__ = interp2app(W_PHPClassAdapter.descr_call),
    __getattr__ = interp2app(W_PHPClassAdapter.descr_getattr),
    __setattr__ = interp2app(W_PHPClassAdapter.descr_setattr),
)

class W_PHPFuncAdapter(W_Root):
    """A Python callable that actually executes a PHP function"""

    _immutable_fields_ = ["space", "w_php_func"]

    def __init__(self, space, w_php_func):
        """Note this does NOT wrap a reference.
        The reason for this is that functions are not first class in PHP and
        building a reference to a one upsets HippyVM"""

        # No double wrappings
        from hippy.module.pypy_bridge.py_adapters import W_PyFuncAdapter, W_PyFuncGlobalAdapter
        assert not isinstance(w_php_func, W_PyFuncAdapter) and \
            not isinstance(w_php_func, W_PyFuncGlobalAdapter)

        # compiling python functions inside python makes no sense
        # We catch this before it is called.
        from hippy.module.pypy_bridge.bridge import (
            embed_py_func, embed_py_func_global, embed_py_meth)
        if w_php_func is embed_py_func or \
                w_php_func is embed_py_func_global or \
                w_php_func is embed_py_meth:
            _raise_py_bridgeerror(space,
                                  "Adapting forbidden PHP function")

        self.space = space
        self.w_php_func = w_php_func

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
    def fast_call(self, args):
        py_space = self.space
        php_interp = self.space.get_php_interp()
        w_php_func = self.w_php_func

        w_php_args_elems = [None] * len(args)
        for i, w_py_arg in enumerate(args):
            if w_php_func.needs_ref(i):
                # if you try to pass a reference argument by value, fail.
                if not isinstance(w_py_arg, W_PHPRefAdapter):
                    err_str = "Arg %d of PHP func '%s' is pass by reference" % \
                            (i + 1, w_php_func.name)
                    _raise_py_bridgeerror(py_space, err_str)
                w_php_args_elems[i] = w_py_arg.w_php_ref
            else:
                # if you pass a value argument by reference, fail.
                if isinstance(w_py_arg, W_PHPRefAdapter):
                    err_str = "Arg %d of PHP func '%s' is pass by value" % \
                            (i + 1, w_php_func.name)
                    _raise_py_bridgeerror(py_space, err_str)
                w_php_args_elems[i] = w_py_arg.to_php(php_interp)

        try:
            res = w_php_func.call_args(php_interp, w_php_args_elems)
        except Throw as w_php_throw:
            w_php_exn = w_php_throw.w_exc
            raise OperationError(py_space.builtin.get("PHPException"),
                                 w_php_exn.to_py(php_interp))

        return res.to_py(php_interp)

    def descr_call(self, __args__):
        if __args__.keywords:
            # PHP has no equivalent to keyword arguments.
            _raise_py_bridgeerror(self.space,
                    "Cannot use kwargs when calling PHP functions")
        return self.fast_call(__args__.arguments_w)

    def to_php(self, interp):
        # we can't just unwrap the function, since PHP funcs are
        # not first class.The best we can do is a closure.
        from hippy.objects.closureobject import new_closure
        return new_closure(interp.space, self.w_php_func, None)

W_PHPFuncAdapter.typedef = TypeDef("PHPFunc",
    __call__ = interp2app(W_PHPFuncAdapter.descr_call),
)

class W_PHPUnboundMethAdapter(W_Root):
    """A Python callable that actually executes an unbound PHP method
    When called, we bind the first argument as the instance."""

    _immutable_fields_ = ["space", "w_php_meth"]

    def __init__(self, space, w_php_meth):
        # No double wrappings
        from hippy.module.pypy_bridge.py_adapters import (
            W_PyFuncAdapter, W_PyFuncGlobalAdapter)
        assert not isinstance(w_php_meth, W_PyFuncAdapter) and \
            not isinstance(w_php_meth, W_PyFuncGlobalAdapter)

        self.space = space
        self.w_php_meth = w_php_meth

    def get_wrapped_php_obj(self):
        assert False

    def get_php_interp(self):
        return self.space.get_php_interp()

    def is_w(self, space, other):
        if isinstance(other, W_PHPUnboundMethAdapter):
            return self.w_php_meth is other.w_php_meth
        return False

    @property
    def name(self):
        return self.w_php_meth.get_name()

    @jit.unroll_safe
    def fast_call(self, args):
        py_space = self.space
        php_interp = self.space.get_php_interp()
        if len(args) == 0:
            _raise_py_bridgeerror(py_space, "Call to unbound PHP method " +
                                  "requires at-least one argument (for $this)")

        w_php_meth = self.w_php_meth
        w_php_fst = args[0].to_php(php_interp)
        w_php_bound_meth = w_php_meth.bind(w_php_fst, w_php_fst.getclass())
        w_method_func = w_php_meth.method_func
        w_php_args_elems = [None] * (len(args) - 1)
        for i in range(len(args) - 1):
            w_py_arg = args[i + 1]
            if w_method_func.needs_ref(i):
                # if you try to pass a reference argument by value, fail.
                if not isinstance(w_py_arg, W_PHPRefAdapter):
                    err_str = "Arg %d of PHP func '%s' is pass by reference" % \
                            (i + 1, w_php_meth.get_name())
                    _raise_py_bridgeerror(py_space, err_str)
                w_php_args_elems[i] = w_py_arg.w_php_ref
            else:
                # if you pass a value argument by reference, fail.
                if isinstance(w_py_arg, W_PHPRefAdapter):
                    err_str = "Arg %d of PHP func '%s' is pass by value" % \
                            (i + 1, w_php_meth.get_name())
                    _raise_py_bridgeerror(py_space, err_str)
                w_php_args_elems[i] = w_py_arg.to_php(php_interp)

        try:
            res = w_php_bound_meth.call_args(php_interp, w_php_args_elems)
        except Throw as w_php_throw:
            w_php_exn = w_php_throw.w_exc
            raise OperationError(py_space.builtin.get("PHPException"),
                                 w_php_exn.to_py(php_interp))

        return res.to_py(php_interp)

    def descr_call(self, __args__):
        if __args__.keywords:
            # PHP has no equivalent to keyword arguments.
            _raise_py_bridgeerror(self.space,
                    "Cannot use kwargs when calling PHP functions")
        return self.fast_call(__args__.arguments_w)

    def to_php(self, interp):
        # This doesn't really make sense, so just raise an exception.
        from hippy.objects.closureobject import new_closure
        _raise_py_bridgeerror(self.space, "Cannot unwrap unbound PHP method.")

W_PHPUnboundMethAdapter.typedef = TypeDef("PHPUnboundMeth",
    __call__ = interp2app(W_PHPUnboundMethAdapter.descr_call),
)

class W_PHPRefAdapter(W_Root):
    """Represents a PHP reference (for call by reference Py->PHP only) """

    _immutable_fields_ = ["interp", "w_php_ref"]

    def __init__(self, interp, w_php_ref):
        assert isinstance(w_php_ref, W_Reference)
        self.interp = interp
        self.w_php_ref = w_php_ref

    def get_wrapped_php_obj(self):
        return self.w_php_ref

    def deref(self):
        return self.w_php_ref.deref().to_py(self.interp)

    def store(self, w_py_new_val):
        w_php_val = w_py_new_val.to_php(self.interp)
        self.w_php_ref.store(w_php_val.deref())

    @staticmethod
    def descr_new(space, w_type, w_py_val):
        interp = space.get_php_interp()

        w_php_val = w_py_val.to_php(interp)
        if isinstance(w_php_val, W_Reference):
            w_php_ref = w_php_val # already a reference
        else:
            w_php_ref = W_Reference(w_php_val)

        w_py_obj = space.allocate_instance(W_PHPRefAdapter, w_type)
        w_py_obj.__init__(interp, w_php_ref)
        return w_py_obj

    def to_php(self, interp):
        return self.w_php_ref

w_phprefadapter_typedef = {
    "__new__": interp2app(W_PHPRefAdapter.descr_new),
    "store": interp2app(W_PHPRefAdapter.store),
    "deref": interp2app(W_PHPRefAdapter.deref),
}

W_PHPRefAdapter.typedef = TypeDef("PHPRef", **w_phprefadapter_typedef)
