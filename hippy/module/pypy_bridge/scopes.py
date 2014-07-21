from hippy.objects.reference import W_Reference as Wpy_Reference
from hippy.module.pypy_bridge.conversion import ph_of_py, py_of_ph

class PHP_Scope(object):
    def __init__(self, ph_interp, ph_frame):
        self.ph_interp = ph_interp
        self.ph_frame = ph_frame


    def py_lookup(self, n):
        """Lookup 'n' in this scope and return it as a PyPy object or None
        if not found."""

        ph_interp = self.ph_interp
        ph_frame = self.ph_frame
        ph_v = ph_frame.lookup_ref_by_name(n)
        if ph_v is not None:
            return py_of_ph(ph_interp, ph_v)

        # Search for PHP function of that name
        try:
            ph_v = self.ph_interp.lookup_function(n)
        except KeyError:
            pass
        else:
            return py_of_ph(ph_interp, ph_v)

        py_scope = ph_frame.bytecode.py_scope
        if py_scope is not None:
            return py_scope.py_lookup(n)

        return None


class Py_Scope(object):
    def __init__(self, py_interp, py_frame):
        self.py_interp = py_interp
        self.py_frame = py_frame


    def ph_lookup(self, n):
        """Lookup 'n' in this scope and return it as a Hippy object or None
        if not found."""

        py_v = self.py_lookup(n)
        if py_v is not None:
            return ph_of_py(self.py_interp.get_php_interp(), py_v)
        return None


    def py_lookup(self, n):
        """Lookup 'n' in this scope and return it as a PyPy object or
        not found."""

        py_frame = self.py_frame
        py_interp = self.py_interp

        # Look in regular Python scope
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
