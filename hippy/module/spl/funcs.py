from hippy import rpath
from hippy.builtin import wrap, Optional, BoolArg, StringArg
from hippy.objects.closureobject import W_ClosureObject
from hippy.objects.strobject import W_StringObject
from hippy.objects.base import W_Root


@wrap(['interp', W_Root, Optional(BoolArg()), Optional(BoolArg())],
      error=False)
def spl_autoload_register(interp, w_autoload, throw=True, prepend=False):
    autoload_func = interp.space.get_callback('spl_autoload_register',
                                              0, w_autoload)
    if autoload_func is None:
        if throw:
            interp.fatal("XXX spl_autoload_register(throw=True): implement me!")
        return interp.space.w_False
    #
    pair = (w_autoload, autoload_func)
    if prepend:
        interp.autoload_stack.insert(0, pair)
    else:
        interp.autoload_stack.append(pair)
    return interp.space.w_True


@wrap(['interp', W_Root], error=False)
def spl_autoload_unregister(interp, w_autoload):
    # I'll go with space.eq_w() to compare with already-registered entries
    for i in range(len(interp.autoload_stack)):
        w_autoload1, _ = interp.autoload_stack[i]
        if interp.space.eq_w(w_autoload1, w_autoload):
            del interp.autoload_stack[i]
            return interp.space.w_True
    else:
        return interp.space.w_False


@wrap(['interp'], error=False)
def spl_autoload_functions(interp):
    return interp.space.new_array_from_list([
        w_autoload1 for (w_autoload1, _) in interp.autoload_stack])


@wrap(['interp', Optional(StringArg())], error=False)
def spl_autoload_extensions(interp, file_extensions=None):
    if file_extensions:
        interp.autoload_extensions = file_extensions.split(",")

    return interp.space.wrap(",".join(interp.autoload_extensions))


def _spl_autoload(interp, class_name, file_extensions_list):
    class_id = class_name.lower()

    for extension in file_extensions_list:
        for path in interp.include_path:
            fname = rpath.join(path, ["%s%s" % (class_id, extension)])
            if rpath.exists(fname):
                bc = interp.compile_file(fname)
                interp.run_include(bc, interp.global_frame)


@wrap(['interp', StringArg(), Optional(StringArg())], error=False)
def spl_autoload(interp, class_name, file_extensions=None):
    if file_extensions:
        _spl_autoload(interp, class_name, file_extensions.split(","))
    else:
        _spl_autoload(interp, class_name, interp.autoload_extensions)


@wrap(['interp', StringArg()], error=False)
def spl_autoload_call(interp, class_name):
    class_id = class_name.lower()

    klass = interp.lookup_class_or_intf(class_id, autoload=True)
    if klass:
        return klass

    if interp.autoload_stack:
        return interp._autoload_from_stack(class_name)
    else:
        _spl_autoload(interp, class_name, interp.autoload_extensions)
