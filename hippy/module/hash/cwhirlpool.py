from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.rtyper.tool import rffi_platform as platform
from rpython.rtyper.lltypesystem import rffi, lltype
from hippy.tool.platform import get_gmake
import subprocess
import py


LIBDIR = py.path.local(__file__).join('..', 'lib', 'whirlpool/')
subprocess.check_call([get_gmake(), '-C', str(LIBDIR)])


eci = ExternalCompilationInfo(
    includes=['whirlpool.h'],
    library_dirs=[str(LIBDIR)],
    libraries=['whirlpool1'],
    testonly_libraries=['whirlpool'],
    include_dirs=[str(LIBDIR)])


class CConfig:
    _compilation_info_ = eci
    WHIRLPOOL_CTX = platform.Struct('WHIRLPOOL_CTX', [])

globals().update(platform.configure(CConfig))


def external(name, args, result):
    return rffi.llexternal(name, args, result,
                           compilation_info=eci, releasegil=False)

PTR_WHIRLPOOL_CTX = lltype.Ptr(WHIRLPOOL_CTX)


c_WHIRLPOOLInit = external('WHIRLPOOLInit',
                           [PTR_WHIRLPOOL_CTX], lltype.Void)

c_WHIRLPOOLUpdate = external('WHIRLPOOLUpdate',
                             [PTR_WHIRLPOOL_CTX,
                              rffi.CCHARP,
                              rffi.UINT],
                             lltype.Void)

c_WHIRLPOOLFinal = external('WHIRLPOOLFinal',
                            [rffi.CCHARP,
                             PTR_WHIRLPOOL_CTX],
                            lltype.Void)
