from hippy import consts
from hippy.klass import def_class
from hippy.objects.base import W_Root
from hippy.objects.intobject import W_IntObject
from hippy.objects.instanceobject import W_InstanceObject
from hippy.builtin import Optional
from hippy.builtin_klass import GetterSetterWrapper
from hippy.error import PHPException
from hippy.module.reflections.exception import k_ReflectionException


IS_STATIC = 1
IS_PUBLIC = 256
IS_PROTECTED = 512
IS_PRIVATE = 1024


class W_ReflectionProperty(W_InstanceObject):
    class_name = ''
    name = ''

    def get_str(self):
        prop = self.ref_prop
        if prop is None:
            inner = '<dynamic> public $%s' % self.name
        else:
            access = ''
            if not prop.is_static():
                access += '<default> '
            if prop.is_public():
                access += 'public'
            elif prop.is_protected():
                access += 'protected'
            elif prop.is_private():
                access += 'private'
            else:
                assert False, 'should not happen'
            if prop.is_static():
                access += ' static'
            inner = '%s $%s' % (access, prop.name)
        return 'Property [ %s ]\n' % inner


def _get_class(interp, this):
    return interp.space.newstr(this.class_name)


def _set_class(interp, this, w_value):
    pass


def _get_name(interp, this):
    return interp.space.newstr(this.name)


def _set_name(interp, this, w_value):
    pass


k_ReflectionProperty = def_class(
    'ReflectionProperty',
    ['export', '__construct', 'getName', 'getValue', 'setValue',
     'getDeclaringClass', "isPublic", "isPrivate", "isProtected", "isStatic",
     "isDefault", "getModifiers", "__toString"],
    [GetterSetterWrapper(_get_name, _set_name, 'name', consts.ACC_PUBLIC),
     GetterSetterWrapper(_get_class, _set_class, 'class', consts.ACC_PUBLIC)],
    [('IS_STATIC', W_IntObject(IS_STATIC)),
     ('IS_PUBLIC', W_IntObject(IS_PUBLIC)),
     ('IS_PROTECTED', W_IntObject(IS_PROTECTED)),
     ('IS_PRIVATE', W_IntObject(IS_PRIVATE))],
    instance_class=W_ReflectionProperty)


@k_ReflectionProperty.def_method(['interp', W_Root, str, Optional(bool)],
                               flags=consts.ACC_STATIC)
def export(interp, w_klass, name, return_string=False):
    refl = k_ReflectionProperty.call_args(interp,
            [w_klass, interp.space.wrap(name)])
    result = refl.get_str()
    if return_string:
        return interp.space.wrap(result)
    else:
        interp.writestr(result)
        interp.writestr('\n')
        return interp.space.w_Null


@k_ReflectionProperty.def_method(['interp', 'this', W_Root, str])
def __construct(interp, this, w_class, property_name):
    space = interp.space
    if space.is_str(w_class):
        class_name = space.str_w(w_class)
        klass = interp.lookup_class_or_intf(class_name)
        if klass is None:
            msg = "Class %s does not exist" % class_name
            raise PHPException(k_ReflectionException.call_args(
                interp, [space.wrap(msg)]))
    elif isinstance(w_class, W_InstanceObject):
        klass = w_class.klass
        class_name = klass.name
    else:
        msg = ("The parameter class is expected to be either a string "
               "or an object")
        raise PHPException(k_ReflectionException.call_args(
            interp, [space.wrap(msg)]))

    this.class_name = class_name
    this.name = property_name
    this.ref_klass = klass
    this.flags = 0
    try:
        this.ref_prop = klass.properties[property_name]
        if this.ref_prop.is_static():
            this.flags |= IS_STATIC
        if this.ref_prop.is_public():
            this.flags |= IS_PUBLIC
        elif this.ref_prop.is_private():
            this.flags |= IS_PRIVATE
        elif this.ref_prop.is_protected():
            this.flags |= IS_PROTECTED
    except KeyError:
        if (isinstance(w_class, W_InstanceObject) and
                w_class.map.lookup(property_name) is not None):
            this.ref_prop = None
            this.flags = consts.ACC_IMPLICIT_PUBLIC
            return
        msg = "Property %s::$%s does not exist" % (class_name, property_name)
        raise PHPException(k_ReflectionException.call_args(
            interp, [interp.space.wrap(msg)]))


@k_ReflectionProperty.def_method(['interp', 'this'])
def getName(interp, this):
    return _get_name(interp, this)


# XXX: getValue & setValue don't work in case of accessible private & protected
# properties
@k_ReflectionProperty.def_method(['interp', 'this', Optional(W_Root)])
def getValue(interp, this, w_obj=None):
    property = this.ref_prop
    if property is None:
        return w_obj.getattr(interp, this.name, w_obj.getclass(),
                             give_notice=False)
    if not property.is_public():
        msg = "Cannot access non-public member %s::%s" % (this.class_name,
                                                          this.name)
        raise PHPException(k_ReflectionException.call_args(
            interp, [interp.space.wrap(msg)]))
    if not property.is_static():
        w_value = w_obj.getattr(interp, this.name, w_obj.getclass(),
                                give_notice=False)
    else:
        w_value = property.getvalue(interp.space).deref()
    return w_value


@k_ReflectionProperty.def_method(['interp', 'this', W_Root, Optional(W_Root)])
def setValue(interp, this, w_arg_1, w_arg_2=None):
    if not this.ref_prop.is_public():
        msg = "Cannot access non-public member %s::%s" % (this.class_name,
                                                          this.name)
        raise PHPException(k_ReflectionException.call_args(
            interp, [interp.space.wrap(msg)]))

    if not this.ref_prop.is_static():
        w_obj = w_arg_1
        w_value = w_arg_2
        w_obj.setattr(interp, this.name, w_value, None)
    else:
        if w_arg_2 is None:
            w_value = w_arg_1
        else:
            w_value = w_arg_2
        this.ref_prop.r_value.store(w_value)


@k_ReflectionProperty.def_method(['interp', 'this'])
def getDeclaringClass(interp, this):
    name = this.ref_prop.klass.name
    k_ReflClass = interp.lookup_class_or_intf('ReflectionClass')
    return k_ReflClass.call_args(interp, [interp.space.newstr(name)])


@k_ReflectionProperty.def_method(['interp', 'this'])
def isPublic(interp, this):
    return interp.space.newbool(this.ref_prop.is_public())


@k_ReflectionProperty.def_method(['interp', 'this'])
def isPrivate(interp, this):
    return interp.space.newbool(this.ref_prop.is_private())


@k_ReflectionProperty.def_method(['interp', 'this'])
def isProtected(interp, this):
    return interp.space.newbool(this.ref_prop.is_protected())


@k_ReflectionProperty.def_method(['interp', 'this'])
def isStatic(interp, this):
    return interp.space.newbool(this.ref_prop.is_static())


@k_ReflectionProperty.def_method(['interp', 'this'])
def isDefault(interp, this):
    return interp.space.newbool(True)  # XXX


@k_ReflectionProperty.def_method(['interp', 'this'])
def getModifiers(interp, this):
    return interp.space.newint(this.ref_prop.access_flags)


@k_ReflectionProperty.def_method(['interp', 'this'])
def __toString(interp, this):
    return interp.space.newstr(this.get_str())
