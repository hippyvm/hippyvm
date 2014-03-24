from collections import OrderedDict
from hippy.error import ConvertError, VisibilityError
from hippy.objects.base import W_Object
from hippy.objects.reference import W_Reference
from hippy.objects.iterator import W_InstanceIterator
from hippy.objects.arrayobject import array_var_export, W_ArrayObject
from hippy.function import AbstractFunction
from rpython.rlib.rstring import StringBuilder
from rpython.rlib import jit

# ____________________________________________________________

# Access rules to attributes (called "properties" in PHP): they can
# be declared public/protected/private in each class.  A subclass
# cannot declare an already-declated attribute with a more restricted
# visibility, but can declare it with the same visibility.

# Private attributes are stored as "\x00Class\x00attrname".  Protected
# attributes are stored as "\x00*\x00attrname".  Public attributes are
# stored normally as "attrname".

# If '$foo->bar' occurs syntactically in class A, and class A declares
# 'private $bar', and '$foo' is at run-time an instance of A or a
# subclass, then this is a successful access to "\x00A\x00bar".
# Otherwise, if the exact class F of '$foo' declares 'private $bar',
# then we get a Fatal error: Cannot access private property F::$bar.
# Otherwise, fall back to the remaining rules.

# Look again at the class F of '$foo'.  Find the most derived
# declaration of '$bar' in F's superclasses; let's say it occurs in G.
# If G declares exactly 'protected $bar', then check that '$foo->bar'
# occurs syntactically in a class that is either a parent or a subclass
# of G.  If it does, this is a successful access to "\x00*\x00bar".  If
# it does not, we get a Fatal error: Cannot access protected property
# G::$bar.

# Otherwise, whether declared public, private or not at all, it is a
# successful access to "bar".


# Access rules to methods: the logic seems to be exactly the same.
# Static methods are stored together with non-static methods in the
# class dicts and the same rules apply to them too.

# Static properties are also stored in the same class dict as regular
# properties (there are apparently two dicts: one for all properties,
# and one for all methods).  However, if '$bar' is a static property,
# then 'foo->$bar' will not read or write the value of this static
# property: it is used only for access check and to figure out the
# mangled name (uh).

# A static property cannot be redeclared as non-static in a subclass
# or vice-versa.

# The "F::$bar" syntax does again the same checking as above, but at the
# end it means one of the statically declared $bar, as looked up by the
# logic, or if there is none, we get Fatal error: Access to undeclared
# static property: F::$bar.

# Similarly, "F::meth" does the same checking as above, but calls the
# method with an undefined $this.  If the method is not declared static,
# then it still works as long as we don't access $this.  The only
# difference between static and non-static methods appears to be that it
# is syntactically invalid to use $this in a static method.

# ____________________________________________________________


class GlobalCounter(object):
    instance_counter = 1
global_counter = GlobalCounter()

LOOKUP_GETATTR, LOOKUP_SETATTR, LOOKUP_HASATTR, LOOKUP_DELATTR = range(4)


class SpecialPropertyReturn(Exception):
    """ A hack to return a value from name lookup in properties,
    used to builtin classes
    """
    def __init__(self, w_value):
        self.w_value = w_value


def demangle_property(name):
    if not name.startswith('\0'):
        return name, ''
    i = name.find('\x00', 1)
    if i < 0:
        return name, ''      # malformed name?
    return name[i + 1:], name[1:i]


def dump_property(name, access):
    """Format the output of demangle_property() for use in var_dump()"""
    if access == '':
        return '"%s"' % name
    elif access == '*':
        return '"%s":protected' % name
    else:
        return '"%s":"%s":private' % (name, access)


class W_InstanceObject(W_Object):
    instance_number = 0
    w_rdict_array = None     # lazily built W_RDictArrayObject

    def __init__(self, klass, initial_storage):
        self.klass = klass
        map = klass.base_map
        self.map = map
        self.storage_w = initial_storage

    def getclass(self):
        return jit.hint(self.klass, promote=True)

    def setup(self, interp):
        pass

    def get_instance_attrs(self):
        d = OrderedDict()
        for attr in self.map.get_all_attrs():
            d[attr.name] = self.storage_w[attr.index]
        return d

    def get_rdict_array(self, space):
        if self.w_rdict_array is None:
            dct_w = self.get_instance_attrs()
            self.w_rdict_array = (
                W_ArrayObject.new_array_from_rdict(space, dct_w))
        return self.w_rdict_array

    def get_instance_number(self):
        if self.instance_number == 0:
            self.instance_number = global_counter.instance_counter
            global_counter.instance_counter += 1
        return self.instance_number

    def is_true(self, space):
        return True

    def int_w(self, space):
        return 1

    def as_int_arg(self, space):
        raise ConvertError('object cannot be used as integer argument')

    def as_number(self, space):
        space.ec.notice("Object of class %s could not be converted to int" %
                        self.klass.name)
        return space.newint(1)

    def float_w(self, space):
        space.ec.notice("Object of class %s could not be converted "
                        "to double" % self.klass.name)
        return 1.

    def iterproperties(self, interp):
        for base in self.getclass().immediate_parents:
            for prop in base.properties.values():
                if not prop.is_static() and prop.is_special:
                    w_value = prop.getter(interp, self)
                    name = prop.mangle_name()
                    yield name, w_value

        for prop in self.getclass().properties.values():
            if not prop.is_static() and prop.is_special:
                w_value = prop.getter(interp, self)
                name = prop.mangle_name()
                yield name, w_value
        allattrs = self.map.get_all_attrs()
        for attr in allattrs:
            name = attr.name
            w_value = self.storage_w[attr.index]
            yield name, w_value

    def var_dump(self, space, indent, recursion):
        if self in recursion:
            return '%s*RECURSION*\n' % indent
        s = StringBuilder()
        recursion[self] = None
        header = 'object(%s)#%d ' % (self.getclass().name,
                                     self.get_instance_number())
        orig_indent = indent
        if indent.endswith('&'):
            indent = indent[:-1]
        subindent = indent + '  '
        counter = 0
        for name, w_value in self.iterproperties(space.ec.interpreter):
            counter += 1
            name, access = demangle_property(name)
            key = dump_property(name, access)
            s.append('%s[%s]=>\n' % (subindent, key))
            s.append(w_value.var_dump(space, subindent, recursion))
        s.append('%s}\n' % indent)
        del recursion[self]
        return '%s%s(%d) {\n' % (orig_indent, header, counter) + s.build()
        return s.build()

    def var_export(self, space, indent, recursion, suffix):
        header = '%s::__set_state(array' % (self.getclass().name)
        dct_w = self.get_instance_attrs()
        return array_var_export(dct_w, space,
                                indent, recursion,
                                self, header, suffix=suffix, prefix='')

    def dump(self):
        items = []
        dct_w = self.get_instance_attrs()
        for key, w_value in dct_w.items():
            items.append('%s=>%s' % (key, w_value.dump()))
        return "instance(%s: %s)" % (self.getclass().name, ', '.join(items))

    def add_attribute(self, name):
        self.map = self.map.add_attribute(name)
        self.storage_w = self.map.get_storage(self.storage_w)
        return self.map

    def _create_attr(self, name, w_value):
        """Create a *new* attribute with value w_value.

        Call only when you know that no attribute called 'name' exists.
        """
        mapattr = self.add_attribute(name)
        self.storage_w[mapattr.index] = w_value

    def _getattr(self, interp, attr, contextclass, isref, give_notice=False):
        cls = self.getclass()
        try:
            name = cls.lookup_property_name(LOOKUP_GETATTR,
                                                        interp, self, attr,
                                                        contextclass)
        except VisibilityError, e:
            if cls.method__get is not None:
                return cls.do_get(interp, self, attr, isref)
            raise e.reraise_property(interp)
        except SpecialPropertyReturn, e:
            return e.w_value
        mapattr = self.map.lookup(name)
        if mapattr is not None:
            w_value = self.storage_w[mapattr.index]
            if w_value is not None:
                if isref and not isinstance(w_value, W_Reference):
                    w_value = W_Reference(w_value)
                    self.storage_w[mapattr.index] = w_value
                return w_value
        if cls.method__get is not None:
            return cls.do_get(interp, self, attr, isref)
        if give_notice:
            interp.notice("Undefined property: %s::$%s" % (
                cls.name, attr))
        if isref:
            r_value = interp.space.empty_ref()
            self._create_attr(name, r_value)
            return r_value
        else:
            return interp.space.w_Null

    def getattr(self, interp, attr, contextclass=None, give_notice=False):
        return self._getattr(interp, attr, contextclass,
                             isref=False, give_notice=give_notice)

    def getattr_ref(self, interp, attr, contextclass):
        return self._getattr(interp, attr, contextclass,
                             isref=True, give_notice=False)

    def _setattr(self, interp, attr, w_newvalue, contextclass,
                 unique_item=False):
        cls = self.klass
        try:
            name = cls.lookup_property_name(LOOKUP_SETATTR,
                                            interp, self, attr, contextclass,
                                            w_newvalue)
        except VisibilityError, e:
            if cls.method__set is not None:
                if cls.do_set(interp, self, attr, w_newvalue):
                    return
            raise e.reraise_property(interp)
        except SpecialPropertyReturn:
            return
        mapattr = self.map.lookup(name)
        if mapattr is not None:
            w_oldvalue = self.storage_w[mapattr.index]
        else:
            if cls.method__set is not None:
                if cls.do_set(interp, self, attr, w_newvalue):
                    return
            self._create_attr(name, w_newvalue)
            return
        #
        if (isinstance(w_oldvalue, W_Reference) and
                not isinstance(w_newvalue, W_Reference)):
            # if the old value is a reference, then just update that
            # reference and be done.
            w_oldvalue.store(w_newvalue, unique=unique_item)
        else:
            self.storage_w[mapattr.index] = w_newvalue

    def setattr(self, interp, attr, w_value, contextclass, unique_item=False):
        self._setattr(interp, attr, w_value, contextclass, unique_item)
        return w_value

    def setattr_ref(self, interp, attr, w_value, contextclass):
        self._setattr(interp, attr, w_value, contextclass)
        return w_value.deref()

    def delattr(self, interp, attr, contextclass):
        cls = self.getclass()
        if cls.method__unset is not None:
            if cls.do_unset(interp, self, attr):
                return
        try:
            name = cls.lookup_property_name(LOOKUP_DELATTR, interp, self,
                                            attr, contextclass)
        except VisibilityError, e:
            raise e.reraise_property(interp)
        except SpecialPropertyReturn:
            return # XXX what do we do here?
        attr = self.map.lookup(name)
        if attr is not None:
            self.map, deleted_i = self.map.del_attribute(name)
            assert deleted_i >= 0
            self.storage_w = (self.storage_w[:deleted_i] +
                              self.storage_w[deleted_i + 1:])

    def hasattr(self, interp, attr, contextclass):
        klass = self.getclass()
        name = ''
        mapattr = None
        try:
            name = klass.lookup_property_name(LOOKUP_HASATTR, interp, self,
                                              attr,
                                              contextclass, givenotice=False)
        except SpecialPropertyReturn:
            return True
        except VisibilityError:
            has_attr = False
        else:
            mapattr = self.map.lookup(name)
            has_attr = mapattr is not None
        if not has_attr and klass.method__isset:
            w_res = klass.do_isset(interp, self, attr)
            if w_res is not None:
                return interp.space.is_true(w_res)
        if has_attr:
            return (self.storage_w[mapattr.index].deref_unique()
                    is not interp.space.w_Null)
        return False

    def clone(self, interp, contextclass):
        return self.getclass().do_clone(interp, self, contextclass)

    def _clone(self, interp):
        klass = self.getclass()
        new_storage = self.storage_w[:]
        for i in range(len(self.storage_w)):
            w_value = self.storage_w[i]
            if isinstance(w_value, W_Reference):
                self.storage_w[i] = w_value.deref()
        if klass.custom_instance_class is not None:
            w_res = klass.custom_instance_class(klass, new_storage)
            w_res.setup(interp)
        else:
            w_res = W_InstanceObject(klass, new_storage)
        w_res.map = self.map
        return w_res

    def getmeth(self, space, name, contextclass=None):
        cls = self.getclass()
        method = cls.locate_method(name, contextclass, static=False)
        if method.is_static():
            w_instance = None
        else:
            w_instance = self
        return W_BoundMethod(w_instance, cls, method.method_func)

    def get_callable(self):
        return self.getclass().get_invoke_method(self)

    def set_attribute(self, name, w_value):
        # XXX performance, used by cast_object_from
        attr = self.map.lookup(name)
        if attr is None:
            attr = self.add_attribute(name)
        self.storage_w[attr.index] = w_value

    def cast_object_from(self, space, w_arg):
        if w_arg.tp == space.tp_array:
            with space.iter(w_arg) as itr:
                while not itr.done():
                    w_key, w_value = itr.next_item(space)
                    key = space.str_w(w_key)
                    self.set_attribute(key, w_value)
        elif w_arg.tp != space.tp_null:
            self.set_attribute('scalar', w_arg)

    def as_string(self, space, quiet=False):
        return self.getclass().do_tostring(space, self, quiet=quiet)

    def str(self, space, quiet=False):
        return self.as_string(space, quiet=quiet).unwrap()

    def maybe_str(self, space):
        w_str = self.as_string(space, quiet=True)
        if w_str is not None:
            return w_str.unwrap()
        else:
            return None

    def getinstancearray(self, space):
        raise BogusImplementation("fresh-array has no meaningful current pos")

    def create_iter(self, space, contextclass=None):
        return self._create_iter(space, contextclass, byref=False)

    def create_iter_ref(self, space, r_self, contextclass=None):
        return self._create_iter(space, contextclass, byref=True)

    def _create_iter(self, space, contextclass, byref):
        # not exactly correct, because it computes the list of returned
        # attributes at once.  We might see differences if the object
        # is modified during iteration.  "But well" for now.
        from hippy.objects.arrayiter import W_FixedIterator

        klass = self.getclass()
        if klass.is_iterator:
            return W_InstanceIterator(space, self)
        items_w = []
        attrs = self.map.get_all_attrs()
        for attr in attrs:
            key = attr.name
            w_value = self.storage_w[attr.index]
            key1 = klass.check_access_and_demangle_property(
                key, contextclass)
            if key1 is not None:
                if byref and not isinstance(w_value, W_Reference):
                    w_value = W_Reference(w_value)
                    self.storage_w[attr.index] = w_value
                items_w.append((key1, w_value))
        return W_FixedIterator(items_w)

    def _msg_misuse_as_array(self, space, compat=True):
        raise space.ec.fatal('Cannot use object of type %s as array' %
                             self.klass.name)

    def getitem(self, space, w_arg, give_notice=False):
        self._msg_misuse_as_array(space)

    def serialize(self, space, builder, memo):
        if memo.memo_lookup(self, builder, 'r'):
            return False
        memo.add_counter()
        klass = self.getclass()
        kname = klass.name
        to_serialize = None
        w_field_list = None
        try:
            w_field_list = klass.methods['__sleep'].method_func.call_args(
                space.ec.interpreter, [], w_this=self, thisclass=klass)
        except KeyError:
            pass
        flen = len(self.storage_w)

        if w_field_list is not None:
            if w_field_list.tp != space.tp_array:
                space.ec.notice("serialize(): __sleep should "
                                "return an array only containing "
                                "the names of instance-variables to serialize")
                builder.append("N;")
                return False
            else:
                to_serialize = []
                with space.iter(w_field_list) as itr:
                    while not itr.done():
                        _, w_value = itr.next_item(space)
                        to_serialize.append(space.str_w(w_value))

                flen = len(to_serialize)
        builder.append('O:%d:"%s":%d:{' % (len(kname), kname, flen))
        if to_serialize is not None:
            for attr in to_serialize:
                try:
                    name = klass.lookup_property_name(LOOKUP_GETATTR,
                                                           space.ec.interpreter,
                                                           self,
                                                           attr, klass)
                except VisibilityError:
                    name = attr
                mapattr = self.map.lookup(name)
                if mapattr is not None:
                    w_value = self.storage_w[mapattr.index]
                else:
                    w_value = space.w_Null
                    space.ec.notice("serialize(): \"%s\" returned as "
                                    "member variable from __sleep() "
                                    "but does not exist" % name)
                key = 's:%d:"%s";' % (len(name), name)
                builder.append(key)
                if w_value.serialize(space, builder, memo):
                    memo.add_counter()
        else:
            allattrs = self.map.get_all_attrs()
            for mapattr in allattrs:
                name = mapattr.name
                w_value = self.storage_w[mapattr.index]
                key = 's:%d:"%s";' % (len(name), name)
                builder.append(key)
                if w_value.serialize(space, builder, memo):
                    memo.add_counter()
        builder.append("}")
        return False


class W_BoundMethod(AbstractFunction):
    def __init__(self, w_instance, klass, method_func):
        self.w_instance = w_instance
        self.klass = klass
        self.method_func = method_func

    def needs_ref(self, i):
        return self.method_func.needs_ref(i)

    def call_args(self, interp, args_w, w_this=None, thisclass=None,
                  closureargs=None):
        return self.method_func.call_args(interp, args_w,
                                          w_this=self.w_instance,
                                          thisclass=self.klass)


class BogusImplementation(Exception):
    pass
