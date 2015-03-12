
from hippy.error import InterpreterError, OffsetError

class W_Root(object):
    """ The base class for everything that can be represented as a first-class
    object at applevel
    """
    _attrs_ = ()

    def deref(self):
        return self  # anything but a reference

    def deref_temp(self):
        return self  # anything but a reference

    def deref_unique(self):
        return self  # anything but a reference

    def copy_item(self):
        return self

    def eval_static(self, space):
        """Evaluate for use as a default value"""
        raise TypeError("This object cannot be used as a default value")

    def _note_making_a_copy(self):
        pass       # for test_refcount

    def get_wrapped_py_obj(self):
        """If this object wraps a PyPy object, it returns that object;
        otherwise it returns None."""
        return None

    def call_args(self, interp, args_w, w_this=None, thisclass=None,
                  closureargs=None):
        raise NotImplementedError("abstract")

class W_Object(W_Root):
    _attrs_ = ()
    supports_arithmetics = False

    def eval_static(self, space):
        return self

    def copy(self):
        return self

    def store(self, w_value, unique=False):
        raise InterpreterError("Reference to something that's not a variable")

    def int_w(self, space):
        raise InterpreterError("TypeError: casting to int of wrong type")

    def float_w(self, space):
        return float(self.int_w(space))

    def getchar(self, space):
        raise InterpreterError("TypeError: casting to string of wrong type")
        # XXX cast to string, get first char

    def _msg_misuse_as_array(self, space, compat=True):
        if compat and self.is_scalar(space):
            return 'Cannot use a scalar value as an array'
        else:
            return 'Cannot use %s as an array' % (space.gettypename(self),)

    def _lookup_item_ref(self, space, w_arg):
        return None

    def getitem(self, space, w_arg, give_notice=False, allow_undefined=True):
        if give_notice:
            space.ec.hippy_warn(self._msg_misuse_as_array(space, False))
        return space.w_Null

    def setitem2_maybe_inplace(self, space, w_arg, w_value, unique_item=False):
        space.ec.warn(self._msg_misuse_as_array(space))
        return self, space.w_Null

    def _setitem_ref(self, space, w_arg, w_ref):
        space.ec.warn(self._msg_misuse_as_array(space))
        raise OffsetError('cannot index non-array')

    def appenditem_inplace(self, space, w_item, as_ref=False):
        space.ec.warn(self._msg_misuse_as_array(space))
        return space.w_Null

    def packitem_maybe_inplace(self, space, w_arg, w_value):
        space.ec.warn(self._msg_misuse_as_array(space))
        return self

    def hasitem(self, space, w_index):
        r_value = self._lookup_item_ref(space, w_index)
        if r_value is None:
            return False
        return (r_value.deref_temp() is not space.w_Null)

    def _unsetitem(self, space, w_arg):
        space.ec.hippy_warn(self._msg_misuse_as_array(space, False))
        return self

    def getmeth(self, space, name, contextclass=None, for_callback=None):
        raise space.ec.fatal("Call to a member function %s() on a non-object" % name)

    def is_true(self, space):
        raise InterpreterError("unsupported is_true")

    def as_number(self, space):
        raise InterpreterError("unsupported as_number")

    def str(self, space, quiet=False):
        """Convert the object to an unwrapped string"""
        raise InterpreterError("Unimplemented str()")

    def repr(self):
        """A short representation of the object"""
        raise InterpreterError("Unimplemented repr()")

    def as_string(self, space, quiet=False):
        return space.newstr(self.str(space, quiet=quiet))

    def maybe_str(self, space):
        return self.str(space, quiet=True)

    def as_stringoffset(self, space, give_notice):
        if self.is_scalar(space):
            if give_notice:
                space.ec.notice('String offset cast occurred')
            return self.int_w(space)
        else:
            if give_notice:
                space.ec.warn('Illegal offset type')
                return 0
            else:
                return -1

    def is_scalar(self, space):
        return self.tp in (space.tp_int, space.tp_float, space.tp_null,
                space.tp_bool)

    def abs(self, space):
        return self.as_number(space).abs(space)

    def uplus(self, space):
        raise InterpreterError("unsupport uplus")

    def uminus(self, space):
        raise InterpreterError("unsupport uminus")

    def uplusplus(self, space):
        raise InterpreterError("unsupport uplusplus")

    def uminusminus(self, space):
        return self    # by default, does nothing

    def bitwise_not(self, space):
        raise space.ec.fatal("Unsupported operand types")

    def getattr(self, interp, name, contextclass=None, give_notice=False, fail_with_none=False):
        if give_notice:
            interp.notice('Trying to get property of non-object')
        return interp.space.w_Null

    def getattr_ref(self, interp, name, contextclass=None, fail_with_none=False):
        """Get an attribute by reference

        Implements e.g. ... =& $x->attr
        Returns the new value of $x and the reference.
        """
        interp.warn('Attempt to modify property of non-object')
        return interp.space.empty_ref()

    def setattr(self, interp, attr, w_value, contextclass, unique_item=False):
        """Implements $x->attr = ...

        Returns the new value of $x and the value of the expression
        """
        interp.warn('Attempt to assign property of non-object')
        return interp.space.w_Null

    def setattr_ref(self, interp, attr, w_newvalue, contextclass):
        """Implements $x->attr =& ...

        Returns the new value of $x and the value of the expression
        """
        interp.warn('Attempt to modify property of non-object')
        return interp.space.w_Null

    def hasattr(self, interp, attr, contextclass):
        """Implements isset($x->attr)"""
        #XXX: Warning?
        return False

    def delattr(self, interp, attr, contextclass):
        """Implements unset($x->attr)"""
        #XXX: Warning?
        pass

    def strlen(self):
        raise InterpreterError("unsupported strlen")

    def arraylen(self):
        raise InterpreterError("unsupported arraylen")

    def append(self, space, w_item):
        raise InterpreterError("unsupported append")

    def create_iter(self, space, contextclass=None):
        space.ec.warn("Invalid argument supplied for foreach()")
        return None

    def create_iter_ref(self, space, r_self, contextclass=None):
        space.ec.warn("Invalid argument supplied for foreach()")
        return None

    def hash(self, space):
        raise InterpreterError("unsupported hash")

    def getclass(self):
        return None

    def getinstancearray(self, space):
        raise InterpreterError("unsupported getinstancearray")

    def var_dump(self, space, indent, recursion):
        raise TypeError

    def dump(self):
        return self.repr()

    def is_empty_value(self):
        return False

    def overflow_convert(self, space):
        raise TypeError

    def as_int_arg(self, space):
        return self.int_w(space)

    def serialize(self, space, builder, memo):
        raise NotImplementedError # serialize need to be implemented by everyone

    def to_py(self, interp, w_php_ref=None):
        from hippy.module.pypy_bridge import php_adapters
        return php_adapters.W_PHPGenericAdapter(interp, self)
