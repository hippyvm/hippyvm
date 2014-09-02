from hippy import consts
from hippy.klass import def_class
from hippy.objects.intobject import W_IntObject
from hippy.builtin import wrap_method, ThisUnwrapper
from hippy.builtin_klass import GetterSetterWrapper
from hippy.error import PHPException

from hippy.module.reflections.parameter import k_ReflectionParameter
from hippy.module.reflections.function_abstract import (
    k_ReflectionFunctionAbstract, W_ReflectionFunctionAbstract
)

IS_STATIC = 1
IS_PUBLIC = 256
IS_PROTECTED = 512
IS_PRIVATE = 1024
IS_ABSTRACT = 2
IS_FINAL = 4


class W_ReflectionMethodObject(W_ReflectionFunctionAbstract):
    pass


def _get_class(interp, this):
    return interp.space.wrap(this.ref_klass.name)

def _set_class(interp, this, w_value):
    pass

def _get_name(interp, this):
    return interp.space.wrap(this.ref_method.get_name())

def _set_name(interp, this, w_value):
    pass


k_ReflectionMethod = def_class(
    'ReflectionMethod',
    ['__construct', 'isPublic', 'isstatic', 'getDocComment', 'getParameters',
     'getDeclaringClass'],
    [GetterSetterWrapper(_get_class, _set_class, "class", consts.ACC_PUBLIC),
     GetterSetterWrapper(_get_name, _set_name, "name", consts.ACC_PUBLIC)],
    [('IS_STATIC', W_IntObject(IS_STATIC)),
     ('IS_PUBLIC', W_IntObject(IS_PUBLIC)),
     ('IS_PROTECTED', W_IntObject(IS_PROTECTED)),
     ('IS_PRIVATE', W_IntObject(IS_PRIVATE)),
     ('IS_ABSTRACT', W_IntObject(IS_ABSTRACT)),
     ('IS_FINAL', W_IntObject(IS_FINAL))],
    instance_class=W_ReflectionMethodObject,
    extends=k_ReflectionFunctionAbstract)


@k_ReflectionMethod.def_method(['interp', 'this', str, str])
def __construct(interp, this, class_name, method_name):
    klass = interp.lookup_class_or_intf(class_name)

    this.ref_klass = klass
    try:
        this.ref_method = klass.methods[method_name]
    except KeyError:
        msg = "Method %s does not exist" % method_name
        raise PHPException(interp._class_get('ReflectionException').call_args(
            interp, [interp.space.wrap(msg)]
        ))


@k_ReflectionMethod.def_method(['interp', 'this'])
def isPublic(interp, this):
    return interp.space.wrap(this.ref_method.is_public())


@k_ReflectionMethod.def_method(['interp', 'this'])
def getDeclaringClass(interp, this):
    ReflectionClass = interp._class_get('ReflectionClass')
    klass = this.ref_method.getclass()
    return ReflectionClass.call_args(interp, [interp.space.wrap(klass.name)])


@k_ReflectionMethod.def_method(['interp', 'this'])
def isStatic(interp, this):
    return interp.space.wrap(this.ref_method.is_static())


@k_ReflectionMethod.def_method(['interp', 'this'])
def getParameters(interp, this):
    space = interp.space

    args = this.ref_method.get_signature().args
    parameters = []
    for i in range(len(args)):
        arg = interp.space.new_array_from_list([
            space.wrap(this.ref_klass.name),
            space.wrap(this.ref_method.get_name())
        ])
        parameters.append((
            space.wrap(i),
            k_ReflectionParameter.call_args(interp, [arg, space.wrap(i)])
        ))

    return space.new_array_from_pairs(parameters)



@k_ReflectionMethod.def_method(['interp', 'this'])
def getDocComment(interp, this):
    return interp.space.wrap("")
