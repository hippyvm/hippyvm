import os
from collections import OrderedDict
from rpython.rlib.rsocket import (
    RSocket, SOCK_DGRAM, SOCK_STREAM, INETAddress, SocketTimeout, CSocketError)
from rpython.rlib.rstring import StringBuilder
from rpython.rlib.objectmodel import enforceargs

from hippy.objects.resources import W_Resource
from hippy.objects.resources.file_resource import W_FileResource


CLOSE, OPEN, NONE = range(3)
READ, WRITE = range(2)


class W_SocketResource(W_FileResource):

    def __init__(self, space, hostname, port, type='tcp', fd=0,
                 addr=None,
                 read_filters=[], write_filters=[],
                 errno=0, errstr=None,  timeout=None):
        W_Resource.__init__(self, space)
        # assert hostname is not None
        self.hostname = hostname
        self.port = port
        self.type = type
        self.mode = 'r+'
        self.fd = fd
        self.eof = False
        self.errno = errno
        self.errstr = errstr
        self.space = space
        self.addr = addr
        self.remote_addr = None
        self.state = CLOSE
        self.timed_out = False
        self.write_filters = write_filters
        self.write_filters_params = [space.w_Null] * len(write_filters)
        self.read_filters = read_filters
        self.read_filters_params = [space.w_Null] * len(read_filters)
        self.initialize()

    def initialize(self):
        type = SOCK_STREAM
        if self.type == 'udp':
            type = SOCK_DGRAM
        if self.fd:
            self.socket = RSocket(fd=self.fd)
            self.state = OPEN
        else:
            self.socket = RSocket(type=type)
            self.addr = INETAddress(self.hostname, self.port)
        self.space.ec.interpreter.register_fd(self)

    def settimeout(self, timeout):
        self.socket.settimeout(timeout)

    def accept(self):
        return self.socket.accept()

    def open(self):
        try:
            self.socket.connect(self.addr)
            self.state = OPEN
        except (SocketTimeout, CSocketError), e:
            self.errno = e.errno
            self.errstr = e.get_msg()

    def bind(self):
        try:
            self.socket.bind(self.addr)
            self.state = OPEN
        except CSocketError, e:
            self.errno = e.errno
            self.errstr = e.get_msg()

    def listen(self):
        self.socket.listen(1)

    def close(self):
        try:
            self.socket.close()
            self.state = CLOSE
            self.space.ec.interpreter.unregister_fd(self)
            return True
        except IOError:
            return False

    @enforceargs(None, str, None)
    def do_filter(self, data, direction):
        from hippy.module.standard.strings.funcs import _str_rot13
        from hippy.module.standard.strings.funcs import _chunk_split
        from hippy.module.base64 import b64_decode
        from hippy.module.base64 import b64_encode
        filters = self.write_filters
        params = self.write_filters_params
        if direction == READ:
            filters = self.read_filters
            params = self.read_filters_params
        for i, filter in enumerate(filters):
            w_params = params[i]
            for f in filter.split('|'):
                if f == 'string.rot13':
                    data = _str_rot13(data)
                elif f == 'string.toupper':
                    data = data.upper()
                elif f == 'string.tolower':
                    data = data.lower()
                elif f in ['convert.base64-encode', 'convert.base64-decode']:
                    line_length = 0
                    line_break = None
                    with self.space.iter(w_params) as w_iter:
                        while not w_iter.done():
                            w_key, w_val = w_iter.next_item(self.space)
                            if self.space.str_w(w_key) == 'line-length':
                                line_length = self.space.int_w(w_val)
                            if self.space.str_w(w_key) == 'line-break-chars':
                                line_break = self.space.str_w(w_val)
                    if f == 'convert.base64-encode':
                        data = b64_encode(data).rstrip()
                    else:
                        data = b64_decode(data).rstrip()
                    if line_length > 0:
                        data = _chunk_split(data, line_length,
                                            line_break, last_end=False)
        return data

    def read(self, size=1024):
        try:
            data = self.socket.recv(size)
        except (SocketTimeout, CSocketError):
            self.timed_out = True
            return ""
        assert data is not None
        data = self.do_filter(data, READ)
        if len(data) < size:
            self.eof = True
        return data

    @enforceargs(None, str, int)
    def write(self, data, length):
        if length <= 0:
            return 0
        towrite = self.do_filter(data[:length], WRITE)
        assert towrite is not None
        self.socket.send(towrite)
        self.cur_line_no += towrite.count(os.linesep)
        return min(length, len(data))

    @enforceargs(None, str)
    def writeall(self, data):
        towrite = self.do_filter(data, WRITE)
        assert towrite is not None
        self.socket.send(towrite)
        return len(data)

    def passthru(self):
        return 0

    def feof(self):
        return self.eof

    def seek(self, length, mode):
        pass

    def tell(self):
        """ this is done not in the php way
        in php position of pointer is kept in data structure
        so i.e seek during append mode does not call sytem tell"""
        return 0

    def readline(self, drop_nl=False):
        try:
            l = StringBuilder()
            c = self.socket.recv(1)
            l.append(c)
            while c != os.linesep:
                c = self.socket.recv(1)
                l.append(c)
                if not c:
                    self.eof = True
        except (SocketTimeout, CSocketError):
            self.timed_out = True
            return ""
        data = l.build()
        data = self.do_filter(data, READ)
        return data

    def seek_to_line(self, line, drop_nl=False):
        pass

    def flush(self):
        return True

    def rewind(self):
        pass

    def truncate(self, size):
        return True

    def is_valid(self):
        return self.state == OPEN

    def get_resource_type(self):
        if self.is_valid():
            return "stream"
        return "Unknown"

    def var_dump(self, space, indent, recursion):
        return "%s resource(%d) of type (%s)\n" % (
            indent, self.res_id, self.get_resource_type())

    def chmod(self, mode):
        pass

    def read_filters_append(self, filter):
        self.read_filters.append(filter)

    def write_filters_append(self, filter):
        self.write_filters.append(filter)

    def read_filters_params_append(self, w_params):
        self.read_filters_params.append(w_params)

    def write_filters_params_append(self, w_params):
        self.write_filters_params.append(w_params)

    def get_stream_type(self):
        return '%s_socket/ssl' % self.type

    def get_seekable(self):
        return False

    def get_timed_out(self):
        return self.timed_out

    def get_blocked(self):
        return True

    def get_meta_data(self):
        rdict_w = OrderedDict()
        space = self.space
        stats = [
            ("stream_type", space.newstr(self.get_stream_type())),
            ("mode", space.newstr(self.mode)),
            ("unread_bytes", space.newint(0)),
            ("seekable", space.newbool(self.get_seekable())),
            ("timed_out", space.newbool(self.get_timed_out())),
            ("blocked", space.newbool(self.get_blocked())),
            ("eof", space.newbool(self.eof)),
        ]
        for label, stat in stats:
            rdict_w[label] = stat
        return space.new_array_from_rdict(rdict_w)

    def get_name(self, remote):
        addr = self.socket.getsockname()
        if remote:
            try:
                addr = self.socket.getpeername()
            except CSocketError:
                return self.space.w_False
        return self.space.newstr('%s:%s' % (addr.get_host(), addr.get_port()))
