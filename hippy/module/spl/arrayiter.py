from hippy.builtin_klass import (
    k_Iterator, GetterSetterWrapper, k_ArrayAccess, k_IteratorAggregate, ThisUnwrapper)
from hippy.builtin import Optional, wrap_method
from hippy.klass import def_class
from hippy.objects.base import W_Root
from hippy.objects.arrayobject import W_ArrayObject
from hippy.objects.instanceobject import W_InstanceObject
from hippy import consts
from hippy.module.spl.exception import k_InvalidArgumentException
from hippy.module.spl.interface import k_RecursiveIterator


class W_SplArray(W_InstanceObject):
    w_arr = None

    def get_rdict_array(self, space):
        w_arr = self.w_arr
        while isinstance(w_arr, W_SplArray):
            w_arr = w_arr.w_arr
        if isinstance(w_arr, W_InstanceObject):
            return w_arr.get_rdict_array(space)
        assert isinstance(w_arr, W_ArrayObject)
        return w_arr

class W_ArrayIterator(W_SplArray):
    _iter = None

def _get_storage(interp, this):
    return this.w_arr

def _set_storage(interp, this, w_arr):
    raise NotImplementedError


k_ArrayObject = def_class(
    'ArrayObject',
    ['__construct', 'offsetExists', 'offsetGet', 'offsetSet', 'offsetUnset',
     'append', 'count',
     'getIterator'],
    [GetterSetterWrapper(_get_storage, _set_storage, 'storage', consts.ACC_PRIVATE)],
    instance_class=W_SplArray,
    implements=[k_IteratorAggregate, k_ArrayAccess])


k_ArrayIterator = def_class(
    'ArrayIterator',
    ['__construct', 'offsetExists', 'offsetGet', 'offsetSet', 'offsetUnset',
     'append', 'count',
     'current', 'next', 'key', 'rewind', 'valid'],
    [GetterSetterWrapper(_get_storage, _set_storage, 'storage', consts.ACC_PRIVATE)],
    instance_class=W_ArrayIterator,
    implements=[k_ArrayAccess, k_Iterator])


@k_ArrayObject.def_method(['interp', 'this', Optional(W_Root), Optional(int),
    Optional(str)])
def __construct(interp, this, w_arr=None, flags=0,
        iterator_class='ArrayIterator'):
    if w_arr is None:
        w_arr = interp.space.new_array_from_list([])
    if (not isinstance(w_arr, W_InstanceObject) and
            not isinstance(w_arr, W_ArrayObject)):
        raise interp.throw("Passed variable is not an array or object, using "
            "empty array instead", klass=k_InvalidArgumentException)
    this.iterator_class = iterator_class
    this.w_arr = w_arr


@k_ArrayIterator.def_method(['interp', 'this', Optional(W_Root)])
def __construct(interp, this, w_arr=None):
    if w_arr is None:
        w_arr = interp.space.new_array_from_list([])
    if (not isinstance(w_arr, W_InstanceObject) and
            not isinstance(w_arr, W_ArrayObject)):
        raise interp.throw("Passed variable is not an array or object, using "
            "empty array instead", klass=k_InvalidArgumentException)
    this.w_arr = w_arr
    while isinstance(w_arr, W_SplArray):
        w_arr = w_arr.w_arr
    this._iter = w_arr.create_iter(interp.space)


@k_ArrayObject.def_method(['interp', 'this', W_Root])
@k_ArrayIterator.def_method(['interp', 'this', W_Root])
def offsetExists(interp, this, w_index):
    return interp.space.newbool(this.w_arr.isset_index(interp.space, w_index))


@k_ArrayObject.def_method(['interp', 'this', W_Root])
@k_ArrayIterator.def_method(['interp', 'this', W_Root])
def offsetGet(interp, this, w_index):
    w_arr = this.get_rdict_array(interp.space)
    return w_arr.getitem(interp.space, w_index, give_notice=True)

@k_ArrayObject.def_method(['interp', 'this', W_Root, W_Root])
@k_ArrayIterator.def_method(['interp', 'this', W_Root, W_Root])
def offsetSet(interp, this, w_index, w_newval):
    w_arr = this.get_rdict_array(interp.space)
    if w_index == interp.space.w_Null:
        w_arr.appenditem_inplace(interp.space, w_newval)
    else:
        w_arr, _ = this.w_arr.setitem2_maybe_inplace(interp.space,
                                                    w_index, w_newval)
        this.w_arr = w_arr


@k_ArrayObject.def_method(['interp', 'this', W_Root])
@k_ArrayIterator.def_method(['interp', 'this', W_Root])
def offsetUnset(interp, this, w_index):
    w_arr = this.get_rdict_array(interp.space)
    this.w_arr = w_arr._unsetitem(interp.space, w_index)

@k_ArrayObject.def_method(['interp', 'this', W_Root])
@k_ArrayIterator.def_method(['interp', 'this', W_Root])
def append(interp, this, w_newval):
    w_arr = this.get_rdict_array(interp.space)
    w_arr.appenditem_inplace(interp.space, w_newval)


@k_ArrayObject.def_method(['interp', 'this'])
@k_ArrayIterator.def_method(['interp', 'this'])
def count(interp, this):
    w_arr = this.get_rdict_array(interp.space)
    return interp.space.wrap(w_arr.arraylen())


@k_ArrayObject.def_method(['interp', 'this'])
def getIterator(interp, this):
    k_IteratorClass = interp.locate_class_or_intf(this.iterator_class)
    return k_IteratorClass.call_args(interp, [this])


@k_ArrayIterator.def_method(['interp', 'this'])
def current(interp, this):
    return this._iter.current(interp)


@k_ArrayIterator.def_method(['interp', 'this'])
def next(interp, this):
    return this._iter.next(interp.space)


@k_ArrayIterator.def_method(['interp', 'this'])
def key(interp, this):
    return this._iter.key(interp)


@k_ArrayIterator.def_method(['interp', 'this'])
def rewind(interp, this):
    this._iter.rewind(interp)


@k_ArrayIterator.def_method(['interp', 'this'])
def valid(interp, this):
    return interp.space.newbool(this._iter.valid(interp))


class W_RecursiveArrayIterator(W_ArrayIterator):

    def get_children(self, interp):
        if not self.has_children(interp):
            raise interp.throw("Passed variable is not an array or object, "
                "using empty array instead",
                klass=k_InvalidArgumentException)
        return self._iter.current(interp)

    def has_children(self, interp):
        w_current = self._iter.current(interp)
        if isinstance(w_current, W_ArrayObject):
            return True
        if isinstance(w_current, W_InstanceObject) and \
           w_current.klass.is_iterator:
            return True
        else:
            return False


@wrap_method(['interp', ThisUnwrapper(W_RecursiveArrayIterator)],
             name='RecursiveArrayIterator::getChildren')
def RecursiveArrayIterator_getChildren(interp, this):
    w_children = this.get_children(interp.space)
    return RecursiveArrayIterator.call_args(interp, [w_children])


@wrap_method(['interp', ThisUnwrapper(W_RecursiveArrayIterator)],
             name='RecursiveArrayIterator::hasChildren')
def RecursiveArrayIterator_hasChildren(interp, this):
    return interp.space.wrap(this.has_children(interp.space))


RecursiveArrayIterator = def_class(
    'RecursiveArrayIterator',
    [RecursiveArrayIterator_getChildren,
     RecursiveArrayIterator_hasChildren],
    [],
    instance_class=W_RecursiveArrayIterator,
    implements=[k_RecursiveIterator],
    extends=k_ArrayIterator)
