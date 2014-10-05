from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.rtyper.tool import rffi_platform as platform
from rpython.rtyper.lltypesystem import rffi, lltype
from hippy.tool.platform import get_gmake
import subprocess
import py


LIBDIR = py.path.local(__file__).join('..', 'lib', 'sha/')
subprocess.check_call([get_gmake(), '-C', str(LIBDIR)])


eci = ExternalCompilationInfo(
    includes=['sha.h'],
    library_dirs=[str(LIBDIR)],
    libraries=['sha1'],
    testonly_libraries=['sha'],
    include_dirs=[str(LIBDIR)])


class CConfig:
    _compilation_info_ = eci
    SHA1_CTX = platform.Struct('SHA1_CTX', [])
    SHA224_CTX = platform.Struct('SHA224_CTX', [])
    SHA256_CTX = platform.Struct('PHP_SHA256_CTX', [])
    SHA384_CTX = platform.Struct('SHA384_CTX', [])
    SHA512_CTX = platform.Struct('PHP_SHA512_CTX', [])

globals().update(platform.configure(CConfig))


def external(name, args, result):
    return rffi.llexternal(name, args, result,
                           compilation_info=eci, releasegil=False)

PTR_SHA1_CTX = lltype.Ptr(SHA1_CTX)
PTR_SHA224_CTX = lltype.Ptr(SHA224_CTX)
PTR_SHA256_CTX = lltype.Ptr(SHA256_CTX)
PTR_SHA384_CTX = lltype.Ptr(SHA384_CTX)
PTR_SHA512_CTX = lltype.Ptr(SHA512_CTX)


c_sha1init = external('SHA1Init',
                      [PTR_SHA1_CTX], lltype.Void)

c_sha1update = external('SHA1Update',
                        [PTR_SHA1_CTX,
                         rffi.CCHARP,
                         rffi.UINT],
                        lltype.Void)

c_sha1final = external('SHA1Final',
                       [rffi.CCHARP, PTR_SHA1_CTX],
                       lltype.Void)


c_sha224init = external('SHA224Init',
                        [PTR_SHA224_CTX], lltype.Void)

c_sha224update = external('SHA224Update',
                          [PTR_SHA224_CTX,
                           rffi.CCHARP,
                           rffi.UINT],
                          lltype.Void)

c_sha224final = external('SHA224Final',
                         [rffi.CCHARP, PTR_SHA224_CTX],
                         lltype.Void)


c_sha256init = external('SHA256Init',
                        [PTR_SHA256_CTX], lltype.Void)

c_sha256update = external('SHA256Update',
                          [PTR_SHA256_CTX,
                           rffi.CCHARP,
                           rffi.UINT],
                          lltype.Void)

c_sha256final = external('SHA256Final',
                         [rffi.CCHARP, PTR_SHA256_CTX],
                         lltype.Void)

c_sha384init = external('SHA384Init',
                        [PTR_SHA384_CTX], lltype.Void)

c_sha384update = external('SHA384Update',
                          [PTR_SHA384_CTX,
                           rffi.CCHARP,
                           rffi.UINT],
                          lltype.Void)

c_sha384final = external('SHA384Final',
                         [rffi.CCHARP, PTR_SHA384_CTX],
                         lltype.Void)

c_sha512init = external('SHA512Init',
                        [PTR_SHA512_CTX], lltype.Void)

c_sha512update = external('SHA512Update',
                          [PTR_SHA512_CTX,
                           rffi.CCHARP,
                           rffi.UINT],
                          lltype.Void)

c_sha512final = external('SHA512Final',
                         [rffi.CCHARP, PTR_SHA512_CTX],
                         lltype.Void)
