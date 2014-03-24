
from hippy.builtin import Optional, wrap
from hippy.builtin import StringArg
from hippy.builtin import BoolArg
from hippy.module.base64 import b64_decode
from hippy.module.base64 import b64_encode
from rpython.rlib.rstring import StringBuilder
from rpython.rlib.unroll import unrolling_iterable
from collections import OrderedDict


CONTROL_CHARS = tuple("\007\b\t\n\v\f\r\1\2\3\4\5\6\16\17\20\21\22\23\24\
\25\26\27\30\31\32\33\34\35\36\37\177".split(" "))


class URLResult(object):
    def __init__(self, scheme=None, host=None, port=-1, user=None,
                 password=None, path=None, query=None, fragment=None):
        self.scheme = scheme
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.path = path
        self.query = query
        self.fragment = fragment

    def sanitize(self, s):
        res = StringBuilder(len(s))
        for c in s:
            if c in CONTROL_CHARS:
                res.append('_')
            else:
                res.append(c)
        return res.build()

    def wrap(self, space):
        rdct_w = OrderedDict()
        if self.scheme is not None:
            rdct_w['scheme'] = space.newstr(
                self.sanitize(self.scheme))
        if self.host is not None:
            rdct_w['host'] = space.newstr(
                self.sanitize(self.host))
        if self.port != -1:
            rdct_w['port'] = space.newint(self.port)
        if self.user is not None:
            rdct_w['user'] = space.newstr(
                self.sanitize(self.user))
        if self.password is not None:
            rdct_w['pass'] = space.newstr(
                self.sanitize(self.password))
        if self.path is not None:
            rdct_w['path'] = space.newstr(
                self.sanitize(self.path))
        if self.query is not None:
            rdct_w['query'] = space.newstr(
                self.sanitize(self.query))
        if self.fragment is not None:
            rdct_w['fragment'] = space.newstr(
                self.sanitize(self.fragment))
        return space.new_array_from_rdict(rdct_w)

    def parse(self, s):
        pos_s = 0
        pos_ue = len(s)
        pos_e = s.find(':')
        if pos_e >= 1:
            pos_p = pos_s
            while pos_p < pos_e:
                c = s[pos_p]
                if not is_valid_scheme(c):
                    if pos_e + 1 < pos_ue:
                        return self._parse_port(s, pos_s, pos_e, pos_ue)
                    else:
                        return self._just_path(s, pos_s)
                pos_p += 1
            # scheme is valid
            if pos_e == len(s) - 1:
                # just scheme
                self.scheme = s[pos_s:pos_e]
                return self
            if s[pos_e + 1] != '/':
                pos_p = pos_e + 1
                while pos_p < len(s) and s[pos_p].isdigit():
                    pos_p += 1
                if ((pos_p == len(s) or s[pos_p] == '/') and
                    pos_p - pos_e < 7):
                    return self._parse_port(s, pos_s, pos_e, pos_ue)
                self.scheme = s[pos_s:pos_e]
                return self._just_path(s, pos_e + 1)
            else:
                self.scheme = s[:pos_e]
                if s[pos_e + 2] == '/':
                    pos_s = pos_e + 3
                    if self.scheme.lower() == 'file':
                        if pos_s < len(s) and s[pos_s] == '/':
                            if pos_s + 2 < len(s) and s[pos_s + 2] == ':':
                                pos_s = pos_e + 4
                            return self._nohost(s, pos_s, pos_ue)
                else:
                    if self.scheme.lower() == 'file':
                        return self._nohost(s, pos_e + 1, pos_ue)
                    else:
                        return self._just_path(s, pos_e + 1)
        elif pos_e == 0:
            # just port
            return self._parse_port(s, pos_s, pos_e, pos_ue)
        elif s[pos_s] == '/' and pos_s + 1 < len(s) and s[pos_s + 1] == '/':
            pos_s += 2
        else:
            return self._just_path(s, pos_s)

        return self._rest(s, pos_s, pos_ue)

    def _parse_port_fragment(self, frag):
        for i, c in enumerate(frag):
            if not c.isdigit():
                frag = frag[:i]
                break
        try:
            port = int(frag)
        except ValueError:
            raise UrlParseException("invalid url")
        if 0 < port <= 65536:
            return port
        else:
            raise UrlParseException("invalid url")

    def _parse_port(self, s, pos_s, pos_e, pos_ue):
        pos_p = pos_e + 1
        pos_pp = pos_p

        while pos_pp - pos_p < 6 and pos_pp < len(s) and s[pos_pp].isdigit():
            pos_pp += 1

        if (pos_pp > pos_p and pos_pp - pos_p < 6 and
            (pos_pp == len(s) or s[pos_pp] == '/')):
            self.port = self._parse_port_fragment(s[pos_p:pos_pp])
        elif pos_p == pos_pp and pos_pp == len(s):
            raise UrlParseException("invalid url")
        elif s[pos_s] == '/' and pos_s + 1 < len(s) and s[pos_s + 1] == '/':
            pos_s += 2
        else:
            return self._just_path(s, pos_s)
        return self._rest(s, pos_s, pos_ue)

    def _rest(self, s, pos_s, pos_ue):
        pos_e = pos_ue
        pos_p = s.find('/', pos_s)

        if pos_p < 0:
            query_pos = s.find('?', pos_s)
            fragment_pos = s.find('#', pos_s)
            if query_pos >= 0 and fragment_pos >= 0:
                if query_pos > fragment_pos:
                    pos_e = fragment_pos
                else:
                    pos_e = query_pos
            elif query_pos >= 0:
                pos_p = pos_e = query_pos
            elif fragment_pos >= 0:
                pos_p = pos_e = fragment_pos
        else:
            pos_e = pos_p

        pos_p = s.rfind('@', pos_s, pos_e)
        if pos_p >= 0:
            pos_pp = s.find(':', pos_s, pos_p)
            if pos_pp >= 0:
                if pos_pp > pos_s:
                    self.user = s[pos_s:pos_pp]
                pos_pp += 1
                if pos_p > pos_pp:
                    self.password = s[pos_pp:pos_p]
            else:
                self.user = s[pos_s:pos_p]
            pos_s = pos_p + 1

        if s[pos_s] == '[' and s[pos_e - 1] == ']':
            pos_p = pos_s
        else:
            pos_p = s.rfind(':', pos_s, pos_e)

        if pos_p >= pos_s and s[pos_p] == ':':
            if self.port == -1:
                pos_p += 1
                if pos_e - pos_p > 5:
                    raise UrlParseException("invalid url")
                elif pos_e - pos_p > 0:
                    self.port = self._parse_port_fragment(s[pos_p:pos_e])
                pos_p -= 1
        else:
            pos_p = pos_e

        if pos_p - pos_s < 1:
            raise UrlParseException("wrong url")

        assert pos_s >= 0
        assert pos_p >= 0

        self.host = s[pos_s:pos_p]

        if pos_e == pos_ue:
            return self

        return self._nohost(s, pos_e, pos_ue)

    def _nohost(self, s, pos_s, pos_ue):
        pos_p = s.find('?', pos_s, pos_ue)
        if pos_p >= 0:
            pos_pp = s.find('#')
            if pos_pp >= 0 and pos_pp < pos_p:
                if pos_pp != pos_s:
                    self.path = s[pos_s:pos_pp]
                return self._label_parse(s, pos_pp, pos_ue)
            if pos_p != pos_s:
                self.path = s[pos_s:pos_p]
            if pos_pp >= 0:
                pos_p += 1
                if pos_pp != pos_p:
                    self.query = s[pos_p:pos_pp]
                return self._label_parse(s, pos_pp, pos_ue)
            else:
                pos_p += 1
                if pos_p != pos_ue:
                    self.query = s[pos_p:pos_ue]
        else:
            pos_p = s.find('#', pos_s, pos_ue)
            if pos_p >= 0:
                if pos_s != pos_p:
                    self.path = s[pos_s:pos_p]
                return self._label_parse(s, pos_p, pos_ue)
            else:
                self.path = s[pos_s:pos_ue]
        return self

    def _label_parse(self, s, pos_p, pos_ue):
        pos_p += 1
        if pos_ue != pos_p:
            self.fragment = s[pos_p:pos_ue]
        return self

    def _just_path(self, s, pos_s):
        return self._nohost(s, pos_s, pos_s + len(s))


@wrap(['space', StringArg(None), Optional(BoolArg(None))])
def base64_decode(space, data, strict=False):
    res = b64_decode(data, strict)
    if res is None:
        return space.w_False
    return space.wrap(res)


@wrap(['space', StringArg(None)])
def base64_encode(space, data):
    res = b64_encode(data)
    if res is None:
        return space.w_False
    return space.wrap(res[:-1])


class UrlParseException(Exception):
    pass


def is_valid_scheme(c):
    return c.isalpha() or c.isdigit() or c == '+' or c == '-' or c == '.'


def urlsplit(url, scheme='', allow_fragments=True):
    """Parse a URL into 5 components:
    <scheme>://<netloc>/<path>?<query>#<fragment>
    Return a 5-tuple: (scheme, netloc, path, query, fragment).
    Note that we don't break the components up in smaller bits
    (e.g. netloc is a single string) and we don't expand % escapes."""

    SCHEME, NETLOC = range(2)

    if not url:
        return URLResult(path='')

    return URLResult().parse(url)

URL_COMPONENTS = unrolling_iterable(enumerate(
    ['scheme', 'host', None, 'user', 'password', 'path', 'query', 'fragment']))


@wrap(['space', StringArg(None), Optional(int)])
def parse_url(space, url, component=-1):
    try:
        res = urlsplit(url)
    except UrlParseException:
        return space.w_False
    if component <= -1:
        return res.wrap(space)
    if component > 7 or component < 0:
        space.ec.warn("parse_url(): Invalid URL component identifier %d"
                      % component)
        return space.w_False
    if component == 2:  # port is special
        if res.port == -1:
            return space.w_Null
        return space.newint(res.port)
    if component == 0:
        if res.scheme is None:
            return space.w_Null
        return space.newstr(res.sanitize(res.scheme))
    if component == 1:
        if res.host is None:
            return space.w_Null
        return space.newstr(res.sanitize(res.host))
    if component == 3:
        if res.user is None:
            return space.w_Null
        return space.newstr(res.sanitize(res.user))
    if component == 4:
        if res.password is None:
            return space.w_Null
        return space.newstr(res.sanitize(res.password))
    if component == 5:
        if res.path is None:
            return space.w_Null
        return space.newstr(res.sanitize(res.path))
    if component == 6:
        if res.query is None:
            return space.w_Null
        return space.newstr(res.sanitize(res.query))
    if component == 7:
        if res.fragment is None:
            return space.w_Null
        return space.newstr(res.sanitize(res.fragment))
    assert False

HEXCHARS = ['0', '1', '2', '3', '4', '5', '6', '7',
            '8', '9', 'A', 'B', 'C', 'D', 'E', 'F']


def _ishexdigit(c):
    if '0' <= c <= '9' or\
       'A' <= c <= 'F' or\
       'a' <= c <= 'f':
        return True
    return False


@wrap(['space', StringArg(None)], aliases=['urlencode'])
def rawurlencode(space, url):
    res = StringBuilder(len(url))
    for c in url:
        if (c < '0' and c != '-' and c != '.') or \
           (c < 'A' and c > '9') or \
           (c > 'Z' and c < 'a' and c != '_') \
           or (c > 'z' and c != '~'):
            res.append('%')
            res.append(HEXCHARS[ord(c) >> 4])
            res.append(HEXCHARS[ord(c) & 15])
        else:
            res.append(c)
    return space.wrap(res.build())


def _decode(c):
    if 'a' <= c <= 'f':
        return ord(c) - ord('a') + 10
    if 'A' <= c <= 'F':
        return ord(c) - ord('A') + 10
    return ord(c) - ord('0')

def _urldecode(url):
    res = StringBuilder(len(url))
    l = len(url)
    i = 0
    while i < l:
        c = url[i]
        if (c == '%' and (i < l - 2) and _ishexdigit(url[i + 1]) and
            _ishexdigit(url[i + 2])):
            k = (_decode(url[i + 1]) << 4) + _decode(url[i + 2])
            res.append(chr(k))
            i += 3
        else:
            res.append(url[i])
            i += 1
    return res.build()
    
@wrap(['space', StringArg(None)], aliases=['rawurldecode'])
def urldecode(space, url):
    return space.wrap(_urldecode(url))
