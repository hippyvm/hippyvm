
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

    group = platform.Struct('struct group',
                            [('gr_name', rffi.CCHARP),
                             ('gr_passwd', rffi.CCHARP),
                             ('gr_gid', lltype.Signed),
                             ('gr_mem', rffi.CCHARPP)])

PASSWD = platform.configure(CConfig)['passwd']
PASSWDPTR = lltype.Ptr(PASSWD)
GROUP =  platform.configure(CConfig)['group']
GROUPPTR = lltype.Ptr(GROUP)

getpwnam = rffi.llexternal('getpwnam', [rffi.CCHARP], PASSWDPTR,
                           compilation_info=eci)
getpwuid = rffi.llexternal('getpwuid', [lltype.Signed], PASSWDPTR,
                           compilation_info=eci)
initgroups = rffi.llexternal('initgroups', [rffi.CCHARP, lltype.Signed],
                             rffi.INT, compilation_info=eci,
                             save_err=rffi.RFFI_SAVE_ERRNO)
getgrgid = rffi.llexternal('getgrgid', [lltype.Signed], GROUPPTR,
                           compilation_info=eci)
getgrnam = rffi.llexternal('getgrnam', [rffi.CCHARP], GROUPPTR,
                           compilation_info=eci)
