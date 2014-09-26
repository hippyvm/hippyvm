from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.rtyper.tool import rffi_platform as platform
from rpython.rtyper.lltypesystem import rffi, lltype
from hippy.tool.platform import get_gmake
import subprocess
import py


LIBDIR = py.path.local(__file__).join('..', 'lib', 'joaat/')
subprocess.check_call([get_gmake(), '-C', str(LIBDIR)])


eci = ExternalCompilationInfo(
    includes=['joaat.h'],
    library_dirs=[str(LIBDIR)],
    libraries=['joaat1'],
    testonly_libraries=['joaat'],
    include_dirs=[str(LIBDIR)])


class CConfig:
    _compilation_info_ = eci
    JOAAT_CTX = platform.Struct('JOAAT_CTX', [])

globals().update(platform.configure(CConfig))


def external(name, args, result):
    return rffi.llexternal(name, args, result,
                           compilation_info=eci, releasegil=False)

PTR_JOAAT_CTX = lltype.Ptr(JOAAT_CTX)


c_JOAATInit = external('JOAATInit',
                       [PTR_JOAAT_CTX], lltype.Void)

c_JOAATUpdate = external('JOAATUpdate',
                         [PTR_JOAAT_CTX,
                          rffi.CCHARP,
                          rffi.UINT],
                         lltype.Void)

c_JOAATFinal = external('JOAATFinal',
                        [rffi.CCHARP,
                         PTR_JOAAT_CTX],
                        lltype.Void)
