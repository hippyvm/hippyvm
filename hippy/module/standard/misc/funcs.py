from rpython.rlib.rstring import StringBuilder
from rpython.rtyper.lltypesystem import lltype, rffi
from rpython.rlib.rarithmetic import intmask
from rpython.rlib.rrandom import Random
from hippy.builtin import wrap, Optional, BoolArg
from hippy.objects.base import W_Root
from hippy.module.date import timelib
_random = Random()


def connection_aborted():
    """ Check whether client disconnected"""
    return NotImplementedError()


def connection_status():
    """ Returns connection status bitfield"""
    return NotImplementedError()


def connection_timeout():
    """ Check if the script timed out"""
    return NotImplementedError()


def _lookup_constant(space, constname):
    i = constname.find(':')
    if i < 0:
        return space.ec.interpreter.constants.get(constname, None)
    elif i + 1 < len(constname) and constname[i + 1] == ':':
        clsname = constname[:i]
        realname = constname[i + 2:]
        klass = space.ec.interpreter.lookup_class_or_intf(clsname)
        if klass is not None:
            return klass.constants_w.get(realname, None)
    return None


@wrap(['space', str])
def constant(space, constname):
    """ Returns the value of a constant"""
    w_obj = _lookup_constant(space, constname)
    if w_obj is None:
        space.ec.warn("constant(): Couldn't find constant %s" % constname)
        return space.w_Null
    return w_obj


@wrap(['space', str, W_Root, Optional(bool)])
def define(space, name, w_obj, case_insensitive=False):
    """ Defines a named constant"""
    if name in space.ec.interpreter.constants:
        space.ec.notice("Constant %s already defined" % name)
        return space.w_False
    space.ec.interpreter.constants[name] = w_obj
    return space.w_True


@wrap(['space', str])
def defined(space, name):
    """ Checks whether a given named constant exists"""
    return space.newbool(_lookup_constant(space, name) is not None)


def die():
    """ Equivalent to exit"""
    return NotImplementedError()


def eval():
    """ Evaluate a string as PHP code"""
    return NotImplementedError()


def exit():
    """ Output a message and terminate the current script"""
    return NotImplementedError()


def get_browser():
    """ Tells what the user's browser is capable of"""
    return NotImplementedError()


def __halt_compiler():
    """ Halts the compiler execution"""
    return NotImplementedError()


def highlight_file():
    """ Syntax highlighting of a file"""
    return NotImplementedError()


def highlight_string():
    """ Syntax highlighting of a string"""
    return NotImplementedError()


def ignore_user_abort():
    """ Set whether a client disconnect should abort script execution"""
    return NotImplementedError()


def pack():
    """ Pack data into binary string"""
    return NotImplementedError()


def php_check_syntax():
    """ Check the PHP syntax of (and execute) the specified file"""
    return NotImplementedError()


def php_strip_whitespace():
    """ Return source with stripped comments and whitespace"""
    return NotImplementedError()


def show_source():
    """ Alias of highlight_file"""
    return NotImplementedError()


def sleep():
    """ Delay execution"""
    return NotImplementedError()


def sys_getloadavg():
    """ Gets system load average"""
    return NotImplementedError()


def time_nanosleep():
    """ Delay for a number of seconds and nanoseconds"""
    return NotImplementedError()


def time_sleep_until():
    """ Make the script sleep until the specified time"""
    return NotImplementedError()


def _zero_pad(s, c):
    l = len(s)
    if l > c:
        return s
    return "0" * (c - l) + s


@wrap(['space', Optional(str), Optional(BoolArg(None))])
def uniqid(space, prefix='', more_entropy=False):
    """ Generate a unique ID"""

    timeval = lltype.malloc(timelib.timeval, flavor='raw')
    void = lltype.nullptr(rffi.VOIDP.TO)
    timelib.c_gettimeofday(timeval, void)
    sec = intmask(timeval.c_tv_sec)
    usec = intmask(timeval.c_tv_usec)
    builder = StringBuilder()
    if prefix:
        builder.append(prefix)
    builder.append(_zero_pad(hex(sec)[2:], 8))
    builder.append(_zero_pad(hex(usec)[2:], 5))
    if more_entropy:
        builder.append(".")
        builder.append(str(_random.random())[2:11])
    return space.newstr(builder.build())


def unpack():
    """ Unpack data from binary string"""
    return NotImplementedError()


def usleep():
    """ Delay execution in microseconds"""
    return NotImplementedError()
