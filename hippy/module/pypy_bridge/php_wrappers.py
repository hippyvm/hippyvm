from hippy.objects.instanceobject import W_InstanceObject
from hippy.klass import def_class
from hippy.builtin import wrap, Optional, wrap_method, ThisUnwrapper
from hippy.objects.base import W_Root as Wph_Root
from hippy.function import AbstractFunction
from hippy.module.pypy_bridge.conversion import ph_of_py, py_of_ph

from pypy.interpreter.argument import Arguments

from rpython.rlib import jit


class W_EmbeddedPyFunc(AbstractFunction):
    def __init__(self, interp, py_callable):
        self.interp = interp
        self.py_callable = py_callable


    @jit.unroll_safe
    def call_args(self, interp, args_w, w_this=None, thisclass=None,
                  closureargs=None):

        wpy_args_elems = [ py_of_ph(interp, x) for x in args_w ]

        # Methods are really just functions with self bound
        if w_this is not None:
            wpy_args_elems = [py_of_ph(interp, w_this)] + wpy_args_elems

        rv = interp.pyspace.call_args(
                self.py_callable, Arguments(interp.pyspace, wpy_args_elems))
        return ph_of_py(interp, rv)


    def needs_ref(self, i):
        return False # XXX reference args


class W_PyBridgeProxy(W_InstanceObject):
    """ Wraps up a Python instance and offers a PHP friendly interface. """

    def __init__(self, klass, dct_w):
        self.wpy_inst = None # set later as we can't change the sig of __init__
        self.interp = None # set later
        W_InstanceObject.__init__(self, klass, dct_w)

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
    return ph_of_py(this.interp, wpy_target)

@wrap_method(['interp', ThisUnwrapper(W_PyBridgeProxy), str, Wph_Root],
        name='PyBridgeProxy::__call')
def magic__call(interp, this, func_name, wph_args):
    from hippy.interpreter import Interpreter
    assert isinstance(interp, Interpreter)

    wpy_func_name = interp.pyspace.wrap(func_name)
    wpy_func = interp.pyspace.getattr(this.wpy_inst, wpy_func_name)

    wpy_args_items = [ py_of_ph(interp, x) for x in wph_args.as_list_w() ]
    wpy_rv = interp.pyspace.call(wpy_func, interp.pyspace.newlist(wpy_args_items))
    return ph_of_py(interp, wpy_rv)

k_PyBridgeProxy = def_class('PyBridgeProxy',
    [magic__get, magic__call],
    [], instance_class=W_PyBridgeProxy
)
