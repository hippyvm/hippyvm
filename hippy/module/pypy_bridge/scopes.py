from rpython.rlib import jit

from hippy.objects.base import W_Root as WPHP_Root
from hippy.objects.reference import W_Reference as Wpy_Reference

from pypy.interpreter.baseobjspace import W_Root as WPy_Root
from pypy.interpreter.typedef import TypeDef
from pypy.interpreter.gateway import interp2app


PHP_UNKNOWN   = 0
PHP_FUNC      = 1
PHP_CLASS     = 2
PHP_CONST     = 3
PHP_NOT_FOUND = 4

class _Name_Map(object):
    _immutable_fields_ = ["name_map", "other_maps"]

    def __init__(self):
        self.name_map = {}
        self.other_maps = {}

    @jit.elidable
    def find(self, n):
        return self.name_map.get(n, PHP_UNKNOWN)

    @jit.elidable
    def extend(self, n, t):
        key = (n, t)
        if key not in self.other_maps:
            nm = _Name_Map()
            nm.name_map.update(self.name_map)
            nm.name_map[n] = t
            self.other_maps[key] = nm
        return self.other_maps[key]


_EMPTY_MAP = _Name_Map()

class PHP_Scope(WPy_Root):
    _immutable_fields_ = ["ph_interp"]
    # ph_frame is in a sense immutable, but the elidable_promote on
    # _lookup_name_map then gets an indirect constant access to a virtualisable
    # which leads to bad things happening.

    def __init__(self, ph_interp, ph_frame):
        self.ph_interp = ph_interp
        self.ph_frame = ph_frame
        self.name_map = _EMPTY_MAP

    def lookup_name_type(self, n):
        return jit.promote(self.name_map).find(n)

    def set_name_type(self, n, t):
        self.name_map = jit.promote(self.name_map).extend(n, t)

    @jit.unroll_safe
    def py_lookup_local_recurse(self, n):
        ph_scope = self
        while ph_scope is not None:
            py_v = ph_scope.ph_lookup_local(n)
            if py_v is not None:
                return py_v.to_py(self.ph_interp)
            py_scope = ph_scope.ph_frame.bytecode.py_scope
            if py_scope is None:
                return
            py_v = py_scope.py_lookup_local(n)
            if py_v is not None:
                return py_v
            ph_scope = py_scope.py_frame.php_scope

    # Same as py_lookup_local_recurse() just returning a PHP result
    def ph_lookup_local_recurse(self, n):
        w_res = self.py_lookup_local_recurse(n)
        if w_res is not None:
            return w_res.to_php(self.ph_interp)
        else:
            return None

    def py_store_local_recurse(self, n, py_v):
        ph_scope = self
        while ph_scope is not None:
            if ph_scope.py_set_local(n, py_v):
                return True
            raise NotImplementedError
            # XXX rest unwritten
            #if py_v is not None:
            #    return py_v.to_py(self.ph_interp)
            #py_scope = ph_scope.ph_frame.bytecode.py_scope
            #if py_scope is None:
            #    return
            #py_v = py_scope.py_lookup_local(n)
            #if py_v is not None:
            #    return py_v
            #ph_scope = py_scope.py_frame.php_scope

    def ph_lookup_local(self, n):
        return self.ph_frame.lookup_ref_by_name_no_create(n)

    def py_set_local(self, n, py_v):
        ref = self.ph_frame.lookup_ref_by_name_no_create(n)
        if ref is None:
            return False
        ref.store(py_v.to_php(self.ph_interp))
        return True

    def ph_lookup_global(self, n):
        ph_interp = self.ph_interp

        t = self.lookup_name_type(n)
        if t == PHP_FUNC:
            return ph_interp.lookup_function(n)
        elif t == PHP_CLASS:
            return ph_interp.lookup_class_or_intf(n)
        elif t == PHP_CONST:
            return ph_interp.lookup_constant(n)
        elif t == PHP_NOT_FOUND:
            return

        # If we haven't looked up n before, we have to slowly go through the
        # possibilities and see which one matches.

        assert t == PHP_UNKNOWN

        ph_v = ph_interp.lookup_function(n)
        if ph_v is not None:
            self.set_name_type(n, PHP_FUNC)
            return ph_v

        ph_v = ph_interp.lookup_class_or_intf(n)
        if ph_v is not None:
            self.set_name_type(n, PHP_CLASS)
            return ph_v

        ph_v = ph_interp.lookup_constant(n)
        if ph_v is not None:
            self.set_name_type(n, PHP_CONST)
            return ph_v


class W_PHPGlobalScope(WPy_Root):
    """Proxy the global PHP namespace."""

    _immutable_fields_ = ["interp"]

    def __init__(self, interp):
        self.interp = interp

    def get_php_interp(self):
        return self.interp

    def descr_get(self, w_name):
        ph_interp = self.interp
        py_space = ph_interp.py_space
        n = py_space.str_w(w_name)

        ph_v = ph_interp.lookup_function(n)
        if ph_v is not None:
            return ph_v.to_py(ph_interp)

        ph_v = ph_interp.lookup_class_or_intf(n)
        if ph_v is not None:
            return ph_v.to_py(ph_interp)

        ph_v = ph_interp.lookup_constant(n)
        if ph_v is not None:
            return ph_v.to_py(ph_interp)

        from hippy.module.pypy_bridge.bridge import _raise_php_bridgeexception
        _raise_php_bridgeexception(ph_interp, "Unknown PHP global variable '%s'" % n)

W_PHPGlobalScope.typedef = TypeDef("PHPGlobalScope",
    __getattr__ = interp2app(W_PHPGlobalScope.descr_get),
    #__setattr__ = interp2app(W_PHPGenericAdapter.descr_set),
)


class Py_Scope(WPHP_Root):
    _immutable_fields_ = ["py_interp"]
    # py_frame is not included in the immutable fields for the same reason as on
    # PHP_Scope.

    def __init__(self, py_interp, py_frame):
        self.py_interp = py_interp
        self.py_frame = py_frame

    @jit.unroll_safe
    def ph_lookup_local_recurse(self, n):
        py_scope = self
        while py_scope is not None:
            py_v = py_scope.py_lookup_local(n)
            if py_v is not None:
                return py_v.to_php(self.py_frame.space.get_php_interp())
            ph_scope = py_scope.py_frame.php_scope
            if ph_scope is None:
                return
            ph_v = ph_scope.ph_lookup_local(n)
            if ph_v is not None:
                return ph_v
            py_scope = ph_scope.ph_frame.bytecode.py_scope

    def ph_lookup_global(self, n):
        return self.py_lookup_global(n).to_php(self.py_frame.space.get_php_interp())

    def py_lookup_local(self, n):
        py_frame = self.py_frame
        py_interp = self.py_interp
        if py_frame.w_locals is None:
            # If no-one has called fast2locals, we can bypass the slow
            # dictionary lookup by accessing locals_stack_w directly.
            off = py_frame.pycode.get_var_off(n)
            if off >= 0:
                return py_frame.locals_stack_w[off]
        else:
            py_frame.fast2locals()
            py_v = py_interp.finditem_str(py_frame.w_locals, n)
            if py_v is not None:
                return py_v

    def py_lookup_global(self, n):
        py_frame = self.py_frame
        py_interp = self.py_interp

        py_v = py_interp.finditem_str(py_frame.w_globals, n)
        if py_v is not None:
            return py_v

        py_v = py_frame.get_builtin().getdictvalue(py_frame.space, n)
        if py_v is not None:
            return py_v

