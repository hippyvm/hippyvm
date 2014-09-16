"""
The data structures defined here all wrap Python objects in some way so
that they can be used in PHP programs.
"""

from hippy.objects.instanceobject import W_InstanceObject
from hippy.klass import def_class, W_InvokeCall
from hippy.builtin import wrap, Optional, wrap_method, ThisUnwrapper
from hippy.objects.base import W_Root as Wph_Root, W_Object as WPh_Object
from hippy.function import AbstractFunction
from hippy.objects.iterator import BaseIterator
from hippy.objects.arrayobject import wrap_array_key, W_ArrayObject
from hippy.objects.reference import W_Reference

from pypy.interpreter.argument import Arguments
from pypy.interpreter.error import OperationError
from pypy.objspace.std.listobject import W_ListObject as WPy_ListObject

from rpython.rlib import jit


class W_PyProxyGeneric(W_InstanceObject):
    """Generic proxy for wrapping Python objects in Hippy when no more specific
    proxy is available."""

    _immutable_fields_ = ["interp", "wpy_inst"]

    def setup_instance(self, interp, wpy_inst):
        self.interp = interp
        self.wpy_inst = wpy_inst

    def get_wrapped_py_obj(self):
        return self.wpy_inst

    # Use this as a low level ctor instead of the above.
    @classmethod
    def from_wpy_inst(cls, interp, wpy_inst):
        wph_pxy = cls(interp, [])
        wph_pxy.set_instance(wpy_inst)
        return wph_pxy

    def get_callable(self):
        """ PHP interpreter calls this when calls a wrapped Python var  """
        return W_EmbeddedPyCallable(self.wpy_inst)

    def to_py(self, interp):
        return self.wpy_inst

@wrap_method(['interp', ThisUnwrapper(W_PyProxyGeneric), str],
        name='GenericPyProxy::__get')
def generic__get(interp, this, name):
    interp = this.interp
    pyspace = interp.pyspace
    wpy_target = pyspace.getattr(this.wpy_inst, pyspace.wrap(name))
    return wpy_target.to_php(interp)

@wrap_method(['interp', ThisUnwrapper(W_PyProxyGeneric), str, Wph_Root],
        name='GenericPyProxy::__call')
@jit.unroll_safe
def generic__call(interp, this, func_name, wph_args):
    from hippy.interpreter import Interpreter
    assert isinstance(interp, Interpreter)

    pyspace = interp.pyspace
    wpy_func_name = pyspace.wrap(func_name)
    wpy_func = pyspace.getattr(this.wpy_inst, wpy_func_name)

    wpy_args_items = [ x.to_py(interp) for x in wph_args.as_list_w() ]
    wpy_rv = interp.pyspace.call(wpy_func, interp.pyspace.newlist(wpy_args_items))
    return wpy_rv.to_php(interp)

k_PyBridgeProxy = def_class('PyBridgeProxy',
    [generic__get, generic__call],
    [], instance_class=W_PyProxyGeneric
)

class W_EmbeddedPyCallable(W_InvokeCall):

    _immutable_fields_ = [ "wpy_func" ]

    def __init__(self, wpy_func):
        W_InvokeCall.__init__(self, None, wpy_func, None)
        self.wpy_func = wpy_func

    def call_args(self, interp, args_w):

        wpy_args_elems = [ x.to_py(interp) for x in args_w ]

        rv = interp.pyspace.call_args(
                self.wpy_func, Arguments(interp.pyspace, wpy_args_elems))
        return rv.to_php(interp)

    def needs_ref(self, i):
        return False

    def needs_val(self, i):
        return False

    def is_py_call(self):
        return True

class W_EmbeddedPyFunc(W_InstanceObject):
    """ A 'lexically scoped' embedded Python function.
    Essentially these instances behave a bit like a PHP closure."""

    _immutable_fields_ = [ "interp", "py_func" ]

    def __init__(self, interp, py_func, klass, storage_w):
        self.interp = interp
        self.py_func = py_func
        W_InstanceObject.__init__(self, klass, storage_w)

    def setattr(self, interp, attr, w_value, contextclass, unique_item=False):
        interp.catchable_fatal(
                "%s object cannot have properties" % type(self))

    def setattr_ref(self, interp, attr, w_value, contextclass):
        interp.catchable_fatal(
                "%s object cannot have properties" % type(self))

    def clone(self, interp, contextclass):
        raise NotImplementedError("Not implemented")

    def get_callable(self):
        return W_EmbeddedPyCallable(self.py_func)

k_EmbeddedPyFunc = def_class('EmbeddedPyFunc', [])

def new_embedded_py_func(interp, py_func):
    return W_EmbeddedPyFunc(interp, py_func, k_EmbeddedPyFunc,
            k_EmbeddedPyFunc.get_initial_storage_w(interp.space)[:])

class W_EmbeddedPyMod(WPh_Object):
    _immutable_fields_ = ["py_space", "py_mod"]

    def __init__(self, py_space, py_mod):
        self.py_space = py_space
        self.py_mod = py_mod

    def get_wrapped_py_obj(self):
        return self.py_mod

    def _getattr(self, interp, space, name):
        py_mod = self.py_mod
        py_space = self.py_space
        try:
            w_obj = py_space.getattr(py_mod, py_space.wrap(name))
        except OperationError, e:
            if not e.match(py_space, py_space.w_AttributeError):
                raise
            raise space.ec.fatal("No such member %s in module" % name)
        return w_obj.to_php(py_space.get_php_interp())

    def getmeth(self, space, name, contextclass=None, for_callback=None):
        interp = self.py_space.get_php_interp()
        return self._getattr(interp, space, name)

    def getattr(self, interp, name, contextclass=None, give_notice=False, fail_with_none=False):
        interp = self.py_space.get_php_interp()
        return self._getattr(interp, interp.space, name)

class W_PyBridgeListProxyIterator(BaseIterator):

    _immutable_fields_ = ["py_space", "storage_w"]

    def __init__(self, py_space, wpy_list):
        self.py_space = py_space
        self.storage_w = py_space.listview(wpy_list)
        self.index = 0
        self.finished = len(self.storage_w) == 0

    def get_wrapped_py_obj(self):
        # Iterators can reasonably be considered opaque from a wrapping
        # perspective.
        return None

    def next(self, space):
        index = self.index
        wpy_value = self.storage_w[index]
        self.index = index + 1
        self.finished = self.index == len(self.storage_w)
        return wpy_value.to_php(self.py_space.get_php_interp())

    def next_item(self, space):
        index = self.index
        wpy_value = self.storage_w[index]
        self.index = index + 1
        self.finished = self.index == len(self.storage_w)
        return space.wrap(index), wpy_value.to_php(self.py_space.get_php_interp())

class W_PyBridgeListProxy(W_ArrayObject):
    """ Wraps a Python list as PHP array. """

    _immutable_fields_ = ["py_space", "wpy_list"]

    _has_string_keys = False

    def __init__(self, py_space, wpy_list):
        assert isinstance(wpy_list, WPy_ListObject)
        self.py_space = py_space
        self.wpy_list = wpy_list

    def get_wrapped_py_obj(self):
        return self.wpy_list

    def arraylen(self):
        py_space = self.py_space
        return py_space.int_w(py_space.len(self.wpy_list))

    def _getitem_int(self, index):
        py_space = self.py_space
        wpy_val = py_space.getitem(self.wpy_list, py_space.wrap(index))
        return wpy_val.to_php(py_space.get_php_interp())

    def _getitem_str(self, index):
        assert False # XXX proper exception (accessing string key of py list)

    def _appenditem(self, w_obj, as_ref=False):
        self.wpy_list.append(w_obj.to_py(self.py_space.get_php_interp()))

    def _setitem_int(self, index, w_value, as_ref, unique_item=False):
        py_space = self.py_space
        wpy_val = w_value.to_py(py_space.get_php_interp())
        wpy_index = py_space.wrap(index)
        py_space.setitem(self.wpy_list, wpy_index, wpy_val)
        return self

    def _setitem_str(self, key, w_value, as_ref,
                     unique_array=False, unique_item=False):
        py_space = self.py_space
        wpy_val = w_value.to_py(py_space.get_php_interp())
        wpy_key = py_space.wrap(key)
        py_space.setitem(self.wpy_list, wpy_key, wpy_val)
        return self

    def create_iter(self, space, contextclass=None):
        return W_PyBridgeListProxyIterator(self.py_space, self.wpy_list)

    def to_py(self, interp):
        return self.wpy_list

class W_PyBridgeDictProxyIterator(BaseIterator):

    _immutable_fields_ = ["interp", "wpy_iter"]

    def __init__(self, py_space, rdct_w):
        self.py_space = py_space
        self.wpy_iter = rdct_w.iteritems()
        self.remaining = py_space.int_w(py_space.len(rdct_w))
        self.finished = self.remaining == 0

    def get_wrapped_py_obj(self):
        # Iterators can reasonably be considered opaque from a wrapping
        # perspective.
        return None

    def next(self, space):
        py_space = self.py_space
        self.remaining -= 1
        self.finished = self.remaining == 0
        wpy_v = self.wpy_iter.next_item()[1]
        return wpy_v.to_php(py_space.get_php_interp())

    def next_item(self, space):
        py_space = self.py_space
        interp = py_space.get_php_interp()
        self.remaining -= 1
        self.finished = self.remaining == 0
        wpy_k, wpy_v = self.wpy_iter.next_item()
        return wpy_k.to_php(interp), wpy_v.to_php(interp)

    def to_py(self, interp):
        return None

class W_PyBridgeDictProxy(W_ArrayObject):
    """ Wraps a Python dict as something PHP array. """

    _immutable_fields_ = ["py_space", "wpy_dict"]

    def __init__(self, py_space, wpy_dict):
        self.py_space = py_space
        self.wpy_dict = wpy_dict

    def get_wrapped_py_obj(self):
        return self.wpy_dict

    def arraylen(self):
        return self.py_space.int_w(self.py_space.len(self.wpy_dict))

    def _getitem_int(self, index):
        py_space = self.py_space
        wpy_val = py_space.getitem(self.wpy_dict, py_space.wrap(index))
        return wpy_val.to_php(py_space.get_php_interp())

    def _getitem_str(self, index):
        py_space = self.py_space
        wpy_val = py_space.getitem(self.wpy_dict, py_space.wrap(index))
        return wpy_val.to_php(py_space.get_php_interp())

    def _setitem_int(self, index, w_value, as_ref, unique_item=False):
        py_space = self.py_space
        wpy_val = w_value.to_py(py_space.get_php_interp())
        wpy_index = py_space.wrap(index)
        py_space.setitem(self.wpy_dict, wpy_index, wpy_val)
        return self

    def _setitem_str(self, key, w_value, as_ref,
                     unique_array=False, unique_item=False):
        py_space = self.py_space
        wpy_val = w_value.to_py(py_space.get_php_interp())
        wpy_key = py_space.wrap(key)
        py_space.setitem(self.wpy_dict, wpy_key, wpy_val)
        return self

    def create_iter(self, space, contextclass=None):
        return W_PyBridgeDictProxyIterator(self.py_space, self.wpy_dict)

    def to_py(self, interp):
        return self.wpy_dict
