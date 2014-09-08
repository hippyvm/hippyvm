from hippy import consts
from hippy.klass import def_class
from hippy.builtin import wrap_method, ThisUnwrapper, Optional
from hippy.builtin_klass import new_abstract_method
from hippy.objects.base import W_Root
from hippy.objects.instanceobject import W_InstanceObject
from hippy.objects.intobject import W_IntObject
from hippy.module.spl.exception import (
    k_LogicException, k_BadMethodCallException, k_InvalidArgumentException,
    k_UnexpectedValueException)
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
    ['rewind', 'next',
     new_abstract_method(["interp"], name="FilterIterator::accept")],
    extends=k_IteratorIterator,
    flags=consts.ACC_ABSTRACT)


@k_FilterIterator.def_method(['interp', 'this'])
def rewind(interp, this):
    interp.call_method(this.inner, 'rewind', [])
    is_true = interp.space.is_true
    while is_true(interp.call_method(this.inner, 'valid', [])):
        if is_true(interp.call_method(this, 'accept', [])):
            return
        interp.call_method(this.inner, 'next', [])


@k_FilterIterator.def_method(['interp', 'this'])
def next(interp, this):
    is_true = interp.space.is_true
    while is_true(interp.call_method(this.inner, 'valid', [])):
        interp.call_method(this.inner, 'next', [])
        if is_true(interp.call_method(this, 'accept', [])):
            return


START, NEXT, TEST, SELF, CHILD = range(5)

class RII_Node(object):
    def __init__(self, w_iter):
        self.w_iter = w_iter
        self.state = START

class W_RecursiveIteratorIterator(W_InstanceObject):
    def get_current_iter(self):
        return self.stack[-1].w_iter

LEAVES_ONLY = 0
SELF_FIRST = 1
CHILD_FIRST = 2

k_RecursiveIteratorIterator = def_class(
    'RecursiveIteratorIterator',
    ['__construct', 'rewind', 'valid', 'key', 'current', 'next',
     'getInnerIterator', 'beginIteration', 'endIteration',
     'callHasChildren', 'callGetChildren', 'beginChildren', 'endChildren',
     'nextElement'],
    constants=[
        ('LEAVES_ONLY', W_IntObject(LEAVES_ONLY)),
        ('SELF_FIRST', W_IntObject(SELF_FIRST)),
        ('CHILD_FIRST', W_IntObject(CHILD_FIRST)),
    ],
    implements=[k_OuterIterator],
    instance_class=W_RecursiveIteratorIterator)

@k_RecursiveIteratorIterator.def_method(['interp', 'this', 'object',
                                         Optional(int)])
def __construct(interp, this, w_iter, mode=LEAVES_ONLY):
    if w_iter.klass.is_iterable:
        w_iter = interp.call_method(w_iter, 'getIterator', [])
    if (not isinstance(w_iter, W_InstanceObject) or
            not w_iter.klass.is_subclass_of_class_or_intf_name('RecursiveIterator')):
        raise interp.throw("An instance of RecursiveIterator or "
                           "IteratorAggregate creating it is required",
                           klass=k_InvalidArgumentException)
    this.w_iter = w_iter
    this.mode = mode
    this.in_iteration = False
    this.stack = [RII_Node(this.w_iter)]
    this.level = 0


@k_RecursiveIteratorIterator.def_method(['interp', 'this'])
def rewind(interp, this):
    this.stack = [RII_Node(this.w_iter)]
    this.level = 0
    if not this.in_iteration:
        interp.call_method(this, 'beginIteration', [])
        this.in_iteration = True
    _rii_next(interp, this)
    return


@k_RecursiveIteratorIterator.def_method(['interp', 'this'])
def valid(interp, this):
    space = interp.space
    level = this.level
    while level >= 0:
        w_sub_iter = this.stack[level].w_iter
        if space.is_true(interp.call_method(w_sub_iter, 'valid', [])):
            return space.w_True
        level -= 1
    if this.in_iteration:
        interp.call_method(this, 'endIteration', [])
        this.in_iteration = False
    return space.w_False

@k_RecursiveIteratorIterator.def_method(['interp', 'this'])
def key(interp, this):
    return interp.call_method(this.get_current_iter(), 'key', [])


@k_RecursiveIteratorIterator.def_method(['interp', 'this'])
def current(interp, this):
    return interp.call_method(this.get_current_iter(), 'current', [])


@k_RecursiveIteratorIterator.def_method(['interp', 'this'])
def next(interp, this):
    _rii_next(interp, this)

def _rii_next(interp, this):
    space = interp.space
    while this.level >= 0:
        while True:
            node = this.stack[-1]
            if node.state == NEXT:
                interp.call_method(node.w_iter, 'next', [])
                node.state = START
            elif node.state == START:
                if not space.is_true(interp.call_method(node.w_iter, 'valid', [])):
                    break
                node.state = TEST
            elif node.state == TEST:
                has_children = space.is_true(
                    interp.call_method(this, 'callHasChildren', []))
                if has_children:
                    if this.mode == SELF_FIRST:
                        node.state = SELF
                    else:
                        node.state = CHILD
                else:
                    node.state = NEXT
                    interp.call_method(this, 'nextElement', [])
                    return
            elif node.state == SELF:
                if this.mode == SELF_FIRST:
                    node.state = CHILD
                else:
                    node.state = NEXT
                interp.call_method(this, 'nextElement', [])
                return
            elif node.state == CHILD:
                w_child = interp.call_method(this, 'callGetChildren', [])
                if (not isinstance(w_child, W_InstanceObject) or
                        not w_child.klass.is_subclass_of_class_or_intf_name('RecursiveIterator')):
                    raise interp.throw(
                        "Objects returned by RecursiveIterator::getChildren() "
                        "must implement RecursiveIterator",
                        klass=k_UnexpectedValueException)
                if this.mode == CHILD_FIRST:
                    node.state = SELF
                else:
                    node.state = NEXT
                this.stack.append(RII_Node(w_child))
                this.level += 1
                interp.call_method(w_child, 'rewind', [])
                interp.call_method(this, 'beginChildren', [])
        if this.level > 0:
            interp.call_method(this, 'endChildren', [])
            this.stack.pop()
            this.level -= 1
        else:
            return


@k_RecursiveIteratorIterator.def_method(['interp', 'this'])
def getInnerIterator(interp, this):
    raise NotImplementedError


@k_RecursiveIteratorIterator.def_method(['interp', 'this'])
def beginIteration(interp, this):
    pass


@k_RecursiveIteratorIterator.def_method(['interp', 'this'])
def endIteration(interp, this):
    pass


@k_RecursiveIteratorIterator.def_method(['interp', 'this'])
def callHasChildren(interp, this):
    return interp.call_method(this.get_current_iter(), 'hasChildren', [])


@k_RecursiveIteratorIterator.def_method(['interp', 'this'])
def callGetChildren(interp, this):
    return interp.call_method(this.get_current_iter(), 'getChildren', [])


@k_RecursiveIteratorIterator.def_method(['interp', 'this'])
def beginChildren(interp, this):
    pass


@k_RecursiveIteratorIterator.def_method(['interp', 'this'])
def endChildren(interp, this):
    pass


@k_RecursiveIteratorIterator.def_method(['interp', 'this'])
def nextElement(interp, this):
    pass
