
from rpython.rlib import jit
from rpython.rlib.objectmodel import specialize, we_are_translated
from rpython.rlib.rarithmetic import intmask
from rpython.rlib.rstring import replace

from hippy.objects.base import W_Object
from hippy.objects.reference import W_Reference, VirtualReference
from hippy.objects.convert import force_float_to_int_in_any_way
from hippy.objects.strobject import string_var_export
from hippy.error import ConvertError
from collections import OrderedDict
from rpython.rlib.rstring import StringBuilder


class CannotConvertToIndex(Exception):
    pass


def new_rdict():
    return OrderedDict()

def try_convert_str_to_int_fast(key):
    if not len(key):
        raise ValueError
    if (key[0] < '0' or key[0] > '9') and key[0] != '-' and key[0] != ' ':
        raise ValueError

def try_convert_str_to_int(key):
    # try to convert 'key' from a string to an int, but carefully:
    # we must not remove any space, make sure the result does not
    # overflows, etc.  In general we have to make sure that the
    # result, when converted back to a string, would give exactly
    # the original string.
    try_convert_str_to_int_fast(key)
    try:
        i = intmask(int(key))     # XXX can be done a bit more efficiently
    except (ValueError, OverflowError):
        raise ValueError
    if str(i) != key:
        raise ValueError
    return i


def compute_next_idx(dct_w):
    next_idx = 0
    for key in dct_w.keys():
        try:
            intkey = try_convert_str_to_int(key)
        except ValueError:
            continue
        if intkey >= next_idx:
            next_idx = intkey + 1
    return next_idx


def wrap_array_key(space,  key):
    try:
        intkey = try_convert_str_to_int(key)
    except ValueError:
        return space.newstr(key)
    return space.newint(intkey)


def convert_to_index(space, w_arg, allow_bogus=False):
    "Returns a pair (int, str), where only one of the two is meaningful"
    if w_arg.tp == space.tp_int:
        return space.int_w(w_arg), None
    elif w_arg.tp == space.tp_str:
        return 0, space.str_w(w_arg)
    elif w_arg.tp == space.tp_float:
        return force_float_to_int_in_any_way(space.float_w(w_arg)), None
    elif w_arg.tp == space.tp_null:
        return 0, ""
    elif w_arg.tp == space.tp_bool:
        if space.is_w(w_arg, space.w_False):
            if allow_bogus:
                return 0, ""
            else:
                return 0, None
        return 1, None
    if allow_bogus:
        if w_arg.tp == space.tp_file_res:
            return 0, space.str_w(w_arg)
        elif w_arg.tp == space.tp_object:
            return 0, space.str_w(w_arg)
        elif w_arg.tp == space.tp_array:
            space.ec.notice("Array to string conversion")
            return 0, "Array"
        else:
            space.ec.warn("Illegal offset type")
            raise CannotConvertToIndex
    else:
        # XXX make a real warning
        space.ec.warn("Illegal offset type")
        raise CannotConvertToIndex


class W_ArrayObject(W_Object):
    """Abstract base class.  Concrete subclasses use various strategies.
    This base class defines the general methods that can be implemented
    without needing to call (too often) the arraylen(), _getitem_str()
    and _getitem_int() methods.
    """

    @staticmethod
    def new_array_from_list(space, lst_w):
        return W_ListArrayObject(space, lst_w)

    @staticmethod
    def new_array_from_rdict(space, dct_w):
        return W_RDictArrayObject(space, dct_w, compute_next_idx(dct_w))

    @staticmethod
    @jit.look_inside_iff(lambda space, pairs_ww, allow_bogus : jit.isvirtual(pairs_ww))
    def new_array_from_pairs(space, pairs_ww, allow_bogus):
        rdct_w = new_rdict()
        next_idx = 0
        for w_key, w_value in pairs_ww:
            if w_key is not None:
                try:
                    as_int, as_str = convert_to_index(space, w_key,
                                                      allow_bogus=allow_bogus)
                except CannotConvertToIndex:
                    continue
                if as_str is not None:
                    # it was string, maybe it can be integer
                    try:
                        as_int = try_convert_str_to_int(as_str)
                        # yes it can
                        as_str = None
                    except ValueError:
                        pass
            # no key, just increment next_idx
            else:
                as_int, as_str = next_idx, None
            if as_str is None:
                if as_int >= next_idx:
                    next_idx = as_int + 1
                as_str = str(as_int)
            rdct_w[as_str] = w_value

        return W_RDictArrayObject(space, rdct_w, next_idx=next_idx)

    def copy_item(self):
        return self.copy()

    def is_true(self, space):
        return self.arraylen() > 0

    def int_w(self, space):
        return int(self.is_true(space))

    def as_int_arg(self, space):
        raise ConvertError('cannot use array as integer argument')

    def as_number(self, space):
        return space.wrap(self.is_true(space))

    def abs(self, space):
        return space.w_False

    def _lookup_item_ref(self, space, w_arg):
        """Return a possibly virtual reference to the item,
        or None if the lookup fails
        """
        try:
            as_int, as_str = convert_to_index(space, w_arg)
        except CannotConvertToIndex:
            space.ec.warn("Illegal offset type")
            return None
        if as_str is None:
            r_item = self._getitem_int(as_int)
            if r_item is None:
                return None
        else:
            r_item = self._getitem_str(as_str)
            if r_item is None:
                return None
        return r_item

    def getitem(self, space, w_arg, give_notice=False):
        try:
            as_int, as_str = convert_to_index(space, w_arg)
        except CannotConvertToIndex:
            space.ec.warn("Illegal offset type")
            return space.w_Null
        if as_str is None:
            r_item = self._getitem_int(as_int)
            if r_item is None:
                if give_notice:
                    space.ec.notice("Undefined offset: %d" % as_int)
                return space.w_Null
        else:
            r_item = self._getitem_str(as_str)
            if r_item is None:
                if give_notice:
                    space.ec.notice("Undefined index: %s" % as_str)
                return space.w_Null
        if isinstance(r_item, VirtualReference):
            return r_item.deref()
        else:
            return r_item

    def setitem2_maybe_inplace(self, space, w_arg, w_value, unique_item=False):
        try:
            as_int, as_str = convert_to_index(space, w_arg)
        except CannotConvertToIndex:
            space.ec.warn("Illegal offset type")
            return self, space.w_Null
        if as_str is None:
            w_arr = self._setitem_int(as_int, w_value, False, unique_item)
        else:
            w_arr = self._setitem_str(as_str, w_value, False, unique_item)
        return w_arr, w_value

    def _setitem_ref(self, space, w_arg, w_ref):
        try:
            as_int, as_str = convert_to_index(space, w_arg)
        except CannotConvertToIndex:
            space.ec.warn("Illegal offset type")
            return self
        if as_str is None:
            return self._setitem_int(as_int, w_ref, True)
        else:
            return self._setitem_str(as_str, w_ref, True)

    def appenditem_inplace(self, space, w_item, as_ref=False):
        # For now this always succeeds in appending the item in-place.
        # It may need to be reconsidered if we add more strategies.
        self._appenditem(w_item, as_ref)
        return w_item

    def packitem_maybe_inplace(self, space, w_arg, w_value):
        as_int, as_str = convert_to_index(space, w_arg)
        if as_str is not None:
            try:
                try_convert_str_to_int(as_str)
            except ValueError:
                # really not an int
                return self._setitem_str(as_str, w_value, False)
        self._appenditem(w_value)
        return self

    def _unsetitem(self, space, w_arg):
        as_int, as_str = convert_to_index(space, w_arg)
        if as_str is None:
            return self._unsetitem_int(as_int)
        else:
            return self._unsetitem_str(as_str)

    def isset_index(self, space, w_index):
        as_int, as_str = convert_to_index(space, w_index)
        if as_str is None:
            return self._isset_int(as_int)
        else:
            return self._isset_str(as_str)

    def _getitem_int(self, index):
        raise NotImplementedError("abstract")

    def _getitem_str(self, key):
        raise NotImplementedError("abstract")

    def _appenditem(self, w_obj, as_ref=False):
        raise NotImplementedError("abstract")

    def _setitem_int(self, index, w_value, as_ref, unique_item=False):
        raise NotImplementedError("abstract")

    def _setitem_str(self, key, w_value, as_ref,
                     unique_array=False, unique_item=False):
        # Note: might be occasionally called with a string like "5" too
        raise NotImplementedError("abstract")

    def _unsetitem_int(self, index):
        raise NotImplementedError("abstract")

    def _unsetitem_str(self, key):
        raise NotImplementedError("abstract")

    def _isset_int(self, index):
        raise NotImplementedError("abstract")

    def _isset_str(self, key):
        raise NotImplementedError("abstract")

    def arraylen(self):
        raise NotImplementedError("abstract")

    def as_rdict(self):
        raise NotImplementedError("abstract")

    def _each(self, space):
        raise NotImplementedError("abstract")

    def _current(self, space):
        raise NotImplementedError("abstract")

    def _key(self, space):
        raise NotImplementedError("abstract")

    def _inplace_pop(self, space):
        raise NotImplementedError("abstract")

    def get_rdict_from_array(self):
        raise NotImplementedError("abstract")

    def as_dict(self):
        "NOT_RPYTHON: for tests only"
        return self.as_rdict()

    def var_dump(self, space, indent, recursion):
        return array_var_dump(self.as_rdict(), space, indent, recursion,
                              self, 'array')

    def var_export(self, space, indent, recursion, suffix):
        return array_var_export(self.as_rdict(), space, indent, recursion,
                                self, suffix)

    def str(self, space, quiet=False):
        if not quiet:
            space.ec.notice("Array to string conversion")
        return "Array"

    def repr(self):
        return "Array"

    def dump(self):
        items = []
        next = 0
        for key, w_value in self.as_rdict().items():
            dumpvalue = w_value.dump()
            try:
                numkey = int(key)
            except ValueError:
                items.append('%s=>%s' % (key, dumpvalue))
                continue
            if numkey == next:
                items.append(dumpvalue)
            else:
                items.append('%d=>%s' % (numkey, dumpvalue))
            next = numkey + 1
        return "array(%s)" % ', '.join(items)

    def as_pair_list(self, space):
        pairs = []
        with space.iter(self) as w_iter:
            while not w_iter.done():
                w_key, w_val = w_iter.next_item(space)
                pairs.append((w_key, w_val))
        return pairs

    def eval_static(self, space):
        return self

    def serialize(self, space, builder, memo):
        builder.append("a:")
        builder.append(str(self.arraylen()))
        builder.append(":{")
        memo.add_counter()
        with space.iter(self) as itr:
            while not itr.done():
                w_key, w_value = itr.next_item(space)
                w_key.serialize(space, builder, memo)
                if w_value.serialize(space, builder, memo):
                    memo.add_counter()
        builder.append("}")
        return False  # counted above already

    def add(self, space, other_array):
        assert isinstance(other_array, W_ArrayObject)

        d = self.as_rdict()
        for k, w_v in other_array.as_rdict().iteritems():
            if k not in d:
                d[k] = w_v
        return space.new_array_from_rdict(d)


class ListItemVRef(VirtualReference):
    def __init__(self, w_array, index):
        assert isinstance(w_array, W_ListArrayObject)
        self.w_array = w_array
        self.index = index

    def deref(self):
        return self.w_array.lst_w[self.index]

    def store(self, w_value, unique=False):
        self.w_array.lst_w[self.index] = w_value

    def __repr__(self):
        return '<ListItemVRef>'


class W_ListArrayObject(W_ArrayObject):
    _has_string_keys = False

    def __init__(self, space, lst_w, current_idx=0):
        self.space = space
        self.lst_w = lst_w
        self.current_idx = current_idx

    def as_unique_arraylist(self):
        self._note_making_a_copy()
        lst_w = [item.copy_item() for item in self.lst_w]
        return W_ListArrayObject(self.space, lst_w, current_idx=self.current_idx)

    def as_list_w(self):
        return self.lst_w[:]

    def as_unique_arraydict(self):
        self._note_making_a_copy()
        d = self.as_rdict()   # make a fresh dictionary
        return W_RDictArrayObject(self.space, d,
                                  next_idx=len(self.lst_w),
                                  current_idx=self.current_idx)

    def arraylen(self):
        return len(self.lst_w)

    def as_rdict(self):
        d = new_rdict()
        for i in range(len(self.lst_w)):
            d[str(i)] = self.lst_w[i].copy_item()
        return d

    def get_rdict_from_array(self):
        return self.as_rdict()

    def _current(self, space):
        index = self.current_idx
        if 0 <= index < len(self.lst_w):
            return self.lst_w[index]
        else:
            return space.w_False

    def _key(self, space):
        index = self.current_idx
        if 0 <= index < len(self.lst_w):
            return space.newint(index)
        else:
            return space.w_Null

    def _getitem_int(self, index):
        if index >= 0:
            try:
                res = self.lst_w[index]
            except IndexError:
                pass
            else:
                if isinstance(res, W_Reference):
                    return res
                else:
                    return ListItemVRef(self, index)
        return None

    def _getitem_str(self, key):
        try:
            i = try_convert_str_to_int(key)
        except ValueError:
            return None
        return self._getitem_int(i)

    def _appenditem(self, w_obj, as_ref=False):
        self.lst_w.append(w_obj)

    def _setitem_int(self, index, w_value, as_ref, unique_item=False):
        length = self.arraylen()
        if index >= length:
            if index > length:
                return self._convert_and_setitem_int(index, w_value)
            self.lst_w.append(w_value)
            return self
        #
        if index < 0:
            return self._convert_and_setitem_int(index, w_value)
        #
        # If overwriting an existing W_Reference object, we only update
        # the value in the reference.  Else we need to update 'lst_w'.
        if not as_ref:
            w_old = self.lst_w[index]
            if isinstance(w_old, W_Reference):
                w_old.store(w_value, unique_item)
                return self
        self.lst_w[index] = w_value
        return self

    def _setitem_str(self, key, w_value, as_ref,
                     unique_array=False, unique_item=False):
        try:
            i = try_convert_str_to_int(key)
        except ValueError:
            return self._convert_and_setitem_str(key, w_value)
        else:
            return self._setitem_int(i, w_value, as_ref, unique_item)

    def _convert_and_setitem_int(self, index, w_value):
        res = self.as_unique_arraydict()
        return res._setitem_int(index, w_value, False)

    def _convert_and_setitem_str(self, key, w_value):
        res = self.as_unique_arraydict()
        return res._setitem_str(key, w_value, False)

    def _unsetitem_int(self, index):
        if index < 0 or index >= self.arraylen():
            return self
        if index == self.arraylen() - 1:
            del self.lst_w[index]
            if self.current_idx > len(self.lst_w):
                self.current_idx = len(self.lst_w)
            return self
        else:
            return self.as_unique_arraydict()._unsetitem_int(index)

    def _unsetitem_str(self, key):
        try:
            i = try_convert_str_to_int(key)
        except ValueError:
            return self     # str key, so not in the array at all
        else:
            return self._unsetitem_int(i)

    def _isset_int(self, index):
        return 0 <= index < self.arraylen()

    def _isset_str(self, key):
        try:
            i = try_convert_str_to_int(key)
        except ValueError:
            return False
        else:
            return self._isset_int(i)

    def create_iter(self, space, contextclass=None):
        from hippy.objects.arrayiter import W_ListArrayIterator
        return W_ListArrayIterator(self.lst_w)

    def create_iter_ref(self, space, r_self, contextclass=None):
        from hippy.objects.arrayiter import ListArrayIteratorRef
        return ListArrayIteratorRef(space, r_self)

    def copy(self):
        return self.as_unique_arraylist()

    def _inplace_pop(self, space):
        self.current_idx = 0
        return self.lst_w.pop()

    def _values(self, space):
        return self.lst_w

    def serialize(self, space, builder, memo):
        # performance-enhanced version
        builder.append("a:")
        lst_w = self.lst_w
        builder.append(str(len(lst_w)))
        builder.append(":{")
        memo.add_counter()
        counting = ['i', ':', '0', ';']
        for i in range(len(lst_w)):
            for c in counting:
                builder.append(c)
            # increment the counting list
            j = len(counting) - 2
            while j >= 2:
                if counting[j] != '9':
                    counting[j] = chr(ord(counting[j]) + 1)
                    break
                counting[j] = '0'
                j -= 1
            else:
                counting = ['i', ':', '1'] + counting[2:]
            #
            if lst_w[i].serialize(space, builder, memo):
                memo.add_counter()
        builder.append("}")
        return False  # counted above already


class DictItemVRef(VirtualReference):
    def __init__(self, w_array, index):
        self.w_array = w_array
        self.index = index

    def deref(self):
        return self.w_array.dct_w[self.index]

    def store(self, w_value, unique=False):
        self.w_array.dct_w[self.index] = w_value


class W_RDictArrayObject(W_ArrayObject):
    _has_string_keys = True
    strategy_name = 'hash'

    _keylist = None

    def __init__(self, space, dct_w, next_idx, current_idx=0):
        if not we_are_translated():
            assert isinstance(dct_w, OrderedDict)
        self.space = space
        self.dct_w = dct_w
        self.next_idx = next_idx
        self.current_idx = current_idx

    def as_rdict(self):
        new_dict = OrderedDict()
        for key, w_value in self.dct_w.iteritems():
            new_dict[key] = w_value.copy_item()
        return new_dict

    def get_rdict_from_array(self):
        return self.dct_w.copy()

    def as_unique_arraydict(self):
        self._note_making_a_copy()
        return W_RDictArrayObject(self.space, self.as_rdict(),
                                  next_idx=self.next_idx,
                                  current_idx=self.current_idx)

    def as_list_w(self):
        return self.dct_w.values()

    def _getkeylist(self):
        keylist = self._keylist
        if keylist is None:
            keylist = self.dct_w.keys()
            self._keylist = keylist
        return keylist

    def _keylist_changed(self):
        self._keylist = None

    def _current(self, space):
        keylist = self._getkeylist()
        index = self.current_idx
        if 0 <= index < len(keylist):
            return self.dct_w[keylist[index]]
        else:
            return space.w_False

    def _key(self, space):
        keylist = self._getkeylist()
        index = self.current_idx
        if 0 <= index < len(keylist):
            return wrap_array_key(space, keylist[index])
        else:
            return space.w_Null

    def arraylen(self):
        return len(self.dct_w)

    def _getitem_int(self, index):
        return self._getitem_str(str(index))

    def _getitem_str(self, key):
        try:
            res = self.dct_w[key]
        except KeyError:
            return None
        if isinstance(res, W_Reference):
            return res
        else:
            return DictItemVRef(self, key)

    def _appenditem(self, w_obj, as_ref=False):
        res = self._setitem_int(self.next_idx, w_obj, as_ref)
        assert res is self

    def _setitem_int(self, index, w_value, as_ref, unique_item=False):
        return self._setitem_str(str(index), w_value, as_ref, unique_item)

    def _setitem_str(self, key, w_value, as_ref,
                     unique_array=False, unique_item=False):
        # If overwriting an existing W_Reference object, we only update
        # the value in the reference and return 'self'.
        if not as_ref:
            try:
                w_old = self.dct_w[key]
            except KeyError:
                w_old = None
            if isinstance(w_old, W_Reference):   # and is not None
                w_old.store(w_value, unique_item)
                return self
        # Else update the 'dct_w'.
        if self._keylist is not None and key not in self.dct_w:
            self._keylist_changed()
        self.dct_w[key] = w_value
        # Blah
        try:
            i = try_convert_str_to_int(key)
        except ValueError:
            pass
        else:
            if self.next_idx <= i:
                self.next_idx = i + 1
        return self

    def _unsetitem_int(self, index):
        return self._unsetitem_str(str(index))

    def _unsetitem_str(self, key):
        if key not in self.dct_w:
            return self
        # XXX slow hacks to know if we must decrement current_idx or not:
        # this is if and only if the removed item is before current_idx.
        current_idx = self.current_idx
        if current_idx > 0:
            keylist = self._getkeylist()
            length = len(self.dct_w)
            if current_idx <= length // 2:
                # look on the left of current_idx
                for i in range(current_idx):
                    if keylist[i] == key:
                        # found: decrement current_idx
                        self.current_idx = current_idx - 1
                        break
            else:
                # look on the right of current_idx
                for i in range(current_idx, length):
                    if keylist[i] == key:
                        # found: don't decrement current_idx
                        break
                else:
                    # not found: decrement current_idx
                    self.current_idx = current_idx - 1
        #
        del self.dct_w[key]
        self._keylist_changed()
        return self

    def _isset_int(self, index):
        return self._isset_str(str(index))

    def _isset_str(self, key):
        return key in self.dct_w

    def create_iter(self, space, contextclass=None):
        from hippy.objects.arrayiter import W_RDictArrayIterator
        return W_RDictArrayIterator(self.dct_w)

    def create_iter_ref(self, space, r_self, contextclass=None):
        from hippy.objects.arrayiter import RDictArrayIteratorRef
        return RDictArrayIteratorRef(space, r_self)

    def copy(self):
        return self.as_unique_arraydict()

    def _inplace_pop(self, space):
        key, w_value = self.dct_w.popitem()
        self._keylist_changed()
        if key == str(self.next_idx - 1):
            self.next_idx -= 1
        self.current_idx = 0
        return w_value

    def _values(self, space):
        return self.dct_w.values()

    def var_export(self, space, indent, recursion, suffix):
        return array_var_export(self.as_rdict(), space, indent, recursion,
                                self, suffix)


def array_var_dump(dct_w, space, indent, recursion, w_reckey, header):
    if w_reckey in recursion:
        return '%s*RECURSION*\n' % indent
    res = StringBuilder()
    recursion[w_reckey] = None
    res.append('%s%s(%d) {\n' % (indent, header, len(dct_w)))
    if indent.endswith('&'):
        indent = indent[:-1]
    subindent = indent + '  '
    for key, w_value in dct_w.iteritems():
        try:
            index = try_convert_str_to_int(key)
        except ValueError:
            s = '%s["%s"]=>\n' % (subindent, key)
        else:
            s = '%s[%d]=>\n' % (subindent, index)
        res.append(s)
        res.append(w_value.var_dump(space, subindent, recursion))
    res.append('%s}\n' % indent)
    del recursion[w_reckey]
    return res.build()


def array_var_export(dct_w, space, indent, recursion, w_reckey,
                     header, prefix=' ', suffix='', arr_in_arr=False):
    acc = StringBuilder()
    if w_reckey in recursion:
        return '%s*RECURSION*\n' % indent
    recursion[w_reckey] = None
    if arr_in_arr:
        acc.append('%s%s%s(\n' % (' ', header, prefix))
    else:
        acc.append('%s%s%s(\n' % (indent, header, prefix))

    if indent.endswith('&'):
        indent = indent[:-1]
    subindent = indent + '  '
    for key, w_value in dct_w.iteritems():
        w_value = w_value.deref_temp()
        # case where atrrib is protected...
        if key.startswith('\x00') and len(key) > 1:
            key = key[3:]
        if w_value is w_reckey:
            # space.ec.error("Nesting level too deep - recursive dependency?")
            space.ec.warn("var_export does not handle circular references")
            return ""

        try:
            index = try_convert_str_to_int(key)
            s = '%s%d =>' % (subindent, index)
        except ValueError:
            key = string_var_export(key)
            s = '%s%s =>' % (subindent, key)

        acc.append(s)
        if isinstance(w_value, W_ArrayObject):
            acc.append(array_var_export(w_value.as_rdict(), space,
                                    '  ', recursion, w_value,
                                    '\n  array', suffix=',',  arr_in_arr=True))
        elif w_value.tp == space.tp_object:
            acc.append('\n')
            acc.append(w_value.var_export(space, ' ', recursion, suffix='),'))
        else:
            acc.append(w_value.var_export(space, ' ', recursion, suffix=','))
        acc.append('\n')

    acc.append('%s)%s' % (indent, suffix))
    del recursion[w_reckey]
    return acc.build()
