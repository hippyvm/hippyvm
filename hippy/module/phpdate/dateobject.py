
from hippy.objects.instanceobject import W_InstanceObject
from hippy.builtin_klass import def_class
from hippy.builtin import wrap_method
from hippy.function import AbstractFunction, Function

# XXX maybe we don't need a special object, but it's kinda convinient
#     to have a _func attribute instead of fishing in a dict (that we
#     can't modify anyway)


class W_CallDate(AbstractFunction):
    def __init__(self, closure_obj):
        self.closure_obj = closure_obj

    def call_args(self, space, args_w, w_this=None, thisclass=None,
                  closureargs=None):
        closureargs = self.closure_obj.closure_args
        return self.closure_obj._func.call_args(space, args_w,
                                                closureargs=closureargs)


class W_DateObject(W_InstanceObject):
    def __init__(self, func, klass, dct_w):
        assert isinstance(func, Function)
        self._func = func
        self.closure_args = [None] * (len(func.names) - len(func.types))
        W_InstanceObject.__init__(self, klass, dct_w)

    def get_callable(self):
        return W_CallDate(self)


@wrap_method(['space', 'args_w'])
def closure_invoke(space, args_w):
    self = args_w[0]
    assert isinstance(self, W_DateObject)
    return self._func.call_args(space, args_w[1:])

def_class('Date',
        __invoke=closure_invoke,
)
