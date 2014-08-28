from hippy.klass import def_class
from hippy.builtin import wrap_method, ThisUnwrapper
from hippy.objects.instanceobject import W_InstanceObject
from hippy.module.spl.interface import k_OuterIterator


class W_IteratorIterator(W_InstanceObject):
    inner = None


@wrap_method(['interp', ThisUnwrapper(W_IteratorIterator), 'object'],
             name='IteratorIterator::__construct')
def ii_construct(interp, this, iterator):
    this.inner = iterator


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
