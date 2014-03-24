
from hippy.objects.base import W_Root

class W_BaseIterator(W_Root):

    def done(self):
        return self.finished

    def next(self, space):
        raise NotImplementedError

    def next_item(self, space):
        raise NotImplementedError

class W_InstanceIterator(W_BaseIterator):
    def __init__(self, space, w_inst):
        self.w_inst = w_inst
        self.space = space
        interp = space.ec.interpreter
        interp.getmeth(w_inst, "rewind").call_args(interp, [])
        self.first_item = False
        self.w_valid = interp.getmeth(w_inst, "valid")
        self.w_key = interp.getmeth(w_inst, "key")
        self.w_current = interp.getmeth(w_inst, "current")
        self.w_next = None

    def next(self, space):
        interp = space.ec.interpreter
        w_val = self.w_current.call_args(interp, [])
        return w_val

    def next_item(self, space):
        interp = space.ec.interpreter
        w_val = self.w_current.call_args(interp, [])
        w_key = self.w_key.call_args(interp, [])
        return w_key, w_val

    def done(self):
        interp = self.space.ec.interpreter
        if self.w_next is None:
            self.w_next = interp.getmeth(self.w_inst, "next")
        else:
            self.w_next.call_args(interp, [])
        w_res = self.w_valid.call_args(interp, [])
        return not self.space.is_true(w_res)
