from hippy.builtin import wrap, Optional
from rpython.rlib import rzlib
import sys


ZLIB_ENCODING_RAW = -15
ZLIB_ENCODING_GZIP = 31
ZLIB_ENCODING_DEFLATE = 15
ZLIB_ENCODING_ANY = 99


def _encode(data, level, encoding):
    stream = rzlib.deflateInit(level=level, wbits=encoding)
    bytes = rzlib.compress(stream, data)
    bytes += rzlib.compress(stream, "", rzlib.Z_FINISH)
    rzlib.deflateEnd(stream)
    return bytes


def _decode(data, encoding):
    stream = rzlib.inflateInit(wbits=encoding)
    bytes, finished, unused = rzlib.decompress(stream, data,
                                               rzlib.Z_FINISH)
    rzlib.inflateEnd(stream)
    return bytes


@wrap(['interp', str, Optional(int), Optional(int)])
def gzdeflate(interp, source, level=-1, encoding=ZLIB_ENCODING_RAW):
    res = _encode(source, level, encoding)
    return interp.space.wrap(res)


@wrap(['interp', str, Optional(int), Optional(int)])
def gzencode(interp, source, level=-1, encoding=ZLIB_ENCODING_GZIP):
    res = _encode(source, level, encoding)
    return interp.space.wrap(res)


@wrap(['interp', str, Optional(int), Optional(int)])
def gzcompress(interp, source, level=-1, encoding=ZLIB_ENCODING_DEFLATE):
    res = _encode(source, level, encoding)
    return interp.space.wrap(res)


@wrap(['interp', str, Optional(int)])
def gzinflate(interp, source, length=0):
    res = _decode(source, ZLIB_ENCODING_RAW)
    return interp.space.wrap(res)


@wrap(['interp', str, Optional(int)])
def gzdecode(interp, source, length=0):
    res = _decode(source, ZLIB_ENCODING_GZIP)
    return interp.space.wrap(res)


@wrap(['interp', str, Optional(int)])
def gzuncompress(interp, source, length=0):
    res = _decode(source, ZLIB_ENCODING_DEFLATE)
    return interp.space.wrap(res)
