from hippy.error import ConvertError
from hippy.objects.base import W_Object

CLOSED, OPEN = range(2)


class W_Resource(W_Object):

    state = CLOSED

    def __init__(self, space, res_id=-1):
        self.space = space
        if res_id == -1:
            self.res_id = space.get_new_res_id()
        else:
            self.res_id = res_id

    def int_w(self, space):
        return self.res_id

    def str(self, space, quiet=False):
        return "Resource id #%d" % self.res_id

    def as_int_arg(self, space):
        raise ConvertError('resource cannot be used as integer argument')

    def as_number(self, space):
        return space.wrap(self.int_w(space))

    def is_true(self, space):
        return self.is_valid()

    def is_valid(self):
        return self.state == OPEN

    def get_resource_type(self):
        if self.is_valid():
            return "stream"
        return "Unknown"

    def var_dump(self, space, indent, recursion):
        return "%s resource(%d) of type (%s)\n" % (indent,
                                                   self.res_id,
                                                   self.get_resource_type())

    def repr(self):
        return "Resource id #%d" % self.res_id

    def close(self):
        raise NotImplementedError

    def open(self):
        raise NotImplementedError

    def serialize(self, space, builder, memo):
        # I have no idea what number goes here, let's make it 0, it makes
        # no sense, because it's not like you can unserialize it
        builder.append("i:%d;" % 0)
        return True
