
from rpython.rlib import jit

from hippy.vars import W_Vars
from hippy.objects.base import W_Root
from hippy.objects.reference import W_Reference
from hippy.objects.arrayobject import new_rdict
from hippy.builtin_klass import W_ExceptionObject
from hippy.module.pypy_bridge.scopes import PHPScope
from hippy.module.pypy_bridge.py_adapters import W_PyExceptionAdapter

from pypy.interpreter.error import OperationError

class ExceptionHandler(object):
    def handle(self, w_exc, frame):
        raise NotImplementedError("Abstract base class")


class CatchBlock(ExceptionHandler):
    def __init__(self, exc_class, position, stackdepth):
        self.exc_class = exc_class
        self.position = position
        self.stackdepth = stackdepth

    def match(self, interp, w_exc):
        assert isinstance(w_exc, W_ExceptionObject)
        k_exc = w_exc.getclass()
        k_catch = interp.lookup_class_or_intf(self.exc_class, autoload=False)
        if k_catch is None:
            return False
        return k_exc.is_subclass_of_class_or_intf_name(k_catch.name)

    def py_match(self, frame, w_exc):
        'Try to match w_exc to a Python exception.'
        if not isinstance(w_exc, W_PyExceptionAdapter):
            return False

        interp = frame.interp
        # try python builtin if there is no py parent
        if frame.bytecode.py_scope is None:
            try:
                w_py_cls = interp.py_space.builtin.get(self.exc_class)
            except OperationError:
                return False
        else:
            ph_scope = PHPScope(interp, frame)
            # w_py_cls = ph_scope.py_lookup_local_recurse(self.exc_class)
            w_py_cls = frame.bytecode.py_scope.py_lookup_local(self.exc_class)
            if w_py_cls is None:
                w_py_cls = frame.bytecode.py_scope.py_lookup_global(self.exc_class)
                if w_py_cls is None:
                    return False

        return interp.py_space.isinstance_w(w_exc.w_py_exn, w_py_cls)


    @jit.unroll_safe
    def handle(self, w_exc, frame):
        if self.match(frame.interp, w_exc) or self.py_match(frame, w_exc):
            frame.pop_n(frame.stackpos - self.stackdepth)
            frame.push(w_exc)
            while frame.ptrs:
                frame.ptrs = frame.ptrs.ptr_next
            return self.position
        else:
            return -1


class Unsilence(ExceptionHandler):
    def __init__(self, error_level):
        self.prev_level = error_level

    def handle(self, w_exc, frame):
        if frame.interp.error_level == 0:
            frame.interp.error_level = self.prev_level
        return -1


class Frame(object):
    """ Frame implementation. Note that 'vars_w' and 'stack' can each
    store normal values or references.
    """
    _virtualizable_ = ['vars_w[*]', 'stack[*]', 'stackpos', 'f_backref',
                       'next_instr']
    _immutable_fields_ = ['unique_items',   # the list itself, not its content
                          '_contextclass',
                          'is_global_level', 'bytecode']

    is_global_level = False
    extra_variables = None
    args_w = None

    @jit.unroll_safe
    def __init__(self, interp, code, context=None,
                 thisclass=None, w_this=None, is_global_level=False):
        self = jit.hint(self, fresh_virtualizable=True, access_directly=True)
        self.interp = interp
        self.stack = [None] * code.stackdepth
        self.stackpos = 0
        self.bytecode = code
        self.init_contextclass(code)
        self.next_instr = 0
        self.known_line = -1  # set explicitly when there is a lineno but no next_instr
        self.ptrs = None     # chained list of BasePointers
        self.context = context  # the callable that is being executed
        self.thisclass = thisclass
        self.w_this = w_this
        self.is_global_level = is_global_level
        self.unique_items = [False] * len(code.varnames)
        self.vars_w = [None] * len(code.varnames)
        self.catch_blocks = []
        for num, i in enumerate(code.superglobals):
            if i >= 0:
                self.vars_w[i] = interp.superglobals[num]
        i = code.this_var_num
        if i >= 0:
            if w_this is None:
                self.vars_w[i] = None
            else:
                self.vars_w[i] = w_this

    def init_contextclass(self, code):
        if code.method_of_class is None:
            self._contextclass = None
        else:
            try:
                self._contextclass = code.method_of_class.try_current_class()
            except KeyError:
                raise self.interp.fatal("Internal error: call to %s::%s() "
                    "but the class definition was not met" % (
                        code.method_of_class.name, code.name))

    def get_contextclass(self):
        return self._contextclass

    def get_lineno(self):
        code = self.bytecode
        if self.known_line == -1:
            next_instr = min(self.next_instr, len(code.bc_mapping) - 1)
            return code.bc_mapping[next_instr]
        else:
            return self.known_line

    def get_position(self):
        code = self.bytecode
        funcname = code.name
        filename = code.filename
        return filename, funcname, self.get_lineno()

    def push(self, w_v):
        stackpos = jit.hint(self.stackpos, promote=True)
        assert w_v is None or isinstance(w_v, W_Root)
        self.stack[stackpos] = w_v
        self.stackpos = stackpos + 1

    def pop(self):
        stackpos = jit.hint(self.stackpos, promote=True) - 1
        assert stackpos >= 0
        res = self.stack[stackpos]
        #if self.stack[stackpos] is not None:
        #    self.stack[stackpos].mark_invalid()
        self.stack[stackpos] = None  # don't artificially keep alive stuff
        self.stackpos = stackpos
        return res

    @jit.unroll_safe
    def pop_n(self, count):
        stackpos = jit.hint(self.stackpos, promote=True) - count
        assert stackpos >= 0
        for i in range(count):
            self.stack[stackpos + i] = None
        self.stackpos = stackpos

    def clean(self, bytecode):
        "deprecated"

    def peek(self):
        stackpos = jit.hint(self.stackpos, promote=True) - 1
        assert stackpos >= 0
        return self.stack[stackpos]

    def peek_nth(self, n):
        # peek() == peek_nth(0)
        stackpos = jit.hint(self.stackpos, promote=True) + ~n
        assert stackpos >= 0
        return self.stack[stackpos]

    def poke_nth(self, n, w_obj):
        stackpos = jit.hint(self.stackpos, promote=True) + ~n
        assert stackpos >= 0
        assert isinstance(w_obj, W_Root) or w_obj is None
        self.stack[stackpos] = w_obj

    def push_ptr(self, p):
        # add the BasePointer 'p' to the head of the chained list '.ptrs'
        p.ptr_next = self.ptrs
        self.ptrs = p

    def pop_ptr(self):
        # pop the next BasePointer from the head of the chained list
        p = self.ptrs
        self.ptrs = p.ptr_next
        return p

    def peek_ptr(self):
        p = self.ptrs
        assert p is not None
        return p

    def lookup_variable_temp(self, no):
        """Note: same issues as deref_temp() on W_Reference: be careful
        when reading variables with this function if it's meant to be
        stored somewhere else."""
        assert no >= 0
        return self.vars_w[no]

    def lookup_deref(self, no, give_notice=False):
        w_var = self.lookup_variable_temp(no)
        if w_var is not None:
            if isinstance(w_var, W_Reference):
                return w_var.deref()
            else:
                self.unique_items[no] = False
                return w_var

        vn = self.bytecode.varnames[no] # varname
        py_scope = self.bytecode.py_scope
        if py_scope is not None:
            ph_v = py_scope.ph_lookup_local_recurse(vn)
            if ph_v is not None:
                return ph_v

        if give_notice:
            self.interp.notice("Undefined variable: %s" % vn)
        return self.interp.space.w_Null

    def lookup_deref_temp(self, no, give_notice=False):
        w_var = self.lookup_variable_temp(no)
        if w_var is not None:
            return w_var.deref_temp()
        else:
            if give_notice:
                self.interp.notice("Undefined variable: %s" % (
                    self.bytecode.varnames[no],))
            return self.interp.space.w_Null

    def store_variable(self, no, w_value, unique_item=False):
        """'w_value' must not be a reference."""
        assert not isinstance(w_value, W_Reference)
        assert no >= 0
        w_oldvalue = self.vars_w[no]
        if not isinstance(w_oldvalue, W_Reference):
            if not self.is_global_level:
                # common path inside functions
                self.vars_w[no] = w_value
                self.unique_items[no] = unique_item
                return
            else:
                # at global level, must wrap all variables into W_References
                w_ref = self.vars_w[no] = self.interp.space.empty_ref()
                globals = self.interp.globals
                globals.set_var(self.bytecode.varnames[no], w_ref)
                w_oldvalue = w_ref
        w_oldvalue.store(w_value, unique_item)

    def load_ref(self, no):
        """Return a W_Reference and force it on the frame if necessary."""
        w_value = self.lookup_variable_temp(no)
        if w_value is None:
            vn = self.bytecode.varnames[no] # varname
            py_scope = self.bytecode.py_scope
            if py_scope is not None:
                w_value = py_scope.ph_lookup_local_recurse(vn)

        if isinstance(w_value, W_Reference):
            return w_value
        r_value = self.interp.space.empty_ref()
        if w_value is not None:
            r_value.store(w_value, unique=self.unique_items[no])
        self.store_ref(no, r_value)
        return r_value

    def store_ref(self, no, w_ref):
        assert isinstance(w_ref, W_Reference)
        assert no >= 0
        self.vars_w[no] = w_ref
        #
        if self.is_global_level:
            # we just changed the reference stored into a local variable,
            # but if we are the main level, it means we need to change
            # as well the reference stored in interp.globals
            globals = self.interp.globals
            globals.set_var(self.bytecode.varnames[no], w_ref)

    def unset_ref(self, no):
        assert no >= 0
        self.vars_w[no] = None
        #
        if self.is_global_level:
            globals = self.interp.globals
            globals.unset_var(self.bytecode.varnames[no])

    def get_ref_by_name(self, name, create_new=True):
        """Get or create a reference to the variable `$name`."""
        no = self.bytecode.lookup_var_pos(name)
        if no == -1:
            ev = self.extra_variables
            if ev is None:
                if not create_new:
                    return None
                ev = self.extra_variables = W_Vars(self.interp.space)
            w_ref = ev.lookup_var(name)
            if w_ref is None:
                if not create_new:
                    return None
                w_ref = self.interp.space.empty_ref()
                ev.set_var(name, w_ref)
            return w_ref
        return self.load_ref(no)

    def lookup_ref_by_name(self, name):
        """Get an existing reference to the variable `$name`.

        Returns None if the variable does not exist.
        """
        no = self.bytecode.lookup_var_pos(name)
        if no == -1:
            ev = self.extra_variables
            if ev is None:
                return None
            return ev.lookup_var(name)
        return self.load_ref(no)

    def lookup_ref_by_name_no_create(self, name):
        """Get an existing reference to the variable `$name`.

        Returns None if the variable does not exist.
        """
        no = self.bytecode.lookup_var_pos(name)
        if no == -1:
            ev = self.extra_variables
            if ev is None:
                return None
            return ev.lookup_var(name)
        w_v = self.lookup_variable_temp(no)
        if w_v is None:
            return None
        elif isinstance(w_v, W_Reference):
            return w_v

        r_value = self.interp.space.empty_ref()
        r_value.store(w_v, unique=self.unique_items[no])
        self.store_ref(no, r_value)
        return r_value

    def set_ref_by_name(self, name, r_value):
        no = self.bytecode.lookup_var_pos(name)
        if no == -1:
            ev = self.extra_variables
            if ev is None:
                ev = self.extra_variables = W_Vars(self.interp.space)
            ev.set_var(name, r_value)
        else:
            assert no >= 0
            self.vars_w[no] = r_value

    def unset_ref_by_name(self, name):
        no = self.bytecode.lookup_var_pos(name)
        if no == -1:
            ev = self.extra_variables
            if ev is not None:
                ev.unset_var(name)
        else:
            self.unset_ref(no)

    @jit.unroll_safe
    def load_from_scope(self, scope):
        self.extra_variables = scope
        varnames = self.bytecode.varnames
        for i in range(len(varnames)):
            name = varnames[i]
            w_ref = scope.lookup_var(name)
            if w_ref is not None:
                self.vars_w[i] = w_ref

    @jit.unroll_safe
    def load_from_frame(self, frame):
        self.thisclass = frame.thisclass
        self.w_this = frame.w_this
        for i, name in enumerate(frame.bytecode.varnames):
            v = frame.vars_w[i]
            if v is not None:
                self.set_ref_by_name(name, frame.vars_w[i])
        if frame.extra_variables is not None:
            for name, r_value in frame.extra_variables.as_rdict().items():
                self.set_ref_by_name(name, r_value)

    @jit.unroll_safe
    def clear(self):
        for i in range(len(self.vars_w)):
            self.vars_w[i] = None
        self.extra_variables = None
