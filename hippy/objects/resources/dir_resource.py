import os
from hippy.objects.resources import W_Resource

CLOSED, OPEN = range(2)


class W_DirResource(W_Resource):
    state = CLOSED

    resource_name = 'Directory'

    def __init__(self, space, dirname, skip_dots=False):
        W_Resource.__init__(self, space)
        self.dirname = dirname
        self.index = 0
        self.items = []
        self.skip_dots = skip_dots

    def as_number(self, space):
        return space.wrap(self.int_w(space))

    def create_dir_iter(self):
        if self.skip_dots:
            self.items = os.listdir(self.dirname)
        else:
            self.items = os.listdir(self.dirname) + ['.', '..']
        self.index = 0
        self.no_of_items = len(self.items)
        return iter(self.items)

    def open(self):
        try:
            self.dir_iter = self.create_dir_iter()
            self.state = OPEN
            self.space.ec.interpreter.last_dir_resource = self
            self.space.ec.interpreter.register_fd(self)
            return self
        except OSError:
            self.space.ec.warn("opendir(%s): "
                               "failed to open dir: %s" %
                               (self.dirname, self.dirname))
            return self.space.newbool(False)

    def read(self):
        if self.state == CLOSED:
            return self.space.w_False
        self.index += 1
        try:
            item = self.dir_iter.next()
            return self.space.wrap(item)
        except StopIteration:
            return self.space.w_False

    def rewind(self):
        self.dir_iter = self.create_dir_iter()

    def seek_to_item(self, pos):
        if self.index > pos:
            self.rewind()
        while self.index < self.no_of_items and self.index < pos:
            self.read()

    def close(self):
        self.space.ec.interpreter.unregister_fd(self)
        self.state = CLOSED
        return True

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
