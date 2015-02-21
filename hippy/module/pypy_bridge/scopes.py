from rpython.rlib import jit

from hippy.objects.base import W_Root as WPHP_Root
from hippy.objects.reference import W_Reference as Wpy_Reference

from pypy.interpreter.baseobjspace import W_Root as WPy_Root
from pypy.interpreter.typedef import TypeDef
from pypy.interpreter.gateway import interp2app


PHP_UNKNOWN = 0
PHP_FRAME   = 1
PHP_FUNC    = 2
PHP_CLASS   = 3
PHP_CONST   = 4
PHP_PARENT  = 5

class _Name_Map(object):
    _immutable_fields_ = ["name_map", "other_maps"]

    def __init__(self):
        self.name_map = {}
        self.other_maps = {}

    @jit.elidable_promote()
    def find(self, n):
        return self.name_map.get(n, -1)

    @jit.elidable
    def extend(self, n):
        if n not in self.other_maps:
            nm = _Name_Map()
            nm.name_map.update(self.name_map)
            nm.name_map[n] = len(self.name_map)
            self.other_maps[n] = nm
        return self.other_maps[n]


_EMPTY_MAP = _Name_Map()

class PHP_Scope(WPy_Root):
    _immutable_fields_ = ["ph_interp", "name_map?"]
    # ph_frame is in a sense immutable, but the elidable_promote on
    # _lookup_name_map then gets an indirect constant access to a virtualisable
    # which leads to bad things happening.

    def __init__(self, ph_interp, ph_frame):
        self.ph_interp = ph_interp
        self.ph_frame = ph_frame
        self.name_map = _EMPTY_MAP
        self.name_types = []

    def lookup_name_type(self, n):
        off = self.name_map.find(n)
        if off != -1:
            return self.name_types[off]
        return PHP_UNKNOWN

    def set_name_type(self, n, t):
        self.name_map = self.name_map.extend(n)
        self.name_types.append(t)

    def py_lookup(self, n):
        """Lookup 'n' in this scope and return it as a PyPy object or None
        if not found."""

        ph_interp = self.ph_interp
        ph_frame = self.ph_frame

        # If we've looked up n in the past, we use the same lookup scheme as
        # before.

        t = self.lookup_name_type(n)
        if t == PHP_FRAME:
            ph_v = self.ph_frame.lookup_ref_by_name_no_create(n)
            if ph_v is None:
                # Someone unset a variable.
                from hippy.module.pypy_bridge.bridge import _raise_php_bridgeexception
                _raise_php_bridgeexception(ph_interp,
                   "Variable '%s' has been unset" % n)
            return ph_v.to_py(self.ph_interp)
        elif t == PHP_FUNC:
            return ph_interp.lookup_function(n).to_py(ph_interp)
        elif t == PHP_CLASS:
            return ph_interp.lookup_class_or_intf(n).to_py(ph_interp)
        elif t == PHP_CONST:
            return ph_interp.lookup_constant(n).to_py(ph_interp)
        elif t == PHP_PARENT:
            return self.ph_frame.bytecode.py_scope.py_lookup(n)

        # If we haven't looked up n before, we have to slowly go through the
        # possibilities and see which one matches.

        assert t == PHP_UNKNOWN

        if ph_frame is not None:
            ph_v = ph_frame.lookup_ref_by_name_no_create(n)
            if ph_v is not None:
                self.set_name_type(n, PHP_FRAME)
                return ph_v.to_py(ph_interp)

        ph_v = ph_interp.lookup_function(n)
        if ph_v is not None:
            self.set_name_type(n, PHP_FUNC)
            return ph_v.to_py(ph_interp)

        ph_v = ph_interp.lookup_class_or_intf(n)
        if ph_v is not None:
            self.set_name_type(n, PHP_CLASS)
            return ph_v.to_py(ph_interp)

        ph_v = ph_interp.lookup_constant(n)
        if ph_v is not None:
            self.set_name_type(n, PHP_CONST)
            return ph_v.to_py(ph_interp)

        py_scope = ph_frame.bytecode.py_scope
        if py_scope is not None:
            self.set_name_type(n, PHP_PARENT)
            return py_scope.py_lookup(n)


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


    def ph_lookup(self, n):
        """Lookup 'n' in this scope and return it as a Hippy object or None
        if not found."""

        py_v = self.py_lookup(n)
        if py_v is not None:
            return py_v.to_php(self.py_interp.get_php_interp())
        return None


    def py_lookup(self, n):
        """Lookup 'n' in this scope and return it as a PyPy object or
        not found."""

        py_frame = self.py_frame
        py_interp = self.py_interp

        # Look in regular Python scope
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

        # Look in Python globals
        py_v = py_interp.finditem_str(py_frame.w_globals, n)

        if py_v is not None:
            return py_v

        php_scope = py_frame.php_scope
        if php_scope is not None:
            return php_scope.py_lookup(n)
        return None
