
""" This module contains various internal php functions
"""

from collections import OrderedDict
from hippy.builtin import wrap, W_Root, Optional
from hippy.objects.instanceobject import W_InstanceObject
from hippy.error import VisibilityError


@wrap(['space', W_Root, Optional(bool), Optional('reference')])
def is_callable(space, w_name, syntax_only=False, w_callable_name=None):
    assert w_callable_name is None
    if syntax_only:
        if space.is_str(w_name):
            return space.w_True
        if space.is_array(w_name):
            if space.arraylen(w_name) != 2:
                return space.w_False
            w_item = space.getitem(w_name, space.wrap(0))
            if (not isinstance(w_item, W_InstanceObject) and
                not space.is_str(w_item)):
                return space.w_False
            w_name = space.getitem(w_name, space.wrap(1))
            return space.wrap(space.is_str(w_name))
        if isinstance(w_name, W_InstanceObject):
            return space.w_True
        return space.w_False
    interp = space.ec.interpreter
    w_callable = interp.space.get_callback(None, 0, w_name, False)
    if w_callable:
        return space.w_True
    return space.w_False

@wrap(['frame', 'interp'])
def func_get_args(frame, interp):
    if frame.args_w is None:
        interp.warn("func_get_args(): Called from the global scope"
                    " - no function context")
        return interp.space.w_Null
    return interp.space.new_array_from_list(frame.args_w)

@wrap(['frame', 'interp'])
def func_num_args(frame, interp):
    if frame.args_w is None:
        interp.warn("func_num_args():  Called from the global scope"
                    " - no function context")
        return interp.space.wrap(-1)
    return interp.space.wrap(len(frame.args_w))

@wrap(['interp', 'frame', W_Root])
def get_object_vars(interp, frame, obj):
    if not isinstance(obj, W_InstanceObject):
        interp.warn("get_object_vars(): excepts parameter 1 to be an object")
        return interp.space.w_Null
    contextclass = frame.get_contextclass()
    o = OrderedDict()
    dct_w = obj.get_instance_attrs()
    for k, w_v in dct_w.iteritems():
        key1 = obj.klass.check_access_and_demangle_property(
            k, contextclass)
        if key1 is not None:
            o[key1] = w_v
    return interp.space.new_array_from_rdict(o)

@wrap(['space', 'callback', 'args_w'])
def call_user_func(space, callback_func, args_w):
    return space.call_args(callback_func, args_w)

@wrap(['space', 'callback', W_Root])
def call_user_func_array(space, callback_func, w_args):
    if not space.is_array(w_args):
        space.ec.warn("call_user_func_array() expects parameter 2 to be array")
        return space.w_Null
    no_args = space.arraylen(w_args)
    args_w = []
    for item in range(no_args):
        args_w.append(space.getitem(w_args, space.wrap(item)))
    return space.call_args(callback_func, args_w)

@wrap(['interp', 'callback', 'args_w'])
def forward_static_call(interp, func, args_w):
    return interp.space.call_args(func, args_w)

@wrap(['space', 'callback'])
def set_exception_handler(space, w_callback):
    space.ec.interpreter.w_exception_handler = w_callback

@wrap(['space'])
def get_defined_constants(space):
    rdct_w = OrderedDict()
    for k, w_v in space.ec.interpreter.constants.iteritems():
        rdct_w[k] = w_v
    return space.new_array_from_rdict(rdct_w)

def backtrace_to_applevel(space, tb):
    items_w = []
    for filename, funcname, line, source in tb:
        entry_w = OrderedDict()
        entry_w['file'] = space.newstr(filename)
        entry_w['line'] = space.newint(line)
        entry_w['function'] = space.newstr(funcname)
        entry_w['args'] = space.w_Null     # XXX
        # XXX check the order, add other entries
        items_w.append(space.new_array_from_rdict(entry_w))
    return space.new_array_from_list(items_w)

@wrap(['interp'])
def debug_backtrace(interp):
    return backtrace_to_applevel(interp.space, interp.get_traceback())
