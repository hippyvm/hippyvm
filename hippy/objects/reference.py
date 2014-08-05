from hippy.objects.base import W_Root, W_Object


class W_Reference(W_Root):
    """This is a reference got by &$stuff.  It is also used for local
    variables, which are all reference objects.  This is the only core
    PHP object that is mutable (we can change what it refers to).
    """
    _COUNTER = 0
    _unique = False

    def __init__(self, w_value):
        assert isinstance(w_value, W_Object) or w_value is None
        assert not isinstance(w_value, W_Reference)
        self._w_value = w_value

    def deref(self):
        """The standard way to read the w_value stored in the reference.
        You must not call the inplace_*() operations on the result,
        because it may be shared by unrelated pieces of code."""
        self._unique = False
        return self._w_value

    def deref_temp(self):
        """Read the w_value, but promizes that we won't do any operation
        that changes the result or keep it around for a long time."""
        return self._w_value

    def deref_unique(self):
        """Read the w_value, if necessary making a copy in order to
        return a unique reference."""
        from hippy.objects.arrayobject import W_ArrayObject
        from hippy.objects.strobject import W_StringObject
        w_value = self._w_value
        if (isinstance(w_value, W_ArrayObject) or
            isinstance(w_value, W_StringObject)):
            if not self._unique:
                w_value = w_value.copy()
                self._w_value = w_value
                self._unique = True
        return w_value

    def store(self, w_value, unique=False):
        """Stores a reference to the given W_Object into myself.
        Saying unique=False is always correct.  You can say unique=True
        if you know for sure that 'w_value' is a fresh object (typically
        an array or a string) that nobody else has seen, and that you're
        not going to use after the call to store().
        """
        assert not isinstance(w_value, W_Reference)
        self._w_value = w_value
        self._unique = unique

    def __repr__(self):
        if not hasattr(self, '_counter'):
            self._counter = W_Reference._COUNTER
            W_Reference._COUNTER += 1
        if self._unique:
            unique = ',U'
        else:
            unique = ''
        return '<Ref%d%s: %s>' % (self._counter, unique, self._w_value)

    def lookup_item_ref(self, space, w_index):
        w_value = self.deref_temp()
        return w_value._lookup_item_ref(space, w_index)

    def getitem_ref(self, space, w_index):
        r_result = self.lookup_item_ref(space, w_index)
        if r_result is None:
            r_result = space.empty_ref()
            self.setitem_ref(space, w_index, r_result)
        elif isinstance(r_result, VirtualReference):
            r_result = W_Reference(r_result.deref())
            self.setitem_ref(space, w_index, r_result)
        return r_result

    def setitem_ref(self, space, w_index, r_value):
        w_obj = self.deref_unique()
        w_new = w_obj._setitem_ref(space, w_index, r_value)
        if w_new is not w_obj:
            self.store(w_new, unique=True)

    def unsetitem(self, space, w_index):
        w_obj = self.deref_unique()
        w_new = w_obj._unsetitem(space, w_index)
        if w_new is not w_obj:
            self.store(w_new, unique=True)

    def var_dump(self, space, indent, recursion):
        return self.deref().var_dump(space, indent + '&', recursion)

    def is_scalar(self, space):
        return self.deref().is_scalar(space)

    def var_export(self, space, indent, recursion, suffix):
        w_value = self.deref()
        return w_value.var_export(space, indent, recursion, suffix=suffix)

    def dump(self):
        return self.deref_temp().dump()

    def serialize(self, space, builder, memo):
        if memo.memo_lookup(self, builder):
            return False
        self.deref().serialize(space, builder, memo)
        return True

    # compat hack: prevent direct reads/writes from 'w_value'
    w_value = property(None, None)

    def to_py(self, interp):
        wph_inside = self.deref_temp()

        # Arrays are special, passed by reference
        from hippy.objects.arrayobject import W_ArrayObject
        if isinstance(wph_inside, W_ArrayObject):
            from hippy.module.pypy_bridge.py_wrappers import (
                    make_wrapped_mixed_key_php_array)
            return make_wrapped_mixed_key_php_array(interp, self) # pass in ref
        else:
            wph_inside = self.deref()
            return wph_inside.to_py(interp)

class VirtualReference(W_Reference):
    """A handle to an object stored in some container.

    Caution: a virtual reference is only valid as long as the underlying
    container has not been modified.
    """
    _unique = True

    def deref_temp(self):
        return self.deref()

    def deref_unique(self):
        return self.deref()
