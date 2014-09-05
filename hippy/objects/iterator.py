
from hippy.objects.base import W_Root

class BaseIterator(W_Root):

    def done(self):
        return self.finished

    def next(self, space):
        raise NotImplementedError

    def next_item(self, space):
        raise NotImplementedError

    def current(self, interp):
        raise NotImplementedError

    def move_forward(self, interp):
        raise NotImplementedError

    def key(self, interp):
        raise NotImplementedError

    def rewind(self, interp):
        raise NotImplementedError

    def valid(self, interp):
        return not self.finished


class InstanceIterator(BaseIterator):
    def __init__(self, space, w_inst):
        self.w_inst = w_inst
        self.space = space
        interp = space.ec.interpreter
        self.rewind(interp)
        self.first_item = False
        self.w_valid = interp.getmeth(w_inst, "valid")
        self.w_key = interp.getmeth(w_inst, "key")
        self.w_current = interp.getmeth(w_inst, "current")
        self.w_next = None

    def next(self, space):
        interp = space.ec.interpreter
        return self.current(interp)

    def next_item(self, space):
        interp = space.ec.interpreter
        w_value = self.current(interp)
        return self.key(interp), w_value

    def done(self):
        interp = self.space.ec.interpreter
        if self.w_next is None:
            self.w_next = interp.getmeth(self.w_inst, "next")
        else:
            self.w_next.call_args(interp, [])
        return not self.valid(interp)

    def current(self, interp):
        return self.w_current.call_args(interp, [])

    def key(self, interp):
        return self.w_key.call_args(interp, [])

    def rewind(self, interp):
        interp.call_method(self.w_inst, "rewind", [])

    def valid(self, interp):
        w_res = self.w_valid.call_args(interp, [])
        return self.space.is_true(w_res)
