import sys, math
from collections import OrderedDict

from rpython.rlib.rstring import StringBuilder
from rpython.rlib import jit
from rpython.rlib.unroll import unrolling_iterable
from rpython.rlib import rmd5
from rpython.rlib.objectmodel import newlist_hint
from rpython.rlib.objectmodel import specialize
from rpython.rlib.rsha import sha

from hippy.objspace import ObjSpace, getspace, PHP_WHITESPACE
from hippy.builtin import (
    wrap, Optional, LongArg, StringArg, BoolArg, ExitFunctionWithError)
from hippy.objects.resources.file_resource import W_FileResource
from hippy.error import ConvertError
from hippy.objects.base import W_Root
from hippy.constants import CONSTS
from hippy.sourceparser import is_hexdigit, hexdigit
from rpython.rlib.rfloat import double_to_string
from rpython.rlib.rfloat import DTSF_CUT_EXP_0
from rpython.rlib.rarithmetic import r_uint
from hippy.objects.convert import strtol
from rpython.rlib.rarithmetic import intmask, ovfcheck
from rpython.rlib.rrandom import Random
from hippy.module.standard.math.funcs import _bin
from hippy.module.url import _urldecode

# Side-effect: register the functions defined there:
from hippy import localemodule as locale


_random = Random()


class ValidationError(ExitFunctionWithError):
    """Raised when a PHP function gets wrong arguments"""
    def __init__(self, msg="Bad arguments", return_value=None):
        self.msg = msg
        self.return_value = return_value


def unwrap_needle(space, w_needle):
    """Helper to convert the `needle` argument of some string functions"""
    if w_needle.tp == space.tp_str:
        return space.str_w(w_needle)
    elif w_needle.tp in (space.tp_array, space.tp_object):
        raise ValidationError("needle is not a string or an integer")
    else:
        return chr(space.int_w(w_needle) % 256)


def intsign(n):
    """Return the sign of an integer."""
    if n == 0:
        return n
    elif n < 0:
        return -1
    else:
        return 1


@jit.elidable
def rstrcmp(s1, s2, case_insensitive=False):
    """RPythonic version of cmp(s1, s2)."""
    if case_insensitive:
        normalize = locale.lower_char
    else:
        normalize = lambda c: c
    cmplen = min(len(s1), len(s2))
    for i in xrange(cmplen):
        diff = ord(normalize(s1[i])) - ord(normalize(s2[i]))
        if diff != 0:
            return intsign(diff)
    else:
        return intsign(len(s1) - len(s2))


def _substr_window(n, start, length):
    if start < 0:
        start += n
        if start < 0:
            start = 0
    if length == sys.maxint:
        end = n
    elif length < 0:
        end = n + length
    else:
        end = min(start + length, n)
    assert start >= 0
    # NB: end can be < start, handling that case is the caller's responsibility
    return start, end


@specialize.arg(3)
def _broadcast_as_list(w_arr, n_items, default, convert):
    """Return a list of possibly unwrapped objects of given length"""
    space = getspace()
    if w_arr is None:
        l = [default] * n_items
    elif w_arr.tp == space.tp_array:
        l = []
        arr_iter = space.create_iter(w_arr)
        for i in range(n_items):
            if not arr_iter.done():
                _, w_val = arr_iter.next_item(space)
                l.append(convert(w_val))
            else:
                l.append(default)
    else:
        value = convert(w_arr)
        l = [value] * n_items
    return l


@specialize.argtype(1)
def _make_charmap(from_, to):
    table = [chr(n) for n in range(256)]
    for i in range(min(len(from_), len(to))):
        table[ord(from_[i])] = to[i]
    return table


def _apply_charmap(string, charmap, alloc):
    builder = StringBuilder(alloc)
    for c in string:
        builder.append(charmap[ord(c)])
    s = builder.build()
    return s


def _pairs_from_array(space, w_replacements):
    pairs = {}
    with space.iter(w_replacements) as w_iter:
        while not w_iter.done():
            w_key, w_val = w_iter.next_item(space)
            key = space.str_w(w_key)
            if len(key) == 0:
                raise ValidationError
            val = space.str_w(w_val)
            pairs.setdefault(len(key), {})[key] = val
    return pairs


def _apply_replacement(pairs, string):
    if not pairs:
        return string
    minlen = sys.maxint
    maxlen = 0
    for pair in pairs:
        minlen = min(minlen, pair)
        maxlen = max(maxlen, pair)
    builder = StringBuilder(len(string))
    i = 0
    while i < len(string):
        j = min(maxlen, len(string) - i)
        while j >= minlen:
            substr = string[i:i + j]
            try:
                builder.append(pairs[j][substr])
                i += j
                break
            except KeyError:
                pass
            j -= 1
        else:
            builder.append(string[i])
            i += 1
    s = builder.build()
    return s


def charmask(space, char_list, caller):
    """Return a character mask based on a character range specification.

    Note: the caller's name must be specified to get correct warnings.
    """
    def _warn(space, msg, caller):
        space.ec.warn(caller + "(): Invalid '..'-range" + msg)

    mask = [False] * 256
    n = len(char_list)
    i = 0
    while i < n:
        if (i + 3 < n and char_list[i + 1] == '.' and
            char_list[i + 2] == '.' and
            ord(char_list[i]) <= ord(char_list[i + 3])):
            for k in range(ord(char_list[i]), ord(char_list[i + 3]) + 1):
                mask[k] = True
            i += 4
            continue
        elif i + 1 < n and char_list[i] == '.' == char_list[i + 1]:
            if i == 0:
                _warn(space, ", no character to the left of '..'", caller)
            elif i + 2 >= n:
                _warn(space, ", no character to the right of '..'", caller)
            elif ord(char_list[i - 1]) > ord(char_list[i + 2]):
                _warn(space, ", '..'-range needs to be incrementing", caller)
            else:
                _warn(space, "", caller)
        else:
            mask[ord(char_list[i])] = True
        i += 1
    return mask


C_ESCAPE_DICT = {'\a': r'\a', '\b': r'\b', '\f': r'\f',
                 '\n': r'\n', '\r': r'\r', '\t': r'\t', '\v': r'\v'}
C_UNESCAPE_DICT = {'a': '\a', 'b': '\b', 'f': '\f',
                   'n': '\n', 'r': '\r', 't': '\t', 'v': '\v'}


def _cslashes_charmap():
    charmap = []
    for i in range(256):
        if 32 <= i <= 126:
            charmap.append('\\' + chr(i))
        elif chr(i) in C_ESCAPE_DICT:
            charmap.append(C_ESCAPE_DICT[chr(i)])
        else:
            charmap.append(r"\%03o" % i)
    return charmap
CSLASHES_CHARMAP = _cslashes_charmap()


@wrap(['space', str, str])
def addcslashes(space, string, char_list):
    """Quote string with slashes in a C style."""
    mask = charmask(space, char_list, "addcslashes")
    charmap = [CSLASHES_CHARMAP[i] if mask[i] else chr(i)
            for i in range(256)]
    s = _apply_charmap(string, charmap, 2 * len(string))
    return space.newstr(s)


@wrap(['space', str])
def stripcslashes(space, string):
    """Un-quote string quoted with addcslashes."""
    builder = StringBuilder(len(string))
    seen_backslash = False
    i = 0
    while i < len(string):
        c = string[i]
        if c != '\\':
            builder.append(c)
            i += 1
        else:
            if i == len(string) - 1:
                builder.append(c)
                break
            next = string[i + 1]
            for char in unrolling_iterable(C_UNESCAPE_DICT.keys()):
                if next == char:
                    builder.append(C_UNESCAPE_DICT[char])
                    break
            else:
                if next == 'x' and i < len(string) - 2 \
                   and is_hexdigit(string[i + 2]):
                    charvalue = hexdigit(string[i + 2])
                    if i < len(string) - 3 and is_hexdigit(string[i + 3]):
                        charvalue <<= 4
                        charvalue |= hexdigit(string[i + 3])
                        i += 1
                    i += 1
                    builder.append(chr(charvalue))
                elif '0' <= next <= '7':
                    charvalue = ord(next) - ord('0')
                    if i < len(string) - 2 and '0' <= string[i + 2] <= '7':
                        charvalue <<= 3
                        charvalue |= (ord(string[i + 2]) - ord('0'))
                        i += 1
                        if i < len(string) - 2 and '0' <= string[i + 2] <= '7':
                            charvalue <<= 3
                            charvalue &= 0xFF
                            charvalue |= (ord(string[i + 2]) - ord('0'))
                            i += 1
                    builder.append(chr(charvalue))
                else:
                    builder.append(next)
            i += 2
    s = builder.build()
    return space.newstr(s)


@wrap(['space', str])
def addslashes(space, string):
    """Quote string with slashes."""
    repl = _make_charmap("'\"\\\0", [r"\'", r'\"', r"\\", r"\0"])
    # XXX: optimize alloc?
    return space.newstr(_apply_charmap(string, repl, 2 * len(string)))


@wrap(['space', str])
def stripslashes(space, string):
    """Un-quotes a quoted string."""
    builder = StringBuilder(len(string))
    seen_backslash = False
    for c in string:
        if not seen_backslash:
            if c == '\\':
                seen_backslash = True
            else:
                builder.append(c)
        else:
            if c == '0':
                builder.append('\0')
            else:
                builder.append(c)
            seen_backslash = False
    s = builder.build()
    return space.newstr(s)


@wrap(['space', str])
def bin2hex(space, string):
    """Convert binary data into hexadecimal representation."""
    encode = '0123456789abcdef'
    builder = StringBuilder(2 * len(string))
    for c in string:
        n = ord(c)
        hi, low = n // 16, n % 16
        builder.append(encode[hi])
        builder.append(encode[low])
    s = builder.build()
    return space.newstr(s)


@wrap(['space', 'args_w'], name='chr')
def chr_(space, args_w):
    """Return a specific character."""
    if len(args_w) != 1:
        space.ec.warn("Wrong parameter count for chr()")
        return space.w_Null
    w_ascii, = args_w
    try:
        ascii = w_ascii.as_int_arg(space)
    except ConvertError:
        ascii = 0
    return space.newstr(chr(ascii % 256))


def _chunk_split(body, chunklen, end, last_end=True):
    n_chunks = (len(body) - 1) // chunklen + 1
    builder = StringBuilder(len(body) + 2 * n_chunks)
    for i in range(n_chunks - 1):
        builder.append(body[i * chunklen:(i + 1) * chunklen])
        builder.append(end)
    start = (n_chunks - 1) * chunklen
    assert start >= 0
    builder.append(body[start:])
    if last_end:
        builder.append(end)
    return builder.build()


@wrap(['space', str, Optional(int), Optional(str)])
def chunk_split(space, body, chunklen=76, end='\r\n'):
    """Split a string into smaller chunks."""
    if chunklen <= 0:
        space.ec.warn("chunk_split(): "
                "Chunk length should be greater than zero")
        return space.w_False
    if len(body) == 0:
        return space.newstr(end)
    s = _chunk_split(body, chunklen, end)
    return space.newstr(s)

#
#@wrap(['space', 'args_w'])
#def convert_cyr_string(space, args_w):
#    """Convert from one Cyrillic character set to another."""
#    raise NotImplementedError()


class UUDecodeError(ValueError):
    """Invalid uuencoded data"""


def _uudecode_char(c):
    return (ord(c) - 0x20) % 64


def _uudecode_quad(builder, A, B, C, D):
    builder.append(chr(A << 2 | B >> 4))
    builder.append(chr((B & 0xf) << 4 | C >> 2))
    builder.append(chr((C & 0x3) << 6 | D))


def _uudecode_line(data, pos, builder):
    "Decode a line of uuencoded data. Returns the new position in the data."
    length = _uudecode_char(data[pos])
    if length == 0:
        return len(data)  # stop decoding and return the string
    pos += 1
    for i in range(length // 3):
        if pos >= len(data):
            raise UUDecodeError
        A = _uudecode_char(data[pos])
        B = _uudecode_char(data[pos + 1]) if pos < len(data) - 1 else 0
        C = _uudecode_char(data[pos + 2]) if pos < len(data) - 2 else 0
        D = _uudecode_char(data[pos + 3]) if pos < len(data) - 3 else 0
        pos += 4
        if pos >= len(data):
            raise UUDecodeError
        _uudecode_quad(builder, A, B, C, D)
    if length % 3 == 1:
        A = _uudecode_char(data[pos])
        B = _uudecode_char(data[pos + 1]) if pos < len(data) - 1 else 0
        builder.append(chr(A << 2 | B >> 4))
        pos += 4
    elif length % 3 == 2:
        A = _uudecode_char(data[pos])
        B = _uudecode_char(data[pos + 1]) if pos < len(data) - 1 else 0
        C = _uudecode_char(data[pos + 2]) if pos < len(data) - 2 else 0
        builder.append(chr(A << 2 | B >> 4))
        builder.append(chr((B & 0xf) << 4 | C >> 2))
        pos += 4
    if length != 45:
        return len(data)
    pos += 1  # skip '\n'
    return pos


@wrap(['space', str], error=False)
def convert_uudecode(space, data):
    """Decode a uuencoded string."""
    if len(data) == 0:
        return space.w_False
    i = 0
    builder = StringBuilder(((len(data) // 4) * 3))
    try:
        while i < len(data):
            i = _uudecode_line(data, i, builder)
        s = builder.build()
        return space.newstr(s)
    except UUDecodeError:
        space.ec.warn("convert_uudecode(): "
                "The given parameter is not a valid uuencoded string")
        return space.w_False


def _uuencode_int6(n):
    """uuencode a 6-bit element into a char"""
    if n == 0:
        return '`'
    else:
        return chr(0x20 + n)


def _uuencode_triple(builder, A, B, C):
    A, B, C = ord(A), ord(B), ord(C)
    builder.append(_uuencode_int6(A >> 2))
    builder.append(_uuencode_int6((A & 0x3) << 4 | B >> 4))
    builder.append(_uuencode_int6((B & 0xF) << 2 | C >> 6))
    builder.append(_uuencode_int6(C & 0x3F))


def _uuencode_chunk(builder, chunk):
    "Uuencode a line of data."
    length = len(chunk)
    assert length <= 45
    builder.append(_uuencode_int6(length))
    for i in range(0, length, 3):
        A = chunk[i]
        B = chunk[i + 1] if i < length - 1 else '\0'
        C = chunk[i + 2] if i < length - 2 else '\0'
        _uuencode_triple(builder, A, B, C)
    builder.append('\n')


@wrap(['space', str], error=False)
def convert_uuencode(space, data):
    """Uuencode a string."""
    n = len(data)
    if n == 0:
        return space.w_False
    builder = StringBuilder((n // 2) * 3)
    i = -45
    for i in range(0, len(data) - 45, 45):
        _uuencode_chunk(builder, data[i:i + 45])
    start = i + 45
    assert start >= 0
    _uuencode_chunk(builder, data[start:])
    _uuencode_chunk(builder, '')
    s = builder.build()
    return space.newstr(s)

@wrap(['interp', str, Optional(int)])
def count_chars(interp, s, mode=0):
    space = interp.space
    if mode < 0 or mode > 4:
        interp.warn("count_chars(): Unknown mode")
        return space.w_False
    lst = [0] * 256
    for c in s:
        lst[ord(c)] += 1
    if mode == 0:
        lst_w = [space.wrap(elem) for elem in lst]
        return space.new_array_from_list(lst_w)
    if mode == 1:
        dct = OrderedDict()
        for i, elem in enumerate(lst):
            if elem:
                dct[str(i)] = space.wrap(elem)
        return space.new_array_from_rdict(dct)
    if mode == 2:
        dct = OrderedDict()
        for i, elem in enumerate(lst):
            if not elem:
                dct[str(i)] = space.wrap(elem)
        return space.new_array_from_rdict(dct)
    if mode == 3:
        res = []
        for i, elem in enumerate(lst):
            if elem:
                res.append(chr(i))
        return space.wrap("".join(res))
    if mode == 4:
        res = []
        for i, elem in enumerate(lst):
            if not elem:
                res.append(chr(i))
        return space.wrap("".join(res))
    assert False # unreachable code


# Table taken from PHP's ext/standard/crc32.h
_crc32tab = [
    0x00000000, 0x77073096, 0xee0e612c, 0x990951ba,
    0x076dc419, 0x706af48f, 0xe963a535, 0x9e6495a3,
    0x0edb8832, 0x79dcb8a4, 0xe0d5e91e, 0x97d2d988,
    0x09b64c2b, 0x7eb17cbd, 0xe7b82d07, 0x90bf1d91,
    0x1db71064, 0x6ab020f2, 0xf3b97148, 0x84be41de,
    0x1adad47d, 0x6ddde4eb, 0xf4d4b551, 0x83d385c7,
    0x136c9856, 0x646ba8c0, 0xfd62f97a, 0x8a65c9ec,
    0x14015c4f, 0x63066cd9, 0xfa0f3d63, 0x8d080df5,
    0x3b6e20c8, 0x4c69105e, 0xd56041e4, 0xa2677172,
    0x3c03e4d1, 0x4b04d447, 0xd20d85fd, 0xa50ab56b,
    0x35b5a8fa, 0x42b2986c, 0xdbbbc9d6, 0xacbcf940,
    0x32d86ce3, 0x45df5c75, 0xdcd60dcf, 0xabd13d59,
    0x26d930ac, 0x51de003a, 0xc8d75180, 0xbfd06116,
    0x21b4f4b5, 0x56b3c423, 0xcfba9599, 0xb8bda50f,
    0x2802b89e, 0x5f058808, 0xc60cd9b2, 0xb10be924,
    0x2f6f7c87, 0x58684c11, 0xc1611dab, 0xb6662d3d,
    0x76dc4190, 0x01db7106, 0x98d220bc, 0xefd5102a,
    0x71b18589, 0x06b6b51f, 0x9fbfe4a5, 0xe8b8d433,
    0x7807c9a2, 0x0f00f934, 0x9609a88e, 0xe10e9818,
    0x7f6a0dbb, 0x086d3d2d, 0x91646c97, 0xe6635c01,
    0x6b6b51f4, 0x1c6c6162, 0x856530d8, 0xf262004e,
    0x6c0695ed, 0x1b01a57b, 0x8208f4c1, 0xf50fc457,
    0x65b0d9c6, 0x12b7e950, 0x8bbeb8ea, 0xfcb9887c,
    0x62dd1ddf, 0x15da2d49, 0x8cd37cf3, 0xfbd44c65,
    0x4db26158, 0x3ab551ce, 0xa3bc0074, 0xd4bb30e2,
    0x4adfa541, 0x3dd895d7, 0xa4d1c46d, 0xd3d6f4fb,
    0x4369e96a, 0x346ed9fc, 0xad678846, 0xda60b8d0,
    0x44042d73, 0x33031de5, 0xaa0a4c5f, 0xdd0d7cc9,
    0x5005713c, 0x270241aa, 0xbe0b1010, 0xc90c2086,
    0x5768b525, 0x206f85b3, 0xb966d409, 0xce61e49f,
    0x5edef90e, 0x29d9c998, 0xb0d09822, 0xc7d7a8b4,
    0x59b33d17, 0x2eb40d81, 0xb7bd5c3b, 0xc0ba6cad,
    0xedb88320, 0x9abfb3b6, 0x03b6e20c, 0x74b1d29a,
    0xead54739, 0x9dd277af, 0x04db2615, 0x73dc1683,
    0xe3630b12, 0x94643b84, 0x0d6d6a3e, 0x7a6a5aa8,
    0xe40ecf0b, 0x9309ff9d, 0x0a00ae27, 0x7d079eb1,
    0xf00f9344, 0x8708a3d2, 0x1e01f268, 0x6906c2fe,
    0xf762575d, 0x806567cb, 0x196c3671, 0x6e6b06e7,
    0xfed41b76, 0x89d32be0, 0x10da7a5a, 0x67dd4acc,
    0xf9b9df6f, 0x8ebeeff9, 0x17b7be43, 0x60b08ed5,
    0xd6d6a3e8, 0xa1d1937e, 0x38d8c2c4, 0x4fdff252,
    0xd1bb67f1, 0xa6bc5767, 0x3fb506dd, 0x48b2364b,
    0xd80d2bda, 0xaf0a1b4c, 0x36034af6, 0x41047a60,
    0xdf60efc3, 0xa867df55, 0x316e8eef, 0x4669be79,
    0xcb61b38c, 0xbc66831a, 0x256fd2a0, 0x5268e236,
    0xcc0c7795, 0xbb0b4703, 0x220216b9, 0x5505262f,
    0xc5ba3bbe, 0xb2bd0b28, 0x2bb45a92, 0x5cb36a04,
    0xc2d7ffa7, 0xb5d0cf31, 0x2cd99e8b, 0x5bdeae1d,
    0x9b64c2b0, 0xec63f226, 0x756aa39c, 0x026d930a,
    0x9c0906a9, 0xeb0e363f, 0x72076785, 0x05005713,
    0x95bf4a82, 0xe2b87a14, 0x7bb12bae, 0x0cb61b38,
    0x92d28e9b, 0xe5d5be0d, 0x7cdcefb7, 0x0bdbdf21,
    0x86d3d2d4, 0xf1d4e242, 0x68ddb3f8, 0x1fda836e,
    0x81be16cd, 0xf6b9265b, 0x6fb077e1, 0x18b74777,
    0x88085ae6, 0xff0f6a70, 0x66063bca, 0x11010b5c,
    0x8f659eff, 0xf862ae69, 0x616bffd3, 0x166ccf45,
    0xa00ae278, 0xd70dd2ee, 0x4e048354, 0x3903b3c2,
    0xa7672661, 0xd06016f7, 0x4969474d, 0x3e6e77db,
    0xaed16a4a, 0xd9d65adc, 0x40df0b66, 0x37d83bf0,
    0xa9bcae53, 0xdebb9ec5, 0x47b2cf7f, 0x30b5ffe9,
    0xbdbdf21c, 0xcabac28a, 0x53b39330, 0x24b4a3a6,
    0xbad03605, 0xcdd70693, 0x54de5729, 0x23d967bf,
    0xb3667a2e, 0xc4614ab8, 0x5d681b02, 0x2a6f2b94,
    0xb40bbe37, 0xc30c8ea1, 0x5a05df1b, 0x2d02ef8d,
]


@wrap(['space', str])
def crc32(space, data):
    """Calculates the crc32 polynomial of a string."""
    # Implementation based on PHP's ext/standard/crc32.h
    crc = 0xFFFFFFFF
    for c in data:
        crc = ((crc >> 8) & 0x00FFFFFF) ^ _crc32tab[(crc ^ ord(c)) & 0xFF]
    crc ^= 0xFFFFFFFF

    # PHP returns a value that depends on the platform. On 32 bits systems the
    # value is in the range [-2**31, 2**31-1] but on 64 bits systems it is in
    # the range [0, 2**32-1].
    # See http://php.net//manual/en/function.crc32.php
    if sys.maxint < 2 ** 31 and crc >= 2 ** 31:  # 32 bits
        return space.newint(crc - 2 ** 32)
    else:
        return space.newint(crc)


#@wrap(['space', 'args_w'])
#def crypt(space, args_w):
#    """One-way string hashing."""
#    raise NotImplementedError()


@wrap(['space', str, str, Optional(int)])
def explode(space, delimiter, string, limit=sys.maxint):
    """Split a string by string."""
    if len(delimiter) == 0:
        space.ec.warn("explode(): Empty delimiter")
        return space.w_False
    if limit == sys.maxint:
        result = string.split(delimiter)
    elif limit > 0:
        result = string.split(delimiter, limit - 1)
    elif limit == 0:
        result = string.split(delimiter, 0)
    else:
        result = string.split(delimiter)
        end = max(limit + len(result), 0)
        result = result[:end]
    return space.new_array_from_list([space.newstr(item) for item in result])


# @wrap(['space', FileResourceArg(False), str, 'args_w'])
@wrap(['space', 'args_w'], error=False)
def fprintf(space, args_w):
    """Write a formatted string to a stream."""
    if len(args_w) < 2:
        space.ec.warn("Wrong parameter count for fprintf()")
        return space.w_Null
    w_res = args_w[0]
    format = space.str_w(args_w[1])
    w_args = args_w[2:]
    if w_res.tp != space.tp_file_res:
        space.ec.warn("fprintf() expects parameter 1 "
                      "to be resource, %s given"
                      % space.get_type_name(w_res.tp).lower())
        return space.w_False
    assert isinstance(w_res, W_FileResource)

    if not w_res.is_valid():
        space.ec.warn("fprintf(): %d is not a valid "
                      "stream resource" % w_res.res_id)
        return space.w_False
    assert isinstance(w_res, W_FileResource)
    s = _printf(space, format, w_args, "fprintf")
    w_res.writeall(s)
    return space.newint(len(s))


#@wrap(['space', 'args_w'])
#def get_html_translation_table(space, args_w):
#    """Returns the translation table used by htmlspecialchars and htmlentities."""
#    raise NotImplementedError()

#
#@wrap(['space', 'args_w'])
#def hebrev(space, args_w):
#    """Convert logical Hebrew text to visual text."""
#    raise NotImplementedError()

#
#@wrap(['space', 'args_w'])
#def hebrevc(space, args_w):
#    """Convert logical Hebrew text to visual text with newline conversion."""
#    raise NotImplementedError()


@wrap(['space', str])
def hex2bin(space, data):
    """Decodes a hexadecimally encoded binary string."""
    if len(data) % 2 != 0:
        space.ec.warn("hex2bin(): Hexadecimal input string must have an even length")
        return space.w_False

    builder = StringBuilder(len(data) / 2)
    for i in xrange(0, len(data), 2):
        if not is_hexdigit(data[i]) or not is_hexdigit(data[i + 1]):
            return space.w_False
        char = chr(hexdigit(data[i]) << 4 | hexdigit(data[i + 1]))
        builder.append(char)

    return space.newstr(builder.build())


@wrap(['space',   str,   Optional(int),   Optional(str)])
def html_entity_decode(space,   html,   flags=2,   encoding='UTF-8'):
    """Convert all HTML entities to their applicable characters."""
    single = flags & 1 != 0
    double = flags & 2 != 0
    xml = flags & 16 != 0
    xhtml = flags & 32 != 0
    html5 = flags & 48 != 0
    acc = None
    orig_acc = None
    got_entity = False
    res = ""
    for c in html:
        if acc is None and c == "&":
            got_entity = True
            acc = ""
            orig_acc = ""
        if got_entity:
            if acc == "&#" and c == "0":
                orig_acc += c
                continue
            acc += c
            orig_acc += c
        if got_entity and (c == ";" or c == " "):
            got_entity = False
            if acc == "&lt;" or acc == "&#60;" or \
               acc == "&#x3C;":
                res += "<"
            elif acc == "&gt;" or acc == "&#62;" or \
                 acc == "&#x3E;":
                res += ">"
            elif acc == "&amp;" or acc == "&#38;" or \
                 acc == "&#x26;":
                res += "&"
            elif single and (acc == "&apos;" or
                             acc == "&#39;" or
                             acc == "&#x27;"):
                if acc == "&apos;":
                    if xml or xhtml or html5:
                        res += "\'"
                    else:
                        res += acc
                else:
                        res += "\'"

            elif double and (acc == "&quot;" or
                             acc == "&#34;" or
                             acc == "&#x22;"):
                res += "\""
            else:
                res += orig_acc
            acc = None
            continue
        if not got_entity:
            res += c
    return space.wrap(res)

#@wrap(['space', 'args_w'])
#def html_entity_decode(space, args_w):
#    """Convert all HTML entities to their applicable characters."""
#    raise NotImplementedError()

#
#@wrap(['space', 'args_w'])
#def htmlentities(space, args_w):
#    """Convert all applicable characters to HTML entities."""
#    raise NotImplementedError()


@wrap(['interp',  str,  Optional(int),  Optional(str),  Optional(bool)])
def htmlentities(interp,  html,  flags=1, encoding='UTF8',
                 double_encode=True):
    """Convert all applicable characters to HTML entities."""

    from rpython.rlib.runicode import str_decode_utf_8
    from hippy.module.standard.strings.htmlentities import UTF8
    outstr = StringBuilder()
    s,  l = str_decode_utf_8(html,  len(html),  'ignore')
    for c in s:
        try:
            outstr.append(UTF8[ord(c)])
        except KeyError:
            outstr.append(str(c))
    return interp.space.newstr(outstr.build())


def _htmlspecialchars_decode(space, html, flags):

    single = flags & 1 != 0
    double = flags & 2 != 0

    acc = None
    got_entity = False
    res = ""

    subs = {
        "&lt;": "<",
        "&gt;": ">",
        "&amp;": "&",
    }

    if single:
        subs["&#039;"] = "\'"
    if double:
        subs["&quot;"] = "\""

    for c in html:
        if acc is None and c == "&":
            got_entity = True
            acc = ""
        if got_entity:
            acc += c
        if got_entity and c == ";":
            got_entity = False
            res += subs.get(acc, acc)
            acc = None
            continue
        if not got_entity:
            res += c
    return space.wrap(res)


@wrap(['space', StringArg(), Optional(int)])
def htmlspecialchars_decode(space, html, flags=2):
    """Convert special HTML entities back to characters.
       'ENT_COMPAT': 2,
       'ENT_QUOTES': 3,
       'ENT_NOQUOTES': 0,
       'ENT_HTML401': 0,
       'ENT_XML1': 16,
       'ENT_XHTML': 32,
       'ENT_HTML5': 48,
    """

    single = flags & 1 != 0
    double = flags & 2 != 0
    xml = flags & 16 != 0
    xhtml = flags & 32 != 0
    html5 = flags & 48 != 0

    acc = None
    orig_acc = None
    got_entity = False
    res = ""

    for c in html:
        if acc is None and c == "&":
            got_entity = True
            acc = ""
            orig_acc = ""
        if got_entity:
            if acc == "&#" and c == "0":
                orig_acc += c
                continue
            acc += c
            orig_acc += c
        if got_entity and (c == ";" or c == " "):
            got_entity = False
            if acc == "&lt;" or acc == "&#60;" or \
               acc == "&#x3C;":
                res += "<"
            elif acc == "&gt;" or acc == "&#62;" or \
                 acc == "&#x3E;":
                res += ">"
            elif acc == "&amp;" or acc == "&#38;" or \
                 acc == "&#x26;":
                res += "&"
            elif single and (acc == "&apos;" or
                             acc == "&#39;" or
                             acc == "&#x27;"):
                if acc == "&apos;":
                    if xml or xhtml or html5:
                        res += "\'"
                    else:
                        res += acc
                else:
                        res += "\'"

            elif double and (acc == "&quot;" or
                             acc == "&#34;" or
                             acc == "&#x22;"):
                res += "\""
            else:
                res += orig_acc
            acc = None
            continue
        if not got_entity:
            res += c
    return space.wrap(res)


def _new_chars_to_replace(double_encode, single, double):
    chars_to_replace = [chr(i) for i in range(256)]
    chars_to_replace[ord('<')] = '&lt;'
    chars_to_replace[ord('>')] = '&gt;'
    if double_encode:
        chars_to_replace[ord('&')] = '&amp;'
    if single:
        chars_to_replace[ord("'")] = "&#039;"
    if double:
        chars_to_replace[ord('"')] = "&quot;"
    return chars_to_replace

CHAR_REPLACE_TABLE = [None] * 16

for double_encode in (True, False):
    for single in (True, False):
        for double in (True, False):
            CHAR_REPLACE_TABLE[double_encode * 4 + single * 2 + double] = \
              _new_chars_to_replace(double_encode, single, double)


@wrap(['space', StringArg(), Optional(int), Optional(StringArg()),
       Optional(BoolArg())])
def htmlspecialchars(space, html, flags=2, encoding='UTF-8',
                     double_encode=True):
    """Convert special characters to HTML entities.
    """
    single = flags & 1 != 0
    double = flags & 2 != 0
    table = CHAR_REPLACE_TABLE[double_encode * 4 + single * 2 + double]
    lgt = 0
    for c in html:
        lgt += len(table[ord(c)])
    s = StringBuilder(lgt)
    for c in html:
        s.append(table[ord(c)])
    return space.wrap(s.build())


def _implode(space, string, w_arr):
    iter = space.create_iter(w_arr)
    values = []
    while not iter.done():
        _, w_val = iter.next_item(space)
        values.append(space.str_w(w_val))
    return space.newstr(string.join(values))


@wrap(['space', W_Root, Optional(W_Root)], aliases=['join'])
def implode(space, w_arg1, w_arg2=None):
    """Join array elements with a string."""
    if w_arg2 is None:
        if w_arg1.tp != space.tp_array:
            space.ec.warn("implode(): Argument must be an array")
            return space.w_Null
        else:
            w_arr = w_arg1
            string = ""
    else:
        if w_arg1.tp == space.tp_array:
            w_arr = w_arg1
            string = space.str_w(w_arg2)
        elif w_arg2.tp == space.tp_array:
            w_arr = w_arg2
            string = space.str_w(w_arg1)
        else:
            space.ec.warn("implode(): Invalid arguments passed")
            return space.w_Null
    return _implode(space, string, w_arr)


@wrap(['space', str])
def lcfirst(space, string):
    """Make a string's first character lowercase."""
    n = len(string)
    if n == 0:
        return space.newstr('')
    builder = StringBuilder(n)
    builder.append(locale.lower_char(string[0]))
    builder.append_slice(string, 1, n)
    s = builder.build()
    return space.newstr(s)


@wrap(['space', 'num_args', Optional(str), Optional(str), Optional(W_Root), Optional(int), Optional(int)], check_num_args=False)
def levenshtein(space, num_args, str1='', str2='', w_cost_ins=None, cost_rep=1, cost_del=1):
    """Calculate Levenshtein distance between two strings."""
    # Code based on ext/standard/levenshtein.c
    # check_num_args is set to False because levenshtein always shows a custom
    # warning message when the number of arguments is incorrect.
    if num_args == 3:
        space.ec.warn('levenshtein(): The general Levenshtein support is not there yet')
        return space.newint(-1)
    elif num_args not in (2, 5):
        space.ec.warn('Wrong parameter count for levenshtein()')
        return space.w_Null

    cost_ins = 1
    # levenshtein first shows the warning for the general function first and
    # then checks if the argument is valid. So we have to do parse it manually
    # here.
    if num_args == 5:
        try:
            cost_ins = w_cost_ins.as_int_arg(space)
        except ConvertError:
            space.ec.warn('levenshtein() expects parameter 3 to be long, %s given' % w_cost_ins.tp)
            return space.w_Null

    if len(str1) > 255 or len(str2) > 255:
        space.ec.warn('levenshtein(): Argument string(s) too long')
        return space.newint(-1)

    if not str1:
        return space.newint(len(str2) * cost_ins)
    if not str2:
        return space.newint(len(str1) * cost_del)
    if str1 == str2:
        return space.newint(0)

    p1 = range(0, (len(str2) + 1) * cost_ins, cost_ins)
    p2 = [0] * (len(str2) + 1)

    for i in xrange(len(str1)):
        p2[0] = p1[0] + cost_del
        for j in xrange(len(str2)):
            c0 = p1[j]
            if str1[i] != str2[j]:
                c0 += cost_rep
            c1 = p1[j + 1] + cost_del
            c2 = p2[j] + cost_ins
            # Rpython only allow two arguments to min
            p2[j + 1] = min(c0, min(c1, c2))
        p1, p2 = p2, p1

    return space.newint(p1[-1])


#@wrap(['space', 'args_w'])
#def md5_file(space, args_w):
#    """Calculates the md5 hash of a given file."""
#    raise NotImplementedError()


@wrap(['space', str, Optional(bool)])
def md5(space, input, raw_output=False):
    """Calculate the md5 hash of a string."""
    d = rmd5.RMD5(input)
    if raw_output:
        return space.newstr(d.digest())
    else:
        return space.newstr(d.hexdigest())

#
#@wrap(['space', 'args_w'])
#def metaphone(space, args_w):
#    """Calculate the metaphone key of a string."""
#    raise NotImplementedError()

#

@wrap(['space', str, Optional(bool)])
def nl2br(space, arg, is_xhtml=True):
    """Inserts HTML line breaks before all newlines in a string."""
    i = 0
    s = StringBuilder(len(arg))
    if is_xhtml:
        marker = '<br />'
    else:
        marker = '<br>'
    while i < len(arg):
        c = arg[i]
        if c == '\n':
            s.append(marker)
            s.append("\n")
            if i < len(arg) - 1 and arg[i + 1] == '\r':
                s.append("\r")
                i += 1
            i += 1
            continue
        elif c == '\r':
            s.append(marker)
            s.append("\r")
            if i < len(arg) - 1 and arg[i + 1] == '\n':
                s.append("\n")
                i += 1
            i += 1
            continue
        i += 1
        s.append(c)
    return space.wrap(s.build())


@wrap(['interp', 'num_args', float, Optional(int), Optional(str),
       Optional(str)])
def number_format(interp, num_args, number, decimals=0, dec_point='.',
                  thousands_sep=','):
    """Format a number with grouped thousands."""
    if num_args == 3:
        return interp.space.w_False
    ino = int(number)
    dec = abs(number - ino)
    rest = ""
    if decimals == 0 and dec >= 0.5:
        if number > 0:
            ino += 1
        else:
            ino -= 1
    elif decimals > 0:
        s_dec = str(dec)
        if decimals + 2 < len(s_dec):
            if ord(s_dec[decimals + 2]) >= ord('5'):
                dec += math.pow(10, -decimals)
                if dec >= 1:
                    if number > 0:
                        ino += 1
                    else:
                        ino -= 1
                    rest = "0" * decimals
                else:
                    s_dec = str(dec)
            if not rest:
                rest = s_dec[2:decimals + 2]
        else:
            rest = s_dec[2:] + "0" * (decimals - len(s_dec) + 2)
    s = str(ino)
    res = []
    i = 0
    while i < len(s):
        res.append(s[i])
        if s[i] != '-' and i != len(s) - 1 and (len(s) - i - 1) % 3 == 0:
            for item in thousands_sep:
                res.append(item)
        i += 1
    if decimals > 0:
        for item in dec_point:
            res.append(item)
    return interp.space.wrap("".join(res) + rest)

@wrap(['space', str], name='ord')
def ord_(space, string):
    """Return ASCII value of character."""
    # Special case: ord("") -> 0
    if len(string) == 0:
        return space.newint(0)
    return space.newint(ord(string[0]))


@wrap(['space',   str,   Optional('reference')])
def parse_str(space,   to_parse,   w_arr=None):
    """Parses the string into variables."""
    frame = space.ec.interpreter.topframeref()
    arrs = {}
    vars = to_parse.split("&")
    if len(vars) == 0:
        return
    for var in vars:
        val = None
        if var == '':
            return
        try:
            var,   val = var.split("=",   1)
        except ValueError:
            pass
        val = _urldecode(val)
        if var.endswith('[]'):
            var = var.rstrip('[]')
            if var in arrs:
                arrs[var].append(space.wrap(val))
            else:
                arrs[var] = [space.wrap(val)]
        else:
            frame.get_ref_by_name(var).store(space.wrap(val))
    for var,   val in arrs.items():
        frame.get_ref_by_name(var).store(space.new_array_from_list(val))


def format_str(_str, width=0, to_left=False,
               pad_char=' ', cutoff=0, prefix=''):
    prefix = ''
    just = ''
    if pad_char == '0' and len(_str) > 0:
        if _str[0] == '-':
            prefix = '-'
            _str = _str[1:]
    if cutoff:
        assert cutoff >= 0
        _str = _str[:cutoff]

    l = width - len(_str) - len(prefix)
    if width:
        just = pad_char * l
        if to_left:
            return prefix + _str + just
        else:
            return prefix + just + _str
    return prefix + _str


def _printf(space, format, args_w, caller):
    no = 0
    bits = 31 if sys.maxint == 2 ** 31 - 1 else 63
    MASK = (2 << bits) - 1
    # improve the estimate
    builder = StringBuilder(len(format) + 5 * format.count('%'))
    i = 0
    while i < len(format):
        c = format[i]
        i += 1
        res = ''
        tmp = ''
        if c == '%':
            plus_sign = False
            modifier = None
            addjust_width = 0
            precision = 0
            prec_adjust = False
            to_left = False
            pad_char = ' '
            w_arg = space.w_Null
            e = 0

            try:
                next = format[i]
                warn_if_unknown = True
                i += 1
            except IndexError:
                next = '\x00'
                warn_if_unknown = False
                continue
                # msg = "%s(): Trailing '%%' character" % caller
                # if no < len(args_w):
                #     msg += ", the next argument is going to be ignored"
                # space.ec.hippy_warn(msg)

            if next != '%':
                if no == len(args_w):
                    raise ValidationError("Too few arguments")
                w_arg = args_w[no]
                no += 1

            while next == ' ':
                next = format[i]
                i += 1

            if next == '%':
                res = '%'

            if next.isdigit() and format[i] == '$':
                try:
                    w_arg = args_w[int(next) - 1]
                except IndexError:
                    raise ValidationError("Too few arguments")

                i += 1
                next = format[i]
                i += 1
                no -= 1

            if next in ['L', 'I', 'l', 'z', 'j', 't']:
                modifier = next
                next = format[i]
                if next in ['l', 'h']:
                    modifier += next
                    i += 1
                i += 1

            if modifier == 'L':
                builder.append(next)
                continue

            # if next in ['h']:
            #     next = format[i]
            #     i += 1

            if next == '-':
                to_left = True
                next = format[i]
                i += 1
            if next == '+':
                plus_sign = True
                next = format[i]
                i += 1
            # if next == '#':
            #     # XXXX missing tests
            #     next = format[i]
            #     i += 1
            if next == '0':
                pad_char = '0'
                next = format[i]
                i += 1

            if next == '\'':
                next = format[i]
                i += 1
                pad_char = next
                next = format[i]
                i += 1

            if next.isdigit():
                p = ""
                while next.isdigit():
                    p += next
                    next = format[i]
                    i += 1
                addjust_width = int(p)
            # elif next == '*':
            #     # XXXX missing tests
            #     pass
            if next == '.':
                next = format[i]
                i += 1
                p = ""
                while next.isdigit():
                    p += next
                    next = format[i]
                    i += 1
                try:
                    precision = int(p)
                    prec_adjust = True
                except ValueError:
                    pass

            if plus_sign and space.float_w(w_arg) >= 0:
                res = '+'
            # binary
            if next == 'b':
                int_val = space.force_int(w_arg)
                if int_val > 0:
                    tmp = int_val
                else:
                    tmp = int_val & MASK
                res = _bin(r_uint(int_val))

            # char
            if next == 'c':
                int_val = space.int_w(w_arg)

                try:
                    builder.append(chr(int_val % 256))
                    continue
                except ValueError:
                    pass
            # decimal
            if next == 'd':
                int_val = space.int_w(w_arg)

                if to_left and pad_char == '0':
                    addjust_width = 0
                res += str(int_val)
            # exponant
            if next == 'e' or next == 'E':
                if not prec_adjust:
                    precision = 6
                f = space.float_w(w_arg)
                _str, _ = double_to_string(f, next, precision,
                                               DTSF_CUT_EXP_0)
                res += _str
            # unsigned
            if next == 'u':
                res = ''
                try:
                    int_val = intmask(int(space.float_w(w_arg)))
                    if abs(int_val - space.float_w(w_arg)) > 1.0:
                        int_val = 0
                except OverflowError:
                    int_val = 0
                ui = r_uint(int_val)
                res += str(ui)

            # float
            if next == 'f' or next == 'F':
                f = space.float_w(w_arg)
                if not prec_adjust:
                    precision = 6
                _str, _ = double_to_string(f, next, precision,
                                           DTSF_CUT_EXP_0)
                res += _str
            # science
            if next == 'g' or next == 'G':
                if not prec_adjust:
                    precision = 6
                else:
                    if precision == 0:
                        precision = 1
                f = space.float_w(w_arg)
                _str, _ = double_to_string(f, next, precision,
                                           DTSF_CUT_EXP_0)
                if next == 'g':
                    if 'e' in _str and '.' not in _str:
                        a, b = _str.split('e')
                        _str = a + '.0e' + b
                else:
                    if 'E' in _str and '.' not in _str:
                        a, b = _str.split('E')
                        _str = a + '.0E' + b
                res += _str
            # oct
            if next == 'o':
                int_val = space.int_w(w_arg)
                _o = oct(int_val & MASK)
                if int_val == 0:
                    tmp = "0"
                else:
                    e = len(_o) - 1
                    assert e >= 0
                    tmp = _o[1:e]
                if prec_adjust:
                    tmp = ""
                res = tmp
            # string
            if next == 's':
                res = space.str_w(w_arg, quiet=True)
            # hex
            if next == 'x' or next == 'X':
                int_val = space.int_w(w_arg)
                if w_arg.tp == space.tp_str:
                    int_val, _ = strtol(space.str_w(w_arg))

                _h = hex(int_val & MASK)
                e = len(_h) - 1
                assert e >= 0

                tmp = _h[2:e]
                if next == 'X':
                    tmp = tmp.upper()
                if prec_adjust:
                    tmp = ""
                res = tmp

            if res is not None and next != ' ':
                cutoff = 0
                if next == 's':
                    cutoff = precision
                res = format_str(res,
                                 width=addjust_width,
                                 to_left=to_left,
                                 pad_char=pad_char,
                                 cutoff=cutoff)
                builder.append(res)
                continue
            elif warn_if_unknown:
                space.ec.hippy_warn("%s(): Unknown format char %%%s, "
                        "ignoring corresponding argument" % (caller, next))
        else:
            builder.append(c)
    # if no < len(args_w):
    #     space.ec.hippy_warn("%s(): Too many arguments passed, "
    #             "ignoring the %d extra" % (caller, len(args_w) - no,))
    s = builder.build()
    return s


@wrap(['space', W_Root, 'args_w'], error=False)
def printf(space, w_obj, args_w):
    """Output a formatted string."""
    format = space.str_w(w_obj)
    s = _printf(space, format, args_w, "printf")
    space.ec.interpreter.echo(space, space.newstr(s))
    return space.newint(len(s))


@wrap(['space', W_Root, 'args_w'], error=False)
def sprintf(space, w_obj, args_w):
    """Return a formatted string."""
    format = space.str_w(w_obj)
    s = _printf(space, format, args_w, "printf")
    return space.newstr(s)


# XXX: move elsewhere
def _as_list(w_arr):
    space = getspace()
    iter = space.create_iter(w_arr)
    values = []
    while not iter.done():
        _, w_val = iter.next_item(getspace())
        w_val = w_val.deref()
        if w_val.tp != space.tp_null:
            values.append(w_val)
    return values


def unpack_array(w_arr):
    if w_arr.tp != ObjSpace.tp_array:
        if w_arr.tp not in [ObjSpace.tp_null, ObjSpace.tp_object]:
            return [w_arr]
        return []
    else:
        return _as_list(w_arr)


@wrap(['space', W_Root, W_Root])
def vprintf(space, w_obj, w_args):
    """Output a formatted string."""
    format = space.str_w(w_obj)
    args_w = unpack_array(w_args)
    try:
        s = _printf(space, format, args_w, "printf")
    except ValidationError as e:
        space.ec.warn("vprintf(): " + e.msg)
        return space.w_False
    space.ec.interpreter.echo(space, space.newstr(s))
    return space.newint(len(s))


@wrap(['space', W_Root, W_Root])
def vsprintf(space, w_obj, w_args):
    """Return a formatted string."""
    format = space.str_w(w_obj)
    args_w = unpack_array(w_args)
    try:
        s = _printf(space, format, args_w, "printf")
        return space.newstr(s)
    except ValidationError as e:
        space.ec.warn("vsprintf(): " + e.msg)
        return space.w_False


@wrap(['space', str])
def quoted_printable_decode(space, data):
    """Convert a quoted-printable string to an 8 bit string."""
    builder = StringBuilder(len(data))
    i = 0
    while i < len(data):
        c = data[i]
        if c == '=':
            next_two_chars = data[i + 1: i + 3]
            if (i + 2 < len(data) and
                    is_hexdigit(data[i + 1]) and is_hexdigit(data[i + 2])):
                hex_char = hexdigit(data[i + 1]) << 4 | hexdigit(data[i + 2])
                builder.append(chr(hex_char))
                i += 3
            else:
                k = 1
                # Skip spaces and tabs
                while i + k < len(data) and data[i + k] in ' \t':
                    k += 1
                if data[i + k: i + k + 2] == '\r\n':
                    i += k + 2
                elif data[i + k] in '\n\r':
                    i += k + 1
                else:
                    builder.append(c)
                    i += 1
        else:
            builder.append(c)
            i += 1

    return space.newstr(builder.build())


def _add_data(builder, line_length, data, extra_length=0):
    max_length = 75
    length = len(data)
    if line_length + length + extra_length > max_length:
        builder.append('=\r\n')
        builder.append(data)
        return length
    else:
        builder.append(data)
        return line_length + length


def _to_hex(value):
    # TODO: refactor this as it could be used in bin2hex. Although there they
    # require lowercase digits.
    encode = '0123456789ABCDEF'
    hi, low = value // 16, value % 16
    return encode[hi] + encode[low]


@wrap(['space', str])
def quoted_printable_encode(space, data):
    """Convert a 8 bit string to a quoted-printable string."""
    builder = StringBuilder(int(3 * len(data) * (1 + 3.0 / 75)))
    pending_cr = False
    pending_space = False
    line_length = 0
    for c in data:
        value = ord(c)
        if pending_cr:
            if c == '\n':
                builder.append('\r\n')
                line_length = 0
                pending_cr = False
                continue
            else:
                line_length = _add_data(builder, line_length, '=0D')
        if pending_space:
            if c == '\r':
                line_length = _add_data(builder, line_length, '=20')
            else:
                line_length = _add_data(builder, line_length, ' ')
        pending_cr = False
        pending_space = False
        if value == 61:
            line_length = _add_data(builder, line_length, '=3D')
        elif 33 <= value <= 126:
            line_length = _add_data(builder, line_length, c)
        elif c == '\r':
            pending_cr = True
        elif c == ' ':
            pending_space = True
        else:
            # This hack is specific to PHP, so that the output is the same.
            extra_length = 0
            if value > 0x7f:
                extra_length += 3
            if value > 0xdf:
                extra_length += 3
            if value > 0xef:
                extra_length += 3
            line_length = _add_data(builder, line_length, '=' + _to_hex(value),
                                    extra_length=extra_length)

    if pending_cr:
        line_length = _add_data(builder, line_length, '=0D')
    if pending_space:
        line_length = _add_data(builder, line_length, ' ')

    return space.newstr(builder.build())


@wrap(['space', str])
def quotemeta(space, string):
    """Quote meta characters."""
    if len(string) == 0:
        return space.w_False
    print string
    builder = StringBuilder(2 * len(string))
    for c in string:
        if c in r".\+*?[^]($)":
            builder.append('\\')
        builder.append(c)
    s = builder.build()
    return space.newstr(s)

#
#@wrap(['space', 'args_w'])
#def sha1_file(space, args_w):
#    """Calculate the sha1 hash of a file."""
#    raise NotImplementedError()

#

@wrap(['space', str, Optional(bool)])
def sha1(space, s, raw_output=False):
    """Calculate the sha1 hash of a string."""
    o = sha(s)
    if raw_output:
        return space.wrap(o.digest())
    return space.wrap(o.hexdigest())

#
#@wrap(['space', 'args_w'])
#def similar_text(space, args_w):
#    """Calculate the similarity between two strings."""
#    raise NotImplementedError()


@wrap(['space', str])
def soundex(space, data):
    """Calculate the soundex key of a string."""
    #                ABCDEFGHIJKLMNOPQRSTUVWXYZ
    soundex_table = '01230120022455012623010202'

    if not data:
        return space.w_False

    # build soundex string
    soundex_data = ['0'] * 4

    data = data.upper()
    last_code = None
    i = 0
    for letter in data:
        # Strip non-letter chars
        # BUG: should also map here accented letters used in non
        # English words or names (also found in English text!):
        # esstsett, thorn, n-tilde, c-cedilla, s-caron, ...
        if 'A' <= letter <= 'Z':
            code = soundex_table[ord(letter) - ord('A')]
            if i == 0:
                # remember first valid char
                soundex_data[i] = letter
                i += 1
                last_code = code
            elif code != last_code:
                # ignore sequences of consonants with same soundex
                # code in trail, and vowels unless they separate
                # consonant letters
                if code != '0':
                    soundex_data[i] = code
                    i += 1
                    if i == 4:
                        break
                last_code = code

    return space.newstr(''.join(soundex_data))


#@wrap(['space', 'args_w'])
#def sscanf(space, args_w):
#    """Parses input from a string according to a format."""
#    raise NotImplementedError()

#
#@wrap(['space', 'args_w'])
#def str_getcsv(space, args_w):
#    """Parse a CSV string into an array."""
#    raise NotImplementedError()


STR_PAD_RIGHT = CONSTS['standard']['STR_PAD_RIGHT']
STR_PAD_LEFT = CONSTS['standard']['STR_PAD_LEFT']
STR_PAD_BOTH = CONSTS['standard']['STR_PAD_BOTH']


@wrap(['space', str, int, Optional(str), Optional(int)])
def str_pad(space, input, pad_length, pad_string=" ", pad_type=STR_PAD_RIGHT):
    """Pad a string to a certain length with another string."""
    if pad_length <= len(input):
        return space.newstr(input)
    if len(pad_string) == 0:
        space.ec.warn("str_pad(): Padding string cannot be empty")
        return space.w_Null

    padding = pad_length - len(input)
    assert padding > 0
    if pad_type == STR_PAD_RIGHT:
        pad_left = 0
        pad_right = padding
    elif pad_type == STR_PAD_LEFT:
        pad_left = padding
        pad_right = 0
    elif pad_type == STR_PAD_BOTH:
        pad_left = padding // 2
        pad_right = padding - pad_left
    else:
        space.ec.warn("str_pad(): "
                "Padding type has to be STR_PAD_LEFT, STR_PAD_RIGHT, or "
                "STR_PAD_BOTH")
        return space.w_Null

    builder = StringBuilder(pad_length)
    for i in range(pad_left):
        builder.append(pad_string[i % len(pad_string)])
    builder.append(input)
    for i in range(pad_right):
        builder.append(pad_string[i % len(pad_string)])
    s = builder.build()
    return space.newstr(s)


@wrap(['space', str, int])
def str_repeat(space, s, repeat):
    """Repeat a string."""
    if repeat < 0:
        space.ec.warn('str_repeat(): Second argument has to be greater than or equal to 0')
        return space.w_Null
    return space.newstr(s * repeat)


# XXX: specialize
def _do_replace(search, replace, subject, case_insensitive):
    if len(search) == 0:
        return subject, 0
    if case_insensitive:
        search = locale.lower(search)
        normalize = locale.lower_char
    else:
        normalize = lambda s: s
    s = StringBuilder(len(subject))
    i = 0
    j = 0
    count = 0
    while i < len(subject):
        i0 = i
        j = 0
        while j < len(search):
            if i >= len(subject):
                s.append(subject[i0:])
                break
            if normalize(subject[i]) == search[j]:
                i += 1
                j += 1
                continue
            else:
                s.append(subject[i0])
                i = i0 + 1
                break
        else:
            s.append(replace)
            count += 1
            j = 0
    return s.build(), count


def _str_xreplace_item(space, w_search, w_replace, subject, w_count,
        case_insensitive):
    if w_search.tp == space.tp_array:
        count = 0
        s = subject
        search_iter = space.create_iter(w_search)
        n_search = space.arraylen(w_search)
        repls = _broadcast_as_list(w_replace, n_search, "", space.str_w)
        for i in range(n_search):
            _, w_val = search_iter.next_item(space)
            search = space.str_w(w_val)
            s, _count = _do_replace(search, repls[i], s, case_insensitive)
            count += _count
        return s, count
    else:
        search = space.str_w(w_search)
        replace = space.str_w(w_replace)
        return _do_replace(search, replace, subject, case_insensitive)


def _str_xreplace(space, w_search, w_replace, w_subject, w_count,
        case_insensitive):
    if w_subject.tp == space.tp_array:
        subject_iter = space.create_iter(w_subject)
        n = space.arraylen(w_subject)
        result = []
        count = 0
        for i in range(n):
            key, w_val = subject_iter.next_item(space)
            if space.is_array(w_val) or space.is_object(w_val):
                result.append((key, w_val))
                continue
            subject = space.str_w(w_val)
            s, _count = _str_xreplace_item(space, w_search, w_replace,
                    subject, w_count, case_insensitive)
            count += _count
            result.append((key, space.newstr(s)))
        if w_count is not None:
            w_count.store(space.newint(count))
        return space.new_array_from_pairs(result)
    else:
        subject = space.str_w(w_subject)
        s, count = _str_xreplace_item(space, w_search, w_replace, subject,
                w_count, case_insensitive)
        if w_count is not None:
            w_count.store(space.newint(count))
        return space.newstr(s)


@wrap(['space', W_Root, W_Root, W_Root, Optional('reference')])
def str_ireplace(space, w_search, w_replace, w_subject, w_count=None):
    """Case-insensitive version of str_replace.."""
    return _str_xreplace(space, w_search, w_replace, w_subject, w_count, True)


@wrap(['space', W_Root, W_Root, W_Root, Optional('reference')])
def str_replace(space, w_search, w_replace, w_subject, w_count=None):
    """Replace all occurrences of the search string
    with the replacement string."""
    return _str_xreplace(space, w_search, w_replace, w_subject, w_count, False)


_ROT13_FROM = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
_ROT13_TO = 'NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm'
_ROT13_CHARMAP = _make_charmap(_ROT13_FROM, _ROT13_TO)


def _str_rot13(string):
    return _apply_charmap(string, _ROT13_CHARMAP, len(string))


@wrap(['space', str])
def str_rot13(space, string):
    """Perform the rot13 transform on a string."""
    return space.newstr(_str_rot13(string))


@wrap(['space', str])
def str_shuffle(space, data):
    """Randomly shuffles a string."""
    chars = newlist_hint(len(data))
    for c in data:
        chars.append(c)
    # TODO: refactor this logic as it is copied from array/funcs.py:shuffle.
    for i in xrange(len(chars) - 1, 0, -1):
        j = int(_random.random() * (i + 1))
        chars[i], chars[j] = chars[j], chars[i]
    return space.newstr(''.join(chars))


@wrap(['interp', str, Optional(int)])
def str_split(interp, s, split_length=1):
    space = interp.space
    if not s:
        return space.new_array_from_list([space.wrap("")])
    if split_length < 1:
        interp.warn("str_split(): The length of each segment must "
                    "be greater than zero")
        return space.w_False
    l_w = []
    for i in range(len(s) // split_length + 1):
        part = s[i * split_length:(i + 1) * split_length]
        if part:
                l_w.append(space.wrap(part))
    return space.new_array_from_list(l_w)

#
#@wrap(['space', 'args_w'])
#def str_word_count(space, args_w):
#    """Return information about words used in a string."""
#    raise NotImplementedError()


@wrap(['space', str, str])
def strcasecmp(space, str1, str2):
    """
    Binary safe case-insensitive string comparison.

    See note for `strcmp()`.
    """
    return space.newint(rstrcmp(str1, str2, case_insensitive=True))


@wrap(['space', str, str])
def strcmp(space, str1, str2):
    """Binary safe string comparison.

    Note that in Zend PHP, strcmp("a", "aaa") === -2. But the PHP Manual only
    mentions positive and negative values, so hippy's implementation always
    returns a value in {-1, 0, 1}.
    """
    return space.newint(rstrcmp(str1, str2))


@wrap(['space',   str,   Optional(str)])
def strip_tags(space,   tostrip,   allow=""):
    """Strip HTML and PHP tags from a string."""
    tag = False
    res = StringBuilder()
    for c in tostrip:
        if c == '<':
            tag = True
            continue
        if c == '>':
            tag = False
            continue
        if not tag:
            res.append(c)
    return space.newstr(res.build())


@wrap(['space', str, W_Root, Optional(int)])
def stripos(space, haystack, w_needle, offset=0):
    """
    Find the position of the first occurrence of a case-insensitive
    substring in a string.
    """
    if offset < 0 or offset > len(haystack):
        space.ec.warn("stripos(): Offset not contained in string")
        return space.w_False

    try:
        needle = unwrap_needle(space, w_needle)
    except ValidationError as exc:
        space.ec.warn("stripos(): " + exc.msg)
        return space.w_False
    if len(needle) == 0:
        return space.w_False

    result = locale.lower(haystack).find(locale.lower(needle), offset)
    if result == -1:
        return space.w_False
    return space.newint(result)


@wrap(['space', str, W_Root, Optional(bool)])
def stristr(space, haystack, w_needle, before_needle=False):
    """Case-insensitive strstr."""
    try:
        needle = unwrap_needle(space, w_needle)
    except ValidationError as exc:
        space.ec.warn("stristr(): " + exc.msg)
        return space.w_False
    if len(needle) == 0:
        space.ec.warn("stristr(): Empty needle")
        return space.w_False
    needle = locale.lower(needle)
    hay_lower = locale.lower(haystack)
    pos = hay_lower.find(needle)
    if pos < 0:
        return space.w_False
    if before_needle:
        return space.newstr(haystack[:pos])
    else:
        return space.newstr(haystack[pos:])


@wrap(['space', W_Root])
def strlen(space, w_obj):
    """Get string length."""
    return space.wrap(space.strlen(space.as_string(w_obj)))


def _cmp_right(s1, s2):
    l = max(len(s1), len(s2))
    bias = 0
    aend = 0
    bend = 0
    a = ""
    b = ""
    for i in xrange(l):
        try:
            a = s1[i]
        except IndexError:
            aend = 1
        try:
            b = s2[i]
        except IndexError:
            bend = 1
        if (aend or not a.isdigit()) and (bend or not b.isdigit()):
            return bias
        elif aend or not a.isdigit():
            return -1
        elif bend or not b.isdigit():
            return 1
        elif a < b:
            if not bias:
                bias = -1
        elif a > b:
            if not bias:
                bias = 1
    return bias


def _cmp_left(s1, s2):
    l = max(len(s1), len(s2))
    aend = 0
    bend = 0
    a = ""
    b = ""
    for i in xrange(l):
        try:
            a = s1[i]
        except IndexError:
            aend = 1
        try:
            b = s2[i]
        except IndexError:
            bend = 1
        if (aend or not a.isdigit()) \
           and (bend or not b.isdigit()):
            return 0
        elif aend or not a.isdigit():
            return -1
        elif bend or not b.isdigit():
            return 1
        elif a < b:
            return -1
        elif a > b:
            return 1
    return 0


def _clean_string(_str):
    res = []
    leading = 1
    for i, c in enumerate(_str):
        try:
            if c == '0' and _str[i + 1].isdigit() and leading:
                continue
        except IndexError:
            pass
        if c != '0':
            leading = 0
        if not c.isspace():
            res.append(c)
    s = "".join(res)
    return s


def _strnatcmp(s1, s2):
    cs1 = _clean_string(s1)
    cs2 = _clean_string(s2)
    if len(cs1) == 0 or len(cs2) == 0:
        return len(cs1) - len(cs2)

    l1 = len(s1) - 1
    l2 = len(s2) - 1
    if cs1 == cs2:
        # case there on the end of string was space which was removed
        if s1[-1].isspace():
            return 1
        if s2[-1].isspace():
            return -1
        return 0

    l = max(len(cs1), len(cs2))
    for i in xrange(l):
        try:
            a = cs1[i]
        except IndexError:
            return -1
        try:
            b = cs2[i]
        except IndexError:
            return 1

        if a.isdigit() and b.isdigit():
            res = 0
            if a == '0' or b == '0':
                res = _cmp_left(cs1[i:], cs2[i:])
            else:
                res = _cmp_right(cs1[i:], cs2[i:])
            if res != 0:
                return res
            if i == l1 and i == l2:
                return 0
        else:
            if a > b:
                return 1
            elif a < b:
                return -1
            else:
                continue
    return 0


@wrap(['space', str, str])
def strnatcasecmp(space, a, b):
    """Case insensitive string comparisons
    using a "natural order" algorithm."""
    return space.wrap(_strnatcmp(a.lower(), b.lower()))


@wrap(['space', str, str])
def strnatcmp(space, a, b):
    """String comparisons using a "natural order" algorithm."""
    return space.wrap(_strnatcmp(a, b))


@wrap(['space', str, str, int])
def strncasecmp(space, str1, str2, n):
    """Binary safe case-insensitive string
    comparison of the first n characters."""
    if n < 0:
        space.ec.warn("Length must be greater than or equal to 0")
        return space.w_False
    return space.newint(rstrcmp(str1[:n], str2[:n], case_insensitive=True))


@wrap(['space', str, str, int])
def strncmp(space, str1, str2, n):
    """Binary safe string comparison of the first n characters."""
    if n < 0:
        space.ec.warn("Length must be greater than or equal to 0")
        return space.w_False
    return space.newint(rstrcmp(str1[:n], str2[:n]))


@wrap(['space', str, str], error=False)
def strpbrk(space, haystack, char_list):
    """Search a string for any of a set of characters."""
    if len(char_list) == 0:
        space.ec.warn('strpbrk(): The character list cannot be empty')
        return space.w_False
    pos = 0
    for c in haystack:
        if c in char_list:
            break
        pos += 1
    else:
        return space.w_False
    return space.newstr(haystack[pos:])


@wrap(['space', str, W_Root, Optional(int)])
def strpos(space, haystack, w_needle, offset=0):
    """Find the position of the first occurrence of a substring in a string."""
    if offset < 0 or offset > len(haystack):
        space.ec.warn("strpos(): Offset not contained in string")
        return space.w_False

    try:
        needle = unwrap_needle(space, w_needle)
    except ValidationError as exc:
        space.ec.warn("strpos(): " + exc.msg)
        return space.w_False
    if len(needle) == 0:
        space.ec.warn("strpos(): Empty needle")
        return space.w_False

    result = haystack.find(needle, offset)
    if result == -1:
        return space.w_False
    return space.newint(result)


@wrap(['space', str, W_Root])
def strrchr(space, haystack, w_needle):
    """Find the last occurrence of a character in a string."""
    try:
        needle = unwrap_needle(space, w_needle)
    except ValidationError as exc:
        space.ec.warn("strrchr(): " + exc.msg)
        return space.w_False
    if len(needle) == 0:
        space.ec.hippy_warn("strrchr(): Empty delimiter converted to NUL")
        needle = "\0"
    needle = needle[0]
    pos = haystack.rfind(needle)
    if pos < 0:
        return space.w_False
    return space.newstr(haystack[pos:])


@wrap(['space', str])
def strrev(space, string):
    """Reverse a string."""
    s = StringBuilder(len(string))
    for i in range(len(string) - 1, -1, -1):
        s.append(string[i])
    return space.newstr(s.build())


@wrap(['space', str, W_Root, Optional(int)], error=False)
def strripos(space, haystack, w_needle, offset=0):
    """
    Find the position of the last occurrence of a case-insensitive substring
    in a string.
    """
    if abs(offset) > len(haystack):
        space.ec.warn("strripos(): "
                "Offset is greater than the length of haystack string")
        return space.w_False

    needle = unwrap_needle(space, w_needle)
    if len(needle) == 0:
        return space.w_False
    haystack = locale.lower(haystack)
    needle = locale.lower(needle)
    if offset >= 0:
        result = haystack.rfind(needle, offset)
    else:
        end = len(haystack) + offset + 1
        assert end >= 0
        result = haystack.rfind(needle, 0, end)
    if result == -1:
        return space.w_False
    return space.newint(result)


@wrap(['space', str, W_Root, Optional(int)], error=False)
def strrpos(space, haystack, w_needle, offset=0):
    """Find the position of the last occurrence of a substring in a string."""
    needle = unwrap_needle(space, w_needle)
    if len(needle) == 0:
        return space.w_False
    if abs(offset) > len(haystack):
        space.ec.warn("strrpos(): "
                "Offset is greater than the length of haystack string")
        return space.w_False
    if offset >= 0:
        result = haystack.rfind(needle, offset)
    else:
        end = len(haystack) + offset + 1
        assert end >= 0
        result = haystack.rfind(needle, 0, end)
    if result == -1:
        return space.w_False
    return space.newint(result)


@wrap(['space', str, str, Optional(int), Optional(int)])
def strspn(space, subject, mask, start=0, length=sys.maxint):
    """Finds the length of the initial segment of a string consisting entirely
    of characters contained within a given mask.."""
    if start > len(subject):
        return space.w_False
    start, end = _substr_window(len(subject), start, length)
    pos = start
    n = 0
    while pos < end and subject[pos] in mask:
        n += 1
        pos += 1
    return space.newint(n)


@wrap(['space', str, str, Optional(int), Optional(int)])
def strcspn(space, subject, mask, start=0, length=sys.maxint):
    """Find length of initial segment not matching mask."""
    if start > len(subject):
        return space.w_False
    start, end = _substr_window(len(subject), start, length)
    pos = start
    n = 0
    if not mask:
        mask = "\0"  # PHP does that
    if len(mask) == 1:
        mask_0 = mask[0]
        while pos < end and subject[pos] != mask_0:
            n += 1
            pos += 1
    else:
        while pos < end and subject[pos] not in mask:
            n += 1
            pos += 1
    return space.newint(n)


@wrap(['space', str, W_Root, Optional(bool)], aliases=['strchr'])
def strstr(space, haystack, w_needle, before_needle=False):
    """Find the first occurrence of a string."""
    try:
        needle = unwrap_needle(space, w_needle)
    except ValidationError as exc:
        space.ec.warn("strstr(): " + exc.msg)
        return space.w_False
    if len(needle) == 0:
        space.ec.warn("strstr(): Empty needle")
        return space.w_False
    pos = haystack.find(needle)
    if pos < 0:
        return space.w_False
    if before_needle:
        return space.newstr(haystack[:pos])
    else:
        return space.newstr(haystack[pos:])

@wrap(['interp', str, Optional(str)])
def strtok(interp, s, token=None):
    """Tokenize string."""
    if token is not None:
        interp.last_strtok_str = s
        interp.last_strtok_pos = pos = 0
    else:
        token = s
        s = interp.last_strtok_str
        if s is None:
            return interp.space.w_False
        pos = interp.last_strtok_pos
    start_pos = pos
    while start_pos < len(s):
        for c in token:
            if s[start_pos] == c:
                break
        else:
            break
        start_pos += 1
    pos = start_pos
    if start_pos == len(s):
        interp.last_strtok_str = None
        return interp.space.w_False
    while pos < len(s):
        for c in token:
            if s[pos] == c:
                interp.last_strtok_pos = pos + 1
                return interp.space.wrap(s[start_pos:pos])
        pos += 1
    interp.last_strtok_str = None
    if pos != start_pos:
        return interp.space.wrap(s[start_pos:pos])
    return interp.space.w_False

@wrap(['space', str, W_Root, Optional(str)])
def strtr(space, string, w_from, to=None):
    """Translate characters or replace substrings."""
    if to is None:
        if w_from.tp != space.tp_array:
            space.ec.warn("strtr(): The second argument is not an array")
            return space.w_False
        if not string:
            return space.newstr(string)
        try:
            pairs = _pairs_from_array(space, w_from)
        except ValidationError:
            return space.w_False
        return space.newstr(_apply_replacement(pairs, string))
    else:
        if not string:
            return space.newstr(string)
        from_ = space.str_w(w_from)
        table = _make_charmap(from_, to)
        return space.newstr(_apply_charmap(string, table, len(string)))


@wrap(['space', str, str, int, 'num_args', Optional(int), Optional(bool)],
      error=False)
def substr_compare(space, main_str, str_, offset, num_args, length=0,
                   case_insensitivity=False):
    """Binary safe comparison of two strings from
    an offset, up to length characters."""
    if offset >= len(main_str) or len(main_str) == 0:
        space.ec.warn('substr_compare(): '
                'The start position cannot exceed initial string length')
        return space.w_False
    if offset < 0:
        offset = len(main_str) + offset
        if offset < 0:
            offset = 0
    str1 = main_str[offset:]
    str2 = str_
    if num_args == 3:
        pass
    elif length < 1:
        space.ec.warn('substr_compare(): '
                'The length must be greater than zero')
        return space.w_False
    else:
        str1 = str1[:length]
        str2 = str2[:length]
    return space.newint(rstrcmp(str1, str2, case_insensitivity))


@wrap(['space', str, str, 'num_args', Optional(int), Optional(int)])
def substr_count(space, haystack, needle, num_args, offset=0,
                 length=sys.maxint):
    """Count the number of substring occurrences."""
    if len(needle) == 0:
        space.ec.warn('substr_count(): Empty substring')
        return space.w_False
    if offset < 0:
        space.ec.warn('substr_count(): '
                'Offset should be greater than or equal to 0')
        return space.w_False
    if offset > len(haystack):
        space.ec.warn('substr_count(): '
                'Offset value %d exceeds string length' % offset)
        return space.w_False
    if num_args <= 3:
        return space.newint(haystack[offset:].count(needle))
    elif length <= 0:
        space.ec.warn('substr_count(): '
                'Length should be greater than 0')
        return space.w_False
    end = length + offset
    if end > len(haystack):
        space.ec.warn('substr_count(): '
                'Length value %d exceeds string length' % length)
        return space.w_False
    return space.newint(haystack[offset:end].count(needle))


def _substr_replace(string, replacement, start, length):
    start, end = _substr_window(len(string), start, length)
    if end < start:
        end = start
    builder = StringBuilder()
    builder.append(string[:start])
    builder.append(replacement)
    builder.append(string[end:])
    return builder.build()


def _sreplace_array(space, w_string, w_replacement, w_start, w_length):
    assert w_string.tp == space.tp_array
    n_items = w_string.arraylen()
    string_iter = space.create_iter(w_string)
    repls = _broadcast_as_list(w_replacement, n_items, "", space.str_w_quiet)
    starts = _broadcast_as_list(w_start, n_items, 0, space.int_w)
    lengths = _broadcast_as_list(w_length, n_items, sys.maxint, space.int_w)
    result = [None] * n_items
    for i in range(n_items):
        _, w_val = string_iter.next_item(space)
        string = space.str_w(w_val, quiet=True)
        result[i] = space.newstr(
                _substr_replace(string, repls[i], starts[i], lengths[i]))
    return space.new_array_from_list(result)


@wrap(['space', W_Root, W_Root, W_Root, Optional(W_Root)])
def substr_replace(space, w_string, w_replacement, w_start, w_length=None):
    """Replace text within a portion of a string."""
    if w_string.tp == space.tp_array:
        return _sreplace_array(space, w_string,
                               w_replacement, w_start, w_length)
    string = space.str_w(w_string)
    if w_start.tp == space.tp_array and (w_length is not None and
            w_length.tp == space.tp_array):
        if w_start.arraylen() != w_length.arraylen():
            space.ec.warn("substr_replace(): "
                    "'from' and 'len' should have the same number of elements")
        else:
            space.ec.warn("substr_replace(): "
                          "Functionality of 'from' and 'len' "
                          "as arrays is not implemented")
        return space.newstr(string)
    if w_start.tp == space.tp_array or (w_length is not None and
            w_length.tp == space.tp_array):
        space.ec.warn("substr_replace(): "
                      "'from' and 'len' should be of same "
                      "type - numerical or array ")
        return space.newstr(string)
    start = space.int_w(w_start)
    if w_replacement.tp == space.tp_array:
        if w_replacement.arraylen() == 0:
            replacement = ""
        else:
            _, w_val = space.create_iter(w_replacement).next_item(space)
            replacement = space.str_w(w_val)
    else:
        replacement = space.str_w(w_replacement)
    if w_length is not None:
        length = space.int_w(w_length)
    else:
        length = sys.maxint
    s = _substr_replace(string, replacement, start, length)
    return space.newstr(s)


@wrap(['space', str, int, 'num_args', Optional(int)])
def substr(space, string, start, num_args, length=0):
    """Return part of a string."""
    n = len(string)
    if num_args == 2:
        length = n
    elif length < -n:
        return space.w_False
    elif length > n:
        length = n
    if start < -n:
        start = 0
    if length < 0 and n + length < start:
        return space.w_False
    start, end = _substr_window(n, start, length)
    if start >= n:
        return space.w_False
    assert start >= 0
    assert end >= 0
    return space.newstr(string[start:end])


@jit.elidable
def _trim(string, charmask, left=True, right=True):
    lpos = 0
    rpos = len(string)
    if left:
        while lpos < rpos and charmask[ord(string[lpos])]:
            lpos += 1
    if right:
        while rpos > lpos and charmask[ord(string[rpos - 1])]:
            rpos -= 1
    assert rpos >= lpos    # annotator hint
    return string[lpos:rpos]

WHITESPACEMASK = charmask(getspace(), PHP_WHITESPACE, "")


@wrap(['space', str, Optional(str)])
def trim(space, string, char_list=None):
    """Strip whitespace (or other characters)
    from the beginning and end of a string."""
    if char_list is None:
        mask = WHITESPACEMASK
    else:
        mask = charmask(space, char_list, 'trim')
    return space.newstr(_trim(string, mask))


@wrap(['space', str, Optional(str)])
def ltrim(space, string, char_list=None):
    """Strip whitespace (or other characters)
    from the beginning of a string."""
    if char_list is None:
        mask = WHITESPACEMASK
    else:
        mask = charmask(space, char_list, 'ltrim')
    return space.newstr(_trim(string, mask, right=False))


@wrap(['space', str, Optional(str)], aliases=['chop'])
def rtrim(space, string, char_list=None):
    """Strip whitespace (or other characters) from the end of a string."""
    if char_list is None:
        mask = WHITESPACEMASK
    else:
        mask = charmask(space, char_list, 'rtrim')
    return space.newstr(_trim(string, mask, left=False))


@wrap(['space', str])
def ucfirst(space, string):
    """Make a string's first character uppercase."""
    n = len(string)
    if n == 0:
        return space.newstr('')

    builder = StringBuilder(n)
    builder.append(string[0].upper())
    builder.append_slice(string, 1, n)
    s = builder.build()
    return space.newstr(s)


@wrap(['space', str])
def ucwords(space, string):
    """Uppercase the first character of each word in a string."""
    builder = StringBuilder(len(string))
    wordstart = True
    for c in string:
        is_space = c.isspace()
        if wordstart and not is_space:
            builder.append(locale.upper_char(c))
            wordstart = False
        else:
            builder.append(c)
            wordstart = is_space
    s = builder.build()
    return space.newstr(s)


@wrap(['space', 'args_w'])
def vfprintf(space, args_w):
    """Write a formatted string to a stream."""
    if len(args_w) != 3:
        space.ec.warn("Wrong parameter count for vfprintf()")
        return space.w_Null
    w_res = args_w[0]
    format = space.str_w(args_w[1])
    w_args = unpack_array(args_w[2])

    if w_res.tp != space.tp_file_res:
        space.ec.warn("vfprintf() expects parameter 1 "
                      "to be resource, %s given"
                      % space.get_type_name(w_res.tp).lower())
        return space.w_False
    assert isinstance(w_res, W_FileResource)

    if not w_res.is_valid():
        space.ec.warn("vfprintf(): %d is not a valid "
                      "stream resource" % w_res.res_id)
        return space.w_False
    assert isinstance(w_res, W_FileResource)

    try:
        s = _printf(space, format, w_args, "fprintf")
    except ValidationError as e:
        space.ec.warn("vfprintf(): " + e.msg)
        return space.w_False
    w_res.writeall(s)
    return space.newint(len(s))


def _split_word(word, width):
    assert width > 0
    n = 0
    lines = []
    while n < len(word) - width:
        lines.append(word[n:n + width])
        n += width
    lines.append(word[n:])
    return lines


@wrap(['space', str, Optional(LongArg()),
       Optional(str), Optional(BoolArg())])
def wordwrap(space, string, width=75, break_='\n', cut=False):
    """Wraps a string to a given number of characters."""
    if len(string) == 0:
        return space.newstr('')
    if len(break_) == 0:
        space.ec.warn('wordwrap(): Break string cannot be empty')
        return space.w_False
    if width == 0 and cut:
        space.ec.warn("wordwrap(): Can't force cut when width is zero")
        return space.w_False
    if width < 0:
        width = 1
    chunks = string.split(break_)
    lines = []
    for chunk in chunks:
        words = chunk.split(' ')
        curr_len = -1
        curr_line = []
        for w in words:
            curr_len += len(w) + 1
            if curr_len > width:
                if not curr_line:
                    if cut:
                        lines.extend(_split_word(w, width))
                    else:
                        lines.append(w)
                    curr_len = -1
                    curr_line = []
                else:
                    lines.append(' '.join(curr_line))
                    if len(w) > width:
                        if cut:
                            lines.extend(_split_word(w, width))
                        else:
                            lines.append(w)
                        curr_len = -1
                        curr_line = []
                    else:
                        curr_line = [w]
                        curr_len = len(w)
            else:
                curr_line.append(w)
        if curr_line:
            lines.append(' '.join(curr_line))
    return space.newstr(break_.join(lines))
