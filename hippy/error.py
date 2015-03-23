

class InterpreterError(Exception):
    def __init__(self, msg, tb=None):
        self.msg = msg
        self.traceback = tb

    def __str__(self):
        "NOT_RPYTHON"
        return self.msg


class FatalError(InterpreterError):
    pass


class IllegalInstruction(InterpreterError):
    pass


class InvalidCallback(InterpreterError):
    """Raised by space.get_callback()"""


class ConvertError(InterpreterError):
    """Raised when a type conversion fails"""


class OffsetError(InterpreterError):
    """Raised when an indexing operation fails"""


class ExplicitExitException(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message


class Throw(Exception):
    def __init__(self, w_exc):
        from hippy.objects.instanceobject import W_InstanceObject

        assert isinstance(w_exc, W_InstanceObject)
        self.w_exc = w_exc
PHPException = Throw  # deprecated alias


def _contextname(contextclass):
    if contextclass is None:
        return ''
    return contextclass.name


class VisibilityError(Exception):
    def __init__(self, visibility, klass, name, contextclass):
        from hippy.klass import ClassBase
        assert isinstance(klass, ClassBase)
        self.visibility = visibility
        self.klass = klass
        self.name = name
        self.contextclass = contextclass

    def reraise_property(self, interp):
        interp.fatal('Cannot access %s property %s::$%s' % (
            self.visibility, self.klass.name, self.name))

    def msg_fatal(self):
        if self.visibility == "undefined":
            return ("Call to undefined method %s::%s()" % (
                self.klass.name, self.name))
        else:
            return ("Call to %s method %s::%s() from context '%s'" % (
                self.visibility, self.klass.name, self.name,
                _contextname(self.contextclass)))

    def msg_callback(self, static):
        if static:
            cls = self.klass
        else:
            cls = self.contextclass or self.klass
        if self.visibility == 'undefined':
            return ("class '%s' does not have a method '%s'" % (
                cls.name, self.name))
        else:
            return ('cannot access %s method %s::%s()' % (
                self.visibility, cls.name, self.name))

    def reraise_magic(self, interp):
        interp.fatal("Call to %s %s::%s() from context '%s'" % (
            self.visibility, self.klass.name, self.name,
            _contextname(self.contextclass)))

    def __repr__(self):
        return 'VisibilityError(%r, %r, %r, %r)' % (self.visibility,
                                                    self.klass, self.name,
                                                    self.contextclass)


class SignalReceived(Exception):
    pass
