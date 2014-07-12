import os
from hippy import consts
from hippy.builtin import wrap, wrap_method, Optional, StreamContextArg
from hippy.builtin import ThisUnwrapper, Resource
from hippy.klass import def_class
from hippy.objects.instanceobject import W_InstanceObject
from hippy.objects.resources.dir_resource import W_DirResource
from hippy.builtin_klass import GetterSetterWrapper


class W_Directory(W_InstanceObject):

    path = None
    handle = None

    def __init__(self, klass, dct_w):
        W_InstanceObject.__init__(self, klass, dct_w)

# properties


def _set_path(interp, this, w_value):
    this.path = w_value


def _get_path(interp, this):
    return this.path


def _set_handle(interp, this, w_value):
    assert isinstance(w_value, W_DirResource)
    this.handle = w_value


def _get_handle(interp, this):
    return this.handle


@wrap(['interp', str, Optional(StreamContextArg(None))])
def dir(interp, directory, w_ctx=None):
    space = interp.space

    if w_ctx:
        if not interp.space.is_resource(w_ctx):
            interp.warn("dir() expects parameter 2 to be resource, %s given"
                    % interp.space.get_type_name(w_ctx.tp).lower())
            return interp.space.w_Null

    if directory == '':
        return interp.space.w_False

    if not os.path.isdir(directory):
        warn_str = "dir(" + directory + \
                   "): failed to open dir: No such file or directory"
        interp.warn(warn_str)
        return interp.space.w_False

    w_directory = W_Directory(k_Directory, [])
    w_directory.path = space.newstr(directory)

    w_handle = W_DirResource(space, directory)
    w_handle.open()
    w_directory.handle = w_handle

    return w_directory


@wrap_method(['interp', ThisUnwrapper(W_Directory),
              Optional(Resource(W_DirResource, True))],
             name='Directory::read')
def dir_read(interp, this, w_dir=None):
    if w_dir is None:
        w_dir = this.handle
    assert isinstance(w_dir, W_DirResource)
    if not w_dir.is_valid():
        interp.warn("Directory::read(): %d is not a valid Directory resource"
                % w_dir.res_id)
        return interp.space.w_False
    return w_dir.read()


@wrap_method(['interp', ThisUnwrapper(W_Directory),
              Optional(Resource(W_DirResource, True))],
              name='Directory::rewind')
def dir_rewind(interp, this, w_dir=None):
    if w_dir is None:
        w_dir = this.handle
    if not w_dir.is_valid():
        interp.warn("Directory::rewind(): %d is not a valid Directory resource"
                % w_dir.res_id)
        return interp.space.w_False

    else:
        w_dir.rewind()
        return interp.space.w_Null


@wrap_method(['interp', ThisUnwrapper(W_Directory),
              Optional(Resource(W_DirResource, True))],
              name='Directory::close')
def dir_close(interp, this, w_dir=None):
    if not w_dir:
        w_dir = this.handle
    assert isinstance(w_dir, W_DirResource)
    w_dir.close()
    return interp.space.w_Null


k_Directory = def_class('Directory',
    [dir_read, dir_rewind, dir_close],
    [GetterSetterWrapper(_get_path, _set_path, "path", consts.ACC_PUBLIC),
     GetterSetterWrapper(_get_handle, _set_handle, "handle", consts.ACC_PUBLIC)],
    instance_class=W_Directory
)
