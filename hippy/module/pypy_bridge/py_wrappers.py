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
from pypy.objspace.std.dictmultiobject import (AbstractTypedStrategy,
      DictStrategy, create_iterator_classes,
      EmptyDictStrategy)
from pypy.objspace.std.dictmultiobject import (
        W_DictMultiObject as WPy_DictMultiObject)

from hippy.module.pypy_bridge.conversion import php_to_py, py_to_php
from hippy.objects.base import W_Root as WPHP_Root

from rpython.rlib import jit, rerased
from rpython.rlib.objectmodel import import_from_mixin

class W_PHPProxyGeneric(W_Root):
    """Generic proxy for wrapping PHP objects in PyPy when no more specific
    proxy is available."""

    _immutable_fields_ = ["interp", "wph_inst"]

    def __init__(self, interp, wph_inst):
        self.wph_inst = wph_inst
        self.interp = interp

    def get_wrapped_php_obj(self):
        return self.wph_inst

    def get_php_interp(self):
        return self.interp

    def is_w(self, space, other):
        if isinstance(other, W_PHPProxyGeneric):
            return self.wph_inst is other.wph_inst
        return False

    # XXX unwrap spec
    def descr_get(self, w_name):
        """ Python is asking for an attribute of a proxied PHP object """
        interp = self.interp
        php_space = interp.space
        py_space = interp.pyspace

        name = py_space.str_w(w_name)
        wph_inst = self.wph_inst
        wph_target = wph_inst.getattr(interp, name, None, fail_with_none=True)

        if wph_target is None:
            # If the attribute wasn't found in wph_inst, it may be a function,
            # which needs to be searched for separately.
            wph_class = php_space.getclass(wph_inst)
            try:
                wph_meth = wph_class.methods[name]
            except KeyError:
                print "can't lookup", name
                assert False # XXX raise exception
            wph_target = wph_meth.bind(wph_inst, wph_class)

        return php_to_py(interp, wph_target)

    # XXX unwrap spec
    def descr_set(self, w_name, w_obj):
        interp = self.interp
        php_space = self.interp.space
        py_space = self.interp.pyspace

        name = py_space.str_w(w_name)
        wph_inst = self.wph_inst
        self.wph_inst.setattr(interp, name, py_to_php(interp, w_obj), None)

        return py_space.w_None

    @jit.unroll_safe
    def descr_call(self, __args__):
        wpy_args, wpy_kwargs = __args__.unpack()
        assert not wpy_kwargs # XXX exception

        wph_args_elems = [ py_to_php(self.interp, x) for x in wpy_args ]
        wph_rv = self.wph_inst.call_args(self.interp, wph_args_elems)
        return php_to_py(self.interp, wph_rv)

    def descr_eq(self, space, w_other):
        if isinstance(w_other, W_PHPProxyGeneric):
            php_interp = self.interp
            php_space = php_interp.space
            if php_space.eq_w(self.wph_inst, w_other.wph_inst):
                return space.w_True
        return space.w_False

    def descr_ne(self, space, w_other):
        return space.not_(self.descr_eq(space, w_other))

W_PHPProxyGeneric.typedef = TypeDef("PhBridgeProxy",
    __call__ = interp2app(W_PHPProxyGeneric.descr_call),
    __getattr__ = interp2app(W_PHPProxyGeneric.descr_get),
    __setattr__ = interp2app(W_PHPProxyGeneric.descr_set),
    __eq__ = interp2app(W_PHPProxyGeneric.descr_eq),
    __ne__ = interp2app(W_PHPProxyGeneric.descr_ne),
)


class W_EmbeddedPHPFunc(W_Root):
    """ A Python callable that actually executes a PHP function """

    _immutable_fields_ = ["space", "wph_func"]

    def __init__(self, space, wph_func):
        self.space = space
        self.wph_func = wph_func

    def get_wrapped_php_obj(self):
        return self.wph_func

    def get_php_interp(self):
        return self.space.get_php_interp()

    def is_w(self, space, other):
        if isinstance(other, W_EmbeddedPHPFunc):
            return self.wph_func is other.wph_func
        return False

    @property
    def name(self):
        return self.wph_func.name

    @jit.unroll_safe
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

def make_wrapped_int_key_php_array(interp, wphp_arry):
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

    erase, unerase = rerased.new_erasing_pair("php_int_key_array")
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

class WrappedPHPArrayKVIterator(object):
    def __init__(self, interp, wph_arry):
        self.interp = interp
        self.itr = wph_arry.dct_w.iteritems()

    def __iter__(self): return self

    def next(self):
        try:
            (key, wphp_val) = self.itr.next()
        except StopIteration:
            raise

        wpy_val = php_to_py(self.interp, wphp_val)
        return key, wpy_val

class WrappedPHPArrayVIterator(object):
    def __init__(self, interp, wph_arry):
        self.interp = interp
        self.itr = wph_arry.dct_w.itervalues()

    def __iter__(self): return self

    def next(self):
        try:
            wphp_val = self.itr.next()
        except StopIteration:
            raise

        return php_to_py(self.interp, wphp_val)

class WrappedPHPArrayDictStrategy(DictStrategy):
    """ Wrapping a non-int keyed (mixed key) PHP array uses a special Dict strategy """

    erase, unerase = rerased.new_erasing_pair("php_mixed_key_array")
    erase = staticmethod(erase)
    unerase = staticmethod(unerase)

    def wrap(self, unwrapped):
        return php_to_py(self.space.get_php_interp(), unwrapped)

    def getitem(self, w_dict, w_key):
        # XXX if the key is not a string or int, we should do a implicit
        # cast to mimick PHP semantics.

        interp = self.space.get_php_interp()
        pyspace = self.space

        wphp_arry = self.unerase(w_dict.dstorage)
        wphp_key = py_to_php(interp, w_key)
        return php_to_py(interp, interp.space.getitem(wphp_arry, wphp_key))

    def listview_int(self, w_dict):
        raise NotImplementedError("xxx")
        #return self.unerase(w_dict.dstorage).keys()

    def wrapkey(space, key):
        return space.wrap(key)

    def length(self, w_dict):
        wphp_arry = self.unerase(w_dict.dstorage)
        return wphp_arry.arraylen()

    def getiteritems(self, w_dict):
        wphp_arry = self.unerase(w_dict.dstorage)
        return WrappedPHPArrayKVIterator(self.space.get_php_interp(), wphp_arry)

    def getiterkeys(self, w_dict):
        wphp_arry = self.unerase(w_dict.dstorage)
        return wphp_arry.dct_w.iterkeys()

    def getitervalues(self, w_dict):
        wphp_arry = self.unerase(w_dict.dstorage)
        return WrappedPHPArrayVIterator(self.space.get_php_interp(), wphp_arry)

create_iterator_classes(WrappedPHPArrayDictStrategy)

def make_wrapped_mixed_key_php_array(interp, wphp_arry):
    if interp.space.arraylen(wphp_arry) <= 0:
        strategy = interp.pyspace.fromcache(EmptyDictStrategy)
        storage = strategy.erase(None)
    else:
        strategy = interp.pyspace.fromcache(WrappedPHPArrayDictStrategy)
        storage = strategy.erase(wphp_arry)

    return WPy_DictMultiObject(interp.pyspace, strategy, storage)

