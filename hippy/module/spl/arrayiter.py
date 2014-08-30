from hippy.builtin_klass import k_Iterator
from hippy.builtin import Optional
from hippy.klass import def_class
from hippy.objects.base import W_Root
from hippy.objects.instanceobject import W_InstanceObject
from hippy import consts


class W_ArrayIterator(W_InstanceObject):
    def _get_storage(self, interp):
        return self.getattr(interp, "storage", k_ArrayIterator)


k_ArrayIterator = def_class(
    'ArrayIterator',
    ['__construct', 'append', 'count',
     'current', 'next', 'key', 'rewind', 'valid'],
    [('storage', consts.ACC_PRIVATE)],
    instance_class=W_ArrayIterator,
    implements=[k_Iterator])


@k_ArrayIterator.def_method(['interp', 'this', Optional(W_Root)])
def __construct(interp, this, w_arr=None):
    if w_arr is None:
        w_arr = interp.space.new_array_from_list([])
    elif isinstance(w_arr, W_InstanceObject):
        w_arr = w_arr.get_rdict_array(interp.space)
    this.setattr(interp, "storage", w_arr, k_ArrayIterator)


@k_ArrayIterator.def_method(['interp', 'this', W_Root])
def append(interp, this, w_newval):
    w_arr = this._get_storage(interp)
    w_arr.appenditem_inplace(interp.space, w_newval)


@k_ArrayIterator.def_method(['interp', 'this'])
def count(interp, this):
    w_arr = this._get_storage(interp)
    return interp.space.wrap(w_arr.arraylen())


@k_ArrayIterator.def_method(['interp', 'this'])
def current(interp, this):
    w_arr = this._get_storage(interp)
    return w_arr._current(interp.space)


@k_ArrayIterator.def_method([])
def next():
    pass


@k_ArrayIterator.def_method([])
def key():
    pass


@k_ArrayIterator.def_method([])
def rewind():
    pass


@k_ArrayIterator.def_method([])
def valid():
    pass
