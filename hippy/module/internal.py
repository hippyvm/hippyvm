
""" This module contains various internal php functions
"""

from collections import OrderedDict
from hippy.builtin import wrap, W_Root, Optional
from hippy.klass import W_BoundMethod
from hippy.objects.instanceobject import W_InstanceObject
from hippy.error import VisibilityError
from rpython.rlib import jit


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
        interp.warn("func_get_args():  Called from the global scope"
                    " - no function context")
        return interp.space.w_Null
    return interp.space.new_array_from_list(frame.args_w)


@wrap(['frame', 'interp', int])
def func_get_arg(frame, interp, num):
    if frame.args_w is None:
        interp.warn("func_get_arg():  Called from the global scope"
                    " - no function context")
        return interp.space.w_False
    if num < 0:
        interp.warn("func_get_arg():  The argument number should be >= 0")
        return interp.space.w_False
    if num >= len(frame.args_w):
        interp.warn("func_get_arg():  Argument %d not passed to function" % num)
        return interp.space.w_False
    return frame.args_w[num]


@wrap(['frame', 'interp'])
def func_num_args(frame, interp):
    if frame.args_w is None:
        interp.warn("func_num_args():  Called from the global scope"
                    " - no function context")
        return interp.space.wrap(-1)
    return interp.space.wrap(len(frame.args_w))


@wrap(['interp', 'frame', 'object'])
def get_object_vars(interp, frame, w_obj):
    contextclass = frame.get_contextclass()
    o = OrderedDict()
    dct_w = w_obj.get_instance_attrs(interp)
    for k, w_v in dct_w.iteritems():
        key1 = w_obj.klass.check_access_and_demangle_property(
            k, contextclass)
        if key1 is not None:
            o[key1] = w_v
    return interp.space.new_array_from_rdict(o)


@wrap(['interp', 'callback', 'args_w'])
def call_user_func(interp, callback_func, args_w):
    return interp.call(callback_func, args_w)


@jit.look_inside_iff(lambda space, w_args, no_args:
                     jit.isconstant(no_args) and no_args <= 10)
def _collect_arguments(space, w_args, no_args):
    args_w = []
    for item in range(no_args):
        args_w.append(space.getitem(w_args, space.wrap(item)))
    return args_w

@wrap(['interp', 'callback', W_Root])
def call_user_func_array(interp, callback_func, w_args):
    space = interp.space
    if not space.is_array(w_args):
        interp.warn("call_user_func_array() expects parameter 2 to be array")
        return space.w_Null
    no_args = space.arraylen(w_args)
    args_w = _collect_arguments(space, w_args, no_args)
    return interp.call(callback_func, args_w)


@wrap(['interp', 'callback', 'args_w'])
def forward_static_call(interp, func, args_w):
    called_class = interp.get_current_thisclass()
    if called_class is None:
        interp.fatal("Cannot call forward_static_call() when "
                     "no class scope is active")
    if (isinstance(func, W_BoundMethod) and
            func.klass.is_parent_of(called_class)):
        return func.call_args(interp, args_w, thisclass=called_class)
    else:
        return func.call_args(interp, args_w)


@wrap(['interp', 'callback'])
def set_exception_handler(interp, w_callback):
    interp.w_exception_handler = w_callback


@wrap(['interp', 'callback', 'args_w'])
def register_shutdown_function(interp, func, args_w):
    interp.shutdown_functions.append(func)
    interp.shutdown_arguments.append(args_w)

    # called_class = interp.get_current_thisclass()
    # if called_class is None:
    #     interp.fatal("Cannot call forward_static_call() when "
    #                  "no class scope is active")
    # if (isinstance(func, W_BoundMethod) and
    #         func.klass.is_parent_of(called_class)):
    #     return func.call_args(interp, args_w, thisclass=called_class)
    # else:
    #     return func.call_args(interp, args_w)


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


@wrap(['interp'])
def error_get_last(interp):
    pairs = []
    space = interp.space
    pairs.append((space.newstr('type'),
                  space.newint(interp.last_error_type)))
    pairs.append((space.newstr('message'),
                  space.newstr(interp.last_error_msg)))
    pairs.append((space.newstr('file'),
                  space.newstr(interp.last_error_file)))
    pairs.append((space.newstr('line'),
                  space.newint(interp.last_error_line)))
    return space.new_array_from_pairs(pairs)
