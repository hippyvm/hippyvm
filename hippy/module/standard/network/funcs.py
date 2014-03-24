import math
from hippy.builtin import wrap
from hippy.builtin import StringArg
from hippy.builtin import BoolArg
from hippy.builtin import LongArg
from hippy.builtin import Optional
from rpython.rlib import rsocket


def checkdnsrr():
    """Check DNS records corresponding to a given
    Internet host name or IP address"""
    return NotImplementedError()


def closelog():
    """ Close connection to system logger"""
    return NotImplementedError()


def define_syslog_variables():
    """ Initializes all syslog related variables"""
    return NotImplementedError()


def dns_check_record():
    """ Alias of checkdnsrr"""
    return NotImplementedError()


def dns_get_mx():
    """ Alias of getmxrr"""
    return NotImplementedError()


def dns_get_record():
    """ Fetch DNS Resource Records associated with a hostname"""
    return NotImplementedError()


def fsockopen():
    """ Open Internet or Unix domain socket connection"""
    return NotImplementedError()


@wrap(['space',  StringArg(None)])
def gethostbyaddr(space, ip_address):
    """ Get the Internet host name corresponding to a given IP address"""
    h, _, _ = rsocket.gethostbyaddr(ip_address)
    return space.newstr(h)


@wrap(['space',  StringArg(None)])
def gethostbyname(space, name):
    """ Get the IPv4 address corresponding to a given Internet host name"""
    h = rsocket.gethostbyname(name)
    return space.newstr(h.get_host())


@wrap(['space',  StringArg(None)])
def gethostbynamel(space, name):
    """ Get a list of IPv4 addresses corresponding
    to a given Internet host name"""
    h = rsocket.gethostbyname(name)
    return space.new_array_from_list([space.newstr(h.get_host())])


@wrap(['space'])
def gethostname(space):
    """ Gets the host name"""
    n = rsocket.gethostname()
    return space.newstr(n)


def getmxrr():
    """ Get MX records corresponding to a given Internet host name"""
    return NotImplementedError()


@wrap(['space',  StringArg(None)])
def getprotobyname(space, name):
    """ Get protocol number associated with protocol name"""
    n = rsocket.getprotobyname(name)
    return space.newint(n)


@wrap(['space',  LongArg(None)])
def getprotobynumber(space, pnum):
    """ Get protocol name associated with protocol number"""
    try:
        n = rsocket.getservbyport(pnum)
        return space.newstr(n)
    except rsocket.RSocketError:
        return space.w_False


@wrap(['space',  StringArg(None), StringArg(None)])
def getservbyname(space, name, proto):
    """ Get port number associated with an Internet service and protocol"""
    try:
        n = rsocket.getservbyname(name, proto)
        return space.newint(n)
    except rsocket.RSocketError:
        return space.w_False


@wrap(['space',  LongArg(None), StringArg(None)])
def getservbyport(space, port, proto):
    """ Get Internet service which corresponds to port and protocol"""
    try:
        n = rsocket.getservbyport(port, proto)
        return space.newstr(n)
    except rsocket.RSocketError:
        return space.w_False


def header_register_callback():
    """ Call a header function"""
    return NotImplementedError()


def header_remove():
    """ Remove previously set headers"""
    return NotImplementedError()


@wrap(['interp',  StringArg(None), Optional(BoolArg(None)), Optional(int)])
def header(interp, data, replace=True, response_code=0):
    """ Send a raw HTTP header"""
    assert response_code == 0
    interp.header(data, replace)


def headers_list():
    """ Returns a list of response headers sent(or ready to send)"""
    return NotImplementedError()


@wrap(['space'])
def headers_sent(space):
    """ Checks if or where headers have been sent"""
    return space.wrap(space.ec.interpreter.any_output)


def http_response_code():
    """ Get or Set the HTTP response code"""
    return NotImplementedError()


@wrap(['space',  StringArg(None)])
def inet_ntop(space, address):
    """ Converts a packed internet address
    to a human readable representation"""
    try:
        n = rsocket.inet_ntop(rsocket.AF_INET, address)
        return space.newstr(n)
    except rsocket.RSocketError:
        return space.w_False


@wrap(['space',  StringArg(None)])
def inet_pton(space, address):
    """ Converts a human readable IP
    address to its packed in_addr representation"""
    n = rsocket.inet_pton(rsocket.AF_INET, address)
    return space.newstr(n)


@wrap(['space',  StringArg(None)])
def ip2long(space, ipaddr):
    """ Converts a string containing an(IPv4) Internet Protocol
    dotted address into a proper address"""
    parts = ipaddr.split('.')
    if len(parts) != 4:
        return space.newbool(False)
    l = 0
    for i in range(len(parts) - 1, -1, -1):
        p = parts[i]
        try:
            l += int(p) * math.pow(256, i)
        except ValueError:
            return space.newbool(False)
    return space.newint(int(l))


@wrap(['space',  LongArg(None)])
def long2ip(space, l):
    """ Converts an(IPv4) Internet network address into a
    string in Internet standard dotted format"""
    ip = [l >> 24, l >> 16 & 0xFF, l >> 8 & 0xFF, l & 0xFF]
    return space.newstr('.'.join([str(x) for x in ip]))


def openlog():
    """ Open connection to system logger"""
    return NotImplementedError()


def pfsockopen():
    """ Open persistent Internet or Unix domain socket connection"""
    return NotImplementedError()


def setcookie():
    """ Send a cookie"""
    return NotImplementedError()


def setrawcookie():
    """ Send a cookie without urlencoding the cookie value"""
    return NotImplementedError()


def socket_get_status():
    """ Alias of stream_get_meta_data"""
    return NotImplementedError()


def socket_set_blocking():
    """ Alias of stream_set_blocking"""
    return NotImplementedError()


def socket_set_timeout():
    """ Alias of stream_set_timeout"""
    return NotImplementedError()


def syslog():
    """ Generate a system log message"""
    return NotImplementedError()
