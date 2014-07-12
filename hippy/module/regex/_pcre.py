from rpython.rtyper.lltypesystem import lltype, rffi
from rpython.rtyper.tool import rffi_platform as platform
from rpython.translator.tool.cbuild import ExternalCompilationInfo


includes = ('pcre.h',)
libraries = ('pcre',)
post_include_bits = ["""
void hippy_pcre_free2(pcre *p, pcre_extra *x);
"""]
source = """
#include <string.h>

void hippy_pcre_free2(pcre *p, pcre_extra *x) {
#ifdef PCRE_CONFIG_JIT
    pcre_free_study(x);
#else
    pcre_free(x);
#endif
    pcre_free(p);
}

pcre_extra* hippy_pcre_extra_malloc()
{
    pcre_extra* res;
    res = (pcre_extra*)pcre_malloc(sizeof(pcre_extra));
    memset((void*)res, 0, sizeof(pcre_extra));
    return res;
}
"""
eci = ExternalCompilationInfo(includes=includes, libraries=libraries,
                              post_include_bits=post_include_bits,
                              separate_module_sources=[source])


def llexternal(*args, **kwds):
    kwds['compilation_info'] = eci
    return rffi.llexternal(*args, **kwds)

# ____________________________________________________________


class CConfig:
    _compilation_info_ = eci

    pcre_extra = platform.Struct('pcre_extra',
                                 [('flags', lltype.Signed),
                                  ('match_limit', lltype.Signed),
                                  ('match_limit_recursion', lltype.Signed),
                              ])

# list of all integer constants that must be present
for _name in '''
PCRE_CASELESS PCRE_MULTILINE PCRE_DOTALL PCRE_EXTENDED
PCRE_ANCHORED PCRE_DOLLAR_ENDONLY PCRE_UNGREEDY PCRE_EXTRA
PCRE_UTF8 PCRE_NOTEMPTY
PCRE_EXTRA_MATCH_LIMIT PCRE_EXTRA_MATCH_LIMIT_RECURSION
PCRE_NO_UTF8_CHECK
PCRE_ERROR_NOMATCH PCRE_ERROR_MATCHLIMIT PCRE_ERROR_RECURSIONLIMIT
PCRE_ERROR_BADUTF8 PCRE_ERROR_BADUTF8_OFFSET
PCRE_INFO_CAPTURECOUNT PCRE_INFO_NAMECOUNT PCRE_INFO_NAMETABLE
PCRE_INFO_NAMEENTRYSIZE
'''.split():
    setattr(CConfig, _name, platform.ConstantInteger(_name))

# list of all integer constants that are optional

for _name in '''
PCRE_UCP
'''.split():
    setattr(CConfig, _name, platform.DefinedConstantInteger(_name))

globals().update(platform.configure(CConfig))

# ____________________________________________________________

CCHARPPP = lltype.Ptr(lltype.Array(rffi.CCHARPP, hints={'nolength': True}))

pcre = rffi.CStruct('pcre')

pcre_compile = llexternal('pcre_compile',
                          [rffi.CCHARP, rffi.INT,
                           rffi.CCHARPP, rffi.INTP,
                           rffi.CCHARP],
                          lltype.Ptr(pcre), releasegil=False)

pcre_exec = llexternal('pcre_exec',
                       [lltype.Ptr(pcre), lltype.Ptr(pcre_extra),
                        rffi.CCHARP, rffi.INT, rffi.INT,
                        rffi.INT, rffi.INTP, rffi.INT],
                       rffi.INT, releasegil=False)

pcre_fullinfo = llexternal('pcre_fullinfo',
                           [lltype.Ptr(pcre), lltype.Ptr(pcre_extra),
                            rffi.INT, rffi.VOIDP],
                           rffi.INT, releasegil=False)

pcre_study = llexternal('pcre_study',
                        [lltype.Ptr(pcre), rffi.INT, rffi.CCHARPP],
                        lltype.Ptr(pcre_extra), releasegil=False)

hippy_pcre_free2 = llexternal('hippy_pcre_free2',
                              [lltype.Ptr(pcre), lltype.Ptr(pcre_extra)],
                              lltype.Void, _nowrapper=True, releasegil=False)

hippy_pcre_extra_malloc = llexternal('hippy_pcre_extra_malloc', [],
                                     lltype.Ptr(pcre_extra), releasegil=False)
