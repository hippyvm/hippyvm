"""
The data structures defined here all wrap Python objects in some way so
that they can be used in PHP programs.
"""

from hippy.objects.instanceobject import W_InstanceObject
from hippy.klass import def_class
from hippy.builtin import wrap, Optional, wrap_method, ThisUnwrapper
from hippy.objects.base import W_Root as Wph_Root, W_Object as WPh_Object
from hippy.function import AbstractFunction
from hippy.module.pypy_bridge.conversion import py_to_php, php_to_py
from hippy.objects.iterator import W_BaseIterator
from hippy.objects.arrayobject import wrap_array_key, W_ArrayObject

from pypy.interpreter.argument import Arguments
from pypy.interpreter.error import OperationError

from rpython.rlib import jit


class W_EmbeddedPyFunc(AbstractFunction):
    _immutable_fields_ = ["interp", "py_callable"]

    def __init__(self, interp, py_callable):
        self.interp = interp
        self.py_callable = py_callable

    def get_wrapped_py_obj(self):
        return self.py_callable

    @jit.unroll_safe
    def call_args(self, interp, args_w, w_this=None, thisclass=None,
                  closureargs=None):

        wpy_args_elems = [ php_to_py(interp, x) for x in args_w ]

        # Methods are really just functions with self bound
        if w_this is not None:
            wpy_args_elems = [php_to_py(interp, w_this)] + wpy_args_elems

        rv = interp.pyspace.call_args(
                self.py_callable, Arguments(interp.pyspace, wpy_args_elems))
        return py_to_php(interp, rv)


    def needs_ref(self, i):
        return False # XXX reference args


class W_EmbeddedPyMod(WPh_Object):
    _immutable_fields_ = ["interp", "py_mod"]

    def __init__(self, interp, py_mod):
        self.interp = interp
        self.py_mod = py_mod

    def get_wrapped_py_obj(self):
        return self.py_mod

    def _getattr(self, interp, space, name):
        py_mod = self.py_mod
        pyspace = interp.pyspace
        try:
            w_obj = pyspace.getattr(py_mod, pyspace.wrap(name))
        except OperationError, e:
            if not e.match(pyspace, pyspace.w_AttributeError):
                raise
            raise space.ec.fatal("No such member %s in module" % name)
        return py_to_php(interp, w_obj)

    def getmeth(self, space, name, contextclass=None):
        return self._getattr(self.interp, space, name)

    def getattr(self, interp, name, contextclass=None, give_notice=False):
        return self._getattr(interp, interp.space, name)


class W_PyBridgeProxy(W_InstanceObject):
    _immutable_fields_ = ["interp?", "wpy_inst?"]

    def __init__(self, klass, dct_w):
        self.interp = None # set later
        self.wpy_inst = None # set later as we can't change the sig of __init__
        W_InstanceObject.__init__(self, klass, dct_w)

    def get_wrapped_py_obj(self):
        assert self.wpy_inst is not None
        return self.wpy_inst

    # Use this as a low level ctor instead of the above.
    @classmethod
    def from_wpy_inst(cls, interp, wpy_inst):
        wph_pxy = cls(interp, [])
        wph_pxy.set_instance(wpy_inst)
        return wph_pxy

    def setup_instance(self, interp, wpy_inst):
        self.interp = interp
        self.wpy_inst = wpy_inst

    def get_callable(self):
        """ PHP interpreter calls this when calls a wrapped Python var  """
        #assert isinstance(self.wpy_inst, Py_Function) # XXX exception

        # We trick the interpreter into seeing something that looks like
        # the kind of function that came from a PHP closure.
        ph_func = W_EmbeddedPyFunc(self.interp, self.wpy_inst)
        return ph_func

@wrap_method(['interp', ThisUnwrapper(W_PyBridgeProxy), str],
        name='PyBridgeProxy::__get')
def magic__get(interp, this, name):
    wpy_target = this.interp.pyspace.getattr(this.wpy_inst, this.interp.pyspace.wrap(name))
    return py_to_php(this.interp, wpy_target)

@wrap_method(['interp', ThisUnwrapper(W_PyBridgeProxy), str, Wph_Root],
        name='PyBridgeProxy::__call')
def magic__call(interp, this, func_name, wph_args):
    from hippy.interpreter import Interpreter
    assert isinstance(interp, Interpreter)

    wpy_func_name = interp.pyspace.wrap(func_name)
    wpy_func = interp.pyspace.getattr(this.wpy_inst, wpy_func_name)

    wpy_args_items = [ php_to_py(interp, x) for x in wph_args.as_list_w() ]
    wpy_rv = interp.pyspace.call(wpy_func, interp.pyspace.newlist(wpy_args_items))
    return py_to_php(interp, wpy_rv)

k_PyBridgeProxy = def_class('PyBridgeProxy',
    [magic__get, magic__call],
    [], instance_class=W_PyBridgeProxy
)

class W_PyBridgeListProxyIterator(W_BaseIterator):
    def __init__(self, interp, wpy_list):
        self.interp = interp
        self.storage_w = interp.pyspace.listview(wpy_list)
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
        return py_to_php(self.interp, wpy_value)

    def next_item(self, space):
        index = self.index
        wpy_value = self.storage_w[index]
        self.index = index + 1
        self.finished = self.index == len(self.storage_w)
        return space.wrap(index), py_to_php(self.interp, wpy_value)

class W_PyBridgeListProxy(W_ArrayObject):
    """ Wraps a Python list as PHP array. """

    _immutable_fields_ = ["interp", "wpy_list"]

    _has_string_keys = False

    def __init__(self, interp, wpy_list):
        self.interp = interp
        self.wpy_list = wpy_list

    def get_wrapped_py_obj(self):
        return self.wpy_list

    def arraylen(self):
        interp = self.interp
        return interp.pyspace.int_w(interp.pyspace.len(self.wpy_list))

    def _getitem_int(self, index):
        pyspace = self.interp.pyspace
        wpy_val = pyspace.getitem(self.wpy_list, pyspace.wrap(index))
        return py_to_php(self.interp, wpy_val)

    def create_iter(self, space, contextclass=None):
        return W_PyBridgeListProxyIterator(self.interp, self.wpy_list)

class W_PyBridgeDictProxyIterator(W_BaseIterator):
    def __init__(self, interp, rdct_w):
        pyspace = interp.pyspace
        self.interp = interp
        self.rdct_w = rdct_w

        wpy_dict_iteritems = pyspace.getattr(
                rdct_w, pyspace.wrap("iteritems"))
        self.wpy_iter = pyspace.call_args(
                wpy_dict_iteritems, Arguments(pyspace, []))
        self.wpy_iter_next = pyspace.getattr(
                self.wpy_iter, pyspace.wrap("next"))

        # constant offsets used often
        self.wpy_zero = pyspace.wrap(0)
        self.wpy_one = pyspace.wrap(1)

        self.remaining = pyspace.int_w(interp.pyspace.len(rdct_w))
        self.finished = self.remaining == 0

    def get_wrapped_py_obj(self):
        # Iterators can reasonably be considered opaque from a wrapping
        # perspective.
        return None

    def next(self, space):
        interp, pyspace = self.interp, self.interp.pyspace
        self.remaining -= 1
        self.finished = self.remaining == 0
        wpy_k_v = pyspace.call_args(
            self.wpy_iter_next, Arguments(pyspace, []))
        wpy_v = pyspace.getitem(wpy_k_v, self.wpy_one)
        return py_to_php(interp, wpy_v)

    def next_item(self, space):
        interp, pyspace = self.interp, self.interp.pyspace
        self.remaining -= 1
        self.finished = self.remaining == 0
        wpy_k_v = pyspace.call_args(
            self.wpy_iter_next, Arguments(pyspace, []))
        wpy_k = pyspace.getitem(wpy_k_v, self.wpy_zero)
        wpy_v = pyspace.getitem(wpy_k_v, self.wpy_one)
        return py_to_php(interp, wpy_k), py_to_php(interp, wpy_v)

class W_PyBridgeDictProxy(W_ArrayObject):
    """ Wraps a Python dict as something PHP array. """

    _immutable_fields_ = ["interp", "wpy_dict"]

    def __init__(self, interp, wpy_dict):
        self.interp = interp
        self.wpy_dict = wpy_dict

    def get_wrapped_py_obj(self):
        return self.wpy_dict

    def arraylen(self):
        interp = self.interp
        return interp.pyspace.int_w(interp.pyspace.len(self.wpy_dict))

    def _getitem_int(self, index):
        pyspace = self.interp.pyspace
        wpy_val = pyspace.getitem(self.wpy_dict, pyspace.wrap(index))
        return py_to_php(self.interp, wpy_val)

    def _getitem_str(self, index):
        pyspace = self.interp.pyspace
        wpy_val = pyspace.getitem(self.wpy_dict, pyspace.wrap(index))
        return py_to_php(self.interp, wpy_val)

    def create_iter(self, space, contextclass=None):
        return W_PyBridgeDictProxyIterator(self.interp, self.wpy_dict)

