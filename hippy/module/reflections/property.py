from hippy import consts
from hippy.klass import def_class
from hippy.objects.base import W_Root
from hippy.objects.intobject import W_IntObject
from hippy.objects.instanceobject import W_InstanceObject
from hippy.builtin import wrap_method, ThisUnwrapper, Optional
from hippy.builtin_klass import GetterSetterWrapper
from hippy.error import PHPException


IS_STATIC = 1
IS_PUBLIC = 256
IS_PROTECTED = 512
IS_PRIVATE = 1024


class W_ReflectionPropertyObject(W_InstanceObject):
    pass


@wrap_method(['interp', ThisUnwrapper(W_ReflectionPropertyObject), str, str],
             name='ReflectionProperty::__construct')
def construct(interp, this, class_name, property_name):
    klass = interp.lookup_class_or_intf(class_name)
    this.class_name = class_name
    this.name = property_name
    this.ref_klass = klass
    try:
        this.ref_prop = klass.properties[property_name]
    except KeyError:
        msg = "Property %s does not exist" % property_name
        raise PHPException(interp._class_get('ReflectionException').call_args(
            interp, [interp.space.wrap(msg)]
        ))


@wrap_method(['interp', ThisUnwrapper(W_ReflectionPropertyObject)],
             name='ReflectionProperty::getName')
def get_name(interp, this):
    return _get_name(interp, this)


# XXX: getValue & setValue don't work in case of accessible private & protected
# properties
@wrap_method(['interp', ThisUnwrapper(W_ReflectionPropertyObject),
              Optional(W_Root)],
             name='ReflectionProperty::getValue')
def get_value(interp, this, w_obj=None):
    if not this.ref_prop.is_public():
        msg = "Cannot access non-public member %s::%s" % (this.class_name,
                                                          this.name)
        raise PHPException(interp._class_get('ReflectionException').call_args(
            interp, [interp.space.wrap(msg)]
        ))

    if not this.ref_prop.is_static():
        value = w_obj.getattr(interp, this.name, w_obj.getclass(), True)
    else:
        value = interp.space.wrap(this.ref_prop.getvalue(interp.space))
    return value


@wrap_method(['interp', ThisUnwrapper(W_ReflectionPropertyObject),
              W_Root, Optional(W_Root)],
             name='ReflectionProperty::setValue')
def set_value(interp, this, w_arg_1, w_arg_2=None):

    if not this.ref_prop.is_public():
        msg = "Cannot access non-public member %s::%s" % (this.class_name, this.name)
        raise PHPException(interp._class_get('ReflectionException').call_args(
            interp, [interp.space.wrap(msg)]
        ))

    if not this.ref_prop.is_static():
        w_obj = w_arg_1
        w_value = w_arg_2
        w_obj.setattr(interp, this.name, w_value, None)
    else:
        w_value = w_arg_1
        this.ref_prop.r_value.store(w_value)


@wrap_method(['interp', ThisUnwrapper(W_ReflectionPropertyObject)],
             name='ReflectionProperty::isPublic')
def is_public(interp, this):
    return interp.space.newbool(this.ref_prop.is_public())


@wrap_method(['interp', ThisUnwrapper(W_ReflectionPropertyObject)],
             name='ReflectionProperty::isPrivate')
def is_private(interp, this):
    return interp.space.newbool(this.ref_prop.is_private())


@wrap_method(['interp', ThisUnwrapper(W_ReflectionPropertyObject)],
             name='ReflectionProperty::isProtected')
def is_protected(interp, this):
    return interp.space.newbool(this.ref_prop.is_protected())


@wrap_method(['interp', ThisUnwrapper(W_ReflectionPropertyObject)],
             name='ReflectionProperty::isStatic')
def is_static(interp, this):
    return interp.space.newbool(this.ref_prop.is_static())



def _get_class(interp, this):
    return interp.space.newstr(this.ref_klass.name)


def _set_class(interp, this, w_value):
    pass


def _get_name(interp, this):
    return interp.space.newstr(this.ref_prop.name)


def _set_name(interp, this, w_value):
    pass


def_class(
    'ReflectionProperty',
    [construct,
     get_name,
     get_value,
     set_value,
     is_public,
     is_private,
     is_protected,
     is_static],
    [GetterSetterWrapper(_get_name, _set_name, 'name', consts.ACC_PUBLIC),
     GetterSetterWrapper(_get_class, _set_class, 'class', consts.ACC_PUBLIC)],
    [('IS_STATIC', W_IntObject(IS_STATIC)),
     ('IS_PUBLIC', W_IntObject(IS_PUBLIC)),
     ('IS_PROTECTED', W_IntObject(IS_PROTECTED)),
     ('IS_PRIVATE', W_IntObject(IS_PRIVATE))],
    instance_class=W_ReflectionPropertyObject
)
