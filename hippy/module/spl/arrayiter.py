from hippy.builtin_klass import k_Iterator
from hippy.builtin import Optional
from hippy.klass import def_class
from hippy.objects.base import W_Root
from hippy.objects.instanceobject import W_InstanceObject
from hippy import consts


class W_ArrayIterator(W_InstanceObject):
    pass


k_ArrayIterator = def_class(
    'ArrayIterator',
    ['__construct', 'current', 'next', 'key', 'rewind', 'valid'],
    [('storage', consts.ACC_PRIVATE)],
    instance_class=W_ArrayIterator,
    implements=[k_Iterator])


@k_ArrayIterator.def_method(['interp', 'this', Optional(W_Root)])
def __construct(interp, this, w_arr=None):
    if w_arr is None:
        w_arr = interp.space.new_array_from_list([])
    this.setattr(interp, "storage", w_arr, k_ArrayIterator)


@k_ArrayIterator.def_method([])
def current():
    pass


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
