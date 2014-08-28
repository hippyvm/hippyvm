from hippy.builtin_klass import k_Iterator
from hippy.builtin import ThisUnwrapper, Optional, wrap_method
from hippy.klass import def_class
from hippy.objects.base import W_Root
from hippy.objects.instanceobject import W_InstanceObject
from hippy import consts


class W_ApplevelArrayIterator(W_InstanceObject):
    pass


@wrap_method(['interp', ThisUnwrapper(W_ApplevelArrayIterator),
              Optional(W_Root)],
             name='ArrayIterator::__construct')
def ArrayIterator_construct(interp, this, w_arr=None):
    if w_arr is None:
        w_arr = interp.space.new_array_from_list([])
    this.setattr(interp, "storage", w_arr, k_ArrayIterator)


@wrap_method([], name='ArrayIterator::current')
def ArrayIterator_current():
    pass


@wrap_method([], name='ArrayIterator::next')
def ArrayIterator_next():
    pass


@wrap_method([], name='ArrayIterator::key')
def ArrayIterator_key():
    pass


@wrap_method([], name='ArrayIterator::rewind')
def ArrayIterator_rewind():
    pass


@wrap_method([], name='ArrayIterator::valid')
def ArrayIterator_valid():
    pass


k_ArrayIterator = def_class(
    'ArrayIterator',
    [ArrayIterator_construct,
     ArrayIterator_current,
     ArrayIterator_next,
     ArrayIterator_key,
     ArrayIterator_rewind,
     ArrayIterator_valid],
    [('storage', consts.ACC_PRIVATE)],
    instance_class=W_ApplevelArrayIterator,
    implements=[k_Iterator])
