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
from pypy.objspace.std.intobject import W_IntObject

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

    _immutable_fields_ = ["interp", "w_php_inst"]

    def __init__(self, interp, w_php_inst):
        self.w_php_inst = w_php_inst
        self.interp = interp

    def get_wrapped_php_obj(self):
        return self.w_php_inst

    def get_php_interp(self):
        return self.interp

    def to_php(self, php_interp):
        return self.w_php_inst

    def is_w(self, space, other):
        if isinstance(other, W_PHPProxyGeneric):
            return self.w_php_inst is other.w_php_inst
        return False

    @unwrap_spec(name=str)
    def descr_get(self, name):
        """ Python is asking for an attribute of a proxied PHP object """
        interp = self.interp
        php_space = interp.space
        py_space = interp.py_space

        w_php_inst = self.w_php_inst
        w_php_target = w_php_inst.getattr(interp, name, None, fail_with_none=True)

        if w_php_target is None:
            try:
                w_php_target = w_php_inst.getmeth(php_space, name, None)
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

        w_php_inst = self.w_php_inst
        self.w_php_inst.setattr(interp, name, w_obj.to_php(interp), None)

        return py_space.w_None

    @jit.unroll_safe
    def descr_call(self, __args__):
        w_py_args, w_py_kwargs = __args__.unpack()

        if w_py_kwargs:
            _raise_py_bridgeerror(self.interp.py_space,
                    "Cannot use kwargs with callable PHP instances")

        from hippy.klass import ClassBase
        if isinstance(self.w_php_inst, ClassBase):
            # user is calling a PHP class in Python, i.e. instantiating it.
            # XXX PHP classes should have a dedicated wrapper for performance.
            w_php_args_elems = [ x.to_php(self.interp) for x in w_py_args ]
            w_php_rv = self.w_php_inst.call_args(self.interp, w_php_args_elems)
            return w_php_rv.to_py(self.interp)
        else:
            # calling an instance
            w_php_callable = self.w_php_inst.get_callable()
            if w_php_callable is None: # not callable
                _raise_py_bridgeerror(self.interp.py_space,
                        "Wrapped PHP instance is not callable")

            w_php_args_elems = [ x.to_php(self.interp) for x in w_py_args ]
            w_php_rv = w_php_callable.call_args(self.interp, w_php_args_elems)
            return w_php_rv.to_py(self.interp)

    def _descr_generic_unop(self, space, name):
        interp = self.interp
        php_space = interp.space
        w_php_inst = self.w_php_inst
        try:
            w_php_target = w_php_inst.getmeth(php_space, name, None)
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
        w_php_inst = self.w_php_inst
        try:
            w_php_target = w_php_inst.getmeth(php_space, name, None)
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
        if isinstance(w_other, W_PHPProxyGeneric):
            php_interp = self.interp
            php_space = php_interp.space
            if php_space.eq_w(self.w_php_inst, w_other.w_php_inst):
                return space.w_True
        return space.w_False

    def descr_ne(self, space, w_other):
        return space.not_(self.descr_eq(space, w_other))

W_PHPProxyGeneric.typedef = TypeDef("PhBridgeProxy",
    __call__ = interp2app(W_PHPProxyGeneric.descr_call),
    __getattr__ = interp2app(W_PHPProxyGeneric.descr_get),
    __setattr__ = interp2app(W_PHPProxyGeneric.descr_set),
    __str__ = interp2app(W_PHPProxyGeneric.descr_str),
    __add__ = interp2app(W_PHPProxyGeneric.descr_add),
    __sub__ = interp2app(W_PHPProxyGeneric.descr_sub),
    __mul__ = interp2app(W_PHPProxyGeneric.descr_mul),
    __floordiv__ = interp2app(W_PHPProxyGeneric.descr_floordiv),
    __mod__ = interp2app(W_PHPProxyGeneric.descr_mod),
    __divmod__ = interp2app(W_PHPProxyGeneric.descr_divmod),
    __pow__ = interp2app(W_PHPProxyGeneric.descr_pow),
    __lshift__ = interp2app(W_PHPProxyGeneric.descr_lshift),
    __rshift__ = interp2app(W_PHPProxyGeneric.descr_rshift),
    __and__ = interp2app(W_PHPProxyGeneric.descr_and),
    __xor__ = interp2app(W_PHPProxyGeneric.descr_xor),
    __or__ = interp2app(W_PHPProxyGeneric.descr_or),
    __eq__ = interp2app(W_PHPProxyGeneric.descr_eq),
    __ne__ = interp2app(W_PHPProxyGeneric.descr_ne),
)


class W_EmbeddedPHPFunc(W_Root):
    """ A Python callable that actually executes a PHP function """

    _immutable_fields_ = ["space", "w_php_func"]

    def __init__(self, space, w_php_func):
        self.space = space
        self.w_php_func = w_php_func
        self.w_phpexception = space.builtin.get("PHPException")

    def get_wrapped_php_obj(self):
        return self.w_php_func

    def get_php_interp(self):
        return self.space.get_php_interp()

    def is_w(self, space, other):
        if isinstance(other, W_EmbeddedPHPFunc):
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
            _raise_py_bridgeerror(
                    self.space, "Cannot use kwargs when calling PHP functions")

        py_space = self.space
        php_interp = self.space.get_php_interp()
        php_space = php_interp.space

        w_php_args_elems = []
        for arg_no in xrange(len(args)):
            w_py_arg = args[arg_no]

            if self.w_php_func.needs_ref(arg_no):
                # if you try to pass a reference argument by value, fail.
                if not isinstance(w_py_arg, W_PRef):
                    err_str = "Arg %d of PHP func '%s' is pass by reference" % \
                            (arg_no + 1, self.w_php_func.name)
                    _raise_py_bridgeerror(py_space, err_str)

                w_php_args_elems.append(w_py_arg.ref)
            else:
                # if you pass a value argument by reference, fail.
                if isinstance(w_py_arg, W_PRef):
                    err_str = "Arg %d of PHP func '%s' is pass by value" % \
                            (arg_no + 1, self.w_php_func.name)
                    _raise_py_bridgeerror(py_space, err_str)

                w_php_args_elems.append(w_py_arg.to_php(php_interp))

        try:
            res = self.w_php_func.call_args(php_interp, w_php_args_elems)
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

def make_wrapped_int_key_php_array(interp, w_php_arry_ref):
    w_php_arry_tmp = w_php_arry_ref.deref_temp()
    if not isinstance(w_php_arry_tmp, W_ListArrayObject):
        py_space = interp.py_space
        _raise_py_bridgeerror(py_space,
                "can only apply as_list() to a wrapped PHP array in dict form")


    strategy = interp.py_space.fromcache(WrappedPHPArrayStrategy)
    storage = strategy.erase(w_php_arry_ref)

    return WPy_ListObject.from_storage_and_strategy(
            interp.py_space, storage, strategy)

class WrappedPHPArrayStrategy(ListStrategy):
    """ Wrapping of a PHP list is implemented as a PyPy list strategy """

    _none_value = None

    def _check_valid_wrap(self, w_list):
        """ If at any point we find that we no longer wrap a int-keyed
        PHP array then we are invalid """
        w_php_arry = self.unerase(w_list.lstorage).deref_temp()
        if not isinstance(w_php_arry, W_ListArrayObject):
            interp = self.space.get_php_interp()
            py_space = interp.py_space
            _raise_py_bridgeerror(py_space,
                "Stale wrapped PHP array. No longer integer keyed!")

    def wrap(self, w_php_val):
        return w_php_val.to_py(self.space.get_php_interp())

    erase, unerase = rerased.new_erasing_pair("WrappedPHPArrayStrategy")
    erase = staticmethod(erase)
    unerase = staticmethod(unerase)

    def is_correct_type(self, w_obj):
        return isinstance(w_obj, WPHP_Root)

    def list_is_correct_type(self, w_list):
        return w_list.strategy is self.space.fromcache(WrappedPHPArrayStrategy)

    def length(self, w_list):
        self._check_valid_wrap(w_list)

        w_php_arry = self.unerase(w_list.lstorage).deref_temp()
        return w_php_arry.arraylen()

    def getitem(self, w_list, index):
        self._check_valid_wrap(w_list)

        interp = self.space.get_php_interp()
        py_space, php_space = self.space, interp.space

        w_php_arry_ref = self.unerase(w_list.lstorage)
        w_php_index = php_space.wrap(index)
        w_php_elem = w_php_arry_ref.getitem_ref(
                php_space, w_php_index, allow_undefined=False)

        if w_php_elem is None:
            raise IndexError("list index out of range")
        else:
            return self.wrap(w_php_elem)

    def setitem(self, w_list, key, w_value):
        # XXX again with the implicit cast on the key if not str or int
        interp = self.space.get_php_interp()
        py_space, php_space = self.space, interp.space

        w_php_arry_ref = self.unerase(w_list.lstorage)
        w_php_key = php_space.wrap(key) # key always an int
        w_php_value = w_value.to_php(interp)

        w_php_arry_ref.setitem_ref(php_space, w_php_key, w_php_value)

    def append(self, w_list, w_item):
        interp = self.space.get_php_interp()
        py_space, php_space = self.space, interp.space

        w_php_arry_ref = self.unerase(w_list.lstorage)
        w_php_item = w_item.to_php(interp)
        w_php_arry = w_php_arry_ref.deref_temp()
        w_php_next_idx = php_space.wrap(w_php_arry.arraylen())

        w_php_arry_ref.setitem_ref(php_space, w_php_next_idx, w_php_item)

# The following types make the PHP array iterators iterable at the RPython
# level so that we can use create_iterator_classes().
class WrappedPHPArrayDictStrategyKeyIterator(object):

    _immutable_fields_ = ["interp", "w_php_arry", "self.itr"]

    def __init__(self, interp, w_php_arry_ref):

        w_php_arry = w_php_arry_ref.deref_temp()
        self.interp = interp

        from hippy.module.pypy_bridge.php_wrappers import W_PyBridgeListProxy
        if isinstance(w_php_arry, W_ListArrayObject) or \
                isinstance(w_php_arry, W_PyBridgeListProxy):
            self.itr = ListArrayIteratorRef(interp.space, w_php_arry_ref)
        elif isinstance(w_php_arry, W_RDictArrayObject):
            self.itr = RDictArrayIteratorRef(interp.space, w_php_arry_ref)
        else:
            assert False # can't happen

    def __iter__(self): return self

    def next(self):
        return self.itr.next_item(self.interp.space)[0]

class WrappedPHPArrayDictStrategyValueIterator(object):

    _immutable_fields_ = ["interp", "w_php_arry", "self.itr"]

    def __init__(self, interp, w_php_arry_ref):

        w_php_arry = w_php_arry_ref.deref_temp()
        self.interp = interp

        from hippy.module.pypy_bridge.php_wrappers import W_PyBridgeListProxy
        if isinstance(w_php_arry, W_ListArrayObject) or \
                isinstance(w_php_arry, W_PyBridgeListProxy):
            self.itr = ListArrayIteratorRef(interp.space, w_php_arry_ref)
        elif isinstance(w_php_arry, W_RDictArrayObject):
            self.itr = RDictArrayIteratorRef(interp.space, w_php_arry_ref)
        else:
            assert False # can't happen

    def __iter__(self): return self

    def next(self):
        return self.itr.next(self.interp.space)

class WrappedPHPArrayDictStrategyItemIterator(object):

    _immutable_fields_ = ["interp", "w_php_arry", "self.itr"]

    def __init__(self, interp, w_php_arry_ref):

        w_php_arry = w_php_arry_ref.deref_temp()
        self.interp = interp

        from hippy.module.pypy_bridge.php_wrappers import W_PyBridgeListProxy
        if isinstance(w_php_arry, W_ListArrayObject) or \
                isinstance(w_php_arry, W_PyBridgeListProxy):
            self.itr = ListArrayIteratorRef(interp.space, w_php_arry_ref)
        elif isinstance(w_php_arry, W_RDictArrayObject):
            self.itr = RDictArrayIteratorRef(interp.space, w_php_arry_ref)
        else:
            assert False # can't happen

    def __iter__(self): return self

    def next(self):
        return self.itr.next_item(self.interp.space)


class WrappedPHPArrayDictStrategy(DictStrategy):
    """ Wrapping a non-int keyed (mixed key) PHP array uses a special Dict strategy """

    erase, unerase = rerased.new_erasing_pair("WrappedPHPArrayDictStrategy")
    erase = staticmethod(erase)
    unerase = staticmethod(unerase)

    def wrap(self, unwrapped):
        return unwrapped.to_py(self.space.get_php_interp())

    def getitem(self, w_dict, w_key):
        # XXX if the key is not a string or int, we should do a implicit
        # cast to mimick PHP semantics.

        interp = self.space.get_php_interp()
        py_space = self.space

        w_php_arry = self.unerase(w_dict.dstorage)
        w_php_key = w_key.to_php(interp)
        return interp.space.getitem(w_php_arry, w_php_key).to_py(interp)

    def setitem(self, w_dict, w_key, w_value):
        # XXX again with the implicit cast on the key if not str or int
        interp = self.space.get_php_interp()
        py_space, php_space = self.space, interp.space

        w_php_arry_ref = self.unerase(w_dict.dstorage)
        w_php_key = w_key.to_php(interp)
        w_php_value = w_value.to_php(interp)

        w_php_arry_ref.setitem_ref(php_space, w_php_key, w_php_value)

    def setdefault(self, w_dict, w_key, w_default):
        interp = self.space.get_php_interp()
        py_space, php_space = self.space, interp.space

        w_php_key = w_key.to_php(interp)
        w_php_ary_ref = self.unerase(w_dict.dstorage)

        w_php_val = w_php_ary_ref.getitem_ref(
                php_space, w_php_key, allow_undefined=False)
        if w_php_val is None:
            w_php_ary_ref.setitem_ref(
                    php_space, w_php_key, w_default.to_php(interp))
            return w_default
        else:
            return w_php_val.deref().to_py(interp)

    def wrapkey(space, key):
        return key.to_py(space.get_php_interp())

    def wrapvalue(space, val):
        return val.to_py(space.get_php_interp())

    def length(self, w_dict):
        w_php_arry = self.unerase(w_dict.dstorage).deref_temp()
        return w_php_arry.arraylen()

    def getiterkeys(self, w_dict):
        w_php_arry = self.unerase(w_dict.dstorage)
        return WrappedPHPArrayDictStrategyKeyIterator(
                self.space.get_php_interp(), w_php_arry)

    def getitervalues(self, w_dict):
        w_php_arry = self.unerase(w_dict.dstorage)
        return WrappedPHPArrayDictStrategyValueIterator(
                self.space.get_php_interp(), w_php_arry)

    def getiteritems(self, w_dict):
        w_php_arry = self.unerase(w_dict.dstorage)
        return WrappedPHPArrayDictStrategyItemIterator(
                self.space.get_php_interp(), w_php_arry)

    def as_list(self, w_dict):
        """ 'Cast' a PHP array in Python dict form into Python list form """


        interp = self.space.get_php_interp()
        w_php_arry_ref = self.unerase(w_dict.dstorage)
        return make_wrapped_int_key_php_array(interp, w_php_arry_ref)

create_iterator_classes(WrappedPHPArrayDictStrategy)

def make_wrapped_mixed_key_php_array(interp, w_php_arry_ref):
    strategy = interp.py_space.fromcache(WrappedPHPArrayDictStrategy)
    storage = strategy.erase(w_php_arry_ref)

    return WPy_DictMultiObject(interp.py_space, strategy, storage)


class W_PRef(W_Root):
    """ Represents a PHP reference """

    def __init__(self, space, w_py_val):
        from hippy.objects.reference import W_Reference
        w_php_val = w_py_val.to_php(space.get_php_interp())
        self.ref = W_Reference(w_php_val)
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

class W_PyListDictStrategyValueIterator(object):

    _immutable_fields_ = ["py_space", "w_py_itr"]

    def __init__(self, py_space, w_py_list):
        self.py_space = py_space
        from pypy.objspace.std.iterobject import W_FastListIterObject
        self.w_py_itr = W_FastListIterObject(w_py_list)

    def __iter__(self): return self

    def next(self):
        return self.w_py_itr.descr_next(self.py_space)

class W_PyListDictStrategyKeyIterator(object):

    _immutable_fields_ = ["py_space", "itr"]

    def __init__(self, py_space, length):
        self.py_space = py_space
        self.itr = iter(xrange(length))

    def __iter__(self): return self

    def next(self):
        return self.py_space.wrap(self.itr.next())

class W_PyListDictStrategyItemsIterator(object):

    _immutable_fields_ = ["py_space", "itr"]

    def __init__(self, py_space, w_py_list):
        self.py_space = py_space

        length = py_space.int_w(py_space.len(w_py_list))
        self.key_itr = iter(xrange(length))

        from pypy.objspace.std.iterobject import W_FastListIterObject
        self.w_py_val_itr = W_FastListIterObject(w_py_list)

    def __iter__(self): return self

    def next(self):
        w_py_key = self.py_space.wrap(self.key_itr.next())
        w_py_val = self.w_py_val_itr.descr_next(self.py_space)
        return w_py_key, w_py_val

class WrappedPyListDictStrategy(DictStrategy):
    """ Wraps a Python list, pretending to be a Python dictionary.
    This is needed because anything which appears to be array-like in PHP
    (i.e. a Python list) should become dict-like when passed to Python."""

    erase, unerase = rerased.new_erasing_pair("WrappedPyListDictStrategy")
    erase = staticmethod(erase)
    unerase = staticmethod(unerase)

    def wrap(self, unwrapped):
        return unwrapped

    def getitem(self, w_dict, w_key):
        py_space = self.space

        # XXX decide what should happen
        assert isinstance(w_key, W_IntObject)

        w_py_list = self.unerase(w_dict.dstorage)
        return py_space.getitem(w_py_list, w_key)

    def setitem(self, w_dict, w_key, w_value):

        # XXX decide what should happen
        assert isinstance(w_key, W_IntObject)

        py_space = self.space
        w_py_list = self.unerase(w_dict.dstorage)
        py_space.setitem(w_py_list, w_key, w_value)

    def wrapkey(space, key):
        return key

    def wrapvalue(space, val):
        return val

    def length(self, w_dict):
        py_space = self.space
        w_py_list = self.unerase(w_dict.dstorage)
        return py_space.int_w(py_space.len(w_py_list))

    def getiterkeys(self, w_dict):
        py_space = self.space
        w_py_list = self.unerase(w_dict.dstorage)
        length = self.length(w_dict)
        return W_PyListDictStrategyKeyIterator(py_space, length)

    def getitervalues(self, w_dict):
        py_space = self.space
        w_py_list = self.unerase(w_dict.dstorage)
        return W_PyListDictStrategyValueIterator(py_space, w_py_list)

    def getiteritems(self, w_dict):
        py_space = self.space
        w_py_list = self.unerase(w_dict.dstorage)
        return W_PyListDictStrategyItemsIterator(py_space, w_py_list)

    def as_list(self, w_dict):
        """ make it a real Python list again """
        return self.unerase(w_dict.dstorage)

create_iterator_classes(WrappedPyListDictStrategy)

def make_dict_like_py_list(interp, w_py_list):
    strategy = interp.py_space.fromcache(WrappedPyListDictStrategy)
    storage = strategy.erase(w_py_list)
    return WPy_DictMultiObject(interp.py_space, strategy, storage)

