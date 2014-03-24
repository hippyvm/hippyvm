import os
from hippy.objects.resources import W_Resource

CLOSED, OPEN = range(2)


class W_DirResource(W_Resource):
    state = CLOSED

    resource_name = 'Directory'

    def __init__(self, space, dirname):
        W_Resource.__init__(self, space)
        self.dirname = dirname

    def as_number(self, space):
        return space.wrap(self.int_w(space))

    def create_dir_iter(self):
        return iter([".", ".."] + os.listdir(self.dirname))

    def open(self):
        try:
            self.dir_iter = self.create_dir_iter()
            self.state = OPEN
            self.space.ec.interpreter.last_dir_resource = self
            return self
        except OSError:
            self.space.ec.warn("opendir(%s): "
                               "failed to open dir: %s" %
                               (self.dirname, self.dirname))
            return self.space.newbool(False)

    def read(self):
        if self.state == CLOSED:
            return self.space.w_False
        try:
            return self.space.wrap(self.dir_iter.next())
        except StopIteration:
            return self.space.w_False

    def rewind(self):
        self.dir_iter = self.create_dir_iter()

    def close(self):
        self.state = CLOSED

    def is_valid(self):
        return self.state == OPEN

    def get_resource_type(self):
        if self.state == OPEN:
            return "stream"
        return "Unknown"

    def var_dump(self, space, indent, recursion):
        return "%sresource(%d) of type (%s)\n" % (indent,
                                                  self.res_id,
                                                  self.get_resource_type())
