"""
The data structures defined here are Python objects which in some way
wrap PHP objects for use within Python programs.
"""

from pypy.interpreter.baseobjspace import W_Root
from pypy.interpreter.typedef import TypeDef
from pypy.interpreter.gateway import interp2app, unwrap_spec
from pypy.interpreter.function import Function as Py_Function
from pypy.interpreter.argument import Arguments
from pypy.objspace.std.listobject import (ListStrategy, EmptyListStrategy,
        AbstractUnwrappedStrategy, W_ListObject as WPy_ListObject)

from hippy.module.pypy_bridge.conversion import php_to_py, py_to_php
from hippy.objects.base import W_Root as WPHP_Root

from rpython.rlib import jit, rerased
from rpython.rlib.objectmodel import import_from_mixin

class W_EmbeddedPHPFunc(W_Root):
    """ A Python callable that actually executes a PHP function """
    def __init__(self, space, wph_func):
        self.space = space
        self.wph_func = wph_func

    def get_wrapped_php_obj(self):
        return self.wph_func

    def get_php_interp(self):
        return self.space.get_php_interp()

    @property
    def name(self):
        return self.wph_func.name

    def descr_call(self, __args__):
        (args, kwargs) = __args__.unpack()

        # PHP has no equivalent to keyword arguments.
        # For now if the user passes any kwargs, we crap out.
        # XXX raise PHP exception
        assert not kwargs

        pyspace = self.space
        php_interp = self.space.get_php_interp()
        phspace = self.space.get_php_interp().space

        wph_args_elems = [ py_to_php(php_interp, x) for x in args ]
        res = self.wph_func.call_args(php_interp, wph_args_elems)

        return php_to_py(php_interp, res)

W_EmbeddedPHPFunc.typedef = TypeDef("EmbeddedPHPFunc",
    __call__ = interp2app(W_EmbeddedPHPFunc.descr_call),
)



class W_PhBridgeProxy(W_Root):
    """ Wraps up a PHP instance and offers a Python friendly interface. """

    def __init__(self, interp, wph_inst):
        self.wph_inst = wph_inst
        self.interp = interp

    def get_wrapped_php_obj(self):
        return self.wph_inst

    def get_php_interp(self):
        return self.interp

    # XXX unwrap spec
    def descr_get(self, w_name):
        """ Python is asking for an attribute of a proxied PHP object """
        phspace, pyspace = self.interp.space, self.interp.pyspace

        name = pyspace.str_w(w_name)

        wph_target = self.wph_inst.getattr(
                self.interp,
                name,
                phspace.getclass(self.wph_inst)
        )

        # If we didn't find the thing we are looking for, there is a good
        # chance that it is a method of a class. Presumably since methods
        # are not 1st class in PHP, you can't access them via getattr.
        # We instead go poking around inside the class.
        if wph_target is phspace.w_Null:
            try:
                wph_meth = self.interp.space.getclass(self.wph_inst).methods[name]
            except KeyError:
                assert False # XXX raise exception

            wph_target = wph_meth.bind(self.wph_inst, phspace.getclass(self.wph_inst))

        return php_to_py(self.interp, wph_target)

    @jit.unroll_safe
    def descr_call(self, __args__):
        wpy_args, wpy_kwargs = __args__.unpack()
        assert not wpy_kwargs # XXX exception

        wph_args_elems = [ py_to_php(self.interp, x) for x in wpy_args ]
        wph_rv = self.wph_inst.call_args(self.interp, wph_args_elems)
        return php_to_py(self.interp, wph_rv)

    def descr_eq(self, space, w_other):
        if not space.eq_w(space.type(self), space.type(w_other)):
            return space.w_False
        w_other = space.interp_w(W_PhBridgeProxy, w_other)
        eq = self.interp.space.eq_w(self.wph_inst, w_other.wph_inst)
        return space.wrap(eq)

    def descr_ne(self, space, w_other):
        return space.not_(self.descr_eq(space, w_other))


W_PhBridgeProxy.typedef = TypeDef("PhBridgeProxy",
    __call__ = interp2app(W_PhBridgeProxy.descr_call),
    __getattr__ = interp2app(W_PhBridgeProxy.descr_get),
    __eq__ = interp2app(W_PhBridgeProxy.descr_eq),
    __ne__ = interp2app(W_PhBridgeProxy.descr_ne),
)


def make_wrapped_php_array(interp, wphp_arry):
    if interp.space.arraylen(wphp_arry) <= 0:
        strategy = interp.pyspace.fromcache(EmptyListStrategy)
        storage = strategy.erase(None)
    else:
        strategy = interp.pyspace.fromcache(WrappedPHPArrayStrategy)
        storage = strategy.erase(wphp_arry.as_list_w())

    return WPy_ListObject.from_storage_and_strategy(
            interp.pyspace, storage, strategy)

class WrappedPHPArrayStrategy(ListStrategy):
    """ Wrapping of a PHP list is implemented as a PyPy list strategy """
    import_from_mixin(AbstractUnwrappedStrategy)

    _none_value = None

    def wrap(self, wphp_val):
        return php_to_py(self.space.get_php_interp(), wphp_val)

    erase, unerase = rerased.new_erasing_pair("PHP_Array")
    erase = staticmethod(erase)
    unerase = staticmethod(unerase)

    def is_correct_type(self, w_obj):
        return isinstance(w_obj, WPHP_Root)

    def list_is_correct_type(self, w_list):
        return w_list.strategy is self.space.fromcache(WrappedPHPArrayStrategy)

    def sort(self, w_list, reverse):
        raise NotImplementedError("xxx") # XXX

    def getitems_php(self, w_list):
        raise NotImplementedError("xxx") # XXX

    def _extend_from_list(self, w_list, w_other):
        raise NotImplementedError("xxx") # XXX

    def setslice(self, w_list, start, step, slicelength, w_other):
        raise NotImplementedError("xxx") # XXX
