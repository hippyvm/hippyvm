from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.rtyper.tool import rffi_platform as platform
from rpython.rtyper.lltypesystem import rffi, lltype
from hippy.tool.platform import get_gmake
import subprocess
import py


LIBDIR = py.path.local(__file__).join('..', 'lib', 'md/')
subprocess.check_call([get_gmake(), '-C', str(LIBDIR)])


eci = ExternalCompilationInfo(
    includes=['md.h'],
    library_dirs=[str(LIBDIR)],
    libraries=['md1'],
    testonly_libraries=['md'],
    include_dirs=[str(LIBDIR)])


class CConfig:
    _compilation_info_ = eci
    MD5_CTX = platform.Struct('MD5_CTX', [])
    MD4_CTX = platform.Struct('MD4_CTX', [])
    MD2_CTX = platform.Struct('MD2_CTX', [])

globals().update(platform.configure(CConfig))


def external(name, args, result):
    return rffi.llexternal(name, args, result,
                           compilation_info=eci, releasegil=False)

PTR_MD2_CTX = lltype.Ptr(MD2_CTX)
PTR_MD4_CTX = lltype.Ptr(MD4_CTX)
PTR_MD5_CTX = lltype.Ptr(MD5_CTX)

c_md5init = external('MD5Init', [PTR_MD5_CTX], lltype.Void)
c_md5update = external('MD5Update',
                       [PTR_MD5_CTX,
                        rffi.CCHARP,
                        rffi.UINT],
                       lltype.Void)
c_md5final = external('MD5Final',
                      [rffi.CCHARP,
                       PTR_MD5_CTX],
                      lltype.Void)


c_md4init = external('MD4Init', [PTR_MD4_CTX], lltype.Void)
c_md4update = external('MD4Update',
                       [PTR_MD4_CTX,
                        rffi.CCHARP,
                        rffi.UINT],
                       lltype.Void)
c_md4final = external('MD4Final',
                      [rffi.CCHARP,
                       PTR_MD4_CTX],
                      lltype.Void)


c_md2init = external('MD2Init', [PTR_MD2_CTX], lltype.Void)
c_md2update = external('MD2Update',
                       [PTR_MD2_CTX,
                        rffi.CCHARP,
                        rffi.UINT],
                       lltype.Void)
c_md2final = external('MD2Final',
                      [rffi.CCHARP,
                       PTR_MD2_CTX],
                      lltype.Void)
