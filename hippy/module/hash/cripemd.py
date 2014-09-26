from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.rtyper.tool import rffi_platform as platform
from rpython.rtyper.lltypesystem import rffi, lltype
from hippy.tool.platform import get_gmake
import subprocess
import py

LIBDIR = py.path.local(__file__).join('..', 'lib', 'ripemd/')
subprocess.check_call([get_gmake(), '-C', str(LIBDIR)])


eci = ExternalCompilationInfo(
    includes=['ripemd.h'],
    library_dirs=[str(LIBDIR)],
    libraries=['ripemd1'],
    testonly_libraries=['ripemd'],
    include_dirs=[str(LIBDIR)])


class CConfig:
    _compilation_info_ = eci
    ripemd128_ctx = platform.Struct('ripemd128_ctx', [])
    ripemd160_ctx = platform.Struct('ripemd160_ctx', [])
    ripemd256_ctx = platform.Struct('ripemd256_ctx', [])
    ripemd320_ctx = platform.Struct('ripemd320_ctx', [])

globals().update(platform.configure(CConfig))


def external(name, args, result):
    return rffi.llexternal(name, args, result,
                           compilation_info=eci, releasegil=False)

ptr_ripemd128_ctx = lltype.Ptr(ripemd128_ctx)
ptr_ripemd160_ctx = lltype.Ptr(ripemd160_ctx)
ptr_ripemd256_ctx = lltype.Ptr(ripemd256_ctx)
ptr_ripemd320_ctx = lltype.Ptr(ripemd320_ctx)


c_ripemd128_init = external('ripemd128_init',
                            [ptr_ripemd128_ctx], lltype.Void)
c_ripemd128_update = external('ripemd128_update',
                              [ptr_ripemd128_ctx,
                               rffi.CCHARP,
                               rffi.INT],
                              lltype.Void)

c_ripemd128_final = external('ripemd128_final',
                             [rffi.CCHARP,
                              ptr_ripemd128_ctx],
                             lltype.Void)


c_ripemd160_init = external('ripemd160_init',
                            [ptr_ripemd160_ctx], lltype.Void
)
c_ripemd160_update = external('ripemd160_update',
                              [ptr_ripemd160_ctx,
                               rffi.CCHARP,
                               rffi.INT],
                              lltype.Void)

c_ripemd160_final = external('ripemd160_final',
                             [rffi.CCHARP,
                              ptr_ripemd160_ctx],
                             lltype.Void)


c_ripemd256_init = external('ripemd256_init',
                            [ptr_ripemd256_ctx], lltype.Void)

c_ripemd256_update = external('ripemd256_update',
                              [ptr_ripemd256_ctx,
                               rffi.CCHARP,
                               rffi.INT],
                              lltype.Void)

c_ripemd256_final = external('ripemd256_final',
                             [rffi.CCHARP,
                              ptr_ripemd256_ctx],
                             lltype.Void)

c_ripemd320_init = external('ripemd320_init',
                            [ptr_ripemd320_ctx], lltype.Void)
c_ripemd320_update = external('ripemd320_update',
                              [ptr_ripemd320_ctx,
                               rffi.CCHARP,
                               rffi.INT],
                              lltype.Void)

c_ripemd320_final = external('ripemd320_final',
                             [rffi.CCHARP,
                              ptr_ripemd320_ctx],
                             lltype.Void)
