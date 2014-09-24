from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.rtyper.tool import rffi_platform as platform
from rpython.rtyper.lltypesystem import rffi, lltype
from hippy.tool.platform import get_gmake
import subprocess
import py


LIBDIR = py.path.local(__file__).join('..', 'lib', 'haval/')
subprocess.check_call([get_gmake(), '-C', str(LIBDIR)])

eci = ExternalCompilationInfo(
    includes=['haval.h'],
    library_dirs=[str(LIBDIR)],
    libraries=['haval1'],
    testonly_libraries=['haval'],
    include_dirs=[str(LIBDIR)])


class CConfig:
    _compilation_info_ = eci
    HAVAL_CTX = platform.Struct('HAVAL_CTX', [])


globals().update(platform.configure(CConfig))


def external(name, args, result):
    return rffi.llexternal(name, args, result,
                           compilation_info=eci, releasegil=False)


HAVAL_CTX_PTR = lltype.Ptr(HAVAL_CTX)

c_haval_update = external('HAVALUpdate',
                          [HAVAL_CTX_PTR, rffi.CCHARP, rffi.UINT],
                          lltype.Void)


c_haval3_128init = external('HAVAL3_128Init', [HAVAL_CTX_PTR],
                            lltype.Void)
c_haval3_160init = external('HAVAL3_160Init', [HAVAL_CTX_PTR],
                            lltype.Void)
c_haval3_192init = external('HAVAL3_192Init', [HAVAL_CTX_PTR],
                            lltype.Void)
c_haval3_224init = external('HAVAL3_224Init', [HAVAL_CTX_PTR],
                            lltype.Void)
c_haval3_256init = external('HAVAL3_256Init', [HAVAL_CTX_PTR],
                            lltype.Void)

c_haval4_128init = external('HAVAL4_128Init', [HAVAL_CTX_PTR],
                            lltype.Void)
c_haval4_160init = external('HAVAL4_160Init', [HAVAL_CTX_PTR],
                            lltype.Void)
c_haval4_192init = external('HAVAL4_192Init', [HAVAL_CTX_PTR],
                            lltype.Void)
c_haval4_224init = external('HAVAL4_224Init', [HAVAL_CTX_PTR],
                            lltype.Void)
c_haval4_256init = external('HAVAL4_256Init', [HAVAL_CTX_PTR],
                            lltype.Void)

c_haval5_128init = external('HAVAL5_128Init', [HAVAL_CTX_PTR],
                            lltype.Void)
c_haval5_160init = external('HAVAL5_160Init', [HAVAL_CTX_PTR],
                            lltype.Void)
c_haval5_192init = external('HAVAL5_192Init', [HAVAL_CTX_PTR],
                            lltype.Void)
c_haval5_224init = external('HAVAL5_224Init', [HAVAL_CTX_PTR],
                            lltype.Void)
c_haval5_256init = external('HAVAL5_256Init', [HAVAL_CTX_PTR],
                            lltype.Void)

c_haval_128final = external('HAVAL128Final', [rffi.CCHARP,
                                              HAVAL_CTX_PTR],
                            lltype.Void)

c_haval_160final = external('HAVAL160Final', [rffi.CCHARP,
                                              HAVAL_CTX_PTR],
                            lltype.Void)
c_haval_192final = external('HAVAL192Final', [rffi.CCHARP,
                                              HAVAL_CTX_PTR],
                            lltype.Void)
c_haval_224final = external('HAVAL224Final', [rffi.CCHARP,
                                              HAVAL_CTX_PTR],
                            lltype.Void)
c_haval_256final = external('HAVAL256Final', [rffi.CCHARP,
                                              HAVAL_CTX_PTR],
                            lltype.Void)
