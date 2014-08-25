import struct

from rpython.rlib.objectmodel import compute_hash
from rpython.rlib.rstring import StringBuilder, replace
from hippy.objects.base import W_Object
from hippy.objects.reference import VirtualReference
from hippy.objects.convert import convert_string_to_number, strtol
from hippy.error import ConvertError, OffsetError


class StringOffset(VirtualReference):
    """A very special kind of reference that points to a single character
    inside a string.
    """
    def __init__(self, w_str, index):
        self.w_str = w_str
        self.index = index

    def deref(self):
        char = self.w_str.character(self.index)
        return single_char_string(char)


class W_StringObject(W_Object):
    """Abstract base class.  Concrete subclasses use various strategies.
    This base class defines the general methods that can be implemented
    without needing to call (too often) the strlen() and character()
    methods.
    """

    supports_arithmetics = True

    @staticmethod
    def newmutablestr(chars):
        return W_MutableStringObject(chars)

    @staticmethod
    def newconststr(s):
        return W_ConstStringObject(s)

    def hash(self, space):
        # XXX improve
        return compute_hash(self.unwrap())

    def as_string(self, space, quiet=False):
        return self

    def as_stringoffset(self, space, give_notice):
        # pom pom pom
        s = self.unwrap()
        intval, any_digit = strtol(s)
        if not any_digit:
            if give_notice:
                space.ec.warn("Illegal string offset '%s'" % s)
                return 0
            else:
                return -1
        w_number_ignored, valid = convert_string_to_number(s)
        if not valid:
            if give_notice:
                space.ec.notice("A non well formed numeric value encountered")
            else:
                return -1
        if w_number_ignored.tp != space.tp_int:
            if give_notice:
                space.ec.warn("Illegal string offset '%s'" % s)
            else:
                return -1
        return intval

    def str(self, space, quiet=False):
        return self.unwrap()

    def repr(self):
        s = self.unwrap()
        if len(s) > 10:
            s = s[:10] + '...'
        return "'%s'" % s

    def dump(self):
        return "'%s'" % self.unwrap()

    def as_number(self, space=None):
        s = self.unwrap()
        w_number, valid = convert_string_to_number(s)
        return w_number      # ignore 'valid'

    def is_really_valid_number(self, space=None):
        s = self.unwrap()
        w_number, valid = convert_string_to_number(s)
        return valid

    def int_w(self, space):
        return space.int_w(self.as_number())

    def float_w(self, space):
        return self.as_number().float_w(space)

    def uplusplus(self, space):
        if self.is_really_valid_number():
            return self.as_number().uplusplus(space)
        result = self.copy()
        assert isinstance(result, W_MutableStringObject)
        chars = result._arrayval
        #
        if (len(chars) >= 3 and
            '0' <= chr(chars[0]) <= '9' and
            '0' <= chr(chars[-1]) <= '9'):
            count_letters = 0
            for i in range(1, len(chars)-1):
                c = chr(chars[i])
                if '0' <= c <= '9':
                    continue
                elif c.isalpha():
                    count_letters += 1
                else:
                    count_letters = -1
                    break
            if count_letters == 1:
                space.ec.hippy_warn(
                    "'++' on a string <digits><character><digits> "
                    "is dangerous: if <character> would be E, it "
                    "would be interpreted as a float")
        #
        i = len(chars) - 1
        extra = '1'
        while i >= 0:
            c = chr(chars[i])
            if not c.isalnum():
                break
            if c == '9':
                c = '0'
                extra = '1'
            elif c == 'Z':
                c = 'A'
                extra = 'A'
            elif c == 'z':
                c = 'a'
                extra = 'a'
            else:
                chars[i] = ord(c) + 1
                break
            chars[i] = ord(c)
            i -= 1
        else:
            result.set_arrayval(extra + chars)
        return result

    def uminusminus(self, space):
        if self.is_really_valid_number():
            return self.as_number().uminusminus(space)
        return self

    def uminus(self, space):
        return self.as_number().uminus(space)

    def strconcat(self, space, w_other):
        builder = StringBuilder()
        self.append_to_builder(builder)
        w_other.append_to_builder(builder)
        return W_ConcatStringObject(builder)

    def _setitem_ref(self, space, w_arg, w_ref):
        raise OffsetError('cannot set item by reference on a string')

    def appenditem_inplace(self, space, w_item, as_ref=False):
        raise space.ec.fatal('[] operator not supported for strings')

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.unwrap())

##    def hash(self):
##        self.force_concat()
##        return self.strategy.hash(self.storage)

    def var_dump(self, space, indent, recursion):
        s = self.unwrap()
        return '%sstring(%d) "%s"\n' % (indent, len(s), s)

    def var_export(self, space, indent, recursion, suffix):
        s = self.unwrap()
        s = string_var_export(s)

        return '%s%s%s' % (indent, s, suffix)

    def is_empty_value(self):
        return self.strlen() == 0

    def abs(self, space):
        return self.as_number(space).abs(space)

    def overflow_convert(self, space):
        w_obj, fully_processed = convert_string_to_number(self.unwrap())
        if not fully_processed:
            if self.float_w(space) != 0.0:
                space.ec.notice("A non well formed numeric "
                               "value encountered")
            else:
                raise TypeError
        return w_obj

    def as_int_arg(self, space):
        if not self.is_numeric():
            raise ConvertError('not a numeric string')
        s = self.unwrap()
        w_obj, valid = convert_string_to_number(s)
        if not valid:
            space.ec.notice("A non well formed numeric value encountered")
        return w_obj.int_w(space)


class StringMixin(object):
    """This is a mixin to provide a more efficient implementation for
    each subclass.  It defines the methods that call character() a lot.
    Being a mixin, each method is actually repeated in the subclass,
    which allows character() to be inlined.
    """
    _mixin_ = True

    def _lookup_item_ref(self, space, w_arg):
        index = w_arg.as_stringoffset(space, give_notice=False)
        if 0 <= index < self.strlen():
            return StringOffset(self, index)
        else:
            return None

    def getitem(self, space, w_arg, give_notice=False):
        index = w_arg.as_stringoffset(space, give_notice)
        if 0 <= index < self.strlen():
            return single_char_string(self.character(index))
        else:
            if give_notice:
                space.ec.notice("Uninitialized string offset: %d" % index)
                return space.newstr("")
            else:
                return space.w_Null    # xxx hack for test_isset_out_of_bound

    def setitem2_maybe_inplace(self, space, w_arg, w_value, unique_item=False):
        index = w_arg.as_stringoffset(space, give_notice=True)
        c = space.getchar(w_value)
        if index < 0:
            space.ec.warn("Illegal string offset:  %d" % index)
            return self, space.w_Null
        res = self.as_mutable_string()
        res.set_char_at(index, c)
        return res, single_char_string(c)

    def unwrap(self):
        # note: always overriden so far
        length = self.strlen()
        builder = StringBuilder(length)
        self.append_to_builder(builder)
        return builder.build()

    def serialize(self, space, builder, memo):
        builder.append("s:")
        builder.append(str(self.strlen()))
        builder.append(':"')
        self.append_to_builder(builder)
        builder.append('";')
        return True

    def ll_serialize(self, builder):
        builder.append("s")
        builder.append(struct.pack("l", self.strlen()))
        self.append_to_builder(builder)

    def is_true(self, space):
        length = self.strlen()
        if length == 0:
            return False
        elif length == 1:
            return self.character(0) != "0"
        else:
            return True

    def is_numeric(self):
        for i in range(self.strlen()):
            c = self.character(i)
            if not c.isspace():
                break
        else:
            return False
        if c in '+-':
            if i == self.strlen() - 1:
                return False
            c = self.character(i + 1)
        return c.isdigit()

    def getchar(self, space):
        if self.strlen() >= 1:
            return self.character(0)
        else:
            return chr(0)

    def bitwise_not(self, space):
        length = self.strlen()
        builder = StringBuilder(length)
        for i in range(length):
            c = ord(self.character(i))
            builder.append(chr(c ^ 0xff))
        return W_ConstStringObject(builder.build())


class W_ConstStringObject(StringMixin, W_StringObject):

    _immutable_ = True

    def __init__(self, strval):
        assert strval is not None
        assert isinstance(strval, str)
        self._strval = strval

    def __eq__(self, other):
        """ For testing """
        return (isinstance(other, W_ConstStringObject) and
                self._strval == other._strval)

    def strlen(self):
        return len(self._strval)

    def character(self, index):
        return self._strval[index]

    def unwrap(self):
        return self._strval

    def append_to_builder(self, builder):
        builder.append(self._strval)

    def copy(self):
        return self.as_mutable_string()

    def as_mutable_string(self):
        self._note_making_a_copy()
        return W_MutableStringObject(bytearray(self._strval))

    def eval_static(self, space):
        return self


class W_MutableStringObject(StringMixin, W_StringObject):

    def __init__(self, val):
        self._arrayval = val

    def set_arrayval(self, val):
        self._arrayval = val

    def set_char_at(self, index, c):
        if index >= len(self._arrayval):
            self._arrayval += " " * (index + 1 - len(self._arrayval))
            # XXX better complexity needed?
        self._arrayval[index] = ord(c)

    def copy(self):
        self._note_making_a_copy()
        return W_MutableStringObject(bytearray(self._arrayval))

    def as_mutable_string(self):
        return self

    def strlen(self):
        return len(self._arrayval)

    def character(self, index):
        return chr(self._arrayval[index])

    def unwrap(self):
        return str(self._arrayval)

    def append_to_builder(self, builder):
        for i in range(len(self._arrayval)):
            builder.append(chr(self._arrayval[i]))


class W_ConcatStringObject(StringMixin, W_StringObject):
    _immutable_fields_ = ['_builder', '_length']
    _cache = None

    def __init__(self, builder):
        # Grab the current length of the builder now.  Later, more data
        # may be appended to it, but it must not change the present
        # W_ConcatStringObject.
        self._builder = builder
        self._length = builder.getlength()

    def strconcat(self, space, w_other):
        builder = self._builder
        if self._length != builder.getlength():
            return W_StringObject.strconcat(self, space, w_other)
        w_other.append_to_builder(builder)
        return W_ConcatStringObject(builder)

    def strlen(self):
        return self._length

    def character(self, index):
        return self.unwrap()[index]

    def unwrap(self):
        if self._cache is None:
            s = self._builder.build()
            if len(s) > self._length:
                s = s[:self._length]
            self._cache = s
        return self._cache

    def append_to_builder(self, builder):
        builder.append(self.unwrap())

    def copy(self):
        return self.as_mutable_string()

    def as_mutable_string(self):
        self._note_making_a_copy()
        return W_MutableStringObject(bytearray(self.unwrap()))


def single_char_string(c):
    assert len(c) == 1
    return W_ConstStringObject(c)


def string_var_export(string):
    assert string is not None
    parts = string.split('\x00')
    escaped_parts = []
    for part in parts:
        escaped_part = "'%s'" % replace(replace(part, '\\', '\\\\'), "'", "\\'")
        escaped_parts.append(escaped_part)

    return ' . "\\0" . '.join(escaped_parts)


EMPTY_STRING = W_ConstStringObject("")
