import os
from hippy.objects.resources import W_Resource
from rpython.rlib.rStringIO import RStringIO
from rpython.rlib.rfile import RFile
from rpython.rlib.objectmodel import import_from_mixin
from collections import OrderedDict


class RMemoryFile(RFile):
    import_from_mixin(RStringIO)

    def flush(self):
        pass

    def close(self):
        return 1


CLOSE, OPEN, NONE = range(3)
READ, WRITE = range(2)


class W_FileResource(W_Resource):

    def __init__(self, space, filename, mode,
                 read_filters=[], write_filters=[], res_id=-1):
        W_Resource.__init__(self, space, res_id)
        assert filename is not None
        self.filename = filename
        self.mode = mode
        self.state = NONE
        self.space = space
        self.resource = None
        self.eof = False
        self.cur_line = None
        self.cur_line_no = 0
        self.first_line = None
        self.write_filters = write_filters
        self.write_filters_params = [space.w_Null] * len(write_filters)
        self.read_filters = read_filters
        self.read_filters_params = [space.w_Null] * len(read_filters)

    def open(self):
        if self.filename == 'php://memory':
            self.resource = RMemoryFile()
        elif self.filename == 'php://stdin':
            self.resource = os.fdopen(os.dup(0), 'r')
        elif self.filename == 'php://stdout':
            self.resource = os.fdopen(os.dup(1), 'w')
        elif self.filename == 'php://output':
            self.resource = os.fdopen(os.dup(1), 'w')
        elif self.filename == 'php://stderr':
            self.resource = os.fdopen(os.dup(2), 'w')
        elif self.filename == 'php://temp':
            self.resource = os.tmpfile()
        elif self.filename.startswith('php://fd/'):
            fd = self.filename[len('php://fd/'):]
            self.resource = os.fdopen(os.dup(int(fd)), self.mode)
        else:
            self.resource = open(self.filename, self.mode)
            self.resource.seek(0, 0)
        self.state = OPEN
        self.space.ec.interpreter.register_fd(self)

    def close(self):
        try:
            self.resource.close()
            self.state = CLOSE
            self.space.ec.interpreter.unregister_fd(self)
            return True
        except IOError:
            return False

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
        data = self.resource.read(size)
        data = self.do_filter(data, READ)
        if len(data) < size:
            self.eof = True
        return data

    def write(self, data, length):
        if length <= 0:
            return 0
        towrite = self.do_filter(data[:length], WRITE)
        self.resource.write(towrite)
        self.cur_line_no += towrite.count(os.linesep)
        return min(length, len(data))

    def writeall(self, data):
        towrite = self.do_filter(data, WRITE)
        self.resource.write(towrite)
        return len(data)

    def passthru(self):
        res = self.resource.read(-1)
        res = self.do_filter(res, READ)
        self.space.ec.interpreter.writestr(res)
        return len(res)

    def feof(self):
        return self.eof

    def seek(self, length, mode):
        self.eof = False
        self.resource.seek(length, mode)

    def tell(self):
        """ this is done not in the php way
        in php position of pointer is kept in data structure
        so i.e seek during append mode does not call sytem tell"""
        return self.resource.tell()

    def readline(self, drop_nl=False):
        data = self.resource.readline()
        to_add = 0
        if self.cur_line:
            to_add = 1
        if not data or data[-1] != '\n':
            self.eof = True
        if drop_nl:
            i = data.find(os.linesep)
            if i > 0:
                data = data[:i]
        self.cur_line = data
        self.cur_line_no += to_add
        return data

    def seek_to_line(self, line, drop_nl=False):
        self.rewind()
        while self.cur_line_no < line and not self.feof():
            x = self.readline(drop_nl)
            if not x:
                break

    def flush(self):
        try:
            self.resource.flush()
            return True
        except OSError:
            return False

    def rewind(self):
        self.eof = False
        self.cur_line = None
        self.cur_line_no = 0
        self.resource.seek(0, 0)

    def truncate(self, size):
        try:
            self.resource.truncate(size)
            return True
        except OSError:
            return False

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
        os.chmod(self.filename, mode)

    def read_filters_append(self, filter):
        self.read_filters.append(filter)

    def write_filters_append(self, filter):
        self.write_filters.append(filter)

    def read_filters_params_append(self, w_params):
        self.read_filters_params.append(w_params)

    def write_filters_params_append(self, w_params):
        self.write_filters_params.append(w_params)

    def get_wrapper_type(self):
        return 'plainfile'

    def get_stream_type(self):
        return 'STDIO'

    def get_seekable(self):
        return True

    def get_timed_out(self):
        return False

    def get_blocked(self):
        return True

    def get_meta_data(self):
        rdict_w = OrderedDict()
        space = self.space
        stats = [
            ("wrapper_type", space.newstr(self.get_wrapper_type())),
            ("stream_type", space.newstr(self.get_stream_type())),
            ("mode", space.newstr(self.mode)),
            ("unread_bytes", space.newint(0)),
            ("seekable", space.newbool(self.get_seekable())),
            ("uri", space.newstr(self.filename)),
            ("timed_out", space.newbool(self.get_timed_out())),
            ("blocked", space.newbool(self.get_blocked())),
            ("eof", space.newbool(self.eof)),
        ]
        for label, stat in stats:
            rdict_w[label] = stat
        return space.new_array_from_rdict(rdict_w)

    def get_name(self, remote):
        return self.space.w_False


class W_STDIN(W_FileResource):
    def __init__(self, space):
        W_FileResource.__init__(self, space, 'php://stdin', 'w', res_id=1)


class W_STDOUT(W_FileResource):
    def __init__(self, space):
        W_FileResource.__init__(self, space, 'php://stdout', 'w', res_id=2)


class W_STDERR(W_FileResource):
    def __init__(self, space):
        W_FileResource.__init__(self, space, 'php://stderr', 'w', res_id=3)
