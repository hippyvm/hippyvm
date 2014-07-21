from pypy.interpreter.baseobjspace import W_Root
from pypy.interpreter.typedef import TypeDef
from pypy.interpreter.gateway import interp2app, unwrap_spec
from pypy.interpreter.function import Function as Py_Function

from hippy.objects.arrayobject import W_ArrayObject
from hippy.module.pypy_bridge.conversion import py_of_ph, ph_of_py
from hippy.objects.iterator import W_BaseIterator

from rpython.rlib import jit


class W_EmbeddedPHPFunc(W_Root):
    """ A Python callable that actually executes a PHP function """
    def __init__(self, space, wph_func):
        self.space = space
        self.wph_func = wph_func

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

        wph_args_elems = [ ph_of_py(php_interp, x) for x in args ]
        res = self.wph_func.call_args(php_interp, wph_args_elems)

        return py_of_ph(php_interp, res)

W_EmbeddedPHPFunc.typedef = TypeDef("EmbeddedPHPFunc",
    __call__ = interp2app(W_EmbeddedPHPFunc.descr_call),
)



class W_PhBridgeProxy(W_Root):
    """ Wraps up a PHP instance and offers a Python friendly interface. """

    def __init__(self, interp, wph_inst):
        self.wph_inst = wph_inst
        self.interp = interp

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

        return py_of_ph(self.interp, wph_target)

    @jit.unroll_safe
    def descr_call(self, __args__):
        wpy_args, wpy_kwargs = __args__.unpack()
        assert not wpy_kwargs # XXX exception

        wph_args_elems = [ ph_of_py(self.interp, x) for x in wpy_args ]
        wph_rv = self.wph_inst.call_args(self.interp, wph_args_elems)
        return py_of_ph(self.interp, wph_rv)

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

class W_PyBridgeListProxyIterator(W_BaseIterator):

    def __init__(self, interp, wpy_list):
        self.interp = interp
        self.storage_w = interp.pyspace.listview(wpy_list)
        self.index = 0
        self.finished = len(self.storage_w) == 0

    def next(self, space):
        index = self.index
        wpy_value = self.storage_w[index]
        self.index = index + 1
        self.finished = self.index == len(self.storage_w)
        return ph_of_py(self.interp, wpy_value)

    def next_item(self, space):
        index = self.index
        wpy_value = self.storage_w[index]
        self.index = index + 1
        self.finished = self.index == len(self.storage_w)
        return space.wrap(index), ph_of_py(self.interp, wpy_value)

class W_PyBridgeListProxy(W_ArrayObject):
    """ Wraps a Python list as PHP array. """

    _has_string_keys = False

    def __init__(self, interp, wpy_list):
        self.interp = interp
        self.wpy_list = wpy_list

    def arraylen(self):
        interp = self.interp
        return interp.pyspace.int_w(interp.pyspace.len(self.wpy_list))

    def _getitem_int(self, index):
        pyspace = self.interp.pyspace
        wpy_val = pyspace.getitem(self.wpy_list, pyspace.wrap(index))
        return ph_of_py(self.interp, wpy_val)

    def create_iter(self, space, contextclass=None):
        return W_PyBridgeListProxyIterator(self.interp, self.wpy_list)

class W_PyBridgeDictProxy(W_ArrayObject):
    """ Wraps a Python dict as something PHP array. """

    _has_string_keys = False

    def __init__(self, interp, wpy_dict):
        self.interp = interp
        self.wpy_dict = wpy_dict

    def arraylen(self):
        interp = self.interp
        return interp.pyspace.int_w(interp.pyspace.len(self.wpy_dict))

    def _getitem_int(self, index):
        assert type(index) == int
        pyspace = self.interp.pyspace
        wpy_val = pyspace.getitem(self.wpy_dict, pyspace.wrap(index))
        return ph_of_py(self.interp, wpy_val)

    def _getitem_str(self, index):
        assert type(index) == str
        pyspace = self.interp.pyspace
        wpy_val = pyspace.getitem(self.wpy_dict, pyspace.wrap(index))
        return ph_of_py(self.interp, wpy_val)


