"""A cache for immutable values (functions, constants, and classes).
These are immutable for a given interpreter, but may possibly change
if we run multiple Interpreters in sequence.  This logic allows the
JIT-compiled machine code to quickly check if we're in the common
case of seeing the same value as previously.
"""

from rpython.rlib import jit


class ImmutCell(object):
    _immutable_fields_ = ['constant_value', 'is_builtin']

    _class_key = (None, None, None)

    def __init__(self, constant_value, is_builtin=False):
        assert constant_value is not None
        self.constant_value = constant_value
        self.currently_declared = constant_value
        self.constant_value_is_currently_declared = True
        self.is_builtin = is_builtin

    def get_current_value(self):
        if self.is_builtin or self.constant_value_is_currently_declared:
            return self.constant_value     # constant-folded
        else:
            return self.currently_declared


class GlobalImmutCache(object):

    def __init__(self, space, initdict={}, force_lowcase=True):
        self.space = space
        self.all_cells = {}
        self.force_lowcase = force_lowcase
        for key, value in initdict.items():
            self.set_builtin(key, value)

    def set_builtin(self, name, value):
        self.set_cell(name, ImmutCell(value, is_builtin=True))

    def reset(self):
        # un-declare every non-builtin value
        for cell in self.all_cells.itervalues():
            if not cell.is_builtin:
                cell.currently_declared = None
                cell.constant_value_is_currently_declared = False

    @jit.elidable
    def get_cell(self, name):
        if self.force_lowcase:
            name = name.lower()
        try:
            return self.all_cells[name]
        except KeyError:
            return None

    def set_cell(self, name, newcell):
        if self.force_lowcase:
            name = name.lower()
        assert name not in self.all_cells
        self.all_cells[name] = newcell

    def has_definition(self, name):
        cell = self.get_cell(name)
        if cell is None:
            return False
        return cell.currently_declared is not None

    def locate(self, name):
        cell = self.get_cell(name)
        if cell is None:
            return None
        return cell.get_current_value()

    def declare_new(self, name, value):
        assert value is not None
        cell = self.get_cell(name)
        if cell is None:
            cell = ImmutCell(value)
            self.set_cell(name, cell)
        else:
            assert cell.currently_declared is None
            assert not cell.constant_value_is_currently_declared
            cell.currently_declared = value
            cell.constant_value_is_currently_declared = (
                value is cell.constant_value)
        return cell

    def create_class(self, interp, name, decl, key):
        "Special case for classes"
        cell = self.get_cell(name)
        if cell is not None:
            if cell._class_key == key:
                cell.currently_declared = cell.constant_value
                cell.constant_value_is_currently_declared = True
                decl.redefine_old_class(interp, cell.constant_value)
                return
        kls = decl.define_new_class(interp)
        cell = self.declare_new(name, kls)
        decl._immut_cell = cell
        if cell.constant_value_is_currently_declared:
            cell._class_key = key
