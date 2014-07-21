from hippy.objects.instanceobject import W_InstanceObject as Wph_InstanceObject
from hippy.klass import def_class
from hippy.builtin import wrap, Optional, wrap_method, ThisUnwrapper
from hippy.objects.base import W_Root as Wph_Root
from hippy import function

from pypy.interpreter.baseobjspace import W_Root as Wpy_Root


def py_of_ph(interp, wph_any):
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
        return py_none_of_ph_null(interp, wph_any)
    elif wph_tp == phspace.tp_bool:
        return py_bool_of_ph_boolean(interp, wph_any)
    elif wph_tp == phspace.tp_float:
        return py_float_of_ph_float(interp, wph_any)
    elif wph_tp == phspace.tp_int:
        return py_int_of_ph_int(interp, wph_any)
    elif wph_tp == phspace.tp_str:
        return py_str_of_ph_string(interp, wph_any)
    # XXX disable list conversions
    #elif wph_tp == phspace.tp_array:
    #    return py_list_of_ph_array(interp, wph_any)
    elif isinstance(wph_any, function.Function):
        return py_wrappers.W_EmbeddedPHPFunc(phspace, wph_any)
    else:
        return py_wrappers.W_PhBridgeProxy(interp, wph_any)

def py_int_of_ph_int(interp, wph_int):
    return interp.pyspace.newint(interp.space.int_w(wph_int))

def py_float_of_ph_float(interp, wph_float):
    return interp.pyspace.newfloat(interp.space.float_w(wph_float))

def py_str_of_ph_string(interp, wph_string):
    return interp.pyspace.wrap(interp.space.str_w(wph_string))

def py_none_of_ph_null(interp, unused):
    return interp.pyspace.w_None

def py_bool_of_ph_boolean(interp, wph_boolean):
    return interp.pyspace.wrap(interp.space.is_true(wph_boolean))

def py_list_of_ph_array(interp, wph_array):
    wph_elems = wph_array.as_list_w()
    wpy_elems = []
    for i in range(len(wph_elems)):
        wpy_elems.append(py_of_ph(interp, wph_elems[i]))
    return interp.pyspace.newlist(wpy_elems)

# -------------
# Python -> PHP
# -------------


def ph_of_py(interp, wpy_any):
    from hippy.module.pypy_bridge import php_wrappers

    assert isinstance(wpy_any, Wpy_Root)

    # If a proxied PHP instance, a trivial unwrapping? XXX
    #if isinstance(wpy_any, W_PhBridgeProxy):
    #    import pdb; pdb.set_trace()
    #    return wpy_any.wph_inst

    pyspace = interp.pyspace
    if pyspace.is_w(pyspace.type(wpy_any), pyspace.w_bool):
        return ph_boolean_of_py_bool(interp, wpy_any)
    elif pyspace.is_w(pyspace.type(wpy_any), pyspace.w_int):
        return ph_int_of_py_int(interp, wpy_any)
    elif pyspace.is_w(pyspace.type(wpy_any), pyspace.w_float):
        return ph_float_of_py_float(interp, wpy_any)
    elif pyspace.is_w(pyspace.type(wpy_any), pyspace.w_str):
        return ph_string_of_py_str(interp, wpy_any)
    elif wpy_any is pyspace.w_None:
        return ph_null_of_py_none(interp, wpy_any)
    elif pyspace.is_w(pyspace.type(wpy_any), pyspace.w_dict):
        from hippy.module.pypy_bridge.py_wrappers import W_PyBridgeDictProxy
        return W_PyBridgeDictProxy(interp, wpy_any)
    elif pyspace.is_w(pyspace.type(wpy_any), pyspace.w_list):
        from hippy.module.pypy_bridge.py_wrappers import W_PyBridgeListProxy
        return W_PyBridgeListProxy(interp, wpy_any)
    else:
        # XXX bug in RPython translator?
        #return W_PyBridgeProxy.from_wpy_inst(interp, wpy_any)
        wph_pxy = php_wrappers.W_PyBridgeProxy(php_wrappers.k_PyBridgeProxy, [])
        wph_pxy.setup_instance(interp, wpy_any)
        return wph_pxy

def ph_int_of_py_int(interp, wpy_int):
    return interp.space.newint(interp.pyspace.int_w(wpy_int))

def ph_float_of_py_float(interp, wpy_float):
    return interp.space.newfloat(interp.pyspace.float_w(wpy_float))

def ph_string_of_py_str(interp, wpy_str):
    return interp.space.wrap(interp.pyspace.str_w(wpy_str))

def ph_boolean_of_py_bool(interp, wpy_bool):
    return interp.space.wrap(interp.pyspace.bool_w(wpy_bool))

def ph_null_of_py_none(interp, unused):
    return interp.space.w_Null

def ph_array_of_py_list(interp, wpy_list):
    wpy_elems = interp.pyspace.listview(wpy_list)
    wph_elems = [ ph_of_py(interp, x) for x in wpy_elems ]
    return interp.space.new_array_from_list(wph_elems)

