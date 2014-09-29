from rpython.rlib import jit

from hippy.objects.arrayobject import new_rdict, W_RDictArrayObject
from hippy.objects.reference import W_Reference


class _Globals_Version(object): pass

class _Globals_Cell(object):
    def __init__(self, ref):
        self.ref = ref

class W_Globals(W_RDictArrayObject):
    """The $GLOBALS array."""

    # We model this as a normal array, so that $GLOBALS operates as expected,
    # with a shadow dictionary pointing at mutable cells. The shadow dictionary
    # allows us to make reads elidable (writes, however, remain somewhat
    # expensive).
    #
    # To get good performance for writes, we would need to subclass
    # W_RDictArrayObject and override all its methods so that nothing fiddles
    # with dct_w directly. Then we could turn everything to do with globals into
    # reading/writing from mutable cells.

    _immutable_fields_ = ["_globals_arr?", "_globals_map", "_globals_version?"]

    def __init__(self, space):
        W_RDictArrayObject.__init__(self, space, new_rdict(), 0)
        self._globals_map = {}
        self._globals_version = _Globals_Version()

    @jit.elidable
    def _get_cell(self, version, name):
        try:
            return self._globals_map[name]
        except KeyError:
            return None

    def as_unique_arraydict(self):
        return self

    def get_var(self, space, name, give_notice=False):
        cell = self._get_cell(jit.promote(self._globals_version), name)
        if cell is not None:
            return cell.ref
        r_glob = space.empty_ref()
        self._setitem_str(name, r_glob, as_ref=True)
        return r_glob

    def set_var(self, name, r_var):
        assert isinstance(r_var, W_Reference)
        self.dct_w[name] = r_var
        cell = self._get_cell(jit.promote(self._globals_version), name)
        if cell is None:
            self._globals_map[name] = _Globals_Cell(r_var)
            self._globals_version = _Globals_Version()
            return
        cell.ref = r_var

    def _setitem_str(self, key, w_value, as_ref, unique_item=False):
        if not as_ref:
            cell = self._get_cell(jit.promote(self._globals_version), key)
            if cell is not None:
                w_old = self.dct_w[key]
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

    def unset_var(self, name):
        try:
            del self.dct_w[name]
            del self._globals_map[name]
        except KeyError:
            return
        self._globals_version = _Globals_Version()

    def _unsetitem_str(self, key):
        self.unset_var(key)
        gframe = self.space.ec.interpreter.global_frame
        if gframe is not None:
            gframe.set_ref_by_name(key, None)
        return self

    def _inplace_pop(self, space):
        space.ec.hippy_warn("array_pop($GLOBALS) ignored")
        return space.w_Null
