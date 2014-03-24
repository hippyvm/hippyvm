import os
import posix
from hippy.builtin import LongArg, wrap, Optional, FilenameArg
from hippy.objects.base import W_Root
from hippy.objects.resources import W_Resource
from hippy.rpwd import getpwnam, getpwuid, initgroups
from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.rlib import rposix
from rpython.rlib.rarithmetic import intmask
from collections import OrderedDict


@wrap(['space', str, Optional(int)], error=False)
def posix_access(space, fname, mode=0):
    """ posix_access - Determine accessibility of a file
    mode can be
        'POSIX_F_OK': 0,
        'POSIX_R_OK': 4,
        'POSIX_W_OK': 2,
        'POSIX_X_OK': 1,
        """
    r = mode & 4 != 0
    w = mode & 2 != 0
    x = mode & 1 != 0
    try:
        res = os.path.isfile(fname)
        if w:
            res &= os.access(fname, os.W_OK)
        if r:
            res &= os.access(fname, os.R_OK)
        if x:
            res &= os.access(fname, os.X_OK)

        return space.newbool(res)
    except OSError, e:
        space.set_errno(e.errno)
        return space.newbool(False)


@wrap(['space'])
def posix_ctermid(space):
    """ posix_ctermid - Get path name of controlling terminal """
    return space.newstr(os.ctermid())


@wrap(['space'], aliases=["posix_errno"])
def posix_get_last_error(space):
    """ posix_errno - Alias of posix_get_last_error """
    """ posix_get_last_error - Retrieve the error number set by
    the last posix function that failed """
    return space.newint(space.get_errno())


@wrap(['space'])
def posix_getcwd(space):
    """ posix_getcwd - Pathname of current directory """
    return space.newstr(os.getcwd())


@wrap(['space'])
def posix_getegid(space):
    """ posix_getegid - Return the effective group
    ID of the current process """
    return space.newint(os.getegid())


@wrap(['space'])
def posix_geteuid(space):
    """ posix_geteuid - Return the effective user ID of the current process """
    return space.newint(os.geteuid())


@wrap(['space'])
def posix_getgid(space):
    """ posix_getgid - Return the real group ID of the current process """
    return space.newint(os.getgid())

""" posix_getgrgid - Return info about a group by group id """
""" posix_getgrnam - Return info about a group by name """


@wrap(['space'])
def posix_getgroups(space):
    """ posix_getgroups - Return the group set of the current process """
    arr_list = []
    for g in posix.getgroups():
        arr_list.append(space.newint(rffi.cast(lltype.Signed, g)))
    return space.new_array_from_list(arr_list)


@wrap(['space'])
def posix_getlogin(space):
    """ posix_getlogin - Return login name """
    return space.newstr(os.getlogin())


@wrap(['space', int], error=False)
def posix_getpgid(space, pid):
    """ posix_getpgid - Get process group id for job control """
    try:
        return space.newint(os.getpgid(pid))
    except OSError, e:
        space.set_errno(e.errno)
        return space.newbool(False)
    except OverflowError:
        return space.newbool(False)


@wrap(['space'])
def posix_getpgrp(space):
    """ posix_getpgrp - Return the current process group identifier """
    try:
        return space.newint(os.getpgrp())
    except OSError, e:
        space.set_errno(e.errno)
        return space.newbool(False)


@wrap(['space'])
def posix_getpid(space):
    """ posix_getpid - Return the current process identifier """
    try:
        return space.newint(os.getpid())
    except OSError as e:
        space.set_errno(e.errno)
        return space.newbool(False)


@wrap(['space'])
def posix_getppid(space):
    """ posix_getppid - Return the parent process identifier """
    try:
        return space.newint(os.getppid())
    except OSError, e:
        space.set_errno(e.errno)
        return space.newbool(False)


def _build_user_info(space, res):
    return space.new_array_from_pairs([
        (space.newstr("name"), space.newstr(rffi.charp2str(res.c_pw_name))),
        (space.newstr("passwd"), space.newstr(rffi.charp2str(res.c_pw_passwd))),
        (space.newstr("uid"), space.newint(intmask(res.c_pw_uid))),
        (space.newstr("gid"), space.newint(intmask(res.c_pw_gid))),
        (space.newstr("gecos"), space.newstr(rffi.charp2str(res.c_pw_gecos))),
        (space.newstr("dir"), space.newstr(rffi.charp2str(res.c_pw_dir))),
        (space.newstr("shell"), space.newstr(rffi.charp2str(res.c_pw_shell))),
    ])


@wrap(['space', str])
def posix_getpwnam(space, user_name):
    """ posix_getpwnam - Return info about a user by username """
    res = getpwnam(rffi.str2charp(user_name))
    if not res:
        return space.newbool(False)
    return _build_user_info(space, res)

@wrap(['space', int], error=False)
def posix_getpwuid(space, uid):
    """ posix_getpwuid - Return info about a user by user id """
    res = getpwuid(uid)
    if not res:
        return space.newbool(False)
    return _build_user_info(space, res)

""" posix_getrlimit - Return info about system resource limits """


@wrap(['space', int], error=False)
def posix_getsid(space, pid):
    """ posix_getsid - Get the current sid of the process """
    try:
        return space.newint(os.getsid(pid))
    except OSError, e:
        space.set_errno(e.errno)
        return space.newbool(False)


@wrap(['space'])
def posix_getuid(space):
    """ posix_getuid - Return the real user ID of the current process """
    try:
        return space.newint(os.getuid())
    except OSError, e:
        space.set_errno(e.errno)
        return space.newbool(False)

@wrap(['space', str, int], error=False)
def posix_initgroups(space, name, base_group_id):
    """ posix_initgroups - Calculate the group access list """
    buf = rffi.str2charp(name)
    try:
        res = initgroups(buf, base_group_id)
        if res == -1:
            space.set_errno(rposix.get_errno())
            return space.w_False
        return space.w_True
    finally:
        lltype.free(buf, flavor='raw')

@wrap(['space', W_Root])
def posix_isatty(space, w_res):
    """ posix_isatty - Determine if a file descriptor is an
    interactive terminal """
    if not w_res.tp == space.tp_file_res:
        return space.newbool(False)
    try:
        assert isinstance(w_res, W_Resource)
        return space.newbool(os.isatty(w_res.resource.fileno()))
    except OSError, e:
        space.set_errno(e.errno)
        return space.newbool(False)


@wrap(['space', int, int], error=False)
def posix_kill(space, pid, sig):
    """ posix_kill - Send a signal to a process """
    try:
        os.kill(pid, sig)
        return space.newbool(True)
    except OSError, e:
        space.set_errno(e.errno)
        return space.newbool(False)
    except OverflowError:
        return space.newbool(False)


@wrap(['space', FilenameArg(None), int])
def posix_mkfifo(space, fname, mode):
    """ posix_mkfifo - Create a fifo special file (a named pipe) """
    try:
        os.mkfifo(fname, mode)
        return space.newbool(True)
    except OSError, e:
        space.set_errno(e.errno)
        return space.newbool(False)

""" posix_mknod - Create a special or ordinary file (POSIX.1) """


@wrap(['space', int], error=False)
def posix_setegid(space, gid):
    """ posix_setegid - Set the effective GID of the current process """
    try:
        os.setegid(gid)
        return space.newbool(True)
    except OSError, e:
        space.set_errno(e.errno)
        return space.newbool(False)
    except OverflowError:
        return space.newbool(False)


@wrap(['space', int], error=False)
def posix_seteuid(space, uid):
    """ posix_seteuid - Set the effective UID of the current process """
    try:
        os.seteuid(uid)
        return space.newbool(True)
    except OSError, e:
        space.set_errno(e.errno)
        return space.newbool(False)
    except OverflowError:
        return space.newbool(False)


@wrap(['space', int], error=False)
def posix_setgid(space, gid):
    """ posix_setgid - Set the GID of the current process """
    try:
        os.setgid(gid)
        return space.newbool(True)
    except OSError, e:
        space.set_errno(e.errno)
        return space.newbool(False)
    except OverflowError:
        return space.newbool(False)


@wrap(['space', LongArg(False), LongArg(False)])
def posix_setpgid(space, pid, pgrp):
    """ posix_setpgid - Set process group id for job control """
    try:
        os.setpgid(pid, pgrp)
        return space.newbool(True)
    except OSError, e:
        space.set_errno(e.errno)
        return space.newbool(False)


@wrap(['space'])
def posix_setsid(space):
    """ posix_setsid - Make the current process a session leader """
    try:
        os.setsid()
        return space.newbool(True)
    except OSError, e:
        space.set_errno(e.errno)
        return space.newbool(False)


@wrap(['space', int], error=False)
def posix_setuid(space, uid):
    """ posix_setuid - Set the UID of the current process """
    try:
        os.setuid(uid)
        return space.newbool(True)
    except OSError, e:
        space.set_errno(e.errno)
        return space.newbool(False)
    except OverflowError:
        return space.newbool(False)


@wrap(['space', int], error=False)
def posix_strerror(space, eno):
    """ posix_strerror - Retrieve the system error message associated
    with the given errno """
    try:
        return space.newstr(os.strerror(eno))
    except OverflowError:
        return space.newstr("Unknown error %s" % eno)


@wrap(['space'])
def posix_times(space):
    """ posix_times - Get process times """
    utime, stime, cu_time, cs_time, rtime = os.times()
    rdct_w = OrderedDict()
    rdct_w['ticks'] = space.newint(int(rtime))
    rdct_w['utime'] = space.newint(int(utime))
    rdct_w['stime'] = space.newint(int(stime))
    rdct_w['cutime'] = space.newint(int(cu_time))
    rdct_w['cstime'] = space.newint(int(cs_time))
    return space.new_array_from_rdict(rdct_w)


@wrap(['space', W_Root], error=False)
def posix_ttyname(space, w_res):
    """ posix_ttyname - Determine terminal device name """
    if not w_res.tp == space.tp_file_res:
        return space.newbool(False)
    try:
        assert isinstance(w_res, W_Resource)
        return space.newstr(os.ttyname(w_res.resource.fileno()))
    except TypeError:
        return space.newbool(False)


@wrap(['space'])
def posix_uname(space):
    """ posix_uname - Get system name """
    sysname, nodename, release, version, machine = os.uname()
    rdct_w = OrderedDict()
    rdct_w['sysname'] = space.newstr(sysname)
    rdct_w['nodename'] = space.newstr(nodename)
    rdct_w['release'] = space.newstr(release)
    rdct_w['version'] = space.newstr(version)
    rdct_w['machine'] = space.newstr(machine)
    return space.new_array_from_rdict(rdct_w)
