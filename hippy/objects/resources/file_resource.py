import os
from hippy.error import ConvertError
from hippy.objects.resources import W_Resource

CLOSE, OPEN, NONE = range(3)

class W_FileResource(W_Resource):

    def __init__(self, space, filename, mode):
        W_Resource.__init__(self, space)
        assert filename is not None
        self.filename = filename
        self.mode = mode
        self.state = NONE
        self.eof = False
        self.cur_line = None
        self.cur_line_no = 0
        self.first_line = None

    def open(self):
        self.resource = open(self.filename, self.mode)
        self.state = OPEN
        self.resource.seek(0)

    def close(self):
        try:
            self.resource.close()
            self.state = CLOSE
            return True
        except IOError:
            return False

    def read(self, size=1024):
        data = self.resource.read(size)
        if len(data) < size:
            self.eof = True
        return data

    def write(self, data, length):
        if length <= 0:
            return 0
        towrite = data[:length]
        self.resource.write(towrite)
        self.cur_line_no += towrite.count(os.linesep)
        return min(length, len(data))

    def writeall(self, data):
        self.resource.write(data)
        return len(data)

    def passthru(self):
        res = self.resource.read()
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
        return self.resource.seek(0, 0)

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
