
""" Stolen from phpserialize by Armin Ronacher, BSD license.
"""

from hippy.objects.reference import W_Reference
from hippy.objects.convert import convert_string_to_number
from hippy.builtin_klass import k_incomplete


class SerializerMemo(object):
    def __init__(self):
        self.memo = {}
        self.counter = 1

    def memo_lookup(self, w_obj, builder, char='R'):
        if w_obj in self.memo:
            builder.append('%s:%d;' % (char, self.memo[w_obj]))
            return True
        self.memo[w_obj] = self.counter
        return False

    def add_counter(self):
        self.counter += 1

class UnserializerMemo(object):
    def __init__(self):
        self.all_refs = []

    def add_object_reference(self, w_ref):
        assert isinstance(w_ref, W_Reference)
        self.all_refs.append(w_ref)


class SerializerError(Exception):
    pass

class EOFError(SerializerError):
    pass

class StreamIO(object):
    def __init__(self, s):
        self.pos = 0
        self.error_pos = 0
        self.s = s

    def readchr(self):
        prev_pos = self.pos
        assert prev_pos >= 0
        if prev_pos >= len(self.s):
            raise SerializerError("Unexpected end of data")
        self.pos += 1
        return self.s[prev_pos]

    def read(self, n):
        start = self.pos
        assert start >= 0
        stop = start + n
        if stop > len(self.s):
            raise SerializerError("Unexpected end of data")
        self.pos = stop
        return self.s[start:stop]

    def expect(self, e):
        got = self.readchr()
        if got != e:
            raise SerializerError("Got %s expected %s" % (got, e))

    def read_until(self, delim):
        assert len(delim) == 1
        start = self.pos
        assert start >= 0
        newpos = self.s.find(delim, start)
        if newpos < 0:
            raise EOFError("unexpected end of stream")
        res = self.s[start:newpos]
        self.pos = newpos + 1
        return res

    def read_int_until(self, delim):
        s = self.read_until(delim)
        try:
            value = int(s)
        except ValueError:
            raise SerializerError("bad count")
        return value

    def read_nonneg_int_until(self, delim):
        value = self.read_int_until(delim)
        if value < 0:
            raise SerializerError("negative count")
        return value


def load_array(space, fp, memo):
    w_result = space.empty_ref()
    memo.add_object_reference(w_result)

    count = fp.read_nonneg_int_until(':')
    fp.expect('{')
    w_array = space.new_array_from_list([])
    for idx in range(count):
        w_key = load_array_key(space, fp)
        w_value_ref = load_ref(space, fp, memo)
        w_array = space.setitem_maybe_inplace(w_array, w_key, w_value_ref)
    fp.error_pos = fp.pos + 1
    fp.expect('}')
    w_result.store(w_array, unique=True)
    return w_result


def load_object(space, fp, memo):
    w_result = space.empty_ref()
    memo.add_object_reference(w_result)

    length_klass_name = fp.read_nonneg_int_until(':')
    fp.expect('"')
    klass_name = fp.read(length_klass_name)
    fp.expect('"')
    interp = space.ec.interpreter
    klass = interp.lookup_class_or_intf(klass_name)
    if klass is None:
        klass = k_incomplete
        w_instance = klass.get_empty_instance(space)
        w_instance.setattr(interp, '__PHP_Incomplete_Class_Name',
                           space.wrap(klass_name), None)
    else:
        w_instance = klass.get_empty_instance(space)
    w_result.store(w_instance)
    fp.expect(':')
    count_attrs = fp.read_int_until(':')    # negative value accepted :-(
    fp.expect('{')
    for i in xrange(count_attrs):
        w_attr = load_array_key(space, fp)
        w_value_ref = load_ref(space, fp, memo)
        attr_name = space.str_w(w_attr)
        w_instance.setattr(interp, attr_name, w_value_ref, None)
    fp.error_pos = fp.pos + 1
    fp.expect('}')
    if '__wakeup' in klass.methods:
        klass.methods['__wakeup'].method_func.call_args(space.ec.interpreter,
                                                        [], w_this=w_instance,
                                                        thisclass=klass)
    return w_result


def load_array_key(space, fp):
    fp.error_pos = fp.pos
    type_ = fp.readchr()
    w_result = load_primitive(space, fp, type_)
    if w_result.tp != space.tp_str and w_result.tp != space.tp_int:
        fp.error_pos = fp.pos
        raise SerializerError('bad type for array key')
    return w_result

def load_primitive(space, fp, type_):
    if type_ == 's':
        fp.expect(':')
        old1 = fp.pos
        length = fp.read_nonneg_int_until(':')
        fp.expect('"')
        fp.error_pos = old1
        data = fp.read(length)
        fp.error_pos = fp.pos
        fp.expect('"')
        fp.error_pos = fp.pos + 1
        fp.expect(';')
        return space.newstr(data)
    elif type_ == 'N':
        fp.expect(';')
        return space.w_Null
    elif type_ == 'i':
        fp.expect(':')
        data = fp.read_until(';')
        try:
            i = int(data)
        except ValueError:
            raise SerializerError('bad int')
        return space.wrap(i)
    elif type_ == 'd':
        fp.expect(':')
        data = fp.read_until(';')
        w_number, valid = convert_string_to_number(data)
        if not valid:
            raise SerializerError('bad double')
        return space.newfloat(w_number.float_w(space))
    elif type_ == 'b':
        fp.expect(':')
        digit = fp.readchr()
        if digit == '0':
            w_result = space.w_False
        elif digit == '1':
            w_result = space.w_True
        else:
            raise SerializerError('bad bool')
        fp.expect(';')
        return w_result
    elif type_ == '}':
        space.ec.notice("unserialize(): Unexpected end of serialized data")
    raise SerializerError('malformed input')

def load_reference(fp, memo):
    fp.expect(':')
    index = fp.read_int_until(';') - 1
    if index < 0 or index >= len(memo.all_refs):
        fp.error_pos = fp.pos
        raise SerializerError('bad reference number')
    return memo.all_refs[index]

def load_ref(space, fp, memo):
    fp.error_pos = fp.pos
    type_ = fp.readchr()
    if type_ == 'a':
        fp.expect(':')
        w_result = load_array(space, fp, memo)
    elif type_ == 'O':
        fp.expect(':')
        w_result = load_object(space,  fp, memo)
    elif type_ == 'R':
        w_result = load_reference(fp, memo)
    elif type_ == 'r':
        w_temp = load_reference(fp, memo)
        w_result = W_Reference(w_temp.deref())
    else:
        w_result = W_Reference(load_primitive(space, fp, type_))
        memo.add_object_reference(w_result)
    return w_result


def unserialize(space,  s):
    """Unserialize the string s.

    """
    if len(s) == 0:
        space.ec.hippy_warn("unserialize(): empty string")
        return space.w_False
    fp = StreamIO(s)
    try:
        return load_ref(space, fp, UnserializerMemo())
    except SerializerError:
        space.ec.notice("unserialize(): Error at "
                        "offset %d of %d bytes" % (fp.error_pos, len(s)))
        return space.w_False
