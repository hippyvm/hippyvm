from hippy.objects.instanceobject import W_InstanceObject
from hippy.klass import W_InvokeCall, def_class
from hippy.builtin import wrap_method, ThisUnwrapper
from hippy.function import Function

class W_CallClosure(W_InvokeCall):
    def __init__(self, klass, call_func, w_obj, closure):
        W_InvokeCall.__init__(self, klass, call_func, w_obj)
        self.closure = closure

    def call_args(self, interp, args_w, w_this=None, thisclass=None,
                  closureargs=None):
        closureargs = self.closure
        return self.call_func.call_args(interp, args_w, w_this=self.w_obj,
                                        thisclass=self.klass,
                                        closureargs=closureargs)

class W_ClosureObject(W_InstanceObject):
    def __init__(self, func, klass, storage_w, w_this=None, static=False):
        assert isinstance(func, Function)
        self._func = func
        self.closure_args = [None] * len(func.closuredecls)
        W_InstanceObject.__init__(self, klass, storage_w)
        self.w_this = w_this
        self.static = static

    def setattr(self, interp, attr, w_value, contextclass, unique_item=False):
        interp.catchable_fatal("Closure object cannot have properties")

    def setattr_ref(self, interp, attr, w_value, contextclass):
        interp.catchable_fatal("Closure object cannot have properties")

    def clone(self, interp, contextclass):
        w_res = W_ClosureObject(self._func, k_Closure,
                                self.storage_w[:], self.w_this, self.static)
        w_res.closure_args = self.closure_args[:]
        return w_res

    def get_callable(self):
        w_this = self.w_this if self.static is False else None
        thisclass = w_this.klass if w_this is not None else None
        return W_CallClosure(thisclass, self._func, w_this, self.closure_args)

    def put_closure(self, args_w):
        n = len(self.closure_args)
        for i, w_arg in enumerate(args_w):
            self.closure_args[n - i - 1] = w_arg

    def getmeth(self, space, name, contextclass=None):
        if name.lower() == "__invoke":
            return self.get_callable()
        return W_InstanceObject.getmeth(self, space, name, contextclass)

@wrap_method(['interp', ThisUnwrapper(W_ClosureObject), 'args_w'],
             name='Closure::__invoke')
def closure_invoke(interp, this, args_w):
    return this._func.call_args(interp, args_w)

k_Closure = def_class('Closure', [closure_invoke])

def new_closure(space, func, w_this, static=False):
    w_res = W_ClosureObject(func, k_Closure,
                            k_Closure.get_initial_storage_w(space)[:],
                            w_this=w_this, static=static)
    return w_res
