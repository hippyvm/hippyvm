
from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.rtyper.tool import rffi_platform as platform
from rpython.rtyper.lltypesystem import rffi, lltype

eci = ExternalCompilationInfo(includes=['bzlib.h', ],
                              include_dirs=['/usr/include/'],
                              library_dirs=['/usr/lib/x86_64-linux-gnu/', ],
                              libraries=['libbz2'])


class CConfig:
    _compilation_info_ = eci


globals().update(platform.configure(CConfig))


def external(name, args, result):
    return rffi.llexternal(name, args, result, compilation_info=eci)

BZFILEPTR = rffi.VOIDP
FILEP = rffi.COpaquePtr('FILE')

c_bz_read_open = external(
    'BZ2_bzReadOpen',
    [rffi.INTP,
     FILEP,
     rffi.INT,
     rffi.INT,
     rffi.VOIDP,
     rffi.INT],
    BZFILEPTR)

c_bz_read_close = external(
    'BZ2_bzReadClose',
    [rffi.INTP,
     BZFILEPTR
     ],
    lltype.Void)

c_bz_read = external(
    'BZ2_bzRead',
    [rffi.INTP,
     BZFILEPTR,
     rffi.VOIDP,
     rffi.INT
     ],
    rffi.INT)

c_bz_write_open = external(
    'BZ2_bzWriteOpen',
    [rffi.INTP,
     FILEP,
     rffi.INT,
     rffi.INT,
     rffi.INT],
    BZFILEPTR
)

c_bz_write = external(
    'BZ2_bzWrite',
    [rffi.INTP,
     BZFILEPTR,
     rffi.VOIDP,
     rffi.INT],
    lltype.Void
)

c_bz_write_close = external(
    'BZ2_bzWriteClose',
    [rffi.INTP,
     BZFILEPTR,
     rffi.INT,
     rffi.INTP,
     rffi.INTP],
    lltype.Void
)

c_bz_buff_to_buff_compress = external(
    'BZ2_bzBuffToBuffCompress',
    [rffi.CCHARP,
     rffi.INTP,
     rffi.CCHARP,
     rffi.INT,
     rffi.INT,
     rffi.INT,
     rffi.INT],
    rffi.INT
)

c_bz_buff_to_buff_decompress = external(
    'BZ2_bzBuffToBuffDecompress',
    [rffi.CCHARP,
     rffi.INTP,
     rffi.CCHARP,
     rffi.INT,
     rffi.INT,
     rffi.INT],
    rffi.INT
)
