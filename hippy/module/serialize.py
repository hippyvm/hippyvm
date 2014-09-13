
""" Originally from phpserialize by Armin Ronacher, BSD license.
Heavily rewritten by Armin Rigo.
"""

from hippy.objects.reference import W_Reference
from hippy.objects.convert import convert_string_to_number
from hippy.builtin_klass import k_incomplete
from rpython.rlib.debug import check_nonneg
from rpython.rlib.rarithmetic import r_uint, intmask
from rpython.rlib.listsort import make_timsort_class
from rpython.rlib.rfloat import string_to_float
from rpython.rlib.rstring import ParseStringError
from collections import OrderedDict
from rpython.rlib import rfloat


class SerializerMemo(object):
    serialize_precision = 0

    def __init__(self):
        self.memo = {}
        self.counter = 1

    def memo_lookup(self, w_obj, builder, char='R'):
        try:
            m = self.memo[w_obj]
        except KeyError:
            self.memo[w_obj] = self.counter
            return False
        else:
            builder.append(char)
            builder.append(':')
            builder.append(str(m))
            builder.append(';')
            return True

    def add_counter(self):
        self.counter += 1


class SerializerError(Exception):
    pass


IntSort = make_timsort_class()


def remove_duplicates_fin(lst):
    prev = lst[0]
    count = 1
    for i in range(1, len(lst)):
        if prev != lst[i]:
            prev = lst[i]
            count += 1
    result = [0] * (count + 1)
    prev = lst[0]
    result[0] = prev
    count = 1
    for i in range(1, len(lst)):
        if prev != lst[i]:
            prev = lst[i]
            result[count] = prev
            count += 1
    result[count] = -1
    return result


class UnserializerState(object):

    def __init__(self, space, s):
        self.space = space
        self.s = s
        self.pos = 0
        self.error_pos = 0
        self.next_reference_obj = -1
        self._ref_numbers = []
        check_nonneg(self.pos)

    # ----------

    def pp_expect_nonneg_int(self, startpos):
        check_nonneg(startpos)
        s = self.s
        i = startpos
        limit = len(s)
        result = 0
        while i < limit and s[i].isdigit():
            result = result * 10 + (ord(s[i]) - 48)
            i += 1
        self.pos = i
        result = intmask(result)
        if result < 0:
            result = 0   # integer overflow!
        return result

    def _preprocess(self, i=0):
        check_nonneg(i)
        s = self.s
        nesting = 0
        assert i >= 0
        while True:
            if i >= len(s):
                return -1
            tp = s[i]
            if tp == 'b':
                i += 4          # 'b:0;' or 'b:1;'
            elif tp == 'i' or tp == 'd':
                i = s.find(';', i + 1)
                if i < 0:
                    return -1
                i += 1
            elif tp == 's':     # 's:LEN:"....";'
                length = self.pp_expect_nonneg_int(i + 2)
                i = self.pos + length + 4
            elif tp == 'N':
                i += 2          # 'N;'
            elif tp == 'a':     # 'a:LEN:{....}'
                i = s.find('{', i + 1)
                if i < 0:
                    return -1
                i += 1
                nesting += 1
            elif tp == 'O':     # 'O:LEN:"....":LEN:{....}'
                length = self.pp_expect_nonneg_int(i + 2)
                i = self.pos + length + 4
                i = s.find('{', i + 1)
                if i < 0:
                    return -1
                i += 1
                nesting += 1
            elif tp == '}':
                nesting -= 1
                i += 1
            elif tp == 'R' or tp == 'r':     # 'R:BACKREF;'
                backref = self.pp_expect_nonneg_int(i + 2)
                self._ref_numbers.append(backref)
                i = self.pos + 1
            else:
                return -1
            if nesting <= 0:
                return i

    def _preprocess_ref_numbers(self):
        ref_numbers = self._ref_numbers
        if len(ref_numbers) > 0:
            IntSort(ref_numbers).sort()
            self.ref_numbers = remove_duplicates_fin(ref_numbers)
            self.ref_objects = {}
            self.next_reference_obj = self.ref_numbers[0]
            self.next_reference_idx = 0

    def preprocess(self):
        result = self._preprocess()
        self._preprocess_ref_numbers()
        return result >= 0

    def preprocess_session_mode(self):
        # for session.py: the string contains any number of 'KEY|SERIAL'
        i = 0
        while True:
            bar = self.s.find('|', i)
            if bar < 0:
                valid = True
                break
            i = self._preprocess(bar + 1)
            if i < 0:
                valid = False
                break
        self._preprocess_ref_numbers()
        return valid

    def save_reference(self, w_result):
        assert isinstance(w_result, W_Reference)
        i = self.next_reference_idx
        index = self.ref_numbers[i]
        self.ref_objects[index] = w_result
        self.next_reference_obj = self.ref_numbers[i + 1] - self.ref_numbers[i]
        self.next_reference_idx = i + 1

    # ----------

    def expect_closing_brace(self):
        self.error_pos = self.pos + 1
        i = self.consume(1)
        if self.s[i] != '}':
            raise SerializerError("'}' expected")

    def consume(self, n):
        s = self.s
        start = self.pos
        stop = start + n
        if stop > len(s):
            raise SerializerError("Unexpected end of data")
        self.pos = stop
        return start
    consume._always_inline_ = True

    def read_substring_until(self, delim):
        assert len(delim) == 1
        start = self.pos
        s = self.s
        stop = s.find(delim, start)
        if stop < 0:
            raise SerializerError("unexpected end of stream")
        self.pos = stop + 1
        return s[start:stop]

    def read_int_until(self, delim, can_be_negative=True):
        i = self.consume(2)
        s = self.s
        negative = False
        if not s[i].isdigit():
            if not can_be_negative:
                raise SerializerError("unexpected negative int")
            if s[i] != '-':
                raise SerializerError("bad int")
            negative = True
            i += 1
            if not s[i].isdigit():
                raise SerializerError("bad int")
        value = r_uint(ord(s[i]) - 48)
        self.pos = i + 1
        while True:
            i = self.consume(1)
            if not s[i].isdigit():
                break
            value = value * 10 + r_uint(ord(s[i]) - 48)
        if s[i] != delim:
            raise SerializerError("bad int")
        if negative:
            value = -value
        return intmask(value)


def load_str(fp, delim):
    oldpos = fp.pos
    length = fp.read_int_until(':', can_be_negative=False)
    if length < 0:
        raise SerializerError("integer overflow")
    try:
        i = fp.consume(length + 3)      # quote, string, quote, semicolon
    except SerializerError:
        if len(fp.s) > fp.pos:
            extra = len(fp.s) - fp.pos - length
            if extra > 0:
                fp.error_pos = fp.pos + length + 1
                if extra > 1:
                    fp.error_pos += 2
            else:
                fp.error_pos = oldpos
        raise
    check_nonneg(i)
    s = fp.s
    if s[i] != '"':
        raise SerializerError("'\"' expected")
    i += 1
    data = s[i: i + length]
    i += length
    if s[i] != '"':
        raise SerializerError("'\"' expected")
    i += 1
    if s[i] != delim:
        raise SerializerError("delim expected")
    return data


def load_array_key(fp):
    oldpos = fp.pos
    fp.error_pos = fp.pos
    try:
        i = fp.consume(2)
    except SerializerError:
        pass
    else:
        s = fp.s
        tp = s[i]
        if tp == 'i':
            if s[i + 1] != ':':
                raise SerializerError("':' expected")
            i = fp.read_int_until(';')
            return fp.space.wrap(i)
        if tp == 's':
            if s[i + 1] != ':':
                raise SerializerError("':' expected")
            return fp.space.newstr(load_str(fp, ';'))
    fp.pos = oldpos
    load_object(fp)    # to update the .pos to the end of the object
    fp.error_pos = fp.pos
    raise SerializerError('bad type for array key')


def load_reference(fp):
    fp.next_reference_obj += 1     # undo
    index = fp.read_int_until(';')
    try:
        return fp.ref_objects[index]
    except KeyError:
        fp.error_pos = fp.pos
        raise SerializerError('bad reference number')


def load_object(fp):
    fp.next_reference_obj -= 1
    needs_ref = (fp.next_reference_obj == 0)
    #
    fp.error_pos = fp.pos
    try:
        i = fp.consume(2)
    except SerializerError:
        i = fp.consume(1)
        if fp.s[i] == '}':
            fp.space.ec.notice("unserialize(): "
                               "Unexpected end of serialized data")
        raise
    s = fp.s
    tp = s[i]
    check_nonneg(i)
    check_nonneg(fp.pos)
    #
    if tp == 'i':
        if s[i + 1] != ':':
            raise SerializerError("':' expected")
        i = fp.read_int_until(';')
        w_result = fp.space.wrap(i)
    #
    elif tp == 's':
        if s[i + 1] != ':':
            raise SerializerError("':' expected")
        w_result = fp.space.newstr(load_str(fp, ';'))
    #
    elif tp == 'd':
        if s[i + 1] != ':':
            raise SerializerError("':' expected")
        data = fp.read_substring_until(';')
        try:
            result = string_to_float(data)
        except ParseStringError:
            raise SerializerError('bad double')
        w_result = fp.space.newfloat(result)
    #
    elif tp == 'b':
        if s[i + 1] != ':':
            raise SerializerError("':' expected")
        i = fp.consume(2)
        digit = s[i]
        if digit == '0':
            w_result = fp.space.w_False
        elif digit == '1':
            w_result = fp.space.w_True
        else:
            raise SerializerError('bad bool')
        if s[i + 1] != ';':
            raise SerializerError("';' expected")
    #
    elif tp == 'N':
        if s[i + 1] != ';':
            raise SerializerError("';' expected")
        w_result = fp.space.w_Null
    #
    elif tp == 'a':
        if s[i + 1] != ':':
            raise SerializerError("':' expected")
        length = fp.read_int_until(':', can_be_negative=False)
        if length < 0:
            raise SerializerError("integer overflow")
        i = fp.consume(1)
        if s[i] != '{':
            raise SerializerError("'{' expected")
        w_result = None
        if needs_ref:
            w_result = fp.space.empty_ref()
            fp.save_reference(w_result)
        # first try to load the array as a direct list
        lst_w = []
        expected = ['i', ':', '0', ';']
        for n in range(length):
            i = fp.pos
            if i + len(expected) >= len(s):
                break
            for j in range(len(expected)):
                if s[i] != expected[j]:
                    break
                i += 1
            else:
                # ok, we got exactly 'i:N;' where N is the expected index
                fp.pos = i
                lst_w.append(load_object(fp))
                # increment the expected counter
                j = len(expected) - 2
                while j >= 2:
                    if expected[j] != '9':
                        expected[j] = chr(ord(expected[j]) + 1)
                        break
                    expected[j] = '0'
                    j -= 1
                else:
                    expected = ['i', ':', '1'] + expected[2:]
                continue
            break
        else:
            # we succeeded in loading the complete array as a list
            n = length
            _succeeded_as_a_list()   # for tests
        # fill in the remaining entries, if any, the slow way
        w_array = fp.space.new_array_from_list(lst_w)
        for n in range(n, length):
            w_key = load_array_key(fp)
            w_value = load_object(fp)
            w_array = fp.space.setitem_maybe_inplace(w_array, w_key, w_value)
        fp.expect_closing_brace()
        if w_result is not None:    # needs_ref
            w_result.store(w_array, unique=True)
            return w_result
        else:
            return w_array
    #
    elif tp == 'R':
        if s[i + 1] != ':':
            raise SerializerError("':' expected")
        return load_reference(fp)
    #
    elif tp == 'r':
        if s[i + 1] != ':':
            raise SerializerError("':' expected")
        return load_reference(fp).deref()
    #
    elif tp == 'O':
        if s[i + 1] != ':':
            raise SerializerError("':' expected")
        klass_name = load_str(fp, ':')
        space = fp.space
        interp = space.ec.interpreter
        klass = interp.lookup_class_or_intf(klass_name)
        if klass is None:
            klass = k_incomplete
            w_instance = klass.get_empty_instance(space)
            w_instance.setattr(interp, '__PHP_Incomplete_Class_Name',
                               space.wrap(klass_name), None)
        else:
            w_instance = klass.get_empty_instance(space)
        w_result = w_instance
        if needs_ref:
            w_result = W_Reference(w_instance)
            fp.save_reference(w_result)
        count_attrs = fp.read_int_until(':')    # negative value accepted :-(
        i = fp.consume(1)
        if s[i] != '{':
            raise SerializerError("'{' expected")
        attrs = {}
        for i in xrange(count_attrs):
            w_attr = load_array_key(fp)
            w_value = load_object(fp)
            attr_name = space.str_w(w_attr)
            attrs[attr_name] = w_value
            w_instance.setattr(interp, attr_name, w_value, None)
        fp.expect_closing_brace()

        w_instance.unserialize(space, attrs)

        if '__wakeup' in klass.methods:
            klass.methods['__wakeup'].method_func.call_args(space.ec.interpreter,
                                                            [], w_this=w_instance,
                                                            thisclass=klass)
        return w_result
    #
    else:
        if tp == '}':
            fp.space.ec.notice("unserialize(): "
                               "Unexpected end of serialized data")
        raise SerializerError('malformed input')

    # this is for primitive types only; complex types 'return' above
    if needs_ref:
        w_result = W_Reference(w_result)
        fp.save_reference(w_result)
    return w_result


def _succeeded_as_a_list():
    "for tests"


def unserialize(space, s):
    """Unserialize the string s.

    """
    if len(s) == 0:
        space.ec.hippy_warn("unserialize(): empty string")
        return space.w_False
    fp = UnserializerState(space, s)
    valid = fp.preprocess()
    try:
        fp.pos = 0
        w_result = load_object(fp)
    except SerializerError:
        space.ec.notice("unserialize(): Error at "
                        "offset %d of %d bytes" % (fp.error_pos, len(s)))
        return space.w_False
    assert valid
    return w_result


def unserialize_returning_dict(space, s):
    """Unserialize for session.py with an '|' extension
    """
    fp = UnserializerState(space, s)
    valid = fp.preprocess_session_mode()
    d = OrderedDict()
    fp.pos = 0
    while True:
        bar = s.find('|', fp.pos)
        if bar < 0:
            break
        key = s[fp.pos : bar]
        fp.pos = bar + 1
        try:
            w_value = load_object(fp)
        except SerializerError:
            return None
        d[key] = w_value
    assert valid
    return d
