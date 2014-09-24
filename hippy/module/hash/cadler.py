from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.rtyper.tool import rffi_platform as platform
from rpython.rtyper.lltypesystem import rffi, lltype
from hippy.tool.platform import get_gmake
import subprocess
import py


LIBDIR = py.path.local(__file__).join('..', 'lib', 'adler32/')
subprocess.check_call([get_gmake(), '-C', str(LIBDIR)])


eci = ExternalCompilationInfo(
    includes=['adler32.h'],
    library_dirs=[str(LIBDIR)],
    libraries=['adler321'],
    testonly_libraries=['adler32'],
    include_dirs=[str(LIBDIR)])


class CConfig:
    _compilation_info_ = eci
    ADLER32_CTX = platform.Struct('ADLER32_CTX', [])

globals().update(platform.configure(CConfig))


def external(name, args, result):
    return rffi.llexternal(name, args, result,
                           compilation_info=eci, releasegil=False)


PTR_ADLER32_CTX = lltype.Ptr(ADLER32_CTX)


c_adler32init = external('ADLER32Init', [PTR_ADLER32_CTX], lltype.Void)
c_adler32update = external('ADLER32Update',
                           [PTR_ADLER32_CTX,
                            rffi.CCHARP,
                            rffi.UINT],
                           lltype.Void)

c_adler32final = external('ADLER32Final',
                          [rffi.CCHARP,
                           PTR_ADLER32_CTX],
                          lltype.Void)
