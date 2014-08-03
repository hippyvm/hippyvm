from rpython.rlib.objectmodel import we_are_translated

from hippy.objects.instanceobject import W_InstanceObject as Wph_InstanceObject
from hippy.klass import def_class
from hippy.builtin import wrap, Optional, wrap_method, ThisUnwrapper
from hippy.function import AbstractFunction
from hippy.objects.arrayobject import W_ListArrayObject as WPHP_ListArrayObject
from hippy.objects.arrayobject import W_RDictArrayObject as WPHP_RDictArrayObject
from hippy.objects.arrayobject import W_ArrayObject as WPHP_ArrayObject
from hippy.objects.reference import W_Reference

from pypy.interpreter.baseobjspace import W_Root as Wpy_Root
from pypy.interpreter.module import Module as py_Module

# Note: this module is one of the centre-pieces of a lot of (inevitable)
# circular importing, so we use it as the place to push imports to within
# modules. This not only concentrates the ugliness in one place, but has the
# virtue of doing so in what is one of the simplest files in the whole bridge.


def php_to_py(interp, wph_any):
    from hippy.module.pypy_bridge import php_wrappers, py_wrappers
    from hippy import objspace

    phspace = interp.space

    # XXX general trivial unwrappings.

    # We want to pass arrays by reference
    if isinstance(wph_any, W_Reference):
        wph_inside = wph_any.deref_temp()
        if isinstance(wph_inside, WPHP_ArrayObject):
            from hippy.module.pypy_bridge.py_wrappers import make_wrapped_mixed_key_php_array
            return make_wrapped_mixed_key_php_array(interp, wph_any) # pass in ref

    # Everything else is by value, so we discard the reference
    wph_any = wph_any.deref()

    if isinstance(wph_any, php_wrappers.W_PyProxyGeneric):
        return wph_any.wpy_inst
    elif isinstance(wph_any, objspace.W_NullObject):
        return interp.pyspace.w_None
    elif isinstance(wph_any, objspace.W_BoolObject):
        return interp.pyspace.wrap(interp.space.is_true(wph_any))
    elif isinstance(wph_any, objspace.W_FloatObject):
        return interp.pyspace.newfloat(interp.space.float_w(wph_any))
    elif isinstance(wph_any, objspace.W_IntObject):
        return interp.pyspace.newint(interp.space.int_w(wph_any))
    elif isinstance(wph_any, objspace.W_StringObject):
        return interp.pyspace.wrap(interp.space.str_w(wph_any))
    elif isinstance(wph_any, php_wrappers.W_PyBridgeListProxy):
        # Prevent a double wrapping. XXX can go when general unwrappings done
        return wph_any.get_wrapped_py_obj()
    elif isinstance(wph_any, objspace.W_ArrayObject):
        from hippy.module.pypy_bridge.py_wrappers import (
                make_wrapped_mixed_key_php_array)
        wph_arry_ref = W_Reference(wph_any)
        return make_wrapped_mixed_key_php_array(interp, wph_arry_ref)
    else:
        return py_wrappers.W_PHPProxyGeneric(interp, wph_any)

