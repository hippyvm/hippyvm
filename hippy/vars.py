from collections import OrderedDict

from rpython.rlib import jit

from hippy.objects.arrayobject import new_rdict, W_RCellDictArrayObject
from hippy.objects.reference import W_Reference



class W_Vars(W_RCellDictArrayObject):
    """An array of variables."""

    def __init__(self, space):
        W_RCellDictArrayObject.__init__(self, space, OrderedDict(), 0)

    def as_unique_arraydict(self):
        return self

    def _inplace_pop(self, space):
        space.ec.hippy_warn("array_pop($GLOBALS) ignored")
        return space.w_Null

    def has_var(self, name):
        if self.lookup_cell(name):
            return True
        return False

    def lookup_var(self, name):
        c = self.lookup_cell(name)
        if c is not None:
            return c.v
        return None

    def get_var(self, name, give_notice=False):
        c = self.lookup_cell(name)
        if c is not None:
            return c.v
        r = self.space.empty_ref()
        self._setitem_str(name, r, as_ref=True)
        return r

    def set_var(self, name, w_v):
        self.set_cell(name, w_v)

    def _setitem_str(self, key, w_value, as_ref, unique_item=False):
        if not as_ref:
            c = self.lookup_cell(key)
            if c is not None:
                w_old = c.v
                assert isinstance(w_old, W_Reference)
                w_old.store(w_value, unique_item)
                return self
            w_value = W_Reference(w_value)
        assert isinstance(w_value, W_Reference)
            
    def unset_var(self, name):
        self.unset_cell(name)


class W_GlobalVars(W_Vars):
    """An array of global variables. Writes to this also update the global variable
    slots.
    """

    def _setitem_str(self, key, w_value, as_ref, unique_item=False):
        if not as_ref:
            c = self.lookup_cell(key)
            if c is not None:
                w_old = c.v
                assert isinstance(w_old, W_Reference)
                w_old.store(w_value, unique_item)
                return self
            w_value = W_Reference(w_value)
        assert isinstance(w_value, W_Reference)

        self.set_var(key, w_value)
        gframe = self.space.ec.interpreter.global_frame
        if gframe is not None:
            gframe.set_ref_by_name(key, w_value)
        return self

    def _unsetitem_str(self, key):
        gframe = self.space.ec.interpreter.global_frame
        if gframe is not None:
            gframe.set_ref_by_name(key, None)
        return self
