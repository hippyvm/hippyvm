from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.rtyper.tool import rffi_platform as platform
from rpython.rtyper.lltypesystem import rffi, lltype
from hippy.tool.platform import get_gmake
import subprocess
import py

LIBDIR = py.path.local(__file__).join('..', 'lib', 'fnv/')
subprocess.check_call([get_gmake(), '-C', str(LIBDIR)])


eci = ExternalCompilationInfo(
    includes=['fnv.h'],
    library_dirs=[str(LIBDIR)],
    libraries=['fnv1'],
    testonly_libraries=['fnv'],
    include_dirs=[str(LIBDIR)])


class CConfig:
    _compilation_info_ = eci
    FNV132_CTX = platform.Struct('FNV132_CTX', [])
    FNV164_CTX = platform.Struct('FNV164_CTX', [])

globals().update(platform.configure(CConfig))


def external(name, args, result):
    return rffi.llexternal(name, args, result,
                           compilation_info=eci, releasegil=False)


PTR_FNV132_CTX = lltype.Ptr(FNV132_CTX)
PTR_FNV164_CTX = lltype.Ptr(FNV164_CTX)


c_fnv132init = external('FNV132Init', [PTR_FNV132_CTX], lltype.Void)
c_fnv132update = external('FNV132Update',
                          [PTR_FNV132_CTX,
                           rffi.CCHARP,
                           rffi.UINT],
                          lltype.Void)
c_fnv132final = external('FNV132Final',
                         [rffi.CCHARP,
                          PTR_FNV132_CTX],
                         lltype.Void)

c_fnv164init = external('FNV164Init', [PTR_FNV164_CTX], lltype.Void)
c_fnv164update = external('FNV164Update',
                          [PTR_FNV164_CTX,
                           rffi.CCHARP,
                           rffi.UINT],
                          lltype.Void)
c_fnv164final = external('FNV164Final',
                         [rffi.CCHARP,
                          PTR_FNV164_CTX],
                         lltype.Void)
