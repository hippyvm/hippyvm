from hippy import consts
from hippy.klass import def_class
from hippy.objects.instanceobject import W_InstanceObject
from hippy.builtin import wrap_method, ThisUnwrapper
from hippy.builtin_klass import GetterSetterWrapper



class W_ReflectionFunctionAbstractObject(W_InstanceObject):
    pass


@wrap_method(['interp', ThisUnwrapper(W_ReflectionFunctionAbstractObject)],
             name='ReflectionFunctionAbstract::getName')
def get_name(interp, this):
    return _get_name(interp, this)


def _get_class(interp, this):
    return interp.space.wrap(this.ref_klass.name)

def _set_class(interp, this, w_value):
    pass

def _get_name(interp, this):
    return interp.space.wrap(this.ref_method.get_name())

def _set_name(interp, this, w_value):
    pass


ReflectionFunctionAbstract = def_class(
    'ReflectionFunctionAbstract',
    [get_name],
    [GetterSetterWrapper(_get_class, _set_class, "class", consts.ACC_PUBLIC),
     GetterSetterWrapper(_get_name, _set_name, "name", consts.ACC_PUBLIC)],
    [],
    flags=consts.ACC_ABSTRACT,
    instance_class=W_ReflectionFunctionAbstractObject
)
