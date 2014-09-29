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
from pypy.interpreter.error import OperationError

from hippy.objects.base import W_Root as WPHP_Root
from hippy.objects.arrayobject import W_ListArrayObject, W_RDictArrayObject
from hippy.objects.arrayiter import ListArrayIteratorRef, RDictArrayIteratorRef
from hippy.objects.reference import W_Reference
from hippy.klass import def_class
from hippy.builtin import wrap_method
from hippy.error import Throw, VisibilityError

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

    def to_php(self, php_interp):
        return self.wph_inst

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
            try:
                wph_target = wph_inst.getmeth(php_space, name, None)
            except VisibilityError:
                wph_target = None

            if wph_target is None:
                raise OperationError(py_space.w_AttributeError, py_space.wrap(
                        "Wrapped PHP instance has no attribute '%s'" % name))
        return wph_target.to_py(interp)

    # XXX unwrap spec
    def descr_set(self, w_name, w_obj):
        interp = self.interp
        php_space = self.interp.space
        py_space = self.interp.pyspace

        name = py_space.str_w(w_name)
        wph_inst = self.wph_inst
        self.wph_inst.setattr(interp, name, w_obj.to_php(interp), None)

        return py_space.w_None

    @jit.unroll_safe
    def descr_call(self, __args__):
        wpy_args, wpy_kwargs = __args__.unpack()
        assert not wpy_kwargs # XXX exception

        wph_args_elems = [ x.to_php(self.interp) for x in wpy_args ]
        wph_rv = self.wph_inst.call_args(self.interp, wph_args_elems)
        return wph_rv.to_py(self.interp)

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
        self.w_phpexception = space.builtin.get("PHPException")

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
        if kwargs:
            _raise_py_bridgeerror(
                    self.space, "Cannot use kwargs when calling PHP functions")

        pyspace = self.space
        php_interp = self.space.get_php_interp()
        phspace = self.space.get_php_interp().space

        wph_args_elems = []
        for arg_no in xrange(len(args)):
            wpy_arg = args[arg_no]

            if self.wph_func.needs_ref(arg_no):
                # if you try to pass a reference argument by value, fail.
                if not isinstance(wpy_arg, W_PRef):
                    err_str = "Arg %d of PHP func '%s' is pass by reference" % \
                            (arg_no + 1, self.wph_func.name)
                    raise OperationError(
                            self.space.w_ValueError, self.space.wrap(err_str))
                wph_args_elems.append(wpy_arg.ref)
            else:
                # if you pass a value argument by reference, fail.
                if isinstance(wpy_arg, W_PRef):
                    err_str = "Arg %d of PHP func '%s' is pass by value" % \
                            (arg_no + 1, self.wph_func.name)
                    raise OperationError(
                            self.space.w_ValueError, self.space.wrap(err_str))
                wph_args_elems.append(wpy_arg.to_php(php_interp))

        try:
            res = self.wph_func.call_args(php_interp, wph_args_elems)
        except Throw as w_php_throw:
            w_php_exn = w_php_throw.w_exc
            raise OperationError(self.w_phpexception, w_php_exn.to_py(php_interp))

        return res.to_py(php_interp)

W_EmbeddedPHPFunc.typedef = TypeDef("EmbeddedPHPFunc",
    __call__ = interp2app(W_EmbeddedPHPFunc.descr_call),
)

def _raise_py_bridgeerror(py_space, msg):
    w_bridgeerror = py_space.builtin.get("BridgeError")
    raise OperationError(w_bridgeerror, py_space.wrap(msg))

def make_wrapped_int_key_php_array(interp, wphp_arry_ref):
    wphp_arry_tmp = wphp_arry_ref.deref_temp()
    if not isinstance(wphp_arry_tmp, W_ListArrayObject):
        py_space = interp.pyspace
        _raise_py_bridgeerror(py_space,
                "can only apply as_list() to a wrapped PHP array in dict form")


    strategy = interp.pyspace.fromcache(WrappedPHPArrayStrategy)
    storage = strategy.erase(wphp_arry_ref)

    return WPy_ListObject.from_storage_and_strategy(
            interp.pyspace, storage, strategy)

class WrappedPHPArrayStrategy(ListStrategy):
    """ Wrapping of a PHP list is implemented as a PyPy list strategy """

    _none_value = None

    def _check_valid_wrap(self, w_list):
        """ If at any point we find that we no longer wrap a int-keyed
        PHP array then we are invalid """
        wphp_arry = self.unerase(w_list.lstorage).deref_temp()
        if not isinstance(wphp_arry, W_ListArrayObject):
            interp = self.space.get_php_interp()
            py_space = interp.pyspace
            _raise_py_bridgeerror(py_space,
                "Stale wrapped PHP array. No longer integer keyed!")

    def wrap(self, wphp_val):
        return wphp_val.to_py(self.space.get_php_interp())

    erase, unerase = rerased.new_erasing_pair("php_int_key_array")
    erase = staticmethod(erase)
    unerase = staticmethod(unerase)

    def is_correct_type(self, w_obj):
        return isinstance(w_obj, WPHP_Root)

    def list_is_correct_type(self, w_list):
        return w_list.strategy is self.space.fromcache(WrappedPHPArrayStrategy)

    def length(self, w_list):
        self._check_valid_wrap(w_list)

        wphp_arry = self.unerase(w_list.lstorage).deref_temp()
        return wphp_arry.arraylen()

    def getitem(self, w_list, index):
        self._check_valid_wrap(w_list)

        interp = self.space.get_php_interp()
        py_space, php_space = self.space, interp.space

        wphp_arry_ref = self.unerase(w_list.lstorage)
        wphp_index = php_space.wrap(index)
        # XXX will not do the right thing if the index does not exist
        wphp_elem = wphp_arry_ref.getitem_ref(php_space, wphp_index)

        return self.wrap(wphp_elem)

    def setitem(self, w_list, key, w_value):
        # XXX again with the implicit cast on the key if not str or int
        interp = self.space.get_php_interp()
        py_space, php_space = self.space, interp.space

        wphp_arry_ref = self.unerase(w_list.lstorage)
        wphp_key = php_space.wrap(key) # key always an int
        wphp_value = w_value.to_php(interp)

        wphp_arry_ref.setitem_ref(php_space, wphp_key, wphp_value)

    def append(self, w_list, w_item):
        interp = self.space.get_php_interp()
        py_space, php_space = self.space, interp.space

        wphp_arry_ref = self.unerase(w_list.lstorage)
        wphp_item = w_item.to_php(interp)
        wphp_arry = wphp_arry_ref.deref_temp()
        wphp_next_idx = php_space.wrap(wphp_arry.arraylen())

        wphp_arry_ref.setitem_ref(php_space, wphp_next_idx, wphp_item)

# The following types make the PHP array iterators iterable at the RPython
# level so that we can use create_iterator_classes().
class W_ArrayKeyIteratorWrap(object):

    _immutable_fields_ = ["interp", "wph_arry", "self.itr"]

    def __init__(self, interp, wphp_arry_ref):

        wphp_arry = wphp_arry_ref.deref_temp()
        self.interp = interp

        if isinstance(wphp_arry, W_ListArrayObject):
            self.itr = ListArrayIteratorRef(interp.space, wphp_arry_ref)
        elif isinstance(wphp_arry, W_RDictArrayObject):
            self.itr = RDictArrayIteratorRef(interp.space, wphp_arry_ref)
        else:
            assert False # can't happen

    def __iter__(self): return self

    def next(self):
        return self.itr.next_item(self.interp.space)[0]

class W_ArrayValIteratorWrap(object):

    _immutable_fields_ = ["interp", "wph_arry", "self.itr"]

    def __init__(self, interp, wphp_arry_ref):

        wphp_arry = wphp_arry_ref.deref_temp()
        self.interp = interp

        if isinstance(wphp_arry, W_ListArrayObject):
            self.itr = ListArrayIteratorRef(interp.space, wphp_arry_ref)
        elif isinstance(wphp_arry, W_RDictArrayObject):
            self.itr = RDictArrayIteratorRef(interp.space, wphp_arry_ref)
        else:
            assert False # can't happen

    def __iter__(self): return self

    def next(self):
        return self.itr.next(self.interp.space)

class W_ArrayItemIteratorWrap(object):

    _immutable_fields_ = ["interp", "wph_arry", "self.itr"]

    def __init__(self, interp, wphp_arry_ref):

        wphp_arry = wphp_arry_ref.deref_temp()
        self.interp = interp

        if isinstance(wphp_arry, W_ListArrayObject):
            self.itr = ListArrayIteratorRef(interp.space, wphp_arry_ref)
        elif isinstance(wphp_arry, W_RDictArrayObject):
            self.itr = RDictArrayIteratorRef(interp.space, wphp_arry_ref)
        else:
            assert False # can't happen

    def __iter__(self): return self

    def next(self):
        return self.itr.next_item(self.interp.space)


class WrappedPHPArrayDictStrategy(DictStrategy):
    """ Wrapping a non-int keyed (mixed key) PHP array uses a special Dict strategy """

    erase, unerase = rerased.new_erasing_pair("php_mixed_key_array")
    erase = staticmethod(erase)
    unerase = staticmethod(unerase)

    def wrap(self, unwrapped):
        return unwrapped.to_py(self.space.get_php_interp())

    def getitem(self, w_dict, w_key):
        # XXX if the key is not a string or int, we should do a implicit
        # cast to mimick PHP semantics.

        interp = self.space.get_php_interp()
        pyspace = self.space

        wphp_arry = self.unerase(w_dict.dstorage)
        wphp_key = w_key.to_php(interp)
        return interp.space.getitem(wphp_arry, wphp_key).to_py(interp)

    def setitem(self, w_dict, w_key, w_value):
        # XXX again with the implicit cast on the key if not str or int
        interp = self.space.get_php_interp()
        py_space, php_space = self.space, interp.space

        wphp_arry_ref = self.unerase(w_dict.dstorage)
        wphp_key = w_key.to_php(interp)
        wphp_value = w_value.to_php(interp)

        wphp_arry_ref.setitem_ref(php_space, wphp_key, wphp_value)

    def wrapkey(space, key):
        return key.to_py(space.get_php_interp())

    def wrapvalue(space, val):
        return val.to_py(space.get_php_interp())

    def length(self, w_dict):
        wphp_arry = self.unerase(w_dict.dstorage).deref_temp()
        return wphp_arry.arraylen()

    def getiterkeys(self, w_dict):
        wphp_arry = self.unerase(w_dict.dstorage)
        return W_ArrayKeyIteratorWrap(self.space.get_php_interp(), wphp_arry)

    def getitervalues(self, w_dict):
        wphp_arry = self.unerase(w_dict.dstorage)
        return W_ArrayValIteratorWrap(self.space.get_php_interp(), wphp_arry)

    def getiteritems(self, w_dict):
        wphp_arry = self.unerase(w_dict.dstorage)
        return W_ArrayItemIteratorWrap(self.space.get_php_interp(), wphp_arry)

    def as_list(self, w_dict):
        """ 'Cast' a PHP array in Python dict form into Python list form """

        interp = self.space.get_php_interp()
        wphp_arry_ref = self.unerase(w_dict.dstorage)
        return make_wrapped_int_key_php_array(interp, wphp_arry_ref)

create_iterator_classes(WrappedPHPArrayDictStrategy)

def make_wrapped_mixed_key_php_array(interp, wphp_arry_ref):
    strategy = interp.pyspace.fromcache(WrappedPHPArrayDictStrategy)
    storage = strategy.erase(wphp_arry_ref)

    return WPy_DictMultiObject(interp.pyspace, strategy, storage)


class W_PRef(W_Root):
    """ Represents a PHP reference """

    def __init__(self, space, w_py_val):
        from hippy.objects.reference import W_Reference
        w_ph_val = w_py_val.to_php(space.get_php_interp())
        self.ref = W_Reference(w_ph_val)
        self.py_space = space

    def deref(self):
        return self.ref.deref().to_py(self.py_space.get_php_interp())

    @staticmethod
    def descr_new(space, w_type, w_py_val):
        w_obj = space.allocate_instance(W_PRef, w_type)
        w_obj.__init__(space, w_py_val)
        return w_obj

W_PRef.typedef = TypeDef("PRef",
    __new__ = interp2app(W_PRef.descr_new),
    deref = interp2app(W_PRef.deref),
)
