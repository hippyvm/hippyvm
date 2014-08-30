from hippy import consts
from hippy.klass import def_class
from hippy.objects.base import W_Root
from hippy.objects.intobject import W_IntObject
from hippy.builtin_klass import GetterSetterWrapper
from hippy.objects.closureobject import W_ClosureObject

from hippy.module.reflections.parameter import k_ReflectionParameter

from hippy.module.reflections.function_abstract import (
    k_ReflectionFunctionAbstract, W_ReflectionFunctionAbstract
)


IS_DEPRECATED = 262144


class W_ReflectionFunction(W_ReflectionFunctionAbstract):
    pass


class Wrapper(object):
    pass

class ClosureWrapper(Wrapper):

    def __init__(self, interp, w_closure):
        self.interp = interp
        self.space = interp.space

        self.w_closure = w_closure

    def get_name(self):
        return self.space.wrap("{closure}")


class NameWrapper(Wrapper):

    def __init__(self, interp, name):
        self.interp = interp
        self.space = interp.space
        self.name = interp.space.str_w(name)
        self.function = interp.lookup_function(self.name)

    def get_name(self):
        return self.space.wrap(self.function.get_fullname())

    def get_parameters(self):
        args = self.function.get_signature().args
        parameters = []
        for i in range(len(args)):
            parameters.append((self.space.wrap(i),
                k_ReflectionParameter.call_args(
                    self.interp,
                    [self.space.wrap(self.name), self.space.wrap(i)]
                )
            ))

        return self.space.new_array_from_pairs(parameters)


def _get_name(interp, this):
    return this.ref_fun.get_name()

def _set_name(interp, this, w_value):
    pass


k_ReflectionFunction = def_class(
    'ReflectionFunction',
    ["__construct", "getName", "getDocComment", "getParameters"],
    [GetterSetterWrapper(_get_name, _set_name, "name", consts.ACC_PUBLIC)],
    [('IS_DEPRECATED', W_IntObject(IS_DEPRECATED))],
    instance_class=W_ReflectionFunction,
    extends=k_ReflectionFunctionAbstract
)


@k_ReflectionFunction.def_method(['interp', 'this', W_Root])
def __construct(interp, this, function):
    if isinstance(function, W_ClosureObject):
        this.ref_fun = ClosureWrapper(interp, function)
    else:
        this.ref_fun = NameWrapper(interp, function)


@k_ReflectionFunction.def_method(['interp', 'this'])
def getName(interp, this):
    return this.ref_fun.get_name()


@k_ReflectionFunction.def_method(['interp', 'this'])
def getParameters(interp, this):
    return this.ref_fun.get_parameters()


@k_ReflectionFunction.def_method(['interp', 'this'])
def getDocComment(interp, this):
    return interp.space.wrap("")
