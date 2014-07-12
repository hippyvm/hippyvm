from rpython.rlib import rpath

from hippy import consts
from hippy.klass import def_class
from hippy.objects.base import W_Root
from hippy.objects.intobject import W_IntObject
from hippy.builtin_klass import GetterSetterWrapper
from hippy.objects.instanceobject import W_InstanceObject
from hippy.objects.strobject import W_ConstStringObject
from hippy.builtin import wrap_method, ThisUnwrapper


IS_IMPLICIT_ABSTRACT = 16
IS_EXPLICIT_ABSTRACT = 32
IS_FINAL = 64


class ReflectionData(object):

    def __init__(self, filename="", startline=0, endline=0, doc=""):
        self.filename = filename
        self.startline = startline
        self.endline = endline
        self.doc = doc


class W_ReflectionObject(W_InstanceObject):
    refl_klass = None

    def get_refl_klass(self, interp):
        if self.refl_klass is None:
            interp.fatal("Internal error: Failed to retrieve the "
                         "reflection object")
        return self.refl_klass


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject), W_Root],
             name='ReflectionClass::__construct')
def reflection_class_construct(interp, this, klass):
    space = interp.space

    if isinstance(klass, W_ConstStringObject):
        name = space.str_w(klass)
        this.refl_klass = interp.lookup_class_or_intf(name)

    if isinstance(klass, W_InstanceObject):
        this.refl_klass = klass.getclass()


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject), 'args_w'],
             name='ReflectionClass::newInstance')
def reflection_class_new_instance(interp, this, args_w):
    return this.get_refl_klass(interp).call_args(interp, args_w)


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject), W_Root],
             name='ReflectionClass::newInstanceArgs')
def reflection_class_new_instance_args(interp, this, w_arr):
    args_w = interp.space.as_array(w_arr).as_list_w()
    return this.get_refl_klass(interp).call_args(interp, args_w)


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject), str],
             name='ReflectionClass::getConstant')
def reflection_class_get_constant(interp, this, name):
    return this.refl_klass.lookup_w_constant(interp.space, name)


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject)],
             name='ReflectionClass::getConstants')
def reflection_class_get_constants(interp, this):
    items = [(interp.space.wrap(k), v) for k, v in this.refl_klass.constants_w.items()]
    return interp.space.new_array_from_pairs(items)


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject)],
             name='ReflectionClass::getConstructor')
def reflection_class_get_constructor(interp, this):
    return interp._class_get('ReflectionMethod').call_args(
        interp, [interp.space.wrap(this.refl_klass.name),
                 interp.space.wrap("__construct")]
    )


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject)],
             name='ReflectionClass::getDefaultProperties')
def reflection_class_get_default_properties(interp, this):
    space = interp.space
    items = this.refl_klass.properties.items()

    return space.new_array_from_pairs(
        [(space.wrap(name), p.value) for name, p in items]
    )


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject)],
             name='ReflectionClass::getDocComment')
def reflection_class_get_doc_comment(interp, this):
    doc = this.refl_klass.decl.reflection.doc
    return interp.space.wrap(doc)


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject)],
             name='ReflectionClass::getEndLine')
def reflection_class_get_end_line(interp, this):
    endline = this.refl_klass.decl.reflection.endline
    return interp.space.wrap(endline)


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject)],
             name='ReflectionClass::getInterfaceNames')
def reflection_class_get_interface_names(interp, this):
    klass = this.refl_klass
    parrents = klass.immediate_parents

    return interp.space.new_array_from_list(
        [interp.space.wrap(a.name) for a in parrents if a.is_interface()]
    )


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject), str],
             name='ReflectionClass::getMethod')
def reflection_class_get_method(interp, this, name):
    return interp._class_get('ReflectionMethod').call_args(
        interp, [interp.space.wrap(this.refl_klass.name), interp.space.wrap(name)]
    )


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject)],
             name='ReflectionClass::getMethods')
def reflection_class_get_methods(interp, this):
    reflection_method_klass = interp._class_get('ReflectionMethod')

    methods = []
    for name in this.refl_klass.methods.keys():
        reflection_method = reflection_method_klass.call_args(
            interp, [interp.space.wrap(this.refl_klass.name), interp.space.wrap(name)]
        )
        methods.append(reflection_method)

    return interp.space.new_array_from_list(methods)


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject)],
             name='ReflectionClass::getModifiers')
def reflection_class_get_modifiers(interp, this):
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


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject)],
             name='ReflectionClass::getName')
def reflection_class_get_name(interp, this):
    return interp.space.wrap(this.refl_klass.name)


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject)],
             name='ReflectionClass::getStartLine')
def reflection_class_get_start_line(interp, this):
    startline = this.refl_klass.decl.reflection.startline
    return interp.space.wrap(startline)


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject)],
             name='ReflectionClass::getExtension')
def reflection_class_get_extension(interp, this):
    raise NotImplementedError

@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject)],
             name='ReflectionClass::getExtensionName')
def reflection_class_get_extension_name(interp, this):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject)],
             name='ReflectionClass::getInterfaces')
def reflection_class_get_interfaces(interp, this):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject)],
             name='ReflectionClass::getNamespaceName')
def reflection_class_get_namespace_name(interp, this):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject)],
             name='ReflectionClass::getFileName')
def reflection_class_get_file_name(interp, this):
    filename = rpath.realpath(this.refl_klass.decl.reflection.filename)
    return interp.space.wrap(filename)


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject)],
             name='ReflectionClass::getproperties')
def reflection_class_get_properties(interp, this):
    raise NotImplementedError


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject), str],
             name='ReflectionClass::isSubclassOf')
def reflection_class_is_subclass_of(interp, this, name):
    return interp.space.wrap(
        this.refl_klass.is_subclass_of_class_or_intf_name(name)
    )


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject)],
             name='ReflectionClass::isInstantiable')
def reflection_class_is_instantiable(interp, this):

    if this.refl_klass.is_interface():
        return interp.space.w_False

    methods = this.refl_klass._collect_all_methods()
    for m in methods:
        if m.is_abstract():
            return interp.space.w_False

    constructor = this.refl_klass.methods.get('__construct',None)
    if constructor and constructor.is_private():
        return interp.space.w_False

    return interp.space.w_True


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject), str],
             name='ReflectionClass::hasMethod')
def reflection_class_has_method(interp, this, name):
    return interp.space.wrap(name.lower() in this.refl_klass.methods)


@wrap_method(['interp', ThisUnwrapper(W_ReflectionObject)],
             name='ReflectionClass::isAbstract')
def reflection_class_is_abstract(interp, this):
    return interp.space.wrap(this.refl_klass.is_abstract())


def _get_name(interp, this):
    return interp.space.wrap(this.refl_klass.name)

def _set_name(interp, this, w_value):
    pass


def_class(
    'ReflectionClass',
    [reflection_class_construct,
     reflection_class_new_instance,
     reflection_class_new_instance_args,
     reflection_class_get_constant,
     reflection_class_get_constants,
     reflection_class_get_constructor,
     reflection_class_get_default_properties,
     reflection_class_get_doc_comment,
     reflection_class_get_end_line,
     reflection_class_get_interfaces,
     reflection_class_get_interface_names,
     reflection_class_get_method,
     reflection_class_get_methods,
     reflection_class_get_modifiers,
     reflection_class_get_name,
     reflection_class_get_start_line,
     reflection_class_get_file_name,
     reflection_class_get_extension,
     reflection_class_get_extension_name,
     reflection_class_get_namespace_name,
     reflection_class_get_properties,
     reflection_class_is_subclass_of,
     reflection_class_is_instantiable,
     reflection_class_has_method,
     reflection_class_is_abstract],
    [GetterSetterWrapper(_get_name, _set_name, "name", consts.ACC_PUBLIC)],
    [('IS_IMPLICIT_ABSTRACT', W_IntObject(IS_IMPLICIT_ABSTRACT)),
     ('IS_EXPLICIT_ABSTRACT', W_IntObject(IS_EXPLICIT_ABSTRACT)),
     ('IS_FINAL', W_IntObject(IS_FINAL))],
    instance_class=W_ReflectionObject
)
