import math
from hippy.builtin import wrap
from hippy.builtin import StringArg
from hippy.builtin import BoolArg
from hippy.builtin import LongArg
from hippy.builtin import Optional
from rpython.rlib import rsocket
from rpython.rlib.rstring import StringBuilder
from hippy.module.date.funcs import _strftime
from hippy.objects.resources.socket_resource import W_SocketResource
from hippy.module.url import urlsplit, _rawurlencode


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


@wrap(['interp',  StringArg(None), Optional(int), Optional('reference'),
       Optional('reference'), Optional(float)], error=False)
def fsockopen(interp, hostname, port=-1, w_ref_errno=None,
              w_ref_errstr=None, timeout=-1):
    """ Open Internet or Unix domain socket connection"""
    space = interp.space
    r = urlsplit(hostname)
    host = r.host
    if not host:
        host = r.path
    if port == -1:
        port = r.port
    type = 'tcp'
    if r.scheme:
        type = r.scheme
    cstring = "%s://%s:%d" % (type, host, port)
    if type not in ['tcp', 'udp']:
        s = 'Unable to find the socket transport "%s" - did you forget to enable it when you configured PHP?'
        out = s % type
        if w_ref_errstr is not None:
            w_ref_errstr.store(space.wrap(out))
        space.ec.warn("fsockopen(): unable to connect to %s (%s)" % (cstring, out))
        return space.w_False
    w_res = W_SocketResource(space, host, port, type)
    if timeout == -1:
        w_timeout = interp.config.get_ini_w('default_socket_timeout')
        timeout = interp.space.float_w(w_timeout)
    w_res.open()
    w_res.settimeout(timeout)
    if w_ref_errno is not None:
        w_ref_errno.store(space.wrap(w_res.errno))
    if w_ref_errstr is not None:
        w_ref_errstr.store(space.wrap(w_res.errstr))
    if w_res.errno != 0:
        space.ec.warn("fsockopen(): unable to connect to %s (%s)" %
                      (cstring, w_res.errstr))
        return space.w_False
    return w_res


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
    ignore = False
    if data.startswith('Location:'):
        act = interp.http_status_code
        if (act < 300 or act > 307) and act != 201:
            interp.http_status_code = 302
    if data.startswith('HTTP/'):
        response_code = int(data.split(' ')[1])
        ignore = True
    if response_code:
        interp.http_status_code = response_code
    if not ignore:
        interp.header(data, replace)


@wrap(['interp'])
def headers_list(interp):
    """ Returns a list of response headers sent(or ready to send)"""
    l = []
    space = interp.space
    for h in interp.headers:
        l.append(space.wrap(h))
    return space.new_array_from_list(l)


@wrap(['space'])
def headers_sent(space):
    """ Checks if or where headers have been sent"""
    return space.wrap(space.ec.interpreter.any_output)


@wrap(['interp', Optional(int)])
def http_response_code(interp, code=0):
    """ Get or Set the HTTP response code"""
    act = interp.http_status_code
    if code:
        interp.http_status_code = code
        if act != -1:
            return interp.space.wrap(act)
        return interp.space.w_True
    else:
        if act == -1:
            return interp.space.w_False
        return interp.space.wrap(act)


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


@wrap(['interp', str, Optional(str), Optional(int),
       Optional(str), Optional(str),
       Optional(bool), Optional(bool)])
def setcookie(interp, name, value="", expire=0, path=None,
              domain=None, secure=False, httponly=False):
    """ Send a cookie"""
    c = StringBuilder()
    c.append("Set-Cookie: %s=%s" % (name, _rawurlencode(value)))
    if expire > 0:
        d = _strftime(interp, True, '%a, %d %b %Y %H:%M:%S', expire)
        c.append("; Expires=%s" % d)
    if path:
        c.append("; Path=%s" % path)
    if secure:
        c.append("; Secure")
    if httponly:
        c.append("; HttpOnly")
    interp.header(c.build(), True, True)
    return interp.space.w_True


def setrawcookie():
    """ Send a cookie without urlencoding the cookie value"""
    return NotImplementedError()


def socket_get_status():
    """ Alias of stream_get_meta_data"""
    return NotImplementedError()


def socket_set_blocking():
    """ Alias of stream_set_blocking"""
    return NotImplementedError()


def syslog():
    """ Generate a system log message"""
    return NotImplementedError()
