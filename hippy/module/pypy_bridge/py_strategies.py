from pypy.objspace.std.listobject import ListStrategy, W_ListObject
from pypy.objspace.std.dictmultiobject import (
        DictStrategy, create_iterator_classes)
from pypy.objspace.std.dictmultiobject import W_DictMultiObject
from pypy.objspace.std.intobject import W_IntObject

from hippy.objects.arrayobject import W_ListArrayObject, W_RDictArrayObject
from hippy.objects.arrayiter import ListArrayIteratorRef, RDictArrayIteratorRef
from hippy.objects.base import W_Root as WPHP_Root
from hippy.objects.reference import W_Reference
from hippy.module.pypy_bridge.util import _raise_py_bridgeerror

from rpython.rlib import rerased

class PHPArrayListStrategy(ListStrategy):
    """Wrapping of a PHP list is implemented as a PyPy list strategy"""

    _none_value = None

    def _check_valid_wrap(self, w_list):
        """If at any point we find that we no longer wrap a int-keyed
        PHP array then we are invalid"""
        w_php_arry = self.unerase(w_list.lstorage).deref_temp()
        if not isinstance(w_php_arry, W_ListArrayObject):
            interp = self.space.get_php_interp()
            py_space = interp.py_space
            _raise_py_bridgeerror(py_space,
                "Stale wrapped PHP array. No longer integer keyed!")

    def wrap(self, w_php_val):
        return w_php_val.to_py(self.space.get_php_interp())

    erase, unerase = rerased.new_erasing_pair("PHPArrayListStrategy")
    erase = staticmethod(erase)
    unerase = staticmethod(unerase)

    def is_correct_type(self, w_obj):
        return isinstance(w_obj, WPHP_Root)

    def list_is_correct_type(self, w_list):
        return w_list.strategy is self.space.fromcache(PHPArrayListStrategy)

    def length(self, w_list):
        self._check_valid_wrap(w_list)

        w_php_arry = self.unerase(w_list.lstorage).deref_temp()
        return w_php_arry.arraylen()

    def getitem(self, w_list, index):
        self._check_valid_wrap(w_list)

        interp = self.space.get_php_interp()
        php_space = interp.space

        w_php_arry_ref = self.unerase(w_list.lstorage)
        w_php_index = php_space.wrap(index)

        w_php_arry = w_php_arry_ref.deref_temp()
        w_php_elem = w_php_arry.getitem(
                php_space, w_php_index, allow_undefined=False)

        if w_php_elem is None:
            raise IndexError("list index out of range")
        else:
            return self.wrap(w_php_elem)

    def setitem(self, w_list, key, w_value):
        # XXX again with the implicit cast on the key if not str or int
        interp = self.space.get_php_interp()
        php_space = interp.space

        w_php_arry_ref = self.unerase(w_list.lstorage)
        w_php_key = php_space.wrap(key) # key always an int
        w_php_value = w_value.to_php(interp)

        w_php_arry_ref.setitem_ref(php_space, w_php_key, w_php_value)

    def append(self, w_list, w_item):
        interp = self.space.get_php_interp()
        php_space = interp.space

        w_php_arry_ref = self.unerase(w_list.lstorage)
        w_php_item = w_item.to_php(interp)
        w_php_arry = w_php_arry_ref.deref_temp()
        w_php_next_idx = php_space.wrap(w_php_arry.arraylen())

        w_php_arry_ref.setitem_ref(php_space, w_php_next_idx, w_php_item)

    def pop(self, w_list, index):
        # implementation essentially mimics array_pop()
        interp = self.space.get_php_interp()
        php_space = interp.space

        w_php_arry_ref = self.unerase(w_list.lstorage)
        w_php_arry = w_php_arry_ref.deref_temp()
        w_php_val = w_php_arry._inplace_pop(php_space)

        return w_php_val.to_py(interp)

def make_wrapped_int_key_php_array(interp, w_php_arry_ref):
    assert isinstance(w_php_arry_ref, W_Reference)

    w_php_arry_tmp = w_php_arry_ref.deref_temp()
    if not isinstance(w_php_arry_tmp, W_ListArrayObject):
        py_space = interp.py_space
        _raise_py_bridgeerror(py_space,
                "can only apply as_list() to a wrapped PHP array in dict form")

    strategy = interp.py_space.fromcache(PHPArrayListStrategy)
    storage = strategy.erase(w_php_arry_ref)

    return W_ListObject.from_storage_and_strategy(
            interp.py_space, storage, strategy)

class PHPArrayDictStrategy(DictStrategy):
    """Wrapping a non-int keyed (mixed key) PHP array uses a special
    dict strategy"""

    erase, unerase = rerased.new_erasing_pair("PHPArrayDictStrategy")
    erase = staticmethod(erase)
    unerase = staticmethod(unerase)

    def wrap(self, unwrapped):
        return unwrapped.to_py(self.space.get_php_interp())

    def getitem(self, w_dict, w_key):
        # XXX if the key is not a string or int, we should do a implicit
        # cast to mimick PHP semantics.

        interp = self.space.get_php_interp()

        w_php_arry = self.unerase(w_dict.dstorage)
        w_php_key = w_key.to_php(interp)

        return interp.space.getitem(
                w_php_arry, w_php_key, give_notice=True).to_py(interp)

    def setitem(self, w_dict, w_key, w_value):
        # XXX again with the implicit cast on the key if not str or int
        interp = self.space.get_php_interp()
        php_space = interp.space

        w_php_arry_ref = self.unerase(w_dict.dstorage)
        w_php_key = w_key.to_php(interp)
        w_php_value = w_value.to_php(interp)

        w_php_arry_ref.setitem_ref(php_space, w_php_key, w_php_value)

    def setdefault(self, w_dict, w_key, w_default):
        interp = self.space.get_php_interp()
        php_space = interp.space

        w_php_key = w_key.to_php(interp)
        w_php_ary_ref = self.unerase(w_dict.dstorage)

        w_php_val = w_php_ary_ref.getitem_ref(
                php_space, w_php_key, allow_undefined=False)

        if w_php_val is None:
            w_py_default = w_default.to_php(interp)
            w_php_ary_ref.setitem_ref(php_space, w_php_key, w_py_default)
            return w_default
        else:
            return w_php_val.to_py(interp)

    def wrapkey(space, key):
        return key.to_py(space.get_php_interp())

    def wrapvalue(space, val):
        return val.to_py(space.get_php_interp())

    def length(self, w_dict):
        w_php_arry = self.unerase(w_dict.dstorage).deref_temp()
        return w_php_arry.arraylen()

    def getiterkeys(self, w_dict):
        w_php_arry = self.unerase(w_dict.dstorage)
        return PHPArrayDictStrategyKeyIterator(
                self.space.get_php_interp(), w_php_arry)

    def getitervalues(self, w_dict):
        w_php_arry = self.unerase(w_dict.dstorage)
        return PHPArrayDictStrategyValueIterator(
                self.space.get_php_interp(), w_php_arry)

    def getiteritems(self, w_dict):
        w_php_arry = self.unerase(w_dict.dstorage)
        return PHPArrayDictStrategyItemIterator(
                self.space.get_php_interp(), w_php_arry)

    def as_list(self, w_dict):
        """'Cast' a PHP array in Python dict form into Python list form"""
        interp = self.space.get_php_interp()
        w_php_arry_ref = self.unerase(w_dict.dstorage)
        return make_wrapped_int_key_php_array(interp, w_php_arry_ref)

    def delitem(self, w_dict, w_key):
        interp = self.space.get_php_interp()
        php_space = interp.space
        w_php_arry_ref = self.unerase(w_dict.dstorage)
        w_php_arry = w_php_arry_ref.deref_temp()
        w_php_arg = w_key.to_php(interp)
        w_php_arry._unsetitem(php_space, w_php_arg)

class PHPArrayDictStrategyKeyIterator(object):
    _immutable_fields_ = ["interp", "w_php_arry", "self.itr"]

    def __init__(self, interp, w_php_arry_ref):

        w_php_arry = w_php_arry_ref.deref_temp()
        self.interp = interp

        from hippy.module.pypy_bridge.py_adapters import W_PyListAdapter
        if isinstance(w_php_arry, W_ListArrayObject) or \
                isinstance(w_php_arry, W_PyListAdapter):
            self.itr = ListArrayIteratorRef(interp.space, w_php_arry_ref)
        elif isinstance(w_php_arry, W_RDictArrayObject):
            self.itr = RDictArrayIteratorRef(interp.space, w_php_arry_ref)
        else:
            assert False # can't happen

    def __iter__(self): return self

    def next(self):
        return self.itr.next_item(self.interp.space)[0]

class PHPArrayDictStrategyValueIterator(object):
    _immutable_fields_ = ["interp", "w_php_arry", "self.itr"]

    def __init__(self, interp, w_php_arry_ref):

        w_php_arry = w_php_arry_ref.deref_temp()
        self.interp = interp

        from hippy.module.pypy_bridge.py_adapters import W_PyListAdapter
        if isinstance(w_php_arry, W_ListArrayObject) or \
                isinstance(w_php_arry, W_PyListAdapter):
            self.itr = ListArrayIteratorRef(interp.space, w_php_arry_ref)
        elif isinstance(w_php_arry, W_RDictArrayObject):
            self.itr = RDictArrayIteratorRef(interp.space, w_php_arry_ref)
        else:
            assert False # can't happen

    def __iter__(self): return self

    def next(self):
        return self.itr.next(self.interp.space)

class PHPArrayDictStrategyItemIterator(object):
    _immutable_fields_ = ["interp", "w_php_arry", "self.itr"]

    def __init__(self, interp, w_php_arry_ref):

        w_php_arry = w_php_arry_ref.deref_temp()
        self.interp = interp

        from hippy.module.pypy_bridge.py_adapters import W_PyListAdapter
        if isinstance(w_php_arry, W_ListArrayObject) or \
                isinstance(w_php_arry, W_PyListAdapter):
            self.itr = ListArrayIteratorRef(interp.space, w_php_arry_ref)
        elif isinstance(w_php_arry, W_RDictArrayObject):
            self.itr = RDictArrayIteratorRef(interp.space, w_php_arry_ref)
        else:
            assert False # can't happen

    def __iter__(self): return self

    def next(self):
        return self.itr.next_item(self.interp.space)

create_iterator_classes(PHPArrayDictStrategy)

def make_wrapped_mixed_key_php_array(interp, w_php_arry_ref):
    assert isinstance(w_php_arry_ref, W_Reference)
    strategy = interp.py_space.fromcache(PHPArrayDictStrategy)
    storage = strategy.erase(w_php_arry_ref)

    return W_DictMultiObject(interp.py_space, strategy, storage)

class PyListDictStrategy(DictStrategy):
    """Wraps a Python list, pretending to be a Python dictionary.
    This is needed because anything which appears to be array-like in PHP
    (i.e. a Python list) should become dict-like when passed to Python."""

    erase, unerase = rerased.new_erasing_pair("PyListDictStrategy")
    erase = staticmethod(erase)
    unerase = staticmethod(unerase)

    def wrap(self, unwrapped):
        return unwrapped

    def _check_key_is_int(self, w_py_key):
        """ Although this is offering a dict-like interface, it still
        uses a list as internal storage. If the user tries to use a non-int
        key, then they get an exception"""
        if not isinstance(w_py_key, W_IntObject):
            _raise_py_bridgeerror(self.space,
                "Non-integer key used on a Python dict "
                "with internal list storage")

    def getitem(self, w_dict, w_key):
        self._check_key_is_int(w_key)

        py_space = self.space
        w_py_list = self.unerase(w_dict.dstorage)
        return py_space.getitem(w_py_list, w_key)

    def setitem(self, w_dict, w_key, w_value):
        self._check_key_is_int(w_key)

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
        """make it a real Python list again"""
        return self.unerase(w_dict.dstorage)

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

create_iterator_classes(PyListDictStrategy)

def make_dict_like_py_list(interp, w_py_list):
    strategy = interp.py_space.fromcache(PyListDictStrategy)
    storage = strategy.erase(w_py_list)
    return W_DictMultiObject(interp.py_space, strategy, storage)
