from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.rtyper.tool import rffi_platform as platform
from rpython.rtyper.lltypesystem import rffi, lltype
from hippy.tool.platform import get_gmake
import subprocess
import py


LIBDIR = py.path.local(__file__).join('..', 'lib', 'crc32/')
subprocess.check_call([get_gmake(), '-C', str(LIBDIR)])


eci = ExternalCompilationInfo(
    includes=['crc32.h'],
    library_dirs=[str(LIBDIR)],
    libraries=['crc321'],
    testonly_libraries=['crc32'],
    include_dirs=[str(LIBDIR)])


class CConfig:
    _compilation_info_ = eci
    CRC32_CTX = platform.Struct('CRC32_CTX', [])

globals().update(platform.configure(CConfig))


def external(name, args, result):
    return rffi.llexternal(name, args, result,
                           compilation_info=eci, releasegil=False)


PTR_CRC32_CTX = lltype.Ptr(CRC32_CTX)


c_CRC32Init = external('CRC32Init',
                       [PTR_CRC32_CTX], lltype.Void)

c_CRC32Update = external('CRC32Update',
                         [PTR_CRC32_CTX,
                          rffi.CCHARP,
                          rffi.UINT],
                         lltype.Void)


c_CRC32BUpdate = external('CRC32BUpdate',
                            [PTR_CRC32_CTX,
                             rffi.CCHARP,
                             rffi.UINT],
                          lltype.Void)

c_CRC32Final = external('CRC32Final',
                        [rffi.CCHARP,
                         PTR_CRC32_CTX],
                        lltype.Void)

c_CRC32BFinal = external('CRC32BFinal',
                         [rffi.CCHARP,
                          PTR_CRC32_CTX],
                         lltype.Void)
