
from rpython.rtyper.lltypesystem import lltype, rffi
from rpython.rtyper.tool import rffi_platform as platform
from rpython.translator.tool.cbuild import ExternalCompilationInfo
# rffi-based pwd module

eci = ExternalCompilationInfo(includes=['sys/types.h', 'pwd.h', 'grp.h'])

class CConfig(object):
    _compilation_info_ = eci

    passwd = platform.Struct('struct passwd',
                             [('pw_name', rffi.CCHARP),
                              ('pw_passwd', rffi.CCHARP),
                              ('pw_uid', lltype.Signed),
                              ('pw_gid', lltype.Signed),
                              ('pw_gecos', rffi.CCHARP),
                              ('pw_dir', rffi.CCHARP),
                              ('pw_shell', rffi.CCHARP)])

PASSWD = platform.configure(CConfig)['passwd']
PASSWDPTR = lltype.Ptr(PASSWD)

getpwnam = rffi.llexternal('getpwnam', [rffi.CCHARP], PASSWDPTR,
                           compilation_info=eci)
getpwuid = rffi.llexternal('getpwuid', [lltype.Signed], PASSWDPTR,
                           compilation_info=eci)
initgroups = rffi.llexternal('initgroups', [rffi.CCHARP, lltype.Signed],
                             rffi.INT, compilation_info=eci)
