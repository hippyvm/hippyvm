from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.rtyper.tool import rffi_platform as platform
from rpython.rtyper.lltypesystem import rffi, lltype
from hippy.tool.platform import get_gmake
import subprocess
import py


LIBDIR = py.path.local(__file__).join('..', 'lib', 'gost/')
subprocess.check_call([get_gmake(), '-C', str(LIBDIR)])


eci = ExternalCompilationInfo(
    includes=['gost.h'],
    library_dirs=[str(LIBDIR)],
    libraries=['gost1'],
    testonly_libraries=['gost'],
    include_dirs=[str(LIBDIR)])


class CConfig:
    _compilation_info_ = eci
    GOST_CTX = platform.Struct('GOST_CTX', [])

globals().update(platform.configure(CConfig))


def external(name, args, result):
    return rffi.llexternal(name, args, result,
                           compilation_info=eci, releasegil=False)

PTR_GOST_CTX = lltype.Ptr(GOST_CTX)


c_GOSTInit = external('GOSTInit',
                      [PTR_GOST_CTX], lltype.Void)

c_GOSTUpdate = external('GOSTUpdate',
                        [PTR_GOST_CTX,
                         rffi.CCHARP,
                         rffi.UINT],
                        lltype.Void)

c_GOSTFinal = external('GOSTFinal',
                       [rffi.CCHARP,
                        PTR_GOST_CTX],
                       lltype.Void)
