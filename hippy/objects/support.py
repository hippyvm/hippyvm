
import operator

def _new_binop(cls, name, vfield, is_comparison):
    def func(self, space, w_other):
        assert isinstance(w_other, cls)
        v = getattr(operator, name)(
            getattr(self, vfield),
            getattr(w_other, vfield))
        if is_comparison:
            return space.newbool(v)
        return cls(v)
    func.func_name = name
    return func
