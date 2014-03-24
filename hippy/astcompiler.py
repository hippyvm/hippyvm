from hippy.ast import (
    Block, FunctionDecl, ClassBlock, New, Reference, Argument, CompilerError,
    CannotCompileYet, PLACEHOLDER)
from hippy.objects.intobject import W_IntObject
from hippy.objects.floatobject import W_FloatObject
from hippy.objects.interpolate import W_StrInterpolation
from hippy import consts
from hippy.bytecode import ByteCode
from hippy.function import Function
from rpython.rlib.objectmodel import we_are_translated


def compile_ast(filename, source, mainnode, space, print_exprs=False):
    ctx = CompilerContext(filename, source.split("\n"), 1, space,
                          print_exprs=print_exprs)
    assert isinstance(mainnode, Block)
    try:
        # first all function and class declarations that occur at top-level
        remaining = []
        for stmt in mainnode.stmts:
            if not (isinstance(stmt, FunctionDecl) or
                    isinstance(stmt, ClassBlock)):
                remaining.append(stmt)
            else:
                try:
                    stmt.compile(ctx, first_pass=True)
                except CannotCompileYet:
                    remaining.append(stmt)
        # then all the remaining code
        for stmt in remaining:
            stmt.compile(ctx)
    except CompilerError as exc:
        exc.filename = ctx.filename
        exc.lineno = ctx.cur_lineno
        raise
    return ctx.create_bytecode()


def intern(name, cache={}):
    try:
        return cache[name]
    except KeyError:
        cache[name] = name
        return name

SUPERGLOBALS = ['GLOBALS', '_SERVER', '_GET', '_POST', "_COOKIE", "_SESSION"]
SUPERGLOBAL_LOOKUP = {}
for i, v in enumerate(SUPERGLOBALS):
    SUPERGLOBAL_LOOKUP[v] = i


class CompilerContext(object):
    """ Context for compiling a piece of bytecode. It'll store the necessary
    """
    current_class = None

    def __init__(self, filename, sourcelines, startlineno,
                 space, name='<main>',
                 print_exprs=False, is_global=True):
        self.space = space
        self.filename = filename
        self.sourcelines = sourcelines
        self.data = []
        self.consts = []
        self.names = []
        self.names_to_nums = {}
        self.varnames = []
        self.varnames_to_nums = {}
        self.int_cache = {}
        self.float_cache = {}
        self.string_cache = {}
        self.functions = []
        self.llabels = []  # stack of LoopLabels
        self.goto_labels = {}
        self.pending_gotos = {}
        self.startlineno = startlineno
        self.cur_lineno = startlineno
        self.lineno_map = []
        self.name = name
        self.print_exprs = print_exprs
        self.is_global = is_global
        self.static_vars = {}
        self.superglobals = [-1] * len(SUPERGLOBALS)
        self.this_var_num = -1
        self.method_of_class = None
        self.returns_reference = False

    def warn(self, msg):
        from hippy.constants import E_HIPPY_WARN
        self.space.ec.interpreter.log_error(E_HIPPY_WARN, msg)

    def register_superglobal(self, name, index):
        self.superglobals[SUPERGLOBAL_LOOKUP[name]] = index

    def set_lineno(self, lineno):
        self.cur_lineno = lineno

    def emit(self, bc, arg=-42):
        self.lineno_map.append(self.cur_lineno)
        self.data.append(chr(bc))
        if bc >= consts.BYTECODE_HAS_ARG:
            assert arg >= 0
            a = arg
            while a >= 0x80:
                self.data.append(chr((a & 0x7f) | 0x80))
                self.lineno_map.append(self.cur_lineno)
                a ^= 0x80
                a >>= 7
            self.data.append(chr(a))
            self.lineno_map.append(self.cur_lineno)
        else:
            assert arg == -42

    def get_pos(self):
        return len(self.data)

    def patch_with(self, pos, a):
        assert self.data[pos - 3] == '\xA0'
        assert self.data[pos - 2] == '\x8C'
        assert self.data[pos - 1] == '\x07'
        self.data[pos - 3] = chr((a & 0x7f) | 0x80)
        a ^= 0x80
        a >>= 7
        self.data[pos - 2] = chr((a & 0x7f) | 0x80)
        a ^= 0x80
        a >>= 7
        if a >= 0x80:
            raise CompilerError("Internal error: bytecode too big")
        self.data[pos - 1] = chr(a)

    def patch_pos(self, pos):
        # 'pos' must be the position just after a PLACEHOLDER arg; patch it
        self.patch_with(pos, self.get_pos())

    def enter_loop(self, extra_stack=0):
        if len(self.llabels) == 0:
            extra_stack_total = 0
        else:
            extra_stack_total = self.llabels[-1].extra_stack_total
        extra_stack_total += extra_stack
        self.llabels.append(LoopLabels(self.get_pos(), extra_stack,
                                       extra_stack_total))
        return self.get_pos()

    def _emit_break_continue_pop(self, levels):
        # we must (sometimes) emit a BREAK_CONTINUE_POP instruction
        assert levels >= 1
        looplabels = None
        # compute the total stack items to remove
        remove_stack = 0
        for i in range(levels):
            num = len(self.llabels) - i - 1
            if num < 0:
                raise CompilerError("Cannot break/continue %d level%s" % (
                    levels, "s" if levels > 1 else ""))
            looplabels = self.llabels[num]
            remove_stack += looplabels.extra_stack
        # we don't exit the last loop (even a 'break;' jumps just before
        # the final DISCARD_TOP, in case of 'foreach')
        if looplabels is not None:
            remove_stack -= looplabels.extra_stack
        if remove_stack > 0:
            self.emit(consts.BREAK_CONTINUE_POP, remove_stack)
        return looplabels

    def register_break(self):
        self.llabels[-1].pos_of_breaks.append(self.get_pos())

    def emit_break(self, levels=1):
        looplabels = self._emit_break_continue_pop(levels)
        self.emit(consts.JUMP_FORWARD, PLACEHOLDER)
        looplabels.pos_of_breaks.append(self.get_pos())

    def emit_continue(self, levels=1):
        looplabels = self._emit_break_continue_pop(levels)
        if looplabels.pos_of_continues is not None:
            self.emit(consts.JUMP_FORWARD, PLACEHOLDER)
            looplabels.pos_of_continues.append(self.get_pos())
        else:
            self.emit(consts.JUMP_BACKWARD, looplabels.target_continue)

    def _do_check_stack(self):
        if we_are_translated():
            return
        total_extra_stack = sum([llbl.extra_stack for llbl in self.llabels])
        self.emit(consts._CHECKSTACK, total_extra_stack)

    def register_continue_target(self):
        looplabels = self.llabels[-1]
        pos_of_continues = looplabels.pos_of_continues
        looplabels.pos_of_continues = None
        assert pos_of_continues is not None, (
            "register_continue_target() called twice")
        for jmp_pos in pos_of_continues:
            self.patch_pos(jmp_pos)
        looplabels.target_continue = self.get_pos()
        self._do_check_stack()

    def leave_loop(self):
        looplabels = self.llabels[-1]
        assert looplabels.pos_of_continues is None, (
            "register_continue_target() should have been called")
        for jmp_pos in looplabels.pos_of_breaks:
            self.patch_pos(jmp_pos)
        self._do_check_stack()
        self.llabels.pop()
        # labels that have been defined inside this loop are now invalid:
        for label in looplabels.labels_inside_loop:
            self.goto_labels[label] = (-1, -1)

    def get_innermost_loop(self):
        if len(self.llabels) > 0:
            return self.llabels[-1]
        else:
            return None

    def create_interpolation_const(self, strings):
        self.consts.append(W_StrInterpolation(strings[:]))
        return len(self.consts) - 1

    def create_int_const(self, v):
        try:
            return self.int_cache[v]
        except KeyError:
            a = len(self.consts)
            self.consts.append(W_IntObject(v))
            self.int_cache[v] = a
            return a

    def create_other_const(self, w_v):
        # xxx no caching for now, which should not really be a problem
        a = len(self.consts)
        self.consts.append(w_v)
        return a

    def create_float_const(self, v):
        try:
            return self.float_cache[v]
        except KeyError:
            a = len(self.consts)
            self.consts.append(W_FloatObject(v))
            self.float_cache[v] = a
            return a

    def create_name(self, name):
        name = intern(name)
        try:
            return self.names_to_nums[name]
        except KeyError:
            r = len(self.names)
            self.names_to_nums[name] = r
            self.names.append(name)
            return r

    def create_var_name(self, name):
        name = intern(name)
        try:
            return self.varnames_to_nums[name]
        except KeyError:
            r = len(self.varnames)
            self.varnames_to_nums[name] = r
            self.varnames.append(name)
            if name in SUPERGLOBALS:
                self.register_superglobal(name, r)
            return r

    def force_var_name(self, name):
        name = intern(name)
        result = (name not in self.varnames_to_nums)
        self.varnames_to_nums[name] = len(self.varnames)
        self.varnames.append(name)
        return result

    def register_function_or_class(self, w_func_or_class):
        i = len(self.functions)
        self.functions.append(w_func_or_class)
        return i

    def find_class_or_function(self, identifier):
        for func in self.functions:
            if func.get_identifier() == identifier:
                return func

    def create_bytecode(self):
        if self.pending_gotos:
            raise CompilerError("'goto' to undefined label '%s'" % (
                self.pending_gotos.keys()[0],))
        return ByteCode("".join(self.data), self.consts[:], self.names[:],
                        self.varnames[:], self.functions,
                        self.filename, self.sourcelines, self.method_of_class,
                        self.startlineno,
                        self.lineno_map[:], self.name, self.superglobals,
                        self.this_var_num)

    def compile_call(self, args):
        for i, arg in enumerate(args):
            if not arg.can_compile_ptr() and not isinstance(arg, New):
                # ARG_BY_VALUE: [function, argument]
                #            => [argument, function]
                # so the function object remains on top of all arguments, which
                # accumulate below.  ARG_BY_VALUE is essentially a SWAP, but
                # also checks that the function is not expecting a reference
                # argument at position i.
                arg.compile(self)
                self.emit(consts.ARG_BY_VALUE, i)
            else:
                # ARG_BY_PTR: [function] and 'argument' from the 'ptrs' stack
                #   => [argument_or_reference_to_argument, function]
                arg.compile_ptr(self)
                self.emit(consts.ARG_BY_PTR, i)
        self.emit(consts.CALL, len(args))

    def compile_assignment(self, var):
        # POP a value and assign it to 'var'.  If 'var' is a Reference,
        # POP a reference instead and change the assignment of 'var'.
        if isinstance(var, Reference):
            var.item.compile_set(self)
        else:
            var.compile_ptr(self)
            if var.is_unique_result():
                self.emit(consts.STORE_UNIQUE)
            else:
                self.emit(consts.STORE)
        self.emit(consts.DISCARD_TOP)

    def prepare_function(ctx, name, argdecls, closuredecls, lineno,
                         returns_reference, body, is_method_of=None,
                         static=False):
        new_context = CompilerContext(ctx.filename, ctx.sourcelines, lineno,
                                      ctx.space, name, is_global=False)
        args = []
        typehints = []
        for i, arg in enumerate(argdecls):
            assert isinstance(arg, Argument)
            name = arg.name
            if arg.is_reference:
                opcode = consts.ARG_REFERENCE
            else:
                opcode = consts.ARG_ARGUMENT
            if arg.defaultvalue is None:
                w_default = None
            else:
                w_default = arg.defaultvalue.wrap(ctx, ctx.space)
            if arg.typehint is not None:
                typehints.append((i, arg.typehint,
                                w_default is ctx.space.w_Null))
            args.append((opcode, name, w_default))
            if not new_context.force_var_name(name):
                ctx.warn("Argument list contains twice '$%s'" % (name,))
        if is_method_of is not None:
            new_context.method_of_class = is_method_of
            new_context.current_class = is_method_of
            if not static:
                new_context.this_var_num = len(argdecls)
                if not new_context.force_var_name("this"):
                    raise CompilerError("Cannot re-assign $this")
        new_context.returns_reference = returns_reference
        #
        if body is not None:
            for decl in closuredecls:
                new_context.force_var_name(decl.name)
            #
            for i, typehint, allow_null in typehints:
                j = i * 2 + allow_null
                if typehint == 'array':
                    new_context.emit(consts.TYPEHINT_ARRAY, j)
                else:
                    new_context.emit(consts.LOAD_NAME,
                                    new_context.create_name(typehint))
                    new_context.emit(consts.TYPEHINT_CLASS, j)
            #
            body.compile(new_context)
            new_context.emit(consts.LOAD_NULL)
            new_context.emit(consts.RETURN)
        else:
            new_context.emit(consts.ABSTRACT_METHOD)
        bytecode = new_context.create_bytecode()
        return Function(args, closuredecls, typehints, bytecode)


class LoopLabels:
    def __init__(self, start_pos, extra_stack, extra_stack_total):
        self.start_pos = start_pos
        self.extra_stack = extra_stack
        self.extra_stack_total = extra_stack_total
        self.pos_of_breaks = []
        self.pos_of_continues = []
        self.labels_inside_loop = []


def bc_preprocess(source):
    l = []
    for i in source.splitlines():
        if '#' in i:
            i = i[:i.find('#')]
        i = i.strip()
        if not i:
            continue
        l.append(i)
    return "\n".join(l)
