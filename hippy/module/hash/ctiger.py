from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.rtyper.tool import rffi_platform as platform
from rpython.rtyper.lltypesystem import rffi, lltype
from hippy.tool.platform import get_gmake
import subprocess
import py


LIBDIR = py.path.local(__file__).join('..', 'lib', 'tiger/')
subprocess.check_call([get_gmake(), '-C', str(LIBDIR)])


eci = ExternalCompilationInfo(
    includes=['tiger.h'],
    library_dirs=[str(LIBDIR)],
    libraries=['tiger1'],
    testonly_libraries=['tiger'],
    include_dirs=[str(LIBDIR)])


class CConfig:
    _compilation_info_ = eci
    TIGER_CTX = platform.Struct('TIGER_CTX', [])

globals().update(platform.configure(CConfig))


def external(name, args, result):
    return rffi.llexternal(name, args, result,
                           compilation_info=eci, releasegil=False)


PTR_TIGER_CTX = lltype.Ptr(TIGER_CTX)


c_TIGER3Init = external('TIGER3Init',
                        [PTR_TIGER_CTX], lltype.Void)
c_TIGER4Init = external('TIGER4Init',
                        [PTR_TIGER_CTX], lltype.Void)

c_TIGERUpdate = external('TIGERUpdate',
                         [PTR_TIGER_CTX,
                          rffi.CCHARP,
                          rffi.UINT],
                         lltype.Void)

c_TIGER128Final = external('TIGER128Final',
                           [rffi.CCHARP,
                            PTR_TIGER_CTX],
                           lltype.Void)

c_TIGER160Final = external('TIGER160Final',
                           [rffi.CCHARP,
                            PTR_TIGER_CTX],
                           lltype.Void)

c_TIGER192Final = external('TIGER192Final',
                           [rffi.CCHARP,
                            PTR_TIGER_CTX],
                           lltype.Void)
