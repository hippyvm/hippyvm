import sys

from rpython.rlib import longlong2float
from rpython.rlib.unroll import unrolling_iterable
from rpython.rlib.rarithmetic import r_singlefloat, widen
from rpython.rtyper.tool.rfficache import sizeof_c_type
from rpython.rtyper.lltypesystem import lltype, rffi

from hippy.builtin import wrap, StringArg

from rpython.rlib.rarithmetic import intmask


float_buf = lltype.malloc(
    rffi.FLOATP.TO, 1, flavor='raw', immortal=True)

double_buf = lltype.malloc(
    rffi.DOUBLEP.TO, 1, flavor='raw', immortal=True)


class FormatException(Exception):
    def __init__(self, message, char=''):
        self.message = message
        self.char = char


class FmtDesc(object):
    def __init__(self, fmtchar, attrs):
        self.fmtchar = fmtchar
        self.alignment = 1
        self.signed = False
        self.needcount = False
        self.bigendian = False
        self.__dict__.update(attrs)

    def _freeze_(self):
        return True


def table2desclist(table):
    items = table.items()
    items.sort()
    lst = [FmtDesc(key, attrs) for key, attrs in items]
    return unrolling_iterable(lst)


# Pack Methods

def _pack_string(pack_obj, fmtdesc, count, pad):
    if pack_obj.arg_index >= len(pack_obj.arg_w):
        raise FormatException("not enough arguments")

    string = pack_obj.space.str_w(pack_obj.pop_arg())
    if len(string) < count:
        for c in string:
            pack_obj.result.append(c)
        if count != sys.maxint:
            pack_obj.result.append(pad * (count - len(string)))
    else:
        assert count >= 0
        for c in string[:count]:
            pack_obj.result.append(c)


def pack_Z_nul_padded_string(pack_obj, fmtdesc, count):
    if pack_obj.arg_index >= len(pack_obj.arg_w):
        raise FormatException("not enough arguments")
    c = count - 1
    assert c >= 0
    string = pack_obj.space.str_w(pack_obj.pop_arg())[:c]
    for c in string:
        pack_obj.result.append(c)
    pack_obj.result.append('\x00')

    if len(pack_obj.result) < count:
        pack_obj.result.append('\x00' * (count - len(string) - 1))


def pack_nul_padded_string(pack_obj, fmtdesc, count):
    _pack_string(pack_obj, fmtdesc, count, '\x00')


def pack_space_padded_string(pack_obj, fmtdesc, count):
    _pack_string(pack_obj, fmtdesc, count, ' ')


def _pack_hex_string(pack_obj, fmtdesc, count, nibbleshift):
    if pack_obj.arg_index >= len(pack_obj.arg_w):
        raise FormatException("not enough arguments")
    string = pack_obj.space.str_w(pack_obj.pop_arg())
    if len(string) < count and count < sys.maxint:
        raise FormatException("not enough characters in string")

    output = range((len(string) + (len(string) % 2)) / 2)

    value = 0
    first = 1
    outputpos = 0

    for element in string:

        o_element = ord(element)

        o_0, o_9 = ord('0'), ord('9')
        o_A, o_F = ord('A'), ord('F')
        o_a, o_f = ord('a'), ord('f')

        if o_0 <= o_element <= o_9:
            digit = o_element - o_0

        elif o_A <= o_element <= o_F:
            digit = o_element - o_A + 10

        elif o_a <= o_element <= o_f:
            digit = o_element - o_a + 10

        else:
            raise FormatException("illegal hex digit %s" % element)

        value = (value << 4 | digit)
        c = (value & 0xf) << nibbleshift | (value & 0xf0) >> nibbleshift

        if first:
            output[outputpos] = c
            first -= 1
            outputpos += 1
        else:
            output[outputpos-1] = c
            first += 1
            value = 0

        nibbleshift = (nibbleshift + 4) & 7

    for o in output:
        pack_obj.result.append(chr(o))


def pack_hex_string_low_nibble_first(pack_obj, fmtdesc, count):
    _pack_hex_string(pack_obj, fmtdesc, count, 0)


def pack_hex_string_high_nibble_first(pack_obj, fmtdesc, count):
    _pack_hex_string(pack_obj, fmtdesc, count, 4)


def pack_int(pack_obj, fmtdesc, count):
    for _ in range(count):
        if pack_obj.arg_index >= len(pack_obj.arg_w):
            raise FormatException("too few arguments")

        value = pack_obj.space.int_w(pack_obj.pop_arg())

        if fmtdesc.bigendian:
            iterable = range(fmtdesc.size-1, -1, -1)
        else:
            iterable = range(fmtdesc.size)

        for i in iterable:
            if fmtdesc.bigendian:
                x = (value >> (8*i)) & 0xff
                pack_obj.result.append(chr(x))
            else:
                pack_obj.result.append(chr(value & 0xff))
                value >>= 8


def pack_float(pack_obj, fmtdesc, count):
    for _ in range(count):
        if pack_obj.arg_index >= len(pack_obj.arg_w):
            raise FormatException("too few arguments")

        value = pack_obj.space.float_w(pack_obj.pop_arg())
        floatval = r_singlefloat(value)
        value = longlong2float.singlefloat2uint(floatval)
        value = widen(value)

        for i in range(fmtdesc.size):
            pack_obj.result.append(chr(value & 0xff))
            value >>= 8


def pack_double(pack_obj, fmtdesc, count):
    for _ in range(count):
        if pack_obj.arg_index >= len(pack_obj.arg_w):
            raise FormatException("too few arguments")

        value = pack_obj.space.float_w(pack_obj.pop_arg())
        value = longlong2float.float2longlong(value)

        for i in range(fmtdesc.size):
            pack_obj.result.append(chr(value & 0xff))
            value >>= 8


def pack_nul_byte(pack_obj, fmtdesc, count):

    if count == sys.maxint:
        raise FormatException("'*' ignored")

    for _ in range(count):
        pack_obj.result.append(chr(0x00))
        pack_obj.arg_index += 1


def pack_back_up_one_byte(pack_obj, fmtdesc, count):

    if count == sys.maxint:
        raise FormatException("'*' ignored")

    if pack_obj.result:
        pack_obj.result.pop()
        pack_obj.arg_index -= 1
    else:
        raise FormatException("outside of string")


def pack_nullfill_to_absolute_position(pack_obj, fmtdesc, count):

    if count == sys.maxint:
        raise FormatException("'*' ignored")

    if len(pack_obj.result) <= pack_obj.arg_index:
        pack_obj.result.append(chr(0x00) * count)
    else:
        lenght_diff = count - len(pack_obj.result)
        if lenght_diff > 0:
            for _ in range(lenght_diff):
                pack_obj.result.append(chr(0x00))
        if lenght_diff < 0:
            for _ in range(lenght_diff * -1):
                pack_obj.result.pop()


# Unpack Methods

def unpack_nul_padded_string(unpack_obj, fmtdesc, count, name):

    data = []
    for _ in range(count):

        if unpack_obj.string_index >= len(unpack_obj.string):
            raise FormatException(
                "Type %s: not enough input, need %s, have %s" % (
                    fmtdesc.fmtchar, count, len(data)),
                fmtdesc.fmtchar)

        data.append(unpack_obj.string[unpack_obj.string_index])
        unpack_obj.string_index += 1
    unpack_obj.result_append(name, count, 0, "".join(data), 0)


def unpack_space_padded_string(unpack_obj, fmtdesc, count, name):

    data = []
    for _ in range(count):

        if unpack_obj.string_index >= len(unpack_obj.string):
            raise FormatException(
                "Type %s: not enough input, need %s, have %s" % (
                    fmtdesc.fmtchar, count, len(data)),
                fmtdesc.fmtchar)

        element = unpack_obj.string[unpack_obj.string_index]
        unpack_obj.string_index += 1

        data.append(element)

    while data:
        if data[-1] in ['\x00', ' ', '\t', '\r', '\n']:
            data.pop()
        else:
            break
    unpack_obj.result_append(name, count, 0, "".join(data), 0)


def unpack_nul_padded_string_2(unpack_obj, fmtdesc, count, name):
    data = []
    for _ in range(count):

        if unpack_obj.string_index >= len(unpack_obj.string):
            raise FormatException(
                "Type %s: not enough input, need %s, have %s" % (
                    fmtdesc.fmtchar, count, len(data)),
                fmtdesc.fmtchar)

        element = unpack_obj.string[unpack_obj.string_index]
        unpack_obj.string_index += 1

        if element == '\x00':
            break

        data.append(element)

    unpack_obj.result_append(name, count, 0, "".join(data), 0)


hex_digit = ['0', '1', '2', '3',
             '4', '5', '6', '7',
             '8', '9', 'a', 'b',
             'c', 'd', 'e', 'f']


def unpack_hex_string(unpack_obj, fmtdesc, count, name,
                      high_nibble_first=False):
    data = []
    count = count / 2 + count % 2
    for _ in range(count):

        if unpack_obj.string_index >= len(unpack_obj.string):
            raise FormatException(
                "Type %s: not enough input, need %s, have %s" % (
                    fmtdesc.fmtchar, count, len(data)),
                fmtdesc.fmtchar)

        element = ord(unpack_obj.string[unpack_obj.string_index])

        unpack_obj.string_index += 1

        nibbles = element % 16, element / 16
        if high_nibble_first:
            nibbles = element / 16, element % 16
        nibbles_digits = hex_digit[nibbles[0]], hex_digit[nibbles[1]]
        data.append('%s%s' % nibbles_digits)

    _, repetitions, _ = unpack_obj.fmt_interpreted[0]
    to_append = "".join(data)
    assert repetitions >= 0
    to_append = to_append[:repetitions]
    unpack_obj.result_append(name, count, 0, to_append, 0)


def unpack_hex_string_low_nibble_first(unpack_obj, fmtdesc, count, name):
    unpack_hex_string(unpack_obj, fmtdesc, count, name)


def unpack_hex_string_high_nibble_first(unpack_obj, fmtdesc, count, name):
    unpack_hex_string(unpack_obj, fmtdesc, count, name, True)


def unpack_int(unpack_obj, fmtdesc, count, name):
    for pos in range(count):
        a = unpack_obj.string_index
        b = unpack_obj.string_index+fmtdesc.size
        assert a >= 0
        assert b >= 0
        data = unpack_obj.string[
            a:b
        ]

        if not len(data) == fmtdesc.size:
            raise FormatException(
                "Type %s: not enough input, need %s, have %s" % (
                    fmtdesc.fmtchar, count, len(data)),
                fmtdesc.fmtchar)

        unpack_obj.string_index += fmtdesc.size
        value = 0

        if fmtdesc.bigendian:
            for i in range(fmtdesc.size):
                byte = ord(data[i])
                if fmtdesc.signed and i == 0 and byte > 128:
                    byte -= 256
                value |= byte << (fmtdesc.size-1-i) * 8
        else:
            for i in range(fmtdesc.size):
                byte = ord(data[i])
                if fmtdesc.signed and i == fmtdesc.size - 1 and byte > 128:
                    byte -= 256
                value |= byte << i*8
        unpack_obj.result_append(name, count, pos+1, None, intmask(value))


def unpack_signed_char(unpack_obj, fmtdesc, count):
    pass


def unpack_float(unpack_obj, fmtdesc, count, name):
    for pos in range(count):
        a = unpack_obj.string_index
        b = unpack_obj.string_index+fmtdesc.size
        assert a >= 0
        assert b >= 0
        data = unpack_obj.string[
            a:b
        ]

        if not len(data) == fmtdesc.size:
            raise FormatException(
                "Type %s: not enough input, need %s, have %s" % (
                    fmtdesc.fmtchar, count, len(data)),
                fmtdesc.fmtchar)

        unpack_obj.string_index += fmtdesc.size

        p = rffi.cast(rffi.CCHARP, float_buf)
        assert fmtdesc.size >= 0
        for i, element in enumerate(data[:fmtdesc.size]):
            p[i] = element

        floatval = float_buf[0]
        unpack_obj.result_append(name, count, pos+1, None, float(floatval))


def unpack_double(unpack_obj, fmtdesc, count, name):
    for pos in range(count):

        a = unpack_obj.string_index
        b = unpack_obj.string_index+fmtdesc.size
        assert a >= 0
        assert b >= 0
        data = unpack_obj.string[
            a:b
        ]

        if not len(data) == fmtdesc.size:
            raise FormatException(
                "Type %s: not enough input, need %s, have %s" % (
                    fmtdesc.fmtchar, count, len(data)),
                fmtdesc.fmtchar)

        unpack_obj.string_index += fmtdesc.size

        p = rffi.cast(rffi.CCHARP, double_buf)
        assert fmtdesc.size >= 0
        for i, element in enumerate(data[:fmtdesc.size]):
            p[i] = element

        value = double_buf[0]
        unpack_obj.result_append(name, count, pos+1, None, value)


def unpack_nul_byte(unpack_obj, fmtdesc, count, name):
     # Do nothing with input, just skip it
    pass


def unpack_back_up_one_byte(unpack_obj, fmtdesc, count, name):
    unpack_obj.string_index -= count
    if unpack_obj.string_index < 0:
        unpack_obj.string_index = 0


def unpack_nullfill_to_absolute_position(unpack_obj, fmtdesc, count, name):
    unpack_obj.string_index += count


fmt_table = {
    'a': {
        'size': 1,
        'pack': pack_nul_padded_string,
        'unpack': unpack_nul_padded_string
    },
    'A': {
        'size': 1,
        'pack': pack_space_padded_string,
        'unpack': unpack_space_padded_string
    },
    'h': {
        'size': 1,
        'pack': pack_hex_string_low_nibble_first,
        'unpack': unpack_hex_string_low_nibble_first
    },
    'Z': {
        'size': 1,
        'pack': pack_Z_nul_padded_string,
        'unpack': unpack_nul_padded_string_2
    },
    'H': {
        'size': 1,
        'pack': pack_hex_string_high_nibble_first,
        'unpack': unpack_hex_string_high_nibble_first
    },
    'c': {
        'size': 1,
        'pack': pack_int,
        'unpack': unpack_int,
        'signed': True,
    },
    'C': {
        'size': 1,
        'pack': pack_int,
        'unpack': unpack_int,
    },
    's': {
        'size': 2,
        'pack': pack_int,
        'unpack': unpack_int,
        'signed': True,
    },
    'S': {
        'size': 2,
        'pack': pack_int,
        'unpack': unpack_int,
    },
    'n': {
        'size': 2,
        'pack': pack_int,
        'unpack': unpack_int,
        'bigendian': True,
    },
    'v': {
        'size': 2,
        'pack': pack_int,
        'unpack': unpack_int,
        'bigendian': False,
    },
    'i': {
        'size': sizeof_c_type('unsigned int'),
        'pack': pack_int,
        'unpack': unpack_int,
        'signed': True,
    },
    'I': {
        'size': 4,
        'pack': pack_int,
        'unpack': unpack_int,
    },
    'l': {
        'size': 4,
        'pack': pack_int,
        'unpack': unpack_int,
        'signed': True
    },
    'L': {
        'size': 4,
        'pack': pack_int,
        'unpack': unpack_int,
    },
    'N': {
        'size': 4,
        'pack': pack_int,
        'unpack': unpack_int,
        'bigendian': True,
    },
    'V': {
        'size': 4,
        'pack': pack_int,
        'unpack': unpack_int,
    },
    'f': {
        'size': sizeof_c_type('float'),
        'pack': pack_float,
        'unpack': unpack_float
    },
    'd': {
        'size': sizeof_c_type('double'),
        'pack': pack_double,
        'unpack': unpack_double
    },
    'x': {
        'size': 1,
        'pack': pack_nul_byte,
        'unpack': unpack_nul_byte
    },
    'X': {
        'size': 1,
        'pack': pack_back_up_one_byte,
        'unpack': unpack_back_up_one_byte
    },
    '@': {
        'size': 1,
        'pack': pack_nullfill_to_absolute_position,
        'unpack': unpack_nullfill_to_absolute_position
    },

}

unroll_fmttable = table2desclist(fmt_table)


class Pack(object):

    def __init__(self, space, fmt, arg_w):
        self.space = space
        self.fmt = fmt
        # self.table = unroll_fmttable

        self.arg_w = arg_w
        self.arg_index = 0

    def pop_arg(self):
        result = self.arg_w[self.arg_index]
        self.arg_index += 1
        return result

    def _size(self, fmt_interpreted):
        size = 0
        for fmtdesc, repetitions in self.fmt_interpreted:
            size += fmtdesc.size * repetitions
        return size

    def _get_fmtdesc(self, char):
        for fmtdesc in unroll_fmttable:
            if char == fmtdesc.fmtchar:
                return fmtdesc

    def interpret(self):
        results = []
        rep = 0
        from rpython.rlib.rsre.rsre_re import finditer
        itr = finditer('((\S)(\d+|\*)?)', self.fmt)
        try:
            while True:
                _, char, repetitions = itr.next().groups()
                fmtdesc = self._get_fmtdesc(char)
                if repetitions is None:
                    rep = 1
                elif repetitions == '*':
                    rep = sys.maxint
                else:
                    rep = int(repetitions)
                results.append((fmtdesc, rep))
        except StopIteration:
            pass
        return results

    def build(self):
        self.fmt_interpreted = self.interpret()
        self.size = self._size(self.fmt_interpreted)

        self.result = []

        # do not count X as argument that require input from arg_w
        valid_args = 0
        for fmtdesc, repetitions in self.fmt_interpreted:
            if fmtdesc.fmtchar != 'X':
                valid_args += 1

        for fmtdesc, repetitions in self.fmt_interpreted:

            try:
                fmtdesc.pack(self, fmtdesc, repetitions)
            except FormatException as e:
                self.space.ec.warn(
                    "pack(): Type %s: %s" % (fmtdesc.fmtchar, e.message)
                )
        if valid_args < len(self.arg_w):
            self.space.ec.warn(
                "pack(): %s "
                "arguments unused" % (len(self.arg_w) - self.arg_index)
            )

        return "".join(self.result)


class UnpackContainer(object):
    def __init__(self, name, str_value, num_value):
        self.name = name
        self.str_value = str_value
        self.num_value = num_value


class Unpack(object):

    def __init__(self, fmt, string):
        self.fmt = fmt
        self.string = string
        self.string_index = 0

        self.table = unroll_fmttable
        self.result = []

    def _get_fmtdect(self, char):
        for fmtdesc in unroll_fmttable:
            if char == fmtdesc.fmtchar:
                return fmtdesc
        raise FormatException("Invalid format type %s" % char)

    def result_append(self, name, count, pos, str_val, num_value):
        if name:
            if count > 1:
                name += str(pos)
        self.result.append(
            UnpackContainer(name, str_val, num_value))

    def interpret(self):
        results = []
        rep = 0
        from rpython.rlib.rsre.rsre_re import finditer
        itr = finditer('((\S)(\d+|\*)?((\/)|(([a-z]+)(\/)?))?)', self.fmt)
        try:
            while True:
                _, char, repetitions, _, _, _, name, _ = itr.next().groups()
                if char != '/':
                    fmtdesc = self._get_fmtdect(char)
                    if repetitions is None:
                        rep = 1
                    elif repetitions == '*':
                        rep = sys.maxint
                    else:
                        rep = int(repetitions)
                    results.append((fmtdesc, rep, name))
        except StopIteration:
            pass
        return results

    def build(self):
        self.fmt_interpreted = self.interpret()

        for fmtdesc, repetitions, name in self.fmt_interpreted:
            if repetitions == sys.maxint:
                repetitions = len(self.string) - self.string_index
                if fmtdesc.fmtchar in ('h', 'H'):
                    repetitions *= 2
            fmtdesc.unpack(self,  fmtdesc,  repetitions,  name)
        return self.result


@wrap(['space', StringArg(None), 'args_w'])
def pack(space, formats, args_w):
    results = Pack(space, formats, args_w).build()
    return space.newstr(results)


def _unpack(space, formats, string):
    try:
        results = Unpack(formats, string).build()
    except FormatException as e:
        space.ec.warn("unpack(): %s" % (e.message))

        return space.w_False
    pairs = []
    for i, uc in enumerate(results):
        name = uc.name
        if name is None:
            w_key = space.newint(i + 1)
        else:
            w_key = space.newstr(name)
        if uc.str_value:
            pairs.append((w_key, space.wrap(uc.str_value)))
        else:
            pairs.append((w_key, space.wrap(uc.num_value)))

    return space.new_array_from_pairs(pairs)