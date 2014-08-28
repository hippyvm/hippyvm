""" This module implements helpers for implementing builtin classes.
"""

from hippy.klass import GetterSetter, def_class
from hippy.builtin import wrap_method, Optional, ThisUnwrapper, Nullable

from hippy.objects.instanceobject import W_InstanceObject
from hippy import consts


class GetterSetterWrapper(object):
    def __init__(self, getter, setter, name, accflags):
        self.getter = getter
        self.setter = setter
        self.name = name
        self.accflags = accflags

    def build(self, klass):
        """NOT_RPYTHON: we need some magic RPython hackery here to convince
        the getter/setter functions that we're passing a "this" of the
        exact W_Xxx class rather than just a W_InstanceObject."""
        if klass.custom_instance_class is not None:
            W_ExactClass = klass.custom_instance_class
            real_getter = self.getter
            real_setter = self.setter
            def typecasting_getter(interp, this):
                assert isinstance(this, W_ExactClass)
                return real_getter(interp, this)
            def typecasting_setter(interp, this, w_newvalue):
                assert isinstance(this, W_ExactClass)
                return real_setter(interp, this, w_newvalue)
            getter = typecasting_getter
            setter = typecasting_setter
        else:
            getter = self.getter
            setter = self.setter
        return GetterSetter(getter, setter, self.name, klass,
                            self.accflags)


class W_ExceptionObject(W_InstanceObject):
    def setup(self, interp):
        self.traceback = interp.get_traceback()

    def get_message(self, interp):
        return self.getattr(interp, 'message', k_Exception)


@wrap_method(['interp', ThisUnwrapper(W_ExceptionObject),
              Optional(str), Optional(int), Optional(Nullable('object'))],
             name='Exception::__construct')
def new_exception(interp, this, message='', code=0, w_previous=None):
    space = interp.space
    this.setattr(interp, 'file', space.wrap(this.traceback[0][0]), k_Exception)
    this.setattr(interp, 'message', space.wrap(message), k_Exception)
    this.setattr(interp, 'code', space.wrap(code), k_Exception)
    if w_previous is None:
        w_previous = space.w_Null
    elif not k_Exception.is_parent_of(w_previous.klass):
        interp.fatal("Wrong parameters for "
                     "Exception([string $exception [, long $code [, "
                     "Exception $previous = NULL]]])")
    this.setattr(interp, 'previous', w_previous, k_Exception)


@wrap_method(['interp', 'this'], name='Exception::getMessage')
def exc_getMessage(interp, this):
    return this.getattr(interp, 'message', k_Exception)


@wrap_method(['interp', 'this'], name='Exception::getCode')
def exc_getCode(interp, this):
    return this.getattr(interp, 'code', k_Exception)


@wrap_method(['interp', 'this'], name='Exception::getPrevious')
def exc_getPrevious(interp, this):
    return this.getattr(interp, 'previous', k_Exception)


@wrap_method(['interp', ThisUnwrapper(W_ExceptionObject)],
             name='Exception::getTrace')
def exc_getTrace(interp, this):
    from hippy.module.internal import backtrace_to_applevel
    return backtrace_to_applevel(interp.space, this.traceback)

@wrap_method(['interp', ThisUnwrapper(W_ExceptionObject)],
             name='Exception::getFile')
def exc_getFile(interp, this):
    return this.getattr(interp, 'file', k_Exception)

@wrap_method(['interp', ThisUnwrapper(W_ExceptionObject)],
             name='Exception::getLine')
def exc_getLine(interp, this):
    return this.getattr(interp, 'line', k_Exception)

@wrap_method(['interp', ThisUnwrapper(W_ExceptionObject)],
             name='Exception::__toString')
def exc___toString(interp, this):
    name = this.klass.name
    space = interp.space
    message = space.str_w(this.getattr(interp, 'message', k_Exception))
    file = space.str_w(this.getattr(interp, 'file', k_Exception))
    line = space.int_w(this.getattr(interp, 'line', k_Exception))
    msg = ["exception '%s' with message '%s' in %s:%d" %
           (name, message, file, line)]
    msg.append("Stack trace")
    for i, (filename, funcname, line, source) in enumerate(this.traceback):
        msg.append("#%d %s(%d): %s()" % (i, filename, line, funcname))
    return space.wrap("\n".join(msg))

@wrap_method(['interp', ThisUnwrapper(W_ExceptionObject)],
             name='Exception::getTraceAsString')
def exc_getTraceAsString(interp, this):
    msg = []
    for i, (filename, funcname, line, source) in enumerate(this.traceback):
        msg.append("#%d %s(%d): %s()" % (i, filename, line, funcname))
    return interp.space.wrap("\n".join(msg))


k_Exception = def_class('Exception',
    [new_exception, exc_getMessage, exc_getCode, exc_getPrevious,
     exc_getTrace, exc_getFile, exc_getLine, exc___toString,
     exc_getTraceAsString],
    [('message', consts.ACC_PROTECTED),
    ('code', consts.ACC_PROTECTED),
    ('previous', consts.ACC_PRIVATE),
    ('file', consts.ACC_PROTECTED),
    ('line', consts.ACC_PROTECTED)],
    instance_class=W_ExceptionObject)

def_class('OutOfBoundsException', [], extends=k_Exception)
k_stdClass = def_class('stdClass', [])
k_incomplete = def_class('__PHP_Incomplete_Class', [])
k_RuntimeException = def_class('RuntimeException', [], extends=k_Exception)
k_LogicException = def_class('LogicException', [], extends=k_Exception)
k_DomainException = def_class('DomainException', [], extends=k_Exception)
k_UnexpectedValueException = def_class('UnexpectedValueException', [],
                                       extends=k_Exception)


def new_abstract_method(args, **kwds):
    name = kwds['name']
    assert args[0] == 'interp'
    kwds['flags'] = kwds.get('flags', 0) | consts.ACC_ABSTRACT

    def method(interp, *args):
        interp.fatal("Cannot call abstract method %s()" % (name,))
    return wrap_method(args, **kwds)(method)


k_Iterator = def_class('Iterator',
    [new_abstract_method(["interp"], name="Iterator::current"),
     new_abstract_method(["interp"], name="Iterator::next"),
     new_abstract_method(["interp"], name="Iterator::key"),
     new_abstract_method(["interp"], name="Iterator::rewind"),
     new_abstract_method(["interp"], name="Iterator::valid")],
    flags=consts.ACC_INTERFACE | consts.ACC_ABSTRACT,
    is_iterator=True
)


ArrayAccess = def_class('ArrayAccess', [
    new_abstract_method(["interp"], name="ArrayAccess::offsetExists"),
    new_abstract_method(["interp"], name="ArrayAccess::offsetGet"),
    new_abstract_method(["interp"], name="ArrayAccess::offsetSet"),
    new_abstract_method(["interp"], name="ArrayAccess::offsetUnset"),],
    flags=consts.ACC_INTERFACE | consts.ACC_ABSTRACT,
    is_array_access=True)


def_class('Reflector',
          [new_abstract_method(["interp"], name="Reflector::export"),
           new_abstract_method(["interp"], name="Reflector::__toString")],
          flags=consts.ACC_INTERFACE | consts.ACC_ABSTRACT)
