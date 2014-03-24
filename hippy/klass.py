from hippy.function import AbstractFunction
from hippy.ast import MethodDecl, ConstDecl, PropertyDecl
from hippy.error import PHPException, VisibilityError, InterpreterError
from hippy.objects.base import W_Root, W_Object
from hippy.objects.reference import W_Reference
from hippy.objects.instanceobject import W_InstanceObject, W_BoundMethod,\
     LOOKUP_SETATTR, LOOKUP_GETATTR, LOOKUP_HASATTR, LOOKUP_DELATTR,\
     SpecialPropertyReturn
from hippy.objects.strobject import W_StringObject
from hippy.ast import CompilerError
from hippy import consts
from hippy.objects.nullobject import w_Null
from hippy.mapdict import Terminator
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


class ClassBase(AbstractFunction):
    access_flags = 0
    extends_name = None
    base_interface_names = None
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
    immediate_parents = None
    parentclass = None

    def __init__(self, name):
        self.name = name
        self.identifier = name.lower()
        self.properties = OrderedDict()
        self.property_decl = []
        self.methods = OrderedDict()
        self.constants_w = {}
        self.all_parents = {self.identifier: None}  #classes and intfs
        self.base_map = Terminator()
        self.initial_storage_w = None

    def __repr__(self):
        if self.is_interface():
            cat = 'Interface'
        else:
            cat = 'Class'
        return '<%s %r>' % (cat, self.name)

    def is_interface(self):
        return (self.access_flags & consts.ACC_INTERFACE) != 0

    def is_final(self):
        return bool(self.access_flags & consts.ACC_FINAL)

    def is_abstract(self):
        return bool(self.access_flags & consts.ACC_ABSTRACT)

    def _init_constructor(self):
        if '__construct' in self.methods:
            method = self.methods['__construct']
        elif self.identifier in self.methods:
            method = self.methods[self.identifier]
        else:
            return
        if method.is_static():
            raise CompilerError("Constructor %s cannot be static" %
                                (method.repr()))
        self.constructor_method = method

    def _make_property(self, prop, w_initial_value):
        if isinstance(prop, tuple):
            name, access_flags = prop
            p = Property(name, self, access_flags)
            self.properties[name] = p
            self.property_decl.append(p)
            if not p.is_static():
                p.value = w_initial_value
            else:
                if not isinstance(w_initial_value, W_Object):
                    r_value = w_initial_value
                else:
                    r_value = W_Reference(w_initial_value)
                p.r_value = r_value
        elif not we_are_translated(): # compile time only
            prop = prop.build(self)
            self.properties[prop.name] = prop
            self.property_decl.append(prop)

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
        else:
            method = self.methods[meth_id]
            self._check_inheritance(method, parent_method)

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

    def _inherit_property(self, prop):
        if prop.is_private():
            return
        name = prop.name
        if name not in self.properties:
            self.properties[name] = prop.copy_to(self)
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

    def _init_magic_methods(self):
        for name in magic_methods_unrolled:
            if name in self.methods:
                method = self.methods[name]
            else:
                continue
            if name == '__call':
                if (method.getclass() == self and
                        (method.is_static() or not method.is_public())):
                    self.space.ec.warn("The magic method __call() must have "
                            "public visibility and cannot be static")
            setattr(self, 'method' + name, method)

    def _create_initial_storage(self, space):
        l = []
        for p in self.property_decl:
            if not p.is_static() and not p.is_special:
                w_val = p.value.eval_static(space)
                self.base_map = self.base_map.add_attribute(p.mangle_name())
                assert self.base_map.index == len(l)
                l.append(w_val)
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

    def get_identifier(self):
        return self.identifier

    def lookup_property_name(self, TYPE, interp, this, name, contextclass,
                             w_newvalue=None, givenotice=True):
        # Returns the name to use for accessing '$a->name' on instances:
        # usually just 'name', but may be mangled in case it's a non-static
        # protected or private attribute.  This also does access checks and
        # raises if forbidden.  Note that a static member has an effect here
        # too, even though it's not actually used later, as in PHP.
        # (All lookup() methods may raise a VisibilityError.)
        property = self._lookup_property(name, contextclass)
        if property is None:
            return name
        elif givenotice and property.is_static():
            self.space.ec.strict("Accessing static property %s as non static" %
                                 property.repr())
        # the following can raise SpecialPropertyReturn, otherwise does
        # nothing in case it's a builtin property
        property.special_lookup(TYPE, interp, this, w_newvalue)
        return property.mangle_name()

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

    def lookup_staticmember(self, name, contextclass):
        try:
            property = self._lookup_property(name, contextclass)
        except VisibilityError, e:
            raise e.reraise_property(self.space.ec.interpreter)
        if property is not None and property.is_static():
            return property
        return None

    def _lookup_property(self, name, contextclass):
        self = jit.hint(self, promote=True)
        #name = jit.hint(name, promote=True) should be promote_string
        return self._lookup_property_elidable(name, contextclass)

    @jit.elidable
    def _lookup_property_elidable(self, name, contextclass):
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
        self._visibility_check(result, name, contextclass)
        return result

    def locate_method(self, name, contextclass, static, searchclass=None):
        if searchclass is None:
            searchclass = self
        try:
            method = self._lookup_method(name, contextclass,
                                  static)
        except VisibilityError:
            method = searchclass._make_underunder_call(name, static)
            if method is None:
                raise
        return method

    @jit.elidable
    def _lookup_method(self, name, contextclass, static):
        key = name.lower()
        if (not static and contextclass is not None
                    and contextclass.is_parent_of(self)):
            try:
                result = contextclass.methods[key]
                if result.is_private():
                    self._visibility_check(result, name, contextclass)
                    return result
            except KeyError:
                pass
        try:
            result = self.methods[key]
        except KeyError:
            raise VisibilityError("undefined", self, name, None)
        self._visibility_check(result, name, contextclass)
        return result

    def _make_underunder_call(self, name, static):
        if static:
            meth = self.method__callstatic
        else:
            meth = self.method__call
        if meth is None:
            return None
        return Method(W_UnderUnderCall(name, meth.method_func),
                      meth.access_flags, self)

    def _visibility_check(self, result, name, contextclass):
        if self.space.ec.interpreter.allow_direct_class_access:
            return
        if result.is_protected():
            if not self.can_access_protected_properties_from(contextclass):
                raise VisibilityError("protected", result.getclass(),
                        name, contextclass)
        elif result.is_private():
            if result.getclass() is not contextclass:
                raise VisibilityError("private", result.getclass(),
                        name, contextclass)

    def is_parent_of(self, otherclass):
        while otherclass is not self:
            otherclass = otherclass.parentclass
            if otherclass is None:
                return False
        return True

    @jit.elidable
    def is_subclass_of_class_or_intf_name(self, parent_or_interface_name):
        return parent_or_interface_name.lower() in self.all_parents

    def _static_call_warning(self, method, assuming_this):
        self.space.ec.strict("Non-static method %s should not be "
                             "called statically%s" % (method.repr(),
                                                      assuming_this))

    def getstaticmeth(self, methname, contextclass, context_w_this, thisclass):
        interp = self.space.ec.interpreter
        if methname.lower() == '__construct':
            method = self.constructor_method
            if method is None:
                raise interp.fatal("Cannot call constructor")
            return W_BoundMethod(context_w_this, thisclass, method.method_func)
        if context_w_this is not None and self.is_parent_of(contextclass):
            static = False
            searchclass = contextclass
        else:
            static = True
            searchclass = self
        try:
            method = self.locate_method(methname, contextclass, static=static,
                searchclass=searchclass)
        except VisibilityError as e:
            raise interp.fatal(e.msg_fatal())
        if static and not method.is_static():
            if context_w_this is None:
                self._static_call_warning(method, "")
            elif not self.is_parent_of(context_w_this.klass):
                self._static_call_warning(method, ", assuming $this from "
                        "incompatible context")
        if method.is_static():
            return W_BoundMethod(None, thisclass, method.method_func)
        else:
            return W_BoundMethod(context_w_this, thisclass, method.method_func)

    def lookup_w_constant(self, space, constantname):
        try:
            w_value = self.constants_w[constantname]
        except KeyError:
            return None
        return w_value.eval_static(space)

    def check_constructor_from_context(self, contextclass):
        if self.is_abstract():
            if self.is_interface():
                cat = "interface"
            else:
                cat = "abstract class"
            self.space.ec.fatal("Cannot instantiate %s %s" % (cat, self.name))
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
        self.space.ec.fatal("Call to %s %s from invalid context" % (
            visibility_error, method.repr()))

    def needs_ref(self, i):
        method = self.constructor_method
        if method is not None:
            return method.method_func.needs_ref(i)
        return False

    def get_fresh_storage_w(self, space):
        if self.initial_storage_w is None:
            self._create_initial_storage(space)
        return self.initial_storage_w[:]

    def call_args(self, interp, args_w, w_this=None, thisclass=None,
                  closureargs=None):
        storage_w = self.get_fresh_storage_w(interp.space)
        w_res = self.create_instance(interp, storage_w)
        method = self.constructor_method
        if method is not None:
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
            else:
                return None
        try:
            w_res = method.method_func.call_args(space.ec.interpreter, [],
                                                w_this=w_obj,
                                                thisclass=self)
        except PHPException:
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


all_builtin_classes = OrderedDict()


def def_class(name, methods=[], properties=[], constants=[],
        instance_class=None, flags=0, implements=[], extends=None,
        is_iterator=False):
    if name in all_builtin_classes:
        raise ValueError("Class '%s' has already been defined" % name)
    cls = BuiltinClass(name, methods, properties, constants, instance_class,
            flags, implements, extends, is_iterator)
    all_builtin_classes[name] = cls
    return cls


class BuiltinClass(ClassBase):
    def __init__(self, name,
                 methods=[], properties=[], constants=[], instance_class=None,
                 flags=0, implements=[], extends=None, is_iterator=False):
        if extends is not None and not isinstance(extends, BuiltinClass):
            extends = all_builtin_classes[extends]
        implements = [(intf if isinstance(intf, BuiltinClass) else
            all_builtin_classes[intf]) for intf in implements]

        ClassBase.__init__(self, name)

        self.immediate_parents = []
        if extends is not None:
            self.parentclass = extends
            self.extends_name = extends.name

            if self.constructor_method is None:
                self.constructor_method = extends.constructor_method

            if instance_class is None:
                self.custom_instance_class = extends.custom_instance_class
            else:
                assert extends.custom_instance_class is None or issubclass(
                    instance_class, extends.custom_instance_class)
                self.custom_instance_class = instance_class

            for method in extends.methods.itervalues():
                self._inherit_method(method)
            for p in extends.properties.itervalues():
                self._inherit_property(p)
            self.immediate_parents.append(self.parentclass)
        else:
            self.custom_instance_class = instance_class

        for func in methods:
            meth = Method(func, func.flags, self)
            self.methods[meth.get_identifier()] = meth
        for prop in properties:
            self._make_property(prop, w_Null)
        for name, w_value in constants:
            self.constants_w[name] = w_value

        self.access_flags = flags
        self.base_interface_names = [intf.name for intf in implements]
        self.is_iterator = is_iterator

        self._init_constructor()

        for p in self.property_decl:
            self.properties[p.name] = p

        for intf in implements:
            self.immediate_parents.append(intf)
        self._check_abstract_methods()
        for name in magic_methods_unrolled:
            if name in self.methods:
                method = self.methods[name]
                setattr(self, 'method' + name, method)

        if self.immediate_parents:
            for parent in self.immediate_parents:
                if parent.is_iterator:
                    self.is_iterator = True
                    break
        # XXXX to discuss
        for base in self.immediate_parents:
            for parent_id in base.all_parents:
                self.all_parents[parent_id] = None


class UserClass(ClassBase):
    def _property_decl(self, decl, ctx):
        if self.is_interface():
            raise CompilerError("Interfaces may not include member variables")
        name = decl.name
        if name in self.properties:
            raise CompilerError("Cannot redeclare %s::$%s" % (
                self.name, name))
        if decl.expr is None:
            w_initial_value = ctx.space.w_Null
        else:
            w_initial_value = decl.expr.wrap(ctx, ctx.space)
        self._make_property((name, decl.access_flags), w_initial_value)

    def _method_decl(self, decl, ctx):
        af = decl.access_flags
        if self.is_interface():
            af |= consts.ACC_ABSTRACT
        function = decl.prepare_function(ctx, is_method_of=self,
                                         static=bool(af & consts.ACC_STATIC))
        m = Method(function, af, self)
        meth_id = function.get_identifier()
        if meth_id in self.methods:
            raise CompilerError("Cannot redeclare %s::%s" % (
                self.name, function.name))
        self.methods[meth_id] = m
        #
        if m.is_abstract():
            if m.is_private():
                raise CompilerError("Abstract function %s cannot be "
                                    "declared private" % (m.repr()))
            elif decl.body is not None:
                raise CompilerError("Abstract function %s cannot "
                                    "contain body" % (m.repr()))
        else:
            if decl.body is None:
                raise CompilerError("Non-abstract method %s must "
                                    "contain body" % (m.repr()))

    def _check_abstract_local(self):
        if self.is_abstract():
            return
        abstract_methods = []
        for m in self.methods.itervalues():
            if m.is_abstract():
                abstract_methods.append("%s::%s" % (self.name, m.get_name()))
        if abstract_methods:
            msg = _msg_abstract(self.name, abstract_methods)
            raise CompilerError(msg)

    def initialize(self, node, ctx):
        self.access_flags = node.access_flags
        self.extends_name = node.extends
        self.base_interface_names = node.baseinterfaces
        for decl in node.body.getstmtlist():
            if isinstance(decl, ConstDecl):
                if decl.name in self.constants_w:
                    raise CompilerError("Cannot redefine class constant %s::%s"
                            % (self.name, decl.name))
                self.constants_w[decl.name] = decl.const_expr.wrap(ctx, ctx.space)
            elif isinstance(decl, MethodDecl):
                self._method_decl(decl, ctx)
            else:
                assert isinstance(decl, PropertyDecl)
                self._property_decl(decl, ctx)
        self._check_abstract_local()
        self._init_constructor()

    def _check_compatibility(self, interp, method, parent_method):
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

    def class_declaration_now_encountered(self, interp):
        self.space = space = interp.space
        for p in self.property_decl:
            self.properties[p.name] = p

        if self.extends_name is not None:
            interp.check_valid_class_name(self.extends_name)
            self.parentclass = parent = interp.lookup_class_or_intf(
                self.extends_name)
            if parent is None:
                space.ec.fatal("Class '%s' not found" % self.extends_name)
            if parent.is_interface():
                space.ec.fatal("Class %s cannot extend from interface %s"
                               % (self.name, parent.name))
            if parent.is_final():
                space.ec.fatal("Class %s may not inherit from final class (%s)"
                               % (self.name, parent.name))
            if self.constructor_method is None:
                self.constructor_method = parent.constructor_method
            assert self.custom_instance_class is None
            self.custom_instance_class = parent.custom_instance_class
            try:
                for method in parent.methods.itervalues():
                    self._inherit_method(interp, method)
                for p in parent.properties.itervalues():
                    self._inherit_property(p)
            except ClassDeclarationError as e:
                interp.fatal(e.msg)
        else:
            parent = self.parentclass = None
        #
        immediate_parents = []
        if self.parentclass is not None:
            immediate_parents.append(self.parentclass)
        #
        if self.base_interface_names:
            for intfname in self.base_interface_names:
                intf = interp.lookup_class_or_intf(intfname)
                if intf is None:
                    space.ec.fatal("Interface '%s' not found" % intfname)
                #
                if (intf.access_flags & consts.ACC_INTERFACE) == 0:
                    space.ec.fatal("%s cannot implement %s - it is not "
                                   "an interface" % (self.name, intfname))
                #
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
                        space.ec.fatal("Cannot inherit previously-inherited "
                                       "or override constant %s from "
                                       "interface %s" % (key, base.name))
        #
        try:
            self._check_abstract_methods()
        except ClassDeclarationError as e:
            interp.fatal(e.msg)
        self._init_magic_methods()
        for parent in immediate_parents:
            if parent.is_iterator:
                self.is_iterator = True
                break


class DelayedClassConstant(W_Root):
    def __init__(self, cls_name, name):
        self.cls_name = cls_name
        self.name = name

    def eval_static(self, space):
        w_cls = space.ec.interpreter.locate_class_or_intf(self.cls_name)
        # XXX: recursion!
        w_result = w_cls.lookup_w_constant(space, self.name)
        return w_result


class ClassMember(object):
    _immutable_fields_ = ['access_flags']

    r_value = None
    is_special = False

    def __init__(self, access_flags):
        self.access_flags = normalize_access(access_flags)
        if self.is_final() and self.is_abstract():
            raise CompilerError("Cannot use the final modifier on an "
                                "abstract class member")

    def is_final(self):
        return bool(self.access_flags & consts.ACC_FINAL)

    def is_abstract(self):
        return bool(self.access_flags & consts.ACC_ABSTRACT)

    def is_public(self):
        return bool(self.access_flags & consts.ACC_PUBLIC)

    def is_protected(self):
        return bool(self.access_flags & consts.ACC_PROTECTED)

    def is_private(self):
        return bool(self.access_flags & consts.ACC_PRIVATE)

    def is_static(self):
        return bool(self.access_flags & consts.ACC_STATIC)


class Property(ClassMember):
    getter = None
    value = None

    def __init__(self, name, klass, access_flags):
        ClassMember.__init__(self, access_flags)
        self.name = name
        self.klass = klass

    def getclass(self):
        return self.klass

    def mangle_name(self):
        if self.is_public():
            return self.name
        if self.is_protected():
            return '\x00*\x00' + self.name
        if self.is_private():
            return '\x00%s\x00%s' % (self.klass.name, self.name)
        raise AssertionError

    def copy_to(self, cls):
        if not self.is_static():
            return self
        copy = Property(self.name, self.klass, self.access_flags)
        copy.r_value = self.r_value
        return copy

    def getvalue(self, space):
        assert self.is_static()
        r_value = self.r_value
        if not isinstance(r_value, W_Reference):
            return W_Reference(r_value.eval_static(space))
        else:
            return r_value

    def special_lookup(self, LOOKUP, interp, this, w_newvalue):
        pass

    def repr(self):
        return "%s::$%s" % (self.klass.name, self.name)


class GetterSetter(Property):
    """ A special property that's calling getter/setter functions
    """
    is_special = True

    def __init__(self, getter, setter, name, klass, access_flags):
        Property.__init__(self, name, klass, access_flags)
        self.getter = getter
        self.setter = setter

    def special_lookup(self, LOOKUP, interp, this, w_newvalue=None):
        if LOOKUP == LOOKUP_HASATTR or LOOKUP == LOOKUP_DELATTR:
            raise SpecialPropertyReturn(None)
        if LOOKUP == LOOKUP_GETATTR:
            raise SpecialPropertyReturn(self.getter(interp, this))
        if LOOKUP == LOOKUP_SETATTR:
            self.setter(interp, this, w_newvalue)
            raise SpecialPropertyReturn(None)
        assert False # unreachable code


class Method(ClassMember):
    _immutable_fields_ = ['method_func', 'klass', 'access_flags']

    def __init__(self, method_func, access_flags, klass):
        ClassMember.__init__(self, access_flags)
        self.klass = klass
        self.method_func = method_func

    def __repr__(self):
        return "<Method %s of %r>" % (self.method_func.name,
                                      self.klass)

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


def normalize_access(access_flags):
    if not (access_flags & consts.ACCMASK_VISIBILITY):
        access_flags |= consts.ACC_PUBLIC
    assert (access_flags & consts.ACCMASK_VISIBILITY) in (
        consts.ACC_PUBLIC,
        consts.ACC_PROTECTED,
        consts.ACC_PRIVATE)
    return access_flags


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
