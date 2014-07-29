from hippy.klass import def_class
from hippy.objects.base import W_Root
from hippy.builtin_klass import wrap_method
from hippy.builtin import ThisUnwrapper, Optional
from hippy.objects.instanceobject import W_InstanceObject


LEAVES_ONLY = 0
SELF_FIRST = 1
CHILD_FIRST = 2
CATCH_GET_CHILD = 16


class W_RecursiveIteratorIterator(W_InstanceObject):
    pass


@wrap_method(['interp', ThisUnwrapper(W_RecursiveIteratorIterator), Optional(W_Root)],
             name='RecursiveIteratorIterator::__construct')
def RecursiveIteratorIterator_construct(interp, this, w_arr=None):
    if w_arr is None:
        w_arr = interp.space.new_array_from_list([])
    this.setattr(interp, "storage", w_arr, k_ArrayIterator)


@wrap_method(['interp', ThisUnwrapper(W_RecursiveIteratorIterator)],
             name='RecursiveIteratorIterator::beginChildren')
def RecursiveIteratorIterator_beginChildren(interp, this):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_RecursiveIteratorIterator)],
             name='RecursiveIteratorIterator::beginIteration')
def RecursiveIteratorIterator_beginIteration(interp, this):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_RecursiveIteratorIterator)],
             name='RecursiveIteratorIterator::callGetChildren')
def RecursiveIteratorIterator_callGetChildren(interp, this):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_RecursiveIteratorIterator)],
             name='RecursiveIteratorIterator::callHasChildren')
def RecursiveIteratorIterator_callHasChildren(interp, this):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_RecursiveIteratorIterator)],
             name='RecursiveIteratorIterator::current')
def RecursiveIteratorIterator_current(interp, this):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_RecursiveIteratorIterator)],
             name='RecursiveIteratorIterator::endChildren')
def RecursiveIteratorIterator_endChildren(interp, this):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_RecursiveIteratorIterator)],
             name='RecursiveIteratorIterator::endIteration')
def RecursiveIteratorIterator_endIteration(interp, this):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_RecursiveIteratorIterator)],
             name='RecursiveIteratorIterator::getDepth')
def RecursiveIteratorIterator_getDepth(interp, this):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_RecursiveIteratorIterator)],
             name='RecursiveIteratorIterator::getInnerIterator')
def RecursiveIteratorIterator_getInnerIterator(interp, this):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_RecursiveIteratorIterator)],
             name='RecursiveIteratorIterator::getMaxDepth')
def RecursiveIteratorIterator_getMaxDepth(interp, this):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_RecursiveIteratorIterator)],
             name='RecursiveIteratorIterator::getSubIterator')
def RecursiveIteratorIterator_getSubIterator(interp, this):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_RecursiveIteratorIterator)],
             name='RecursiveIteratorIterator::key')
def RecursiveIteratorIterator_key(interp, this):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_RecursiveIteratorIterator)],
             name='RecursiveIteratorIterator::next')
def RecursiveIteratorIterator_next(interp, this):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_RecursiveIteratorIterator)],
             name='RecursiveIteratorIterator::nextElement')
def RecursiveIteratorIterator_nextElement(interp, this):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_RecursiveIteratorIterator)],
             name='RecursiveIteratorIterator::rewind')
def RecursiveIteratorIterator_rewind(interp, this):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_RecursiveIteratorIterator)],
             name='RecursiveIteratorIterator::setMaxDepth')
def RecursiveIteratorIterator_setMaxDepth(interp, this):
    raise NotImplementedError()


@wrap_method(['interp', ThisUnwrapper(W_RecursiveIteratorIterator)],
             name='RecursiveIteratorIterator::valid')
def RecursiveIteratorIterator_valid(interp, this):
    raise NotImplementedError()



def_class(
    'RecursiveIteratorIterator',
    [
        RecursiveIteratorIterator_construct,
        RecursiveIteratorIterator_beginChildren,
        RecursiveIteratorIterator_beginIteration,
        RecursiveIteratorIterator_callGetChildren,
        RecursiveIteratorIterator_callHasChildren,
        RecursiveIteratorIterator_current,
        RecursiveIteratorIterator_endChildren,
        RecursiveIteratorIterator_endIteration,
        RecursiveIteratorIterator_getDepth,
        RecursiveIteratorIterator_getInnerIterator,
        RecursiveIteratorIterator_getMaxDepth,
        RecursiveIteratorIterator_getSubIterator,
        RecursiveIteratorIterator_key,
        RecursiveIteratorIterator_next,
        RecursiveIteratorIterator_nextElement,
        RecursiveIteratorIterator_rewind,
        RecursiveIteratorIterator_setMaxDepth,
        RecursiveIteratorIterator_valid
    ],
    [],
    instance_class=W_RecursiveIteratorIterator,
    implements=["OuterIterator"]
)
