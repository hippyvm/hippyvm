from hippy.error import PHPException
from hippy.klass import def_class
from hippy.builtin import wrap_method, ThisUnwrapper
from hippy.objects.base import W_Root
from hippy.objects.instanceobject import W_InstanceObject
from hippy.builtin_klass import k_LogicException
from hippy.module.spl.interface import k_OuterIterator
from hippy.module.spl.arrayiter import k_ArrayIterator


class W_IteratorIterator(W_InstanceObject):
    inner = None


@wrap_method(['interp', ThisUnwrapper(W_IteratorIterator), 'object'],
             name='IteratorIterator::__construct')
def ii_construct(interp, this, w_iterator):
    if w_iterator.klass.is_iterable:
        w_iterator = interp.getmeth(w_iterator, 'getIterator').call_args(interp, [])
    this.inner = w_iterator


@wrap_method(['interp', ThisUnwrapper(W_IteratorIterator)],
             name='IteratorIterator::current')
def ii_current(interp, this):
    return interp.getmeth(this.inner, 'current').call_args(interp, [])

@wrap_method(['interp', ThisUnwrapper(W_IteratorIterator)],
             name='IteratorIterator::getInnerIterator')
def ii_getInnerIterator(interp, this):
    return this.inner

@wrap_method(['interp', ThisUnwrapper(W_IteratorIterator)],
             name='IteratorIterator::key')
def ii_key(interp, this):
    return interp.getmeth(this.inner, 'key').call_args(interp, [])

@wrap_method(['interp', ThisUnwrapper(W_IteratorIterator)],
             name='IteratorIterator::next')
def ii_next(interp, this):
    return interp.getmeth(this.inner, 'next').call_args(interp, [])

@wrap_method(['interp', ThisUnwrapper(W_IteratorIterator)],
             name='IteratorIterator::rewind')
def ii_rewind(interp, this):
    return interp.getmeth(this.inner, 'rewind').call_args(interp, [])

@wrap_method(['interp', ThisUnwrapper(W_IteratorIterator)],
             name='IteratorIterator::valid')
def ii_valid(interp, this):
    return interp.getmeth(this.inner, 'valid').call_args(interp, [])

k_IteratorIterator = def_class(
    'IteratorIterator',
    [ii_construct, ii_current, ii_getInnerIterator, ii_key, ii_next,
     ii_rewind, ii_valid],
    implements=[k_OuterIterator],
    instance_class=W_IteratorIterator)


class W_AppendIterator(W_IteratorIterator):
    w_iterators = None
    def check_state(self, interp):
        if self.w_iterators is None:
            raise PHPException(k_LogicException.call_args(interp, [interp.space.wrap(
                "The object is in an invalid state as the parent constructor "
                "was not called")]))



k_AppendIterator = def_class(
    'AppendIterator',
    ['__construct', 'append'],
    extends=k_IteratorIterator,
    implements=[k_OuterIterator],
    instance_class=W_AppendIterator)


@k_AppendIterator.def_method(['interp', 'this'])
def __construct(interp, this):
    this.w_iterators = k_ArrayIterator.call_args(interp, [])
    this.inner = this.w_iterators

@k_AppendIterator.def_method(['interp', 'this', W_Root])
def append(interp, this, w_iterator):
    this.check_state(interp)
    interp.getmeth(this.w_iterators, 'append').call_args(interp, [w_iterator])
    this.inner = w_iterator
