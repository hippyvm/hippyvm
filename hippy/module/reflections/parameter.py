from hippy import consts
from hippy.klass import def_class
from hippy.objects.base import W_Root
from hippy.objects.instanceobject import W_InstanceObject
from hippy.objects.strobject import W_ConstStringObject
from hippy.builtin import wrap_method, ThisUnwrapper
from hippy.builtin_klass import GetterSetterWrapper


class W_ReflectionParameterObject(W_InstanceObject):
    pass


@wrap_method(['interp', ThisUnwrapper(W_ReflectionParameterObject), W_Root, int],
             name='ReflectionParameter::__construct')
def construct(interp, this, function, parameter):

    if isinstance(function, W_ConstStringObject):
        name = interp.space.str_w(function)
        function  = interp.lookup_function(name)
        signature = function.get_signature()

        this.ref_parameter = signature.args[parameter]
    else:
        args = function.as_rdict().values()
        klass_name = interp.space.str_w(args[0])
        method_name = interp.space.str_w(args[1])
        klass = interp.lookup_class_or_intf(klass_name)
        method = klass.methods[method_name]
        signature = method.get_signature()

        this.ref_parameter = signature.args[parameter]


@wrap_method(['interp', ThisUnwrapper(W_ReflectionParameterObject)],
             name='ReflectionParameter::getName')
def get_name(interp, this):
    return _get_name(interp, this)


def _get_name(interp, this):
    return interp.space.wrap(this.ref_parameter.name)

def _set_name(interp, this, w_value):
    pass


ReflectionParameter = def_class(
    'ReflectionParameter',
    [construct,
     get_name],
    [GetterSetterWrapper(_get_name, _set_name, "name", consts.ACC_PUBLIC)],
    [],
    instance_class=W_ReflectionParameterObject
)
