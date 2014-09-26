from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.rtyper.tool import rffi_platform as platform
from rpython.rtyper.lltypesystem import rffi, lltype
from hippy.tool.platform import get_gmake
import subprocess
import py


LIBDIR = py.path.local(__file__).join('..', 'lib', 'snefru/')
subprocess.check_call([get_gmake(), '-C', str(LIBDIR)])


eci = ExternalCompilationInfo(
    includes=['snefru.h'],
    library_dirs=[str(LIBDIR)],
    libraries=['snefru1'],
    testonly_libraries=['snefru'],
    include_dirs=[str(LIBDIR)])


class CConfig:
    _compilation_info_ = eci
    SNEFRU_CTX = platform.Struct('SNEFRU_CTX', [])

globals().update(platform.configure(CConfig))


def external(name, args, result):
    return rffi.llexternal(name, args, result,
                           compilation_info=eci, releasegil=False)

PTR_SNEFRU_CTX = lltype.Ptr(SNEFRU_CTX)


c_SNEFRUInit = external('SNEFRUInit',
                        [PTR_SNEFRU_CTX], lltype.Void)

c_SNEFRUUpdate = external('SNEFRUUpdate',
                          [PTR_SNEFRU_CTX,
                           rffi.CCHARP,
                           rffi.UINT],
                          lltype.Void)

c_SNEFRUFinal = external('SNEFRUFinal',
                         [rffi.CCHARP,
                          PTR_SNEFRU_CTX],
                         lltype.Void)
