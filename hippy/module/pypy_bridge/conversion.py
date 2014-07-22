from hippy.objects.instanceobject import W_InstanceObject as Wph_InstanceObject
from hippy.klass import def_class
from hippy.builtin import wrap, Optional, wrap_method, ThisUnwrapper
from hippy.objects.base import W_Root as Wph_Root

from pypy.interpreter.baseobjspace import W_Root as Wpy_Root
from pypy.interpreter.function import Function as py_Function
from pypy.interpreter.module import Module as py_Module


def php_to_py(interp, wph_any):
    from hippy.module.pypy_bridge import py_wrappers
    assert isinstance(wph_any, Wph_Root)

    # If it's a proxied Python instance, a trivial unwrapping? XXX
    #if isinstance(wph_any, W_PyBridgeProxy):
    #    import pdb; pdb.set_trace()
    #    return wph_any.wpy_inst

    phspace = interp.space

    # Note that the primitive types are not objects in PHP, so there is
    # no risk of subclassing interfering there.

    #if hasattr(wph_any, "tp"):
    try:
        wph_tp = wph_any.deref().tp
    except AttributeError:
        return py_wrappers.W_PhBridgeProxy(interp, wph_any)

    if wph_tp == phspace.tp_null:
        return interp.pyspace.w_None
    elif wph_tp == phspace.tp_bool:
        return interp.pyspace.wrap(interp.space.is_true(wph_any))
    elif wph_tp == phspace.tp_float:
        return interp.pyspace.newfloat(interp.space.float_w(wph_any))
    elif wph_tp == phspace.tp_int:
        return interp.pyspace.newint(interp.space.int_w(wph_any))
    elif wph_tp == phspace.tp_str:
        return interp.pyspace.wrap(interp.space.str_w(wph_any))
    # XXX disable list conversions
    #elif wph_tp == phspace.tp_array:
    #    return py_list_of_ph_array(interp, wph_any)
    else:
        return py_wrappers.W_PhBridgeProxy(interp, wph_any)

def py_list_of_ph_array(interp, wph_array):
    wph_elems = wph_array.as_list_w()
    wpy_elems = []
    for i in range(len(wph_elems)):
        wpy_elems.append(php_to_py(interp, wph_elems[i]))
    return interp.pyspace.newlist(wpy_elems)

# -------------
# Python -> PHP
# -------------


def py_to_php(interp, wpy_any):
    from hippy.module.pypy_bridge import php_wrappers, py_wrappers

    assert isinstance(wpy_any, Wpy_Root)

    pyspace = interp.pyspace
    if pyspace.is_w(pyspace.type(wpy_any), pyspace.w_bool):
        return interp.space.wrap(interp.pyspace.bool_w(wpy_any))
    elif pyspace.is_w(pyspace.type(wpy_any), pyspace.w_int):
        return interp.space.newint(interp.pyspace.int_w(wpy_any))
    elif pyspace.is_w(pyspace.type(wpy_any), pyspace.w_float):
        return interp.space.newfloat(interp.pyspace.float_w(wpy_any))
    elif pyspace.is_w(pyspace.type(wpy_any), pyspace.w_str):
        return interp.space.wrap(interp.pyspace.str_w(wpy_any))
    elif wpy_any is pyspace.w_None:
        return interp.space.w_Null
    elif pyspace.is_w(pyspace.type(wpy_any), pyspace.w_dict):
        return php_wrappers.W_PyBridgeDictProxy(interp, wpy_any)
    elif pyspace.is_w(pyspace.type(wpy_any), pyspace.w_list):
        return php_wrappers.W_PyBridgeListProxy(interp, wpy_any)
    elif isinstance(wpy_any, py_Function):
        return php_wrappers.W_EmbeddedPyFunc(interp, wpy_any)
    elif isinstance(wpy_any, py_Module):
        return php_wrappers.W_EmbeddedPyMod(interp, wpy_any)
    elif isinstance(wpy_any, py_wrappers.W_PhBridgeProxy):
        return wpy_any.wph_inst
    else:
        wph_pxy = php_wrappers.W_PyBridgeProxy(php_wrappers.k_PyBridgeProxy, [])
        wph_pxy.setup_instance(interp, wpy_any)
        return wph_pxy

def ph_array_of_py_list(interp, wpy_list):
    wpy_elems = interp.pyspace.listview(wpy_list)
    wph_elems = [ py_to_php(interp, x) for x in wpy_elems ]
    return interp.space.new_array_from_list(wph_elems)

