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
from hippy.builtin_klass import W_ExceptionObject, k_Exception

from pypy.interpreter.argument import Arguments
from pypy.interpreter.error import OperationError
from pypy.objspace.std.listobject import W_ListObject as WPy_ListObject

from rpython.rlib import jit


class W_PyProxyGeneric(W_InstanceObject):
    """Generic proxy for wrapping Python objects in Hippy when no more specific
    proxy is available."""

    _immutable_fields_ = ["interp", "w_py_inst"]

    def setup_instance(self, interp, w_py_inst):
        self.interp = interp
        self.w_py_inst = w_py_inst

    def get_wrapped_py_obj(self):
        return self.w_py_inst

    # Use this as a low level ctor instead of the above.
    @classmethod
    def from_w_py_inst(cls, interp, w_py_inst):
        w_php_pxy = cls(interp, [])
        w_php_pxy.set_instance(w_py_inst)
        return w_php_pxy

    def get_callable(self):
        """ PHP interpreter calls this when calls a wrapped Python var  """
        return W_EmbeddedPyCallable(self.w_py_inst)

    def to_py(self, interp):
        return self.w_py_inst

@wrap_method(['interp', ThisUnwrapper(W_PyProxyGeneric), str],
        name='GenericPyProxy::__get')
def generic__get(interp, this, name):
    interp = this.interp
    py_space = interp.py_space
    w_py_target = py_space.getattr(this.w_py_inst, py_space.wrap(name))
    return w_py_target.to_php(interp)

@wrap_method(['interp', ThisUnwrapper(W_PyProxyGeneric), str, Wph_Root],
        name='GenericPyProxy::__call')
@jit.unroll_safe
def generic__call(interp, this, func_name, w_php_args):
    from hippy.interpreter import Interpreter
    assert isinstance(interp, Interpreter)

    py_space = interp.py_space
    w_py_func_name = py_space.wrap(func_name)
    w_py_func = py_space.getattr(this.w_py_inst, w_py_func_name)

    w_py_args_items = [ x.to_py(interp) for x in w_php_args.as_list_w() ]
    w_py_rv = interp.py_space.call(w_py_func, interp.py_space.newlist(w_py_args_items))
    return w_py_rv.to_php(interp)

k_PyBridgeProxy = def_class('PyBridgeProxy',
    [generic__get, generic__call],
    [], instance_class=W_PyProxyGeneric
)

class W_EmbeddedPyCallable(W_InvokeCall):

    _immutable_fields_ = [ "w_py_func" ]

    def __init__(self, w_py_func):
        W_InvokeCall.__init__(self, None, None, None)
        self.w_py_func = w_py_func

    @jit.unroll_safe
    def call_args(self, interp, args_w,
            w_this=None, thisclass=None, closureargs=None):

        py_space = interp.py_space

        w_py_args_elems = [ x.to_py(interp) for x in args_w ]

        try:
            rv = py_space.call_args(
                    self.w_py_func, Arguments(py_space, w_py_args_elems))
        except OperationError as e:
            # Convert the Python exception to a PHP one.
            w_py_exn = e.get_w_value(py_space)
            w_php_exn = w_py_exn.to_php(interp)
            from hippy.error import Throw
            raise Throw(w_php_exn)

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
                "W_EmbeddedPyFunc object cannot have properties")

    def setattr_ref(self, interp, attr, w_value, contextclass):
        interp.catchable_fatal(
                "W_EmbeddedPyFunc object cannot have properties")

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

    def __init__(self, py_space, w_py_list):
        self.py_space = py_space
        self.storage_w = py_space.listview(w_py_list)
        self.index = 0
        self.finished = len(self.storage_w) == 0

    def get_wrapped_py_obj(self):
        # Iterators can reasonably be considered opaque from a wrapping
        # perspective.
        return None

    def next(self, space):
        index = self.index
        w_py_value = self.storage_w[index]
        self.index = index + 1
        self.finished = self.index == len(self.storage_w)
        return w_py_value.to_php(self.py_space.get_php_interp())

    def next_item(self, space):
        index = self.index
        w_py_value = self.storage_w[index]
        self.index = index + 1
        self.finished = self.index == len(self.storage_w)
        return space.wrap(index), w_py_value.to_php(self.py_space.get_php_interp())

class W_PyBridgeListProxy(W_ArrayObject):
    """ Wraps a Python list as PHP array. """

    _immutable_fields_ = ["py_space", "w_py_list"]

    _has_string_keys = False

    def __init__(self, py_space, w_py_list):
        assert isinstance(w_py_list, WPy_ListObject)
        self.py_space = py_space
        self.w_py_list = w_py_list

    def get_wrapped_py_obj(self):
        return self.w_py_list

    def arraylen(self):
        py_space = self.py_space
        return py_space.int_w(py_space.len(self.w_py_list))

    def copy(self):
        # used for copy on write semantics of PHP
        w_py_list_copy = self.w_py_list.clone()
        return W_PyBridgeListProxy(self.py_space, w_py_list_copy)

    def _getitem_int(self, index):
        py_space = self.py_space
        w_py_val = py_space.getitem(self.w_py_list, py_space.wrap(index))
        return w_py_val.to_php(py_space.get_php_interp())

    def _getitem_str(self, index):
        from hippy.module.pypy_bridge.bridge import _raise_php_bridgeexception
        _raise_php_bridgeexception(self.py_space.get_php_interp(),
               "Cannot access string keys of wrapped Python list")

    def _appenditem(self, w_obj, as_ref=False):
        self.w_py_list.append(w_obj.to_py(self.py_space.get_php_interp()))

    def _setitem_int(self, index, w_value, as_ref, unique_item=False):
        py_space = self.py_space
        w_py_val = w_value.to_py(py_space.get_php_interp())
        w_py_index = py_space.wrap(index)
        py_space.setitem(self.w_py_list, w_py_index, w_py_val)
        return self

    def _setitem_str(self, key, w_value, as_ref, unique_item=False):
        from hippy.module.pypy_bridge.bridge import _raise_php_bridgeexception
        _raise_php_bridgeexception(self.py_space.get_php_interp(),
               "Cannot set string keys of wrapped Python list")

    def create_iter(self, space, contextclass=None):
        return W_PyBridgeListProxyIterator(self.py_space, self.w_py_list)

    def to_py(self, interp):
        return self.w_py_list

class W_PyBridgeDictProxyIterator(BaseIterator):

    _immutable_fields_ = ["interp", "w_py_iter"]

    def __init__(self, py_space, rdct_w):
        self.py_space = py_space
        self.w_py_iter = rdct_w.iteritems()
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
        w_py_v = self.w_py_iter.next_item()[1]
        return w_py_v.to_php(py_space.get_php_interp())

    def next_item(self, space):
        py_space = self.py_space
        interp = py_space.get_php_interp()
        self.remaining -= 1
        self.finished = self.remaining == 0
        w_py_k, w_py_v = self.w_py_iter.next_item()
        return w_py_k.to_php(interp), w_py_v.to_php(interp)

    def to_py(self, interp):
        return None

class W_PyBridgeDictProxy(W_ArrayObject):
    """ Wraps a Python dict as something PHP array. """

    _immutable_fields_ = ["py_space", "w_py_dict"]

    def __init__(self, py_space, w_py_dict):
        self.py_space = py_space
        self.w_py_dict = w_py_dict

    def copy(self):
        # used for copy on write semantics of PHP
        w_py_dict_copy = self.w_py_dict.descr_copy(self.py_space)
        return W_PyBridgeDictProxy(self.py_space, w_py_dict_copy)

    def get_wrapped_py_obj(self):
        return self.w_py_dict

    def arraylen(self):
        return self.py_space.int_w(self.py_space.len(self.w_py_dict))

    def _getitem_int(self, index):
        py_space = self.py_space
        w_py_val = py_space.getitem(self.w_py_dict, py_space.wrap(index))
        return w_py_val.to_php(py_space.get_php_interp())

    def _getitem_str(self, index):
        py_space = self.py_space
        w_py_val = py_space.getitem(self.w_py_dict, py_space.wrap(index))
        return w_py_val.to_php(py_space.get_php_interp())

    def _setitem_int(self, index, w_value, as_ref, unique_item=False):
        py_space = self.py_space
        w_py_val = w_value.to_py(py_space.get_php_interp())
        w_py_index = py_space.wrap(index)
        py_space.setitem(self.w_py_dict, w_py_index, w_py_val)
        return self

    def _setitem_str(self, key, w_value, as_ref, unique_item=False):
        py_space = self.py_space
        w_py_val = w_value.to_py(py_space.get_php_interp())
        w_py_key = py_space.wrap(key)
        py_space.setitem(self.w_py_dict, w_py_key, w_py_val)
        return self

    def create_iter(self, space, contextclass=None):
        return W_PyBridgeDictProxyIterator(self.py_space, self.w_py_dict)

    def to_py(self, interp):
        return self.w_py_dict

class W_PyException(W_ExceptionObject):
    """ Wraps up a Python exception """

    _immutable_fields_ = ["w_py_exn"]

    def __init__(self, klass, dct_w):
        W_ExceptionObject.__init__(self, klass, dct_w)
        self.w_py_exn = None

    def set_w_py_exception(self, php_interp, w_py_exn):
        W_ExceptionObject.setup(self, php_interp)
        self.w_py_exn = w_py_exn

        php_space, py_space = php_interp.space, php_interp.py_space

        # XXX these need to be properly populated to give the user a
        # meaningful error message. The comments show how these fields
        # would be populated if they were a standard PHP exception.

        #this.setattr(interp, 'file', space.wrap(this.traceback[0][0]), k_Exception)
        self.file = None

        #this.setattr(interp, 'line', space.wrap(this.traceback[0][2]), k_Exception)
        self.line = -1

        #this.setattr(interp, 'message', space.wrap(message), k_Exception)
        w_py_exn_str = py_space.getattr(self.w_py_exn, py_space.wrap("message"))
        msg = py_space.str_w(w_py_exn_str)
        self.setattr(php_interp, 'message', php_space.wrap(msg), k_PyException)

        #this.setattr(interp, 'code', space.wrap(code), k_Exception)
        self.code = None

@wrap_method(['interp', ThisUnwrapper(W_PyException)], name='PyException::getMessage')
def w_py_exc_getMessage(interp, this):
    return this.getattr(interp, "message")

k_PyException = def_class('PyException',
    [w_py_exc_getMessage], [], instance_class=W_PyException)

from hippy.builtin_klass import k_Exception
# Indicates an error in PHP->Py glue code
k_BridgeException = def_class('BridgeException', [], [], extends=k_Exception)
