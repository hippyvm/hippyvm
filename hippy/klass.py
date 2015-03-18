from hippy.function import AbstractFunction
from hippy.ast import AccessMixin, CompilerError, DelayedObject
from hippy.error import Throw, VisibilityError, InterpreterError
from hippy.objects.reference import W_Reference
from hippy.objects.instanceobject import (
    W_InstanceObject, LOOKUP_SETATTR, LOOKUP_GETATTR, LOOKUP_HASATTR,
    LOOKUP_DELATTR, SpecialPropertyReturn)
from hippy.objects.strobject import W_StringObject
from hippy import consts
from hippy.objects.nullobject import w_Null
from hippy.mapdict import Terminator, Attribute
from hippy.builtin import (
    BuiltinFunction, ThisUnwrapper, handle_as_warning, new_function)
from rpython.rlib import jit
from rpython.rlib.objectmodel import we_are_translated
from rpython.rlib.unroll import unrolling_iterable
from collections import OrderedDict


class ClassDeclarationError(InterpreterError):
    """Raised when a class declaration violates some constraint of the
    language"""


def _msg_abstract(name, abstract_methods):
    lgt = len(abstract_methods)
    if len(abstract_methods) > 3:
        abstract_methods = abstract_methods[:3] + ['...']
    return ("Class %s contains %d abstract method%s and must "
            "therefore be declared abstract or implement the "
            "remaining methods (%s)" % (name,
                                        lgt,
                                        "s"[:len(abstract_methods) > 1],
                                        ', '.join(abstract_methods)))

_MAGIC_METHODS = ['__clone', '__get', '__set', '__unset', '__isset', '__call',
                  '__callstatic', '__tostring', '__invoke']

magic_methods_unrolled = unrolling_iterable(_MAGIC_METHODS)

rec_custom_get_set = {}


def normalize_access(access_flags):
    if not (access_flags & consts.ACCMASK_VISIBILITY):
        access_flags |= consts.ACC_PUBLIC
    assert (access_flags & consts.ACCMASK_VISIBILITY) in (
        consts.ACC_PUBLIC,
        consts.ACC_PROTECTED,
        consts.ACC_PRIVATE)
    return access_flags


class ClassBase(AbstractFunction, AccessMixin):
    access_flags = 0
    constructor_method = None
    method__clone = None
    method__get = None
    method__set = None
    method__unset = None
    method__isset = None
    method__call = None
    method__callstatic = None
    method__tostring = None
    method__invoke = None
    custom_instance_class = None
    is_iterator = False
    is_array_access = False
    is_iterable = False
    immediate_parents = None
    parentclass = None
    _all_nonstatic_special_properties = None    # lazy

    _immutable_fields_ = ['custom_instance_class', 'constructor_method',
                          'parentclass']

    def __init__(self, name):
        self.name = name
        self.constants_w = {}
        self.properties = OrderedDict()
        self.methods = OrderedDict()
        self.all_parents = {self.get_identifier(): None}  # classes and intfs
        self.base_map = Terminator(self)
        self.initial_storage_w = None
        self.is_subclassed = False # for pypy bridge

    def __repr__(self):
        if self.is_interface():
            cat = 'Interface'
        else:
            cat = 'Class'
        return '<%s %r>' % (cat, self.name)

    def _init_constructor(self):
        if '__construct' in self.methods:
            method = self.methods['__construct']
        elif self.get_identifier() in self.methods:
            method = self.methods[self.get_identifier()]
        else:
            return
        if method is None:
            return
        if method.is_static():
            raise CompilerError("Constructor %s cannot be static" %
                                (method.repr()))
        self.constructor_method = method

    def _collect_all_methods(self):
        all_methods = []
        seen = {}
        seenclasses = {}
        seenclasses[None] = None
        pending = [self]
        while len(pending) > 0:
            fromclass = pending.pop(0)
            if fromclass in seenclasses:
                continue
            seenclasses[fromclass] = None
            for meth_id, m in fromclass.methods.iteritems():
                if meth_id not in seen:
                    seen[meth_id] = None
                    all_methods.append(m)
            pending.extend(fromclass.immediate_parents)
        return all_methods

    def _check_abstract_methods(self):
        if self.is_abstract():
            return
        all_methods = self._collect_all_methods()
        abstract_methods = []
        for m in all_methods:
            if m.is_abstract():
                abstract_methods.append("%s::%s" % (
                    m.getclass().name, m.get_name()))
        if abstract_methods:
            msg = _msg_abstract(self.name, abstract_methods)
            raise ClassDeclarationError(msg)

    def _inherit_method(self, parent_method):
        meth_id = parent_method.get_identifier()
        if meth_id not in self.methods:
            self.methods[meth_id] = parent_method

    def _check_inheritance(self, method, parent_method):
        if parent_method.is_final():
            raise ClassDeclarationError(
                "Cannot override final method %s" % parent_method.repr())
        if parent_method.is_public() and not method.is_public():
            raise ClassDeclarationError(
                "Access level to %s must be public (as in class %s)" %
                (method.repr(), parent_method.getclass().name))
        if parent_method.is_protected() and method.is_private():
            raise ClassDeclarationError(
                "Access level to %s must be protected (as in class %s) or "
                "weaker" % (method.repr(), parent_method.getclass().name))
        if method.is_static() and not parent_method.is_static():
            raise ClassDeclarationError(
                "Cannot make non static method %s static in class %s" %
                (parent_method.repr(), method.getclass().name))
        if not method.is_static() and parent_method.is_static():
            raise ClassDeclarationError(
                "Cannot make static method %s non static in class %s" %
                (parent_method.repr(), method.getclass().name))

    def _init_protocol_flags(self):
        """Handle the builtin interfaces with special meaning in the core"""
        for parent in self.immediate_parents:
            if parent.is_iterator:  # implements Iterator
                self.is_iterator = True
                break
        for parent in self.immediate_parents:
            if parent.is_iterable:  # implements IteratorAggregate
                self.is_iterable = True
                break
        for parent in self.immediate_parents:
            if parent.is_array_access:  # implements ArrayAccess
                self.is_array_access = True
                break
        if self.is_iterator and self.is_iterable:
            raise ClassDeclarationError(
                "Class %s cannot implement both Iterator and IteratorAggregate"
                " at the same time" % self.name)

    def _make_property(self, prop, w_initial_value):
        if isinstance(prop, tuple):
            name, access_flags = prop
            p = Property(name, self, access_flags, w_initial_value)
            self.properties[name] = p
        elif not we_are_translated():  # compile time only
            prop = prop.build(self)
            self.properties[prop.name] = prop

    def _inherit_property(self, prop):
        if prop.is_private():
            return
        name = prop.name
        if name not in self.properties:
            self.properties[name] = prop.copy()
            return
        derived = self.properties[name]
        if derived.is_static() and not prop.is_static():
            raise ClassDeclarationError("Cannot redeclare non static %s as static %s" %
                    (prop.repr(), derived.repr()))
        if not derived.is_static() and prop.is_static():
            raise ClassDeclarationError("Cannot redeclare static %s as non static %s" %
                    (prop.repr(), derived.repr()))
        if prop.is_public() and not derived.is_public():
            raise ClassDeclarationError("Access level to %s must be public "
                    "(as in class %s)" %
                    (derived.repr(), prop.klass.name))
        if prop.is_protected() and derived.is_private():
            raise ClassDeclarationError("Access level to %s must be protected "
                    "(as in class %s) or weaker" %
                    (derived.repr(), prop.klass.name))

    def _init_magic_methods(self, interp):
        for name in magic_methods_unrolled:
            if name in self.methods:
                method = self.methods[name]
            else:
                continue
            if name == '__call':
                if (method.getclass() == self and
                        (method.is_static() or not method.is_public())):
                    interp.warn("The magic method __call() must have "
                            "public visibility and cannot be static")
            setattr(self, 'method' + name, method)

    def _create_initial_storage(self, space):
        l = []
        base_map = self.base_map
        for p in self.properties.itervalues():
            if not p.is_static() and not p.is_special and p.klass is self:
                w_val = p.value.eval_static(space)
                base_map = base_map.add_attribute(p.mangled_name)
                assert isinstance(base_map, Attribute)
                assert base_map.index == len(l)
                l.append(w_val)
        self.base_map = base_map
        if self.parentclass is not None:
            parent = self.parentclass
            if parent.initial_storage_w is None:
                parent._create_initial_storage(space)
            allattrs = parent.base_map.get_all_attrs()
            allmykeys = self.base_map.get_all_keys()
            d = {}
            for key in allmykeys:
                d[key] = None
            for parent_attr in allattrs:
                key = parent_attr.name
                w_value = parent.initial_storage_w[parent_attr.index]
                if (key.startswith('\x00*\x00') and
                        key[3:] in d):
                    continue
                if key in d:
                    continue
                self.base_map = self.base_map.add_attribute(key)
                l.append(w_value)
        self.initial_storage_w = l[:] # make it non-resizable

    def lookup_property_name(self, TYPE, interp, this, name, contextclass,
                             w_newvalue=None, givenotice=True):
        # Returns the name to use for accessing '$a->name' on instances:
        # usually just 'name', but may be mangled in case it's a non-static
        # protected or private attribute.  This also does access checks and
        # raises if forbidden.  Note that a static member has an effect here
        # too, even though it's not actually used later, as in PHP.
        # (All lookup() methods may raise a VisibilityError.)
        property = self._lookup_property(name, contextclass,
                not interp.allow_direct_class_access)
        if property is None:
            return name
        elif givenotice and property.is_static():
            interp.strict("Accessing static property %s as non static" %
                                 property.repr())
        # the following can raise SpecialPropertyReturn, otherwise does
        # nothing in case it's a builtin property
        property.special_lookup(TYPE, interp, this, w_newvalue)
        return property.mangled_name

    def can_access_protected_properties_from(self, contextclass):
        return contextclass is not None and (
            self.is_parent_of(contextclass) or
            contextclass.is_parent_of(self))

    def check_access_and_demangle_property(self, name, contextclass):
        if not name.startswith('\x00'):
            return name
        i = name.find('\x00', 1)
        if i < 0:
            return name      # malformed name?
        prvname = name[1:i]
        # protected property
        if prvname == "*":
            if self.can_access_protected_properties_from(contextclass):
                return name[i+1:]
            return None
        # private property
        if (contextclass is not None and contextclass.is_parent_of(self)
                and prvname == contextclass.name):
            return name[i+1:]
        else:
            return None

    def get_methods(self, contextclass):
        '''Returns a list of accessible method names for the given context.'''
        methods = []
        for method_name, method in self.methods.iteritems():
            try:
                self._visibility_check(method, method_name, contextclass)
                methods.append(method.get_name())
            except VisibilityError:
                pass

        return methods

    def lookup_staticmember(self, name, contextclass, check_visibility):
        property = self._lookup_property(name, contextclass, check_visibility)
        if property is not None and property.is_static():
            return property
        return None

    def _lookup_property(self, name, contextclass, check_visibility):
        self = jit.hint(self, promote=True)
        #name = jit.hint(name, promote=True) should be promote_string
        return self._lookup_property_elidable(name, contextclass, check_visibility)

    @jit.elidable_promote()
    def _lookup_property_elidable(self, name, contextclass, check_visibility):
        # Implementation of the rules described in the big comment in
        # instanceobject.py
        if (contextclass is not None and contextclass.is_parent_of(self)):
            try:
                result = contextclass.properties[name]
            except KeyError:
                pass
            else:
                if result.is_private():
                    return result
        try:
            result = self.properties[name]
        except KeyError:
            return None
        if check_visibility:
            self._visibility_check(result, name, contextclass)
        return result

    def locate_static_method(self, name, contextclass, check_visibility):
        try:
            return self._lookup_static_method(name, contextclass, check_visibility)
        except VisibilityError:
            callstatic = self.method__callstatic
            if callstatic is None:
                raise
            return Method(W_UnderUnderCall(name, callstatic.method_func),
                      callstatic.access_flags, self)

    @jit.elidable_promote()
    def _lookup_static_method(self, name, contextclass, check_visibility):
        key = name.lower()
        try:
            result = self.methods[key]
        except KeyError:
            raise VisibilityError("undefined", self, name, None)
        if check_visibility:
            self._visibility_check(result, name, contextclass)
        return result

    def embed_py_meth(self, name, w_php_func_adapt):
        # Allow overide from a superclass, but not a duplicate from this class.
        existing_meth = self.methods.get(name, None)
        if existing_meth is not None:
            assert existing_meth.klass != self

        assert not self.is_subclassed # XXX

        flags = w_php_func_adapt.php_static | w_php_func_adapt.php_access
        w_py_meth = Method(w_php_func_adapt, flags, self)
        self.methods[name.lower()] = w_py_meth

        # ctor has a special attribute for fast lookup
        if name == "__construct":
            self.constructor_method = w_py_meth

    def locate_method(self, name, contextclass,
                      searchclass=None, check_visibility=True):
        if searchclass is None:
            searchclass = self
        try:
            return self._lookup_method(name, contextclass, check_visibility)
        except VisibilityError:
            call = searchclass.method__call
            if call is None:
                raise
            return Method(W_UnderUnderCall(name, call.method_func),
                          call.access_flags, searchclass)

    @jit.elidable_promote()
    def _lookup_method(self, name, contextclass, check_visibility):
        key = name.lower()
        if (contextclass is not None and contextclass.is_parent_of(self)):
            try:
                result = contextclass.methods[key]
                if result.is_private():
                    if check_visibility:
                        contextclass._visibility_check(
                            result, name, contextclass)
                    return result
            except KeyError:
                pass
        try:
            result = self.methods[key]
        except KeyError:
            raise VisibilityError("undefined", self, name, None)
        if check_visibility:
            self._visibility_check(result, name, contextclass)
        return result

    def _visibility_check(self, result, name, contextclass):
        if result.is_protected():
            if not self.can_access_protected_properties_from(contextclass):
                raise VisibilityError("protected", result.getclass(),
                                      name, contextclass)
        elif result.is_private():
            if result.getclass() is not contextclass:
                raise VisibilityError("private", result.getclass(),
                                      name, contextclass)

    @jit.elidable
    def is_parent_of(self, otherclass):
        while otherclass is not self:
            otherclass = otherclass.parentclass
            if otherclass is None:
                return False
        return True

    @jit.elidable_promote()
    def is_subclass_of_class_or_intf_name(self, parent_or_interface_name):
        return parent_or_interface_name.lower() in self.all_parents

    def get_super_method(self, methname, superclass, check_visibility):
        return self.locate_method(methname, superclass,
                                  searchclass=superclass,
                                  check_visibility=check_visibility)

    def _static_call_warning(self, interp, method, assuming_this):
        interp.strict("Non-static method %s should not be "
                      "called statically%s" % (method.repr(),
                                               assuming_this))

    def getstaticmeth(self, methname, contextclass, context_w_this, interp):
        check_vis = not interp.allow_direct_class_access
        if contextclass is not None and self.is_parent_of(contextclass):
            return self.get_super_method(methname, contextclass, check_vis)
        method = self.locate_static_method(methname, contextclass, check_vis)
        if not method.is_static():
            if context_w_this is None:
                self._static_call_warning(interp, method, "")
            elif not self.is_parent_of(context_w_this.getclass()):
                self._static_call_warning(interp, method,
                    ", assuming $this from incompatible context")
        return method

    def lookup_w_constant(self, space, constantname):
        w_value = self._lookup_w_constant(constantname)
        if w_value is not None:
            return w_value.eval_static(space)

    @jit.elidable_promote()
    def _lookup_w_constant(self, n):
        try:
            return self.constants_w[n]
        except KeyError:
            return None

    def check_constructor_from_context(self, interp, contextclass):
        if self.is_abstract():
            if self.is_interface():
                cat = "interface"
            else:
                cat = "abstract class"
            interp.fatal("Cannot instantiate %s %s" % (cat, self.name))
        method = self.constructor_method
        visibility_error = "" # please the annotator
        if method is None:
            return           # no constructor at all
        elif method.is_public():
            return           # public constructor
        elif method.is_protected():
            if contextclass is not None and (
                    self.is_parent_of(contextclass) or
                    contextclass.is_parent_of(self)):
                return       # protected constructor
            visibility_error = "protected"
        elif method.is_private():
            if contextclass is self:
                return       # private constructor
            visibility_error = "private"
        interp.fatal("Call to %s %s from invalid context" % (
            visibility_error, method.repr()))

    def needs_ref(self, i):
        method = self.constructor_method
        if method is not None:
            return method.method_func.needs_ref(i)
        return False

    def get_fresh_storage_w(self, space):
        return self.get_initial_storage_w(space)[:]

    def get_initial_storage_w(self, space):
        if self.initial_storage_w is None:
            self._create_initial_storage(space)
        return self.initial_storage_w

    def call_args(self, interp, args_w, w_this=None, thisclass=None,
                  closureargs=None):
        storage_w = self.get_fresh_storage_w(interp.space)
        w_res = self.create_instance(interp, storage_w)
        method = self.constructor_method
        if method is not None:
            assert isinstance(method, Method)
            method.method_func.call_args(interp, args_w, w_this=w_res,
                    thisclass=self)
        return w_res

    def create_instance(self, interp, storage_w):
        if self.custom_instance_class is not None:
            w_res = self.custom_instance_class(self, storage_w)
            w_res.setup(interp)
        else:
            w_res = W_InstanceObject(self, storage_w)
        return w_res

    def get_empty_instance(self, space):
        return self.create_instance(space.ec.interpreter,
                                    self.get_fresh_storage_w(space))

    def do_clone(self, interp, w_obj1, contextclass):
        assert isinstance(w_obj1, W_InstanceObject)

        w_res = w_obj1._clone(interp)
        method = self.method__clone
        if method is not None:
            try:
                self._visibility_check(method, method.get_identifier(),
                        contextclass)
            except VisibilityError as exc:
                exc.reraise_magic(interp)
        if method is not None:
            method.method_func.call_args(interp, [], w_this = w_res,
                                         thisclass = self)
        return w_res

    def do_get(self, interp, w_obj, attr, isref):
        key = (w_obj, attr)
        recursion = rec_custom_get_set
        if key in recursion:
            interp.notice("Undefined property: %s::$%s" % (self.name, attr))
            w_res = interp.space.w_Null
        else:
            recursion[key] = None
            try:
                method = self.method__get
                space = interp.space
                w_res = method.method_func.call_args(interp,
                                                     [space.newstr(attr)],
                                                     w_this=w_obj,
                                                     thisclass=self)
            finally:
                del recursion[key]
        if isref and not isinstance(w_res, W_Reference):
            interp.notice("Indirect modification of overloaded property "
                            "%s::$%s has no effect" % (self.name, attr))
            w_res = W_Reference(w_res)
        return w_res

    def do_set(self, interp, w_obj, attr, w_value):
        key = (w_obj, attr)
        space = interp.space
        recursion = rec_custom_get_set
        if key in recursion:
            return False
        recursion[key] = None
        try:
            method = self.method__set
            method.method_func.call_args(interp, [space.newstr(attr), w_value],
                                         w_this=w_obj,
                                         thisclass=self)
        finally:
            del recursion[key]
        return True

    def do_unset(self, interp, w_obj, attr):
        key = (w_obj, attr)
        recursion = rec_custom_get_set
        if key in recursion:
            return False
        recursion[key] = None
        try:
            method = self.method__unset
            method.method_func.call_args(interp, [interp.space.newstr(attr)],
                                         w_this=w_obj,
                                         thisclass=self)
        finally:
            del recursion[key]
        return True

    def do_isset(self, interp, w_obj, attr):
        key = (w_obj, attr)
        recursion = rec_custom_get_set
        if key in recursion:
            return None
        recursion[key] = None
        try:
            method = self.method__isset
            w_res = method.method_func.call_args(interp,
                                                 [interp.space.newstr(attr)],
                                                 w_this=w_obj,
                                                 thisclass=self)
        finally:
            del recursion[key]
        return w_res

    def do_tostring(self, space, w_obj, quiet=False):
        method = self.method__tostring
        if method is None:
            if not quiet:
                space.ec.recoverable_fatal("Object of class %s could not be "
                                           "converted to string" % self.name)
                return space.newstr("")
            else:
                return None
        try:
            w_res = method.method_func.call_args(space.ec.interpreter, [],
                                                w_this=w_obj,
                                                thisclass=self)
        except Throw:
            raise space.ec.fatal("Method %s::__toString() must not "
                                 "throw an exception" % self.name)
        if not isinstance(w_res, W_StringObject):
            space.ec.catchable_fatal("Method %s::__toString() must "
                                     "return a string value" %
                                     self.name)
        return w_res

    def get_invoke_method(self, w_obj):
        method = self.method__invoke
        if method is None:
            return None
        return W_InvokeCall(self, method.method_func, w_obj)

    def get_all_nonstatic_special_properties(self):
        result = self._all_nonstatic_special_properties
        if result is None:
            lst = []
            for base in self.immediate_parents:
                lst.extend(base.get_all_nonstatic_special_properties())
            for prop in self.properties.values():
                if not prop.is_static() and prop.is_special:
                    lst.append((prop.mangled_name, prop))
            result = lst[:]
            self._all_nonstatic_special_properties = result
        return result

    def to_py(self, interp, w_php_ref=None):
        assert w_php_ref is None # Classes are not 1st class. Can't ref them.
        from hippy.module.pypy_bridge import php_adapters
        return php_adapters.W_PHPClassAdapter(interp, self)

def _get_instance_class(extends, instance_class):
    if extends is not None:
        if instance_class is None:
            return extends.custom_instance_class
        else:
            return instance_class
    else:
        return instance_class


all_builtin_classes = OrderedDict()


def def_class(name, methods=[], properties=[], constants=[],
        instance_class=None, flags=0, implements=[], extends=None):
    if name in all_builtin_classes:
        raise ValueError("Class '%s' has already been defined" % name)
    instance_class = _get_instance_class(extends, instance_class)
    cls = BuiltinClass(name, methods, properties, constants, instance_class,
            flags, implements, extends)
    all_builtin_classes[name] = cls
    return cls


class BuiltinClass(ClassBase):
    def __init__(self, name,
                 methods=[], properties=[], constants=[], instance_class=None,
                 flags=0, implements=[], extends=None):
        ClassBase.__init__(self, name)
        assert (extends is None or extends.custom_instance_class is None or
                issubclass(instance_class, extends.custom_instance_class))
        self.custom_instance_class = instance_class
        for method_spec in methods:
            self.declare_method(method_spec)
        for prop in properties:
            self._make_property(prop, w_Null)
        for name, w_value in constants:
            self.constants_w[name] = w_value

        self.immediate_parents = []
        if extends is not None:
            self.parentclass = extends
            if self.constructor_method is None:
                self.constructor_method = extends.constructor_method

            for method in extends.methods.itervalues():
                self._inherit_method(method)
            for p in extends.properties.itervalues():
                self._inherit_property(p)
            for key, w_value in extends.constants_w.iteritems():
                if key not in self.constants_w:
                    self.constants_w[key] = w_value
            self.immediate_parents.append(self.parentclass)

        self.access_flags = flags
        self._init_constructor()

        for intf in implements:
            self.immediate_parents.append(intf)
        for name in magic_methods_unrolled:
            if name in self.methods:
                method = self.methods[name]
                setattr(self, 'method' + name, method)

        self._init_protocol_flags()

        # XXXX to discuss
        for base in self.immediate_parents:
            for parent_id in base.all_parents:
                self.all_parents[parent_id] = None

    def declare_method(self, method_spec):
        if isinstance(method_spec, str):
            self.methods[method_spec.lower()] = None
        elif isinstance(method_spec, BuiltinFunction):
            meth = Method(method_spec, method_spec.flags, self)
            self.methods[meth.get_identifier()] = meth
        else:
            raise TypeError("Invalid method declaration: %s" % method_spec)

    def def_method(self, signature, name=None, error=None, flags=0,
                   error_handler=handle_as_warning, check_num_args=True):
        try:
            i = signature.index('this')
            signature[i] = ThisUnwrapper(self.instance_class)
        except ValueError:
            pass

        def inner(ll_func):
            fname = name or ll_func.__name__
            fullname = self.name + "::" + fname
            func = new_function(ll_func, signature, fullname, error,
                            error_handler, check_num_args)
            method = Method(func, flags, self)
            meth_id = method.get_identifier()
            if not meth_id in self.methods:
                raise ValueError(
                    "Unknown method %s was not declared in the class "
                    "definition" % method.repr())
            if self.methods[meth_id] is not None:
                raise ValueError(
                    "Duplicate implementation for method %s!" % method.repr())
            self.methods[meth_id] = method
            if meth_id == '__construct':
                self.constructor_method = method
            return ll_func
        return inner

    @property
    def instance_class(self):
        return self.custom_instance_class or W_InstanceObject

    def validate(self):
        """Check that the class is valid wrt. inheritance, interfaces, etc.

        Only for testing.
        """
        for name, method in self.methods.iteritems():
            if not isinstance(method, Method):
                raise ValueError("Invalid method object for %s::%s: %s" %
                                 (self.name, name, method))
        self._check_abstract_methods()
        if self.parentclass is not None:
            for parent_method in self.parentclass.methods.itervalues():
                meth_id = parent_method.get_identifier()
                method = self.methods[meth_id]
                if method is not parent_method:
                    self._check_inheritance(method, parent_method)


class ClassDeclaration(AbstractFunction, AccessMixin):
    """Compile-time object representing an app-level class declaration.

    The interpreter reads it to create the run-time UserClass object.
    """
    access_flags = 0
    extends_name = None
    base_interface_names = None
    ctor_id = None

    def __init__(self, name, reflection=None):
        self.name = name
        self.reflection = reflection or {}

        self.constants_w = {}
        self.method_decl = OrderedDict()
        self.property_decl = OrderedDict()

    def get_short_name(self):
        i = self.name.rfind('\\')
        if i < 0:
            return self.name
        return self.name[i + 1:]

    def _property_decl(self, decl, ctx):
        if self.is_interface():
            raise CompilerError("Interfaces may not include member variables")
        name = decl.name
        if name in self.property_decl:
            raise CompilerError("Cannot redeclare %s::$%s" % (
                self.name, name))
        if decl.expr is None:
            w_initial_value = ctx.space.w_Null
        else:
            w_initial_value = decl.expr.wrap(ctx, ctx.space)
        p = PropertyDeclaration(name, decl.access_flags, w_initial_value)
        if p.is_abstract():
            raise CompilerError("Properties cannot be declared abstract")
        if p.is_final():
            raise CompilerError("Cannot declare property %s::$%s final, "
                            "the final modifier is allowed only for "
                            "methods and classes"
                            % (self.name, decl.name))
        self.property_decl[name] = p

    def _compile_method(self, decl, ctx):
        if self.is_interface():
            decl.access_flags |= consts.ACC_ABSTRACT
        meth_id = decl.name.lower()
        if meth_id in self.method_decl:
            raise CompilerError("Cannot redeclare %s::%s()" % (
                self.name, decl.name))
        if decl.is_abstract():
            if decl.is_private():
                raise CompilerError("Abstract function %s::%s() cannot be "
                        "declared private" % (self.name, decl.name))
            elif decl.body is not None:
                raise CompilerError("Abstract function %s::%s() cannot "
                                    "contain body" % (self.name, decl.name))
        else:
            if decl.body is None:
                raise CompilerError("Non-abstract method %s::%s() must "
                                    "contain body" % (self.name, decl.name))
        function = decl.prepare_function(ctx, is_method_of=self)
        m = MethodDeclaration(function, decl.access_flags, self)
        self._check_method(m)
        self.method_decl[meth_id] = m

    def _check_method(self, m):
        ONE_ARGS = ('__isset', '__unset')
        NO_ARGS = ('__clone', '__destruct')
        func = m.func
        arity = len(func.get_signature().args)
        ident = func.get_identifier()
        if ident in ONE_ARGS and arity != 1:
            raise CompilerError("Method %s::%s() must take "
                        "exactly 1 argument" % (self.name, func.name))
        if ident in NO_ARGS and arity != 0:
            raise CompilerError("Method %s::%s() cannot accept any arguments"
                        % (self.name, func.name))
        if ident == '__destruct' and m.is_static():
            raise CompilerError("Destructor %s::%s() cannot be static"
                        % (self.name, func.name))
        if ident == '__clone' and m.is_static():
            raise CompilerError("Clone method %s::%s() cannot be static"
                        % (self.name, func.name))

    def _check_abstract_local(self):
        if self.is_abstract():
            return
        abstract_methods = []
        for decl in self.method_decl.itervalues():
            if decl.is_abstract():
                abstract_methods.append("%s::%s" % (self.name, decl.func.name))
        if abstract_methods:
            msg = _msg_abstract(self.name, abstract_methods)
            raise CompilerError(msg)

    def _init_constructor(self):
        if '__construct' in self.method_decl:
            method = self.method_decl['__construct']
        elif self.get_identifier() in self.method_decl:
            method = self.method_decl[self.get_identifier()]
        else:
            return
        if method.is_static():
            raise CompilerError("Constructor %s::%s() cannot be static" %
                                (self.name, method.func.name))
        self.ctor_id = method.func.get_identifier()

    def define_new_class(self, interp):
        kls = UserClass(interp, self)
        self._current_repr = kls    # for debugging only
        return kls

    def redefine_old_class(self, interp, kls):
        assert isinstance(kls, ClassBase)
        self._current_repr = kls    # for debugging only
        # Reset the properties to their original values
        for p in kls.properties.itervalues():
            p.reset_initial_value()

    def try_current_class(self):
        kls = self._immut_cell.get_current_value()
        assert isinstance(kls, ClassBase)
        return kls


def get_interp_decl_key(interp, decl):
    # Returns a tuple that describes "decl" and its usage in a
    # given "interp".  The equality of the tuple returned is used
    # to know if we can reuse an already-computed UserClass from
    # a previous interp, or not.  Note in particular that the
    # UserClass object should not store "interp".  This can return
    # UserClasses for the parent and the interfaces; it will only
    # be equal if all of them were already found to be equal.
    parent = None
    intfs = None
    if decl.extends_name is not None:
        parent = interp.lookup_class_or_intf_for_clsdecl(decl.extends_name)
    if decl.base_interface_names:
        intfs = [interp.lookup_class_or_intf_for_clsdecl(intfname)
                 for intfname in decl.base_interface_names]
    return (decl, parent, intfs)


class UserClass(ClassBase):
    """Runtime object representing a user-defined class"""
    def __init__(self, interp, decl):
        ClassBase.__init__(self, decl.name)
        self.access_flags = decl.access_flags
        self.constants_w = decl.constants_w
        parent = self.init_parent(interp, decl.extends_name)
        if parent:
            parent.is_subclassed = True
        #
        immediate_parents = []
        if parent is not None:
            immediate_parents.append(self.parentclass)
        if decl.base_interface_names:
            for intfname in decl.base_interface_names:
                intf = interp.lookup_class_or_intf(intfname)
                if intf is None:
                    interp.fatal("Interface '%s' not found" % intfname)
                if (intf.access_flags & consts.ACC_INTERFACE) == 0:
                    interp.fatal("%s cannot implement %s - it is not "
                                 "an interface" % (self.name, intfname))
                immediate_parents.append(intf)
        self.immediate_parents = immediate_parents
        #
        for base in immediate_parents:
            for parent_id in base.all_parents:
                self.all_parents[parent_id] = None
            for key, w_value in base.constants_w.iteritems():
                if key not in self.constants_w:
                    self.constants_w[key] = w_value
                else:
                    if base.is_interface() and (
                            w_value is not self.constants_w[key]):
                        interp.fatal("Cannot inherit previously-inherited "
                                       "or override constant %s from "
                                       "interface %s" % (key, base.name))
        #
        for meth_id, m in decl.method_decl.iteritems():
            self.methods[meth_id] = m.execute(self)
        if decl.ctor_id is not None:
            self.constructor_method = self.methods[decl.ctor_id]
        if parent is not None:
            if self.constructor_method is None:
                self.constructor_method = parent.constructor_method
            try:
                for method in parent.methods.itervalues():
                    self._inherit_method(interp, method)
            except ClassDeclarationError as e:
                interp.fatal(e.msg)
        #
        for name, p in decl.property_decl.iteritems():
            self.properties[name] = p.execute(self)
        if self.parentclass is not None:
            try:
                for p in self.parentclass.properties.itervalues():
                    self._inherit_property(p)
            except ClassDeclarationError as e:
                interp.fatal(e.msg)
        #
        try:
            self._check_abstract_methods()
            self._init_protocol_flags()
        except ClassDeclarationError as e:
            interp.fatal(e.msg)
        self._init_magic_methods(interp)
        self.decl = decl

    def init_parent(self, interp, extends_name):
        if extends_name is None:
            return None
        self.parentclass = parent = interp.lookup_class_or_intf(extends_name)
        if parent is None:
            interp.fatal("Class '%s' not found" % extends_name)
        if parent.is_interface():
            interp.fatal("Class %s cannot extend from interface %s" %
                         (self.name, parent.name))
        if parent.is_final():
            interp.fatal("Class %s may not inherit from final class (%s)" %
                         (self.name, parent.name))
        assert self.custom_instance_class is None
        self.custom_instance_class = parent.custom_instance_class
        return parent

    def _check_compatibility(self, interp, method, parent_method):
        from hippy.module.pypy_bridge import W_PyMethodFuncAdapter
        if isinstance(method.method_func, W_PyMethodFuncAdapter) or isinstance(parent_method.method_func, W_PyMethodFuncAdapter):
            return
        if not method.get_signature().matches(parent_method.get_signature()):
            interp.strict(
                "Declaration of %s should be compatible with %s" %
                    (method.repr(), parent_method.signature_repr()))

    def _inherit_method(self, interp, parent_method):
        meth_id = parent_method.get_identifier()
        if meth_id not in self.methods:
            self.methods[meth_id] = parent_method
        else:
            method = self.methods[meth_id]
            self._check_inheritance(method, parent_method)
            self._check_compatibility(interp, method, parent_method)


class DelayedClassConstant(DelayedObject):
    def __init__(self, cls_name, name):
        self.cls_name = cls_name
        self.name = name

    def eval_static(self, space):
        w_cls = space.ec.interpreter.locate_class_or_intf(self.cls_name)
        # XXX: recursion!
        w_result = w_cls.lookup_w_constant(space, self.name)
        return w_result


class ClassMember(AccessMixin):
    _immutable_fields_ = ['access_flags']

    r_value = None
    is_special = False

    def __init__(self, access_flags):
        self.access_flags = normalize_access(access_flags)
        if self.is_final() and self.is_abstract():
            raise CompilerError("Cannot use the final modifier on an "
                                "abstract class member")

class PropertyDeclaration(ClassMember):
    value = None

    def __init__(self, name, access_flags, w_initial_value):
        ClassMember.__init__(self, access_flags)
        self.name = name
        self.value = w_initial_value

    def execute(self, klass):
        p = Property(self.name, klass, self.access_flags, self.value)
        return p


class Property(ClassMember):
    getter = None

    _immutable_fields_ = ['name', 'mangled_name', 'access_flags', 'w_initial_value', 'getter']

    def __init__(self, name, klass, access_flags, w_initial_value, src=None):
        ClassMember.__init__(self, access_flags)
        self.name = name
        self.klass = klass
        self.mangled_name = self.mk_mangled_name()
        self.src = src      # which Property this one is a copy() of
        assert w_initial_value is not None
        self.w_initial_value = w_initial_value
        self.reset_initial_value()

    def reset_initial_value(self):
        self.value = self.w_initial_value
        if self.src is not None:
            self.r_value = self.src.r_value
        else:
            self.r_value = W_Reference(None)  # a new ref, lazily filled

    def getclass(self):
        return self.klass

    def mk_mangled_name(self):
        if self.is_public():
            return self.name
        if self.is_protected():
            return '\x00*\x00' + self.name
        if self.is_private():
            return '\x00%s\x00%s' % (self.klass.name, self.name)
        raise AssertionError

    def getvalue(self, space):
        assert self.is_static()
        if self.r_value.deref_temp() is None:
            self.r_value.store(self.value.eval_static(space))
        return self.r_value

    def copy(self):
        res = Property(self.name, self.klass, self.access_flags,
                       self.w_initial_value, src=self)
        res.value = self.value
        return res

    def special_lookup(self, LOOKUP, interp, this, w_newvalue):
        pass

    def repr(self):
        return "%s::$%s" % (self.klass.name, self.name)


class GetterSetter(Property):
    """ A special property that's calling getter/setter functions
    """
    is_special = True

    def __init__(self, getter, setter, name, klass, access_flags):
        # NOTE: doesn't call Property.__init__()
        ClassMember.__init__(self, access_flags)
        self.name = name
        self.klass = klass
        self.mangled_name = self.mk_mangled_name()
        self.getter = getter
        self.setter = setter

    def copy(self):
        return self

    def special_lookup(self, LOOKUP, interp, this, w_newvalue=None):
        if LOOKUP == LOOKUP_HASATTR or LOOKUP == LOOKUP_DELATTR:
            raise SpecialPropertyReturn(None)
        if LOOKUP == LOOKUP_GETATTR:
            raise SpecialPropertyReturn(self.getter(interp, this))
        if LOOKUP == LOOKUP_SETATTR:
            self.setter(interp, this, w_newvalue)
            raise SpecialPropertyReturn(None)
        assert False  # unreachable code


class MethodDeclaration(ClassMember):
    def __init__(self, func, access_flags, class_decl):
        ClassMember.__init__(self, access_flags)
        self.class_decl = class_decl
        self.func = func

    def execute(self, klass):
        assert klass.name == self.class_decl.name
        return Method(self.func, self.access_flags, klass)


class Method(ClassMember):
    _immutable_fields_ = ['method_func', 'klass', 'access_flags']

    def __init__(self, method_func, access_flags, klass):
        ClassMember.__init__(self, access_flags)
        self.klass = klass
        self.method_func = method_func

    def __repr__(self):
        return "<Method %s of %r>" % (self.method_func.name,
                                      self.klass)

    def bind(self, w_instance, klass):
        if self.is_static():
            return W_BoundMethod(None, klass, self.method_func)
        else:
            return W_BoundMethod(w_instance, klass, self.method_func)

    def getclass(self):
        return self.klass

    def get_name(self):
        return self.method_func.name

    def get_identifier(self):
        return self.method_func.get_identifier()

    def get_signature(self):
        return self.method_func.get_signature()

    def repr(self):
        return "%s()" % (self.method_func.get_fullname())

    def signature_repr(self):
        return self.method_func.signature_repr()

    def to_py(self, interp):
        from hippy.module.pypy_bridge.php_adapters import (
            W_PHPUnboundMethAdapter, W_PHPFuncAdapter)
        # Should only get here if we address a PHP method statically from PHP.
        w_php_func = self.method_func

        w_py_inside = w_php_func.get_wrapped_py_obj()
        if w_py_inside is not None:
            # trivial unwrapping
            return w_py_inside
        elif self.is_static():
            return W_PHPFuncAdapter(interp.py_space, w_php_func)
        else:
            return W_PHPUnboundMethAdapter(interp.py_space, self)


class W_BoundMethod(AbstractFunction):
    def __init__(self, w_instance, klass, method_func):
        self.w_instance = w_instance
        self.klass = klass
        self.method_func = method_func

    def is_py_call(self):
        return self.method_func.is_py_call()

    def needs_ref(self, i):
        return self.method_func.needs_ref(i)

    def call_args(self, interp, args_w, w_this=None, thisclass=None,
                  closureargs=None):
        if thisclass is None:
            thisclass = self.klass
        return self.method_func.call_args(interp, args_w,
                                          w_this=self.w_instance,
                                          thisclass=thisclass)

class W_UnderUnderCall(AbstractFunction):
    def __init__(self, name, call_func):
        self.name = name
        self.call_func = call_func

    def needs_ref(self, i):
        return False

    def call_args(self, interp, args_w, w_this=None, thisclass=None,
                  closureargs=None):
        space = interp.space
        args_w = [space.newstr(self.name), space.new_array_from_list(args_w)]
        return self.call_func.call_args(interp, args_w, w_this, thisclass)


class W_InvokeCall(AbstractFunction):
    def __init__(self, klass, call_func, w_obj):
        self.klass = klass
        self.call_func = call_func
        self.w_obj = w_obj

    def needs_ref(self, i):
        return self.call_func.needs_ref(i)

    def call_args(self, interp, args_w, w_this=None, thisclass=None,
                  closureargs=None):
        return self.call_func.call_args(interp, args_w,
                                        w_this=self.w_obj, thisclass=self.klass)
