from hippy.klass import def_class
from hippy.builtin import wrap_method, ThisUnwrapper
from hippy.builtin_klass import new_abstract_method
from hippy.objects.base import W_Root
from hippy.objects.instanceobject import W_InstanceObject
from hippy.module.spl.exception import (
    k_LogicException, k_BadMethodCallException)
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
            interp.throw("The object is in an invalid state as the parent "
                "constructor was not called", klass=k_LogicException)

    def valid(self, interp):
        if self.inner is None:
            return False
        w_valid = interp.call_method(self.inner, 'valid', [])
        return interp.space.is_true(w_valid)


k_AppendIterator = def_class(
    'AppendIterator',
    ['__construct', 'append', 'next'],
    extends=k_IteratorIterator,
    instance_class=W_AppendIterator)


@k_AppendIterator.def_method(['interp', 'this'])
def __construct(interp, this):
    if this.w_iterators is not None:
        # This is a lie! AppendIterator::getIterator() doesn't even exist.
        # But who cares? Not PHP.
        interp.throw("AppendIterator::getIterator() must be called exactly "
            "once per instance", klass=k_BadMethodCallException)
    this.w_iterators = k_ArrayIterator.call_args(interp, [])
    this.inner = this.w_iterators

@k_AppendIterator.def_method(['interp', 'this', W_Root])
def append(interp, this, w_iterator):
    this.check_state(interp)
    interp.getmeth(this.w_iterators, 'append').call_args(interp, [w_iterator])
    this.inner = w_iterator
    w_valid = interp.call_method(w_iterator, 'valid', [])
    if not interp.space.is_true(w_valid):
        interp.call_method(w_iterator, 'rewind', [])

@k_AppendIterator.def_method(['interp', 'this'])
def next(interp, this):
    this.check_state(interp)
    if this.valid(interp):
        interp.call_method(this.inner, 'next', [])
    while not this.valid(interp):
        interp.call_method(this.w_iterators, 'next', [])
        w_valid = interp.call_method(this.w_iterators, 'valid', [])
        if interp.space.is_true(w_valid):
            this.inner = interp.call_method(this.w_iterators, 'current', [])
            interp.call_method(this.inner, 'rewind', [])
        else:
            return

k_FilterIterator = def_class(
    'FilterIterator',
    ['next',
     new_abstract_method(["interp"], name="FilterIterator::accept")],
    extends=k_IteratorIterator)

@k_FilterIterator.def_method(['interp', 'this'])
def next(interp, this):
    is_true = interp.space.is_true
    while is_true(interp.call_method(this.inner, 'valid', [])):
        interp.call_method(this.inner, 'next', [])
        if is_true(interp.call_method(this, 'accept', [])):
            return
