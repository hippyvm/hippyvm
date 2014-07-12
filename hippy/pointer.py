from hippy.objects.reference import W_Reference
from hippy.objects.base import W_Object
from hippy.objects.arrayobject import VirtualReference
from hippy.objspace import ObjSpace
from hippy.error import OffsetError, VisibilityError


class BasePointer(object):
    """
    Internal representation of symbolic references, i.e. things that look
    syntactically like references but may not necessarily be valid references.
    Also used as the target of ref-assignments.

    Examples of pointers that cannot be resolved to valid references:
      * string offsets
      * private attributes

    In some cases, the simple act of resolving the pointer has visible
    side-effects, e.g. with references to unset variables or array keys.
    """
    isref = True

    def deref(self, interp, give_notice=False):
        return self._get(interp, give_notice).deref()

    def deref_temp(self, interp, give_notice=False):
        return self._get(interp, give_notice).deref_temp()

    def _get(self, interp, give_notice=False):
        """Return the object pointed to.
        """
        r_value = self.lookup_ref(interp)
        if r_value is None:
            return interp.space.w_Null
        return r_value

    def store(self, interp, w_value, unique_item=False, give_notice=True):
        """Writes w_value inside the pointed-to location.

        'w_value' must not be a reference.  Returns the object
        really written (usually but not always w_value).
        """
        self.get_ref(interp).store(w_value, unique_item)
        return w_value

    def get_ref(self, interp, err_is_ref=True):
        """Get or create the actual reference.

        This can have side-effects.
        """
        raise NotImplementedError

    def lookup_ref(self, interp):
        """Get the actual reference if it exists. Return None otherwise.

        This has no side-effects.
        """
        raise NotImplementedError

    def store_ref(self, interp, w_ref):
        """Write the given W_Reference at the pointed-to location."""
        raise NotImplementedError

    def unset_ref(self, interp):
        """unset() was called."""
        raise NotImplementedError

    def isset_ref(self, interp):
        ref = self.lookup_ref(interp)
        return (ref is not None and
                ref.deref_temp() is not interp.space.w_Null)


class VariablePointer(BasePointer):
    """A Pointer to a variable.  This is used for any '$a=...' expression.
    It is really useful only for '$a=&...'.
    """
    def __init__(self, frame, varnum):
        self.frame = frame
        self.varnum = varnum

    def deref(self, interp, give_notice=False):
        return self.frame.lookup_deref(self.varnum, give_notice=give_notice)

    def deref_temp(self, interp, give_notice=False):
        return self.frame.lookup_deref_temp(self.varnum,
                                            give_notice=give_notice)

    def store(self, interp, w_value, unique_item=False, give_notice=True):
        self.frame.store_variable(self.varnum, w_value, unique_item)
        return w_value

    def get_ref(self, interp, err_is_ref=True):
        return self.frame.load_ref(self.varnum)

    def lookup_ref(self, interp):
        return self.frame.load_ref(self.varnum)

    def __repr__(self):
        return '<VariablePointer %d>' % (self.varnum)


class ThisPointer(BasePointer):
    def __init__(self, w_instance):
        self.w_instance = w_instance

    def _get(self, interp, give_notice=False):
        return self.w_instance

    def get_ref(self, interp, err_is_ref=True):
        return W_Reference(self.w_instance)

    def __repr__(self):
        return '<ThisPointer>'


class UndeclaredVariablePointer(BasePointer):
    """A pointer to a variable that was not present at compilation,
    but is used in '$$name'.
    """
    def __init__(self, frame, name):
        self.frame = frame
        self.name = name

    def get_ref(self, interp, err_is_ref=True):
        return self.frame.get_ref_by_name(self.name)

    def lookup_ref(self, interp):
        return self.frame.lookup_ref_by_name(self.name)

    def __repr__(self):
        return '<UndeclaredVariablePointer %s>' % (self.name,)


class CallResultPointer(BasePointer):
    """A Pointer to the result of a call (typically to 'function &f()').
    """
    def __init__(self, w_ref):
        assert isinstance(w_ref, W_Reference)
        self.w_ref = w_ref

    def lookup_ref(self, interp):
        return self.w_ref

    def get_ref(self, interp, err_is_ref=True):
        return self.w_ref

    def __repr__(self):
        return '<CallResultPointer %s>' % (self.w_ref,)

class ValuePointer(BasePointer):
    """A Pointer to the result of a call that returns-by-value.
    """
    isref = False
    def __init__(self, w_obj):
        assert isinstance(w_obj, W_Object)
        self.w_obj = w_obj

    def lookup_ref(self, interp):
        return W_Reference(self.w_obj)

    def get_ref(self, interp, err_is_ref=True):
        return W_Reference(self.w_obj)

    def store(self, interp, w_value, unique_item=False, give_notice=True):
        assert not give_notice
        return W_Reference(w_value)

    def __repr__(self):
        return '<ValuePointer %s>' % (self.w_obj,)


class StaticMemberPointer(BasePointer):
    """A Pointer to a class' static member.
    """
    def __init__(self, klass, name, contextclass):
        self.klass = klass
        self.name = name
        self.contextclass = contextclass

    def lookup_property(self, interp):
        try:
            return self.klass.lookup_staticmember(self.name, self.contextclass,
                check_visibility=not interp.allow_direct_class_access)
        except VisibilityError as e:
            raise e.reraise_property(interp)

    def get_property(self, interp):
        prop = self.lookup_property(interp)
        if prop is None:
            interp.fatal(
                "Access to undeclared static property: %s::$%s" %
                (self.klass.name, self.name))
        else:
            return prop

    def get_ref(self, interp, err_is_ref=True):
        return self.get_property(interp).getvalue(interp.space)

    def lookup_ref(self, interp):
        prop = self.lookup_property(interp)
        if prop is not None:
            return prop.getvalue(interp.space)
        else:
            return None

    def store_ref(self, interp, w_ref):
        self.get_property(interp).r_value = w_ref
        return w_ref

    def unset_ref(self, interp):
        self.store_ref(interp, W_Reference(interp.space.w_Null))

    def __repr__(self):
        return '<StaticMemberPointer %s>' % (self.klass, self.name)


class BaseItemPointer(BasePointer):
    """Base class for BaseRealItemPointer and AppendPointer"""
    def __init__(self, p_base):
        assert isinstance(p_base, BasePointer)
        self.p_base = p_base          # another BasePointer instance

    def get_array_base(self, interp):
        """Get the base object and convert it to an array as needed"""
        r_base = self.p_base.get_ref(interp, err_is_ref=False)
        if r_base.deref_temp().is_empty_value():
            interp.hippy_warn('Creating array from empty value')
            w_base = interp.space.new_array_from_list([])
            r_base.store(w_base, unique=True)
        return r_base


class BaseRealItemPointer(BaseItemPointer):
    """Base class for ItemPointer and VarItemPointer"""

    def get_w_index(self, interp, give_notice=False):
        raise NotImplementedError

    def _get(self, interp, give_notice=False):
        w_obj = self.p_base.deref_temp(interp, give_notice)
        w_index = self.get_w_index(interp, give_notice)
        return w_obj.getitem(interp.space, w_index, give_notice=give_notice)

    def store(self, interp, w_value, unique_item=False, give_notice=True):
        r_base = self.get_array_base(interp)
        w_base = r_base.deref_unique()
        w_index = self.get_w_index(interp)
        w_new, w_result = w_base.setitem2_maybe_inplace(
            interp.space, w_index, w_value, unique_item=unique_item)
        # NB. this check is more than just an optimization.  It is
        # essential for test_reference_update_does_not_change_array
        # in test_interpreter.py.
        if w_new is not w_base:
            r_base.store(w_new, unique=True)
        return w_result

    def get_ref(self, interp, err_is_ref=True):
        r_base = self.get_array_base(interp)
        w_index = self.get_w_index(interp)
        space = interp.space
        try:
            return r_base.getitem_ref(interp.space, w_index)
        except OffsetError:
            return self._error(space, r_base.deref_temp(), err_is_ref)

    def lookup_ref(self, interp):
        r_base = self.p_base.lookup_ref(interp)
        if r_base is None:
            return None
        w_index = self.get_w_index(interp)
        return r_base.lookup_item_ref(interp.space, w_index)

    def store_ref(self, interp, r_value):
        r_base = self.get_array_base(interp)
        w_index = self.get_w_index(interp)
        try:
            r_base.setitem_ref(interp.space, w_index, r_value)
        except OffsetError:
            return self._error(interp.space, r_base.deref_temp(),
                               err_is_ref=True)
        return r_value

    def _error(self, space, w_obj, err_is_ref):
        if w_obj.tp == space.tp_str:
            if err_is_ref:
                raise space.ec.fatal(
                    'Cannot create references to/from '
                    'string offsets')
            else:
                raise space.ec.fatal(
                    "Cannot use string offset as an array")
        return space.empty_ref()

    def isset_ref(self, interp):
        r_base = self.p_base.lookup_ref(interp)
        if r_base is None:
            return False
        w_index = self.get_w_index(interp)
        return r_base.deref_temp().hasitem(interp.space, w_index)


    def unset_ref(self, interp):
        r_base = self.p_base.lookup_ref(interp)
        if r_base is None:
            interp.warn('Cannot unset offset in a non-array variable')
            return
        w_index = self.get_w_index(interp)
        r_base.unsetitem(interp.space, w_index)


class ItemPointer(BaseRealItemPointer):
    """A pointer to an array item.  Can be nested for expressions like
    '$a[5][6][7]'.
    """
    def __init__(self, p_base, w_index):
        BaseRealItemPointer.__init__(self, p_base)
        self.w_index = w_index

    def get_w_index(self, interp, give_notice=False):
        return self.w_index.deref_temp()

    def __repr__(self):
        return '<ItemPointer %r, %s>' % (self.p_base, self.w_index)


class VarItemPointer(BaseRealItemPointer):
    """A special case for 'some_expression[$var]'.
    """
    def __init__(self, p_base, frame, varnum):
        BaseRealItemPointer.__init__(self, p_base)
        self.frame = frame
        self.varnum = varnum

    def get_w_index(self, interp, give_notice=False):
        return self.frame.lookup_deref_temp(self.varnum,
                                            give_notice=give_notice)

    def __repr__(self):
        return '<VarItemPointer %r, %d>' % (self.p_base, self.varnum)


class AppendPointer(BaseItemPointer):
    """A pointer to append to an array, as in $a[] = 42;

    Cannot really be used for anything else, even though PHP syntax might
    appear to allow it.
    """
    def store(self, interp, w_value, unique_item=False, give_notice=True):
        r_base = self.get_array_base(interp)
        w_base = r_base.deref_unique()
        # 'unique_item' is ignored here
        w_newvalue = w_base.appenditem_inplace(interp.space, w_value)
        return w_newvalue

    def get_ref(self, interp, err_is_ref=True):
        w_newref = interp.space.empty_ref()
        self.store_ref(interp, w_newref)
        return w_newref

    def lookup_ref(self, interp):
        return None

    def store_ref(self, interp, w_ref):
        r_base = self.get_array_base(interp)
        w_base = r_base.deref_unique()
        w_newvalue = w_base.appenditem_inplace(interp.space, w_ref,
                                               as_ref=True)
        return w_newvalue


class AttrPointer(BasePointer):
    """A pointer to an object attribute."""
    def __init__(self, p_base, w_attr, contextclass):
        self.p_base = p_base
        self.w_attr = w_attr
        self.contextclass = contextclass

    def get_name(self, interp):
        return interp.space.str_w(self.w_attr)

    def get_base_obj(self, interp, give_notice=False):
        # We can always use deref_temp() here, because an object is never
        # copy-on-write.  Mutating it with setattr()&co. is always safe,
        # even if the base reference doesn't contain the unique copy of
        # the object.
        w_base = self.p_base.deref_temp(interp)
        if w_base.is_empty_value():
            w_base = interp.space.default_object(interp)
            self.p_base.store(interp, w_base, unique_item=True, give_notice=False)
            msg = 'Creating default object from empty value'
            if give_notice:
                interp.warn(msg)
            else:
                interp.hippy_warn(msg)
        return w_base

    def _get(self, interp, give_notice=False):
        w_base = self.p_base.deref_temp(interp, give_notice)
        return w_base.getattr(interp, self.get_name(interp),
                              self.contextclass, give_notice)

    def store(self, interp, w_value, unique_item=False, give_notice=True):
        w_base = self.get_base_obj(interp, give_notice=give_notice)
        return w_base.setattr(interp, self.get_name(interp),
                              w_value, self.contextclass,
                              unique_item=unique_item)

    def get_ref(self, interp, err_is_ref=True):
        w_base = self.get_base_obj(interp)
        return w_base.getattr_ref(interp, self.get_name(interp),
                                  self.contextclass)

    def lookup_ref(self, interp):
        return self.get_ref(interp)

    def store_ref(self, interp, w_ref):
        w_base = self.get_base_obj(interp)
        return w_base.setattr_ref(interp, self.get_name(interp),
                                  w_ref, self.contextclass)

    def unset_ref(self, interp):
        w_base = self.p_base.deref_temp(interp)
        w_base.delattr(interp, self.get_name(interp), self.contextclass)

    def isset_ref(self, interp):
        w_base = self.p_base.deref_temp(interp)
        return w_base.hasattr(interp, self.get_name(interp), self.contextclass)

    def __repr__(self):
        return '<AttrPointer %s, %s>' % (self.p_base, ObjSpace().str_w(self.w_attr))
