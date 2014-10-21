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

class NameMapVersion(object): pass

class PHP_Scope(WPy_Root):
    _immutable_fields_ = ["ph_interp", "ph_frame", "name_map"]

    def __init__(self, ph_interp, ph_frame):
        self.ph_interp = ph_interp
        self.ph_frame = ph_frame
        self.name_map = {}
        self.name_map_version = NameMapVersion()


    @jit.elidable_promote()
    def _lookup_name_map(self, n, version):
        try:
            return self.name_map[n]
        except KeyError:
            return PHP_UNKNOWN

    def _update_name_map(self, n, t):
        assert n not in self.name_map
        self.name_map[n] = t
        self.name_map_version = NameMapVersion()


    def py_lookup(self, n):
        """Lookup 'n' in this scope and return it as a PyPy object or None
        if not found."""

        ph_interp = self.ph_interp
        ph_frame = self.ph_frame

        # If we've looked up n in the past, we use the same lookup scheme as
        # before.

        t = self._lookup_name_map(n, self.name_map_version)
        if t == PHP_FRAME:
            ph_v = self.ph_frame.lookup_ref_by_name(n)
            if ph_v is None:
                # Someone unset a variable. Raise an exception?
                assert False
            return ph_v.to_py(self.ph_interp)
        elif t == PHP_FUNC:
            return ph_interp.lookup_function(n).to_py(ph_interp)
        elif t == PHP_CLASS:
            return ph_interp.lookup_class_or_intf(n, autoload=False).to_py(ph_interp)
        elif t == PHP_CONST:
            return ph_interp.lookup_constant(n).to_py(ph_interp)
        elif t == PHP_PARENT:
            return self.ph_frame.bytecode.py_scope.py_lookup(n)

        # If we haven't looked up n before, we have to slowly go through the
        # possibilities and see which one matches.

        assert t == PHP_UNKNOWN

        ph_v = ph_frame.lookup_ref_by_name(n)
        if ph_v is not None:
            self._update_name_map(n, PHP_FRAME)
            return ph_v.to_py(ph_interp)

        ph_v = ph_interp.lookup_function(n)
        if ph_v is not None:
            self._update_name_map(n, PHP_FUNC)
            return ph_v.to_py(ph_interp)

        ph_v = ph_interp.lookup_class_or_intf(n)
        if ph_v is not None:
            self._update_name_map(n, PHP_CLASS)
            return ph_v.to_py(ph_interp)

        ph_v = ph_interp.lookup_constant(n)
        if ph_v is not None:
            self._update_name_map(n, PHP_CONST)
            return ph_v.to_py(ph_interp)

        assert ph_frame.bytecode.py_scope
        py_scope = ph_frame.bytecode.py_scope
        if py_scope is not None:
            self._update_name_map(n, PHP_PARENT)
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

        print "can't find", n
        assert False

W_PHPGlobalScope.typedef = TypeDef("PHPGlobalScope",
    __getattr__ = interp2app(W_PHPGlobalScope.descr_get),
    #__setattr__ = interp2app(W_PHPProxyGeneric.descr_set),
)


class Py_Scope(WPHP_Root):
    _immutable_fields_ = ["py_interp", "py_frame"]

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
            co = py_frame.pycode
            try:
                off = co.getvarnames().index(n)
            except ValueError:
                pass
            else:
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
