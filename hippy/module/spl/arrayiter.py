from hippy.builtin_klass import wrap_method
from hippy.builtin import ThisUnwrapper, Optional
from hippy.klass import def_class
from hippy.error import PHPException
from hippy.objects.base import W_Root

from hippy.objects.instanceobject import W_InstanceObject

from hippy.objects.arrayobject import W_ListArrayObject, W_RDictArrayObject
from hippy import consts


class W_ArrayIterator(W_InstanceObject):

    def create_iter(self, space, contextclass=None):
        return self.w_obj_iter

    def offset_exists(self, space, index):
        return space.wrap(self.w_obj.hasitem(space, index))

    def offset_get(self, space, index):
        return self.w_obj.getitem(space, index)

    def offset_set(self, space, index, value):
        _, value = self.w_obj.setitem2_maybe_inplace(space, index, value)
        return value

    def offset_unset(self, space, index):
        self.w_obj._unsetitem(space, index)

    def seek(self, space, index):
        raise NotImplementedError()

    def current(self, space):
        return self.w_obj_iter.current(space)

    def next(self, space):
        return self.w_obj_iter.next(space)

    def key(self, space):
        return self.w_obj_iter.key(space)

    def rewind(self, space):
        return self.w_obj_iter.rewind(space)

    def valid(self, space):
        raise NotImplementedError()

    def count(self, space):
        return self.w_obj_iter.len(space)

    def done(self):
        return self.w_obj_iter.done()


@wrap_method(['interp', ThisUnwrapper(W_ArrayIterator), Optional(W_Root)],
             name='ArrayIterator::__construct')
def ArrayIterator_construct(interp, this, w_obj=None):
    this.w_obj = w_obj
    this.w_obj_iter = w_obj.create_iter(interp.space)

@wrap_method(['interp', ThisUnwrapper(W_ArrayIterator), W_Root],
             name='ArrayIterator::offsetExists')
def ArrayIterator_offsetExists(interp, this, index):
    return this.offset_exists(interp.space, index)


@wrap_method(['interp', ThisUnwrapper(W_ArrayIterator), W_Root],
             name='ArrayIterator::offsetGet')
def ArrayIterator_offsetGet(interp, this, index):
    return this.offset_get(interp.space, index)


@wrap_method(['interp', ThisUnwrapper(W_ArrayIterator), W_Root, W_Root],
             name='ArrayIterator::offsetSet')
def ArrayIterator_offsetSet(interp, this, index, value):
    return this.offset_set(interp.space, index, value)


@wrap_method(['interp', ThisUnwrapper(W_ArrayIterator), W_Root],
             name='ArrayIterator::offsetUnset')
def ArrayIterator_offsetUnset(interp, this, index):
    return this.offset_unset(interp.space, index)


@wrap_method(['interp', ThisUnwrapper(W_ArrayIterator), W_Root],
             name='ArrayIterator::seek')
def ArrayIterator_seek(interp, this, index):
    return this.seek(interp.space, index)


@wrap_method(['interp', ThisUnwrapper(W_ArrayIterator)],
             name='ArrayIterator::current')
def ArrayIterator_current(interp, this):
    return this.current(interp.space)


@wrap_method(['interp', ThisUnwrapper(W_ArrayIterator)],
             name='ArrayIterator::next')
def ArrayIterator_next(interp, this):
    return this.next(interp.space)


@wrap_method(['interp', ThisUnwrapper(W_ArrayIterator)],
             name='ArrayIterator::key')
def ArrayIterator_key(interp, this):
    return this.key(interp.space)


@wrap_method(['interp', ThisUnwrapper(W_ArrayIterator)],
             name='ArrayIterator::rewind')
def ArrayIterator_rewind(interp, this):
    return this.rewind(interp.space)


@wrap_method(['interp', ThisUnwrapper(W_ArrayIterator)],
             name='ArrayIterator::valid')
def ArrayIterator_valid(interp, this):
    pass


@wrap_method(['interp', ThisUnwrapper(W_ArrayIterator)],
             name='ArrayIterator::count')
def ArrayIterator_count(interp, this):
    return this.count(interp.space)


ArrayIterator = def_class(
    'ArrayIterator',
    [ArrayIterator_construct,
     ArrayIterator_offsetExists,
     ArrayIterator_offsetGet,
     ArrayIterator_offsetSet,
     ArrayIterator_offsetUnset,
     ArrayIterator_seek,
     ArrayIterator_current,
     ArrayIterator_next,
     ArrayIterator_key,
     ArrayIterator_rewind,
     ArrayIterator_valid,
     ArrayIterator_count],
    [('storage', consts.ACC_PRIVATE)],
    instance_class=W_ArrayIterator,
    implements=["ArrayAccess", "SeekableIterator", "Countable"]
)


class W_RecursiveArrayIterator(W_ArrayIterator):

    def get_children(self, space):
        interp = space.ec.interpreter
        if not self.has_children(space):
            exception = interp._class_get('InvalidArgumentException')
            raise PHPException(exception.call_args(
                interp, [interp.space.wrap(
                    "Passed variable is not an array or object, using empty array instead"
                )]
            ))

        return self.current(space)

    def has_children(self, space):
        w_current = self.current(space)

        if isinstance(w_current, W_ListArrayObject):
            return True
        if isinstance(w_current, W_RDictArrayObject):
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
    implements=["RecursiveIterator"],
    extends=ArrayIterator
)

