from rpython.translator.tool.cbuild import ExternalCompilationInfo
from rpython.rtyper.tool import rffi_platform as platform
from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.rlib.rarithmetic import intmask


eci = ExternalCompilationInfo(includes=['glob.h'])


class CConfig:
    _compilation_info_ = eci
    glob_t = platform.Struct('glob_t', [
        ('gl_pathc', lltype.Unsigned),
        ('gl_pathv', rffi.CCHARPP),
        ('gl_offs', lltype.Unsigned),
    ])


globals().update(platform.configure(CConfig))


def external(name, args, result):
    return rffi.llexternal(name, args, result, compilation_info=eci,
                           releasegil=False)


callback = lltype.Ptr(lltype.FuncType([rffi.CCHARP, rffi.INT], rffi.INT))

PTR_GLOB_T = lltype.Ptr(glob_t)

c_globfree = external('globfree',
                      [PTR_GLOB_T], lltype.Void)

c_glob = external('glob', [rffi.CCHARP,
                           rffi.INT,
                           callback,
                           PTR_GLOB_T], rffi.INT)


def _glob(pattern, flags):
    ll_glob_t = lltype.malloc(PTR_GLOB_T.TO, flavor='raw')
    files = []
    with rffi.scoped_str2charp(pattern) as ll_pattern:
        ll_res = c_glob(ll_pattern, flags, lltype.nullptr(callback.TO),
                        ll_glob_t)
        num = intmask(ll_glob_t.c_gl_pathc)
        for i in range(num):
            fname = rffi.charp2str(ll_glob_t.c_gl_pathv[i])
            files.append(fname)
    return ll_res, files
