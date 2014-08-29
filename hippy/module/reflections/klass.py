from rpython.rlib import rpath

from hippy import consts
from hippy.klass import def_class
from hippy.objects.base import W_Root
from hippy.objects.intobject import W_IntObject
from hippy.builtin_klass import GetterSetterWrapper
from hippy.objects.instanceobject import W_InstanceObject
from hippy.objects.strobject import W_ConstStringObject
from hippy.builtin import Optional
from hippy.module.reflections.property import (
    W_ReflectionProperty, k_ReflectionProperty)
from hippy.module.reflections.method import k_ReflectionMethod


IS_IMPLICIT_ABSTRACT = 16
IS_EXPLICIT_ABSTRACT = 32
IS_FINAL = 64


class ReflectionData(object):

    def __init__(self, filename="", startline=0, endline=0, doc=""):
        self.filename = filename
        self.startline = startline
        self.endline = endline
        self.doc = doc


class W_ReflectionClass(W_InstanceObject):
    refl_klass = None

    def get_refl_klass(self, interp):
        if self.refl_klass is None:
            interp.fatal("Internal error: Failed to retrieve the "
                         "reflection object")
        return self.refl_klass


def _get_name(interp, this):
    return interp.space.wrap(this.refl_klass.name)

def _set_name(interp, this, w_value):
    pass


k_ReflectionClass = def_class(
    'ReflectionClass',
    ["__construct", "newInstance", "newInstanceArgs", "hasConstant",
     "getConstant", "getConstants", "getConstructor", "getDefaultProperties",
     "getDocComment", "getEndLine", "getInterfaces", "getInterfaceNames",
     "getMethod", "getMethods", "getModifiers", "getName", "getStartLine",
     "getFileName", "getExtension", "getExtensionName", "getNamespaceName",
     "getStaticProperties", "getProperties", "getProperty", "hasProperty",
     "isSubclassOf", "isInstantiable", "hasMethod", "isAbstract"],
    [GetterSetterWrapper(_get_name, _set_name, "name", consts.ACC_PUBLIC)],
    [('IS_IMPLICIT_ABSTRACT', W_IntObject(IS_IMPLICIT_ABSTRACT)),
     ('IS_EXPLICIT_ABSTRACT', W_IntObject(IS_EXPLICIT_ABSTRACT)),
     ('IS_FINAL', W_IntObject(IS_FINAL))],
    instance_class=W_ReflectionClass
)

@k_ReflectionClass.def_method(['interp', 'this', W_Root])
def __construct(interp, this, klass):
    space = interp.space

    if isinstance(klass, W_ConstStringObject):
        name = space.str_w(klass)
        this.refl_klass = interp.lookup_class_or_intf(name)

    if isinstance(klass, W_InstanceObject):
        this.refl_klass = klass.getclass()


@k_ReflectionClass.def_method(['interp', 'this', 'args_w'])
def newInstance(interp, this, args_w):
    return this.get_refl_klass(interp).call_args(interp, args_w)


@k_ReflectionClass.def_method(['interp', 'this', W_Root])
def newInstanceArgs(interp, this, w_arr):
    args_w = interp.space.as_array(w_arr).as_list_w()
    return this.get_refl_klass(interp).call_args(interp, args_w)


@k_ReflectionClass.def_method(['interp', 'this', str])
def hasConstant(interp, this, name):
    return interp.space.wrap(name.lower() in this.refl_klass.constants_w.keys())


@k_ReflectionClass.def_method(['interp', 'this', str])
def getConstant(interp, this, name):
    return this.refl_klass.lookup_w_constant(interp.space, name)


@k_ReflectionClass.def_method(['interp', 'this'])
def getConstants(interp, this):
    items = [(interp.space.wrap(k), v) for k, v in this.refl_klass.constants_w.items()]
    return interp.space.new_array_from_pairs(items)


@k_ReflectionClass.def_method(['interp', 'this'])
def getConstructor(interp, this):
    return interp._class_get('ReflectionMethod').call_args(
        interp, [interp.space.wrap(this.refl_klass.name),
                 interp.space.wrap("__construct")])


@k_ReflectionClass.def_method(['interp', 'this'])
def getDefaultProperties(interp, this):
    space = interp.space
    items = this.refl_klass.properties.items()
    return space.new_array_from_pairs(
        [(space.wrap(name), p.value) for name, p in items])


@k_ReflectionClass.def_method(['interp', 'this'])
def getDocComment(interp, this):
    doc = this.refl_klass.decl.reflection.doc
    return interp.space.wrap(doc)


@k_ReflectionClass.def_method(['interp', 'this'])
def getEndLine(interp, this):
    endline = this.refl_klass.decl.reflection.endline
    return interp.space.wrap(endline)


@k_ReflectionClass.def_method(['interp', 'this'])
def getInterfaceNames(interp, this):
    klass = this.refl_klass
    parrents = klass.immediate_parents

    return interp.space.new_array_from_list(
        [interp.space.wrap(a.name) for a in parrents if a.is_interface()]
    )


@k_ReflectionClass.def_method(['interp', 'this', str])
def getMethod(interp, this, name):
    return k_ReflectionMethod.call_args(
        interp, [interp.space.wrap(this.refl_klass.name), interp.space.wrap(name)]
    )


@k_ReflectionClass.def_method(['interp', 'this'])
def getMethods(interp, this):
    methods = []
    for name in this.refl_klass.methods.keys():
        reflection_method = k_ReflectionMethod.call_args(
            interp, [interp.space.wrap(this.refl_klass.name),
                     interp.space.wrap(name)])
        methods.append(reflection_method)

    return interp.space.new_array_from_list(methods)


@k_ReflectionClass.def_method(['interp', 'this'])
def getModifiers(interp, this):
    methods = this.refl_klass.methods.values()
    is_abstract = this.refl_klass.is_abstract()
    is_abstract_implict = len([m for m in methods if m.is_abstract()]) > 0
    is_final = this.refl_klass.is_final()

    bits = 0
    if is_abstract:
        bits |= IS_EXPLICIT_ABSTRACT
    if is_abstract_implict:
        bits |= IS_IMPLICIT_ABSTRACT
    if is_final:
        bits |= IS_FINAL
    return interp.space.wrap(bits)


@k_ReflectionClass.def_method(['interp', 'this'])
def getName(interp, this):
    return interp.space.wrap(this.refl_klass.name)


@k_ReflectionClass.def_method(['interp', 'this'])
def getStartLine(interp, this):
    startline = this.refl_klass.decl.reflection.startline
    return interp.space.wrap(startline)


@k_ReflectionClass.def_method(['interp', 'this'])
def getExtension(interp, this):
    raise NotImplementedError

@k_ReflectionClass.def_method(['interp', 'this'])
def getExtensionName(interp, this):
    raise NotImplementedError


@k_ReflectionClass.def_method(['interp', 'this'])
def getInterfaces(interp, this):
    raise NotImplementedError


@k_ReflectionClass.def_method(['interp', 'this'])
def getNamespaceName(interp, this):
    raise NotImplementedError


@k_ReflectionClass.def_method(['interp', 'this'])
def getFileName(interp, this):
    filename = rpath.realpath(this.refl_klass.decl.reflection.filename)
    return interp.space.wrap(filename)


@k_ReflectionClass.def_method(['interp', 'this'])
def getStaticProperties(interp, this):
    static_property_values = []
    for k, v in this.refl_klass.properties.items():
        if v.is_static():
            static_property_values.append(v.value)
    return interp.space.new_array_from_list(static_property_values)


@k_ReflectionClass.def_method(['interp', 'this', Optional(int)])
def getProperties(interp, this, flags=0):
    properties = []
    for name in this.refl_klass.properties.keys():
        reflection_prop = k_ReflectionProperty.call_args(
            interp, [interp.space.wrap(this.refl_klass.name),
                     interp.space.wrap(name)])
        assert isinstance(reflection_prop, W_ReflectionProperty)
        prop_flags = reflection_prop.flags
        if flags == 0:
            properties.append(reflection_prop)

        elif flags & prop_flags:
            properties.append(reflection_prop)

    return interp.space.new_array_from_list(properties)


@k_ReflectionClass.def_method(['interp', 'this', str])
def hasProperty(interp, this, name):
    return interp.space.wrap(name.lower() in this.refl_klass.properties)


@k_ReflectionClass.def_method(['interp', 'this', str])
def getProperty(interp, this, name):
    return interp._class_get('ReflectionProperty').call_args(
        interp, [interp.space.wrap(this.refl_klass.name),
                 interp.space.wrap(name)])


@k_ReflectionClass.def_method(['interp', 'this', str])
def isSubclassOf(interp, this, name):
    return interp.space.wrap(
        this.refl_klass.is_subclass_of_class_or_intf_name(name))


@k_ReflectionClass.def_method(['interp', 'this'])
def isInstantiable(interp, this):
    if this.refl_klass.is_interface():
        return interp.space.w_False

    methods = this.refl_klass._collect_all_methods()
    for m in methods:
        if m.is_abstract():
            return interp.space.w_False

    constructor = this.refl_klass.methods.get('__construct', None)
    if constructor and constructor.is_private():
        return interp.space.w_False

    return interp.space.w_True


@k_ReflectionClass.def_method(['interp', 'this', str])
def hasMethod(interp, this, name):
    return interp.space.wrap(name.lower() in this.refl_klass.methods)


@k_ReflectionClass.def_method(['interp', 'this'])
def isAbstract(interp, this):
    return interp.space.wrap(this.refl_klass.is_abstract())
