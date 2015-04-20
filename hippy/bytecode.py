
import struct
from collections import OrderedDict
from hippy.consts import BYTECODE_STACK_EFFECTS, ARGVAL, BYTECODE_HAS_ARG,\
     BYTECODE_NAMES, ARGVAL1, ARGVAL2, _CHECKSTACK
from hippy.error import IllegalInstruction
from rpython.rlib import jit
from rpython.rlib.unroll import unrolling_iterable
from rpython.rlib.objectmodel import we_are_translated
from rpython.rlib.rstring import StringBuilder
from rpython.rlib.rstruct.runpack import runpack

class ByteCode(object):
    """ A representation of a single code block
    """
    _immutable_fields_ = ['code', 'consts[*]', 'varnames[*]',
                          'functions[*]', 'names[*]', 'stackdepth',
                          'var_to_pos', 'names_to_pos', 'late_declarations[*]',
                          'classes[*]', 'functions[*]',
                          'method_of_class', 'superglobals[*]', 'this_var_num',
                          'static_vars[*]', 'py_scope?']
    _marker = None

    def __init__(self, code, consts, names, varnames, late_declarations,
                 classes, functions,
                 filename, sourcelines, method_of_class=None,
                 startlineno=0, bc_mapping=None, name='<main>',
                 superglobals=None, this_var_num=-1, static_vars=None,
                 cloned_static_vars=None):
        # Note: Many list arguments are expected to be provably fixed size.
        self.code = code
        self.name = name      # not necessarily lowercase
        self.filename = filename
        self.startlineno = startlineno
        self.sourcelines = sourcelines
        self.consts = consts
        self.names = names
        self.varnames = varnames # named variables
        self.stackdepth = self.count_stack_depth()
        self.var_to_pos = {}
        self.names_to_pos = {}
        self.late_declarations = late_declarations
        self.classes = classes[:]
        self.functions = functions
        self.method_of_class = method_of_class
        self.bc_mapping = bc_mapping
        for i, v in enumerate(varnames):
            assert i >= 0
            self.var_to_pos[v] = i
        for i, v in enumerate(names):
            self.names_to_pos[v] = i
        self.superglobals = superglobals
        self.this_var_num = this_var_num
        self.static_vars = {}

        # In normal operation, static vars is processed into an internal
        # representation. When cloning, the transformation has already happened,
        # and we just want to copy.
        assert not (static_vars is not None and cloned_static_vars is not None)
        if static_vars is not None:
            for k, (v, cm, no) in static_vars.iteritems():
                self.static_vars[cm] = v
        else:
            self.static_vars = cloned_static_vars
        self.py_scope = None

    def clone(self):
        # Used by PyHyp PHP bytecode cache.
        return ByteCode(self.code, self.consts[:], self.names[:],
                        self.varnames[:], self.late_declarations[:],
                        self.classes[:], self.functions[:],
                        self.filename, self.sourcelines[:],
                        method_of_class=self.method_of_class,
                        startlineno=self.startlineno,
                        bc_mapping=self.bc_mapping,
                        name=self.name, superglobals=self.superglobals,
                        this_var_num=self.this_var_num,
                        cloned_static_vars=self.static_vars)

    def getline(self, no):
        try:
            return self.sourcelines[no - 1]
        except IndexError:
            ## XXX find out why!!!!
            return 'ERROR'

    @jit.elidable
    def lookup_pos(self, v):
        return self.names_to_pos[v]

    @jit.elidable_promote()
    def lookup_var_pos(self, v):
        try:
            return self.var_to_pos[v]
        except KeyError:
            return -1

    def next_arg(self, i):
        a = ord(self.code[i])
        i += 1
        if a >= 0x80:
            for k in unroll_k:
                b = ord(self.code[i])
                i += 1
                a ^= (b << k)
                if b < 0x80:
                    break
            else:
                raise IllegalInstruction("error")
        return i, a
    next_arg._always_inline_ = True

    def count_stack_depth(self):
        i = 0
        counter = 0
        max_eff = 0
        while i < len(self.code):
            c = ord(self.code[i])
            i += 1
            stack_eff = BYTECODE_STACK_EFFECTS[c]
            if c >= BYTECODE_HAS_ARG:
                i, arg = self.next_arg(i)
                if c == _CHECKSTACK:
                    assert counter == arg
            else:
                arg = -999999
            if stack_eff == ARGVAL:
                stack_eff = -arg
            elif stack_eff == ARGVAL1:
                stack_eff = -arg + 1
            elif stack_eff == ARGVAL2:
                stack_eff = -2*arg + 1
            counter += stack_eff
            assert counter >= 0
            max_eff = max(counter, max_eff)
        assert counter == 0
        return max_eff

    def dump(self):
        i = 0
        lines = []
        while i < len(self.code):
            if not we_are_translated() and i == self._marker:   # not translated
                line = ' ===> '
            else:
                num = str(i)
                line = " " * (4 - len(num)) + num + "  "
            c = ord(self.code[i])
            line += BYTECODE_NAMES[c]
            i += 1
            if c >= BYTECODE_HAS_ARG:
                i, arg = self.next_arg(i)
                line += " %s" % arg
            lines.append(line)
        return "\n".join(lines)

    def serialize(self, space):
        return Serializer(space).write_bytecode(self).finish()

    def show(self):
        print self.dump()

    def __repr__(self):
        return '<ByteCode %s (%s:%d)>' % (self.name, self.filename,
                                          self.startlineno)

    def _freeze_(self):
        raise Exception("bytecode should not be prebuilt")

unroll_k = unrolling_iterable([7, 14, 21, 28])

class Serializer(object):
    def __init__(self, space):
        self.builder = StringBuilder()
        self.space = space

    def write_int(self, i):
        self.builder.append(struct.pack("l", i))

    def write_char(self, c):
        assert len(c) == 1
        self.builder.append(c)

    def write_str(self, s):
        self.write_int(len(s))
        self.builder.append(s)

    def write_wrapped_item(self, w_item):
        w_item.ll_serialize(self.builder)

    def write_wrapped_list(self, lst_w):
        self.write_int(len(lst_w))
        for w_item in lst_w:
            self.write_wrapped_item(w_item)

    def write_list_of_str(self, lst):
        self.write_int(len(lst))
        for item in lst:
            self.write_str(item)

    def write_list_of_int(self, lst):
        self.write_int(len(lst))
        for item in lst:
            self.write_int(item)

    def write_list_of_char(self, lst):
        self.write_int(len(lst))
        for item in lst:
            self.write_char(item)

    def write_list_of_functions(self, lst):
        from hippy.function import Function
        from hippy.klass import ClassDeclaration

        self.write_int(len(lst))
        for func in lst:
            if isinstance(func, Function):
                self.write_char("f")
                self.write_function(func)
            elif isinstance(func, ClassDeclaration):
                self.write_char("u")
                self.write_class(func)
            else:
                raise NotImplementedError

    def write_function(self, func):
        self.write_bytecode(func.bytecode)
        self.write_list_of_str(func.names)
        self.write_list_of_char(func.types)
        # closuredecls, defaults_w, typehints are missing

    def write_class(self, klass):
        # extends_name, property_decl, all_parents, access_flags,
        # const_decl, constructor_method, constants_w, initial_instance_dct_w,
        # base_interface_names, identifier, properties, methods
        self.write_str(klass.name)
        self.write_int(klass.lineno)
        self.write_int(len(klass.method_decl))
        for decl in klass.method_decl.itervalues():
            self.write_str(decl.func.name)
            self.write_int(decl.access_flags)
            self.write_function(decl.func)
        # XXX

    def write_bytecode(self, bc):
        self.write_str(bc.code)
        self.write_wrapped_list(bc.consts)
        self.write_str(bc.name)
        self.write_str(bc.filename)
        self.write_int(bc.startlineno)
        self.write_list_of_str(bc.sourcelines[:])
        self.write_list_of_str(bc.names[:])
        self.write_list_of_str(bc.varnames[:])
        self.write_list_of_int(bc.superglobals[:])
        self.write_int(bc.this_var_num)
        self.write_list_of_functions(bc.late_declarations[:])
        self.write_list_of_functions(bc.classes[:])
        self.write_list_of_functions(bc.functions[:])
        self.write_list_of_int(bc.bc_mapping[:])
        return self

    def finish(self):
        return self.builder.build()

LONG_SIZE = struct.calcsize('l')

class UnserializerException(Exception):
    pass

class Unserializer(object):
    def __init__(self, repr, space):
        self.repr = repr
        self.pos = 0
        self.lgt = len(repr)
        self.space = space

    def read_char(self):
        if self.pos + 1 > self.lgt:
            raise UnserializerException
        self.pos += 1
        return self.repr[self.pos - 1]

    def read_int(self):
        if self.pos + LONG_SIZE > self.lgt:
            raise UnserializerException
        stop = self.pos + LONG_SIZE
        assert stop >= 0
        res = runpack('l', self.repr[self.pos:stop])
        self.pos += LONG_SIZE
        return res

    def read_str(self):
        lgt = self.read_int()
        if lgt == -1:
            return None
        if self.pos + lgt > self.lgt:
            raise UnserializerException
        stop = self.pos + lgt
        assert stop >= 0
        res = self.repr[self.pos:stop]
        assert lgt >= 0
        self.pos += lgt
        return res

    def read_wrapped_array(self):
        from hippy.ast import DelayedArray

        lgt = self.read_int()
        items = []
        for i in range(lgt):
            items.append(self.read_wrapped_item())
        return DelayedArray(items)

    def read_wrapped_hash(self):
        from hippy.ast import DelayedHash

        lgt = self.read_int()
        items = []
        for i in range(lgt):
            items.append((self.read_wrapped_item(), self.read_wrapped_item()))
        return DelayedHash(items)

    def read_wrapped_str(self):
        from hippy.objects.strobject import W_ConstStringObject

        return W_ConstStringObject(self.read_str())

    def read_wrapped_interpolation(self):
        from hippy.objects.interpolate import W_StrInterpolation

        lgt = self.read_int()
        lst = []
        for i in range(lgt):
            lst.append(self.read_str())

        return W_StrInterpolation(lst)

    def read_wrapped_item(self):
        type = self.read_char()
        if type == 'i':
            return self.space.wrap(self.read_int())
        elif type == "a":
            return self.read_wrapped_array()
        elif type == "s":
            return self.read_wrapped_str()
        elif type == "h":
            return self.read_wrapped_hash()
        elif type == "p":
            return self.read_wrapped_interpolation()
        else:
            raise UnserializerException("unknown type %s" % (type,))

    def read_wrapped_list(self):
        lgt = self.read_int()
        lst_w = [None] * lgt
        for i in range(lgt):
            lst_w[i] = self.read_wrapped_item()
        return lst_w

    def read_list_of_str(self):
        lgt = self.read_int()
        lst = [None] * lgt
        for i in range(lgt):
            lst[i] = self.read_str()
        return lst

    def read_list_of_chars(self):
        lgt = self.read_int()
        lst = ['\x00'] * lgt
        for i in range(lgt):
            lst[i] = self.read_char()
        return lst

    def read_list_of_int(self):
        lgt = self.read_int()
        lst = [0] * lgt
        for i in range(lgt):
            lst[i] = self.read_int()
        return lst

    def read_list_of_functions(self):
        lgt = self.read_int()
        lst = [None] * lgt
        for i in range(lgt):
            lst[i] = self.read_callable()
        return lst

    def read_class(self):
        from hippy.klass import ClassDeclaration, MethodDeclaration

        name = self.read_str()
        cls = ClassDeclaration(name)
        cls.lineno = self.read_int()
        no_of_methods = self.read_int()
        methods = OrderedDict()
        for i in range(no_of_methods):
            name = self.read_str()
            access_flags = self.read_int()
            func = self.read_function()
            func.bytecode.method_of_class = cls
            decl = MethodDeclaration(func, access_flags, cls)
            methods[func.name] = decl
        cls.method_decl = methods
        cls._init_constructor()
        return cls

    def read_function(self):
        from hippy.function import Function

        bytecode = self.unserialize()
        names = self.read_list_of_str()
        types = self.read_list_of_chars()
        if len(names) != len(types):
            raise UnserializerException
        args = [(types[i], names[i], None) for i in range(len(names))]
        return Function(args, [], [], bytecode)

    def read_callable(self):
        c = self.read_char()
        if c == 'f':
            return self.read_function()
        elif c == 'u':
            return self.read_class()
        else:
            raise UnserializerException

    def unserialize(self):
        code = self.read_str()
        consts_w = self.read_wrapped_list()[:]
        name = self.read_str()
        filename = self.read_str()
        startlineno = self.read_int()
        sourcelines = self.read_list_of_str()[:]
        names = self.read_list_of_str()[:]
        varnames = self.read_list_of_str()[:]
        superglobals = self.read_list_of_int()[:]
        this_var_num = self.read_int()
        late_declarations = self.read_list_of_functions()[:]
        classes = self.read_list_of_functions()[:]
        functions = self.read_list_of_functions()[:]
        bc_mapping = self.read_list_of_int()[:]
        return ByteCode(code, consts_w, names, varnames, late_declarations,
                        classes, functions, filename,
                        sourcelines, name=name, startlineno=startlineno,
                        superglobals=superglobals, this_var_num=this_var_num,
                        bc_mapping=bc_mapping)

def unserialize(bytecode_as_str, space):
    return Unserializer(bytecode_as_str, space).unserialize()
