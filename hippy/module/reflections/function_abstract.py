from hippy import consts
from hippy.klass import def_class
from hippy.objects.instanceobject import W_InstanceObject
from hippy.builtin_klass import GetterSetterWrapper


class W_ReflectionFunctionAbstract(W_InstanceObject):
    pass


def _get_class(interp, this):
    return interp.space.wrap(this.ref_klass.name)

def _set_class(interp, this, w_value):
    pass

def _get_name(interp, this):
    return interp.space.wrap(this.ref_method.get_name())

def _set_name(interp, this, w_value):
    pass


k_ReflectionFunctionAbstract = def_class(
    'ReflectionFunctionAbstract',
    ["getName"],
    [GetterSetterWrapper(_get_class, _set_class, "class", consts.ACC_PUBLIC),
     GetterSetterWrapper(_get_name, _set_name, "name", consts.ACC_PUBLIC)],
    [],
    flags=consts.ACC_ABSTRACT,
    instance_class=W_ReflectionFunctionAbstract
)


@k_ReflectionFunctionAbstract.def_method(['interp', 'this'])
def getName(interp, this):
    return _get_name(interp, this)
