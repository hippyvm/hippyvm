import sys

from rply.token import BaseBox
from rply import ParsingError
from rpython.rlib import rpath
from rpython.rlib.objectmodel import we_are_translated
from hippy import consts
from hippy.error import InterpreterError
from hippy.function import W_Constant, ClosureArgDesc
from hippy.objects.base import W_Root, W_Object
from hippy.objects.reference import W_Reference
from hippy.objects.strobject import W_ConstStringObject


class ParseError(ParsingError):
    def __str__(self):     # for debugging only
        return '%s on line %s' % (self.message, self.source_pos)


class CompilerError(InterpreterError):
    def __init__(self, msg, filename=None, lineno=-1):
        self.msg = msg
        self.filename = filename
        self.lineno = lineno


class CannotCompileYet(Exception):
    pass


class DelayedArray(W_Root):
    def __init__(self, values):
        self.values = values

    def eval_static(self, space):
        vals = [value.eval_static(space) for value in self.values]
        return space.new_array_from_list(vals)

    def repr(self):
        return "array(%s)" % ", ".join([value.repr() for value in self.values])


class DelayedHash(W_Root):
    def __init__(self, pairs):
        self.pairs = pairs

    def eval_static(self, space):
        pairs_ww = []
        for key, value in self.pairs:
            if key is not None:
                w_key = key.eval_static(space)
            else:
                w_key = None
            w_value = value.eval_static(space)
            pairs_ww.append((w_key, w_value))
        return space.new_array_from_pairs(pairs_ww)

    def repr(self):
        return "array(%s)" % ", ".join(["%s=%s" % (key, value.repr())
                                        for key, value in self.pairs])


READ, WRITE, RW, UNSET = range(4)
PLACEHOLDER = 100000   # takes 3 bytes in the bytecode


class Node(BaseBox):
    lineno = 0
    _attrs_ = ()

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return self.repr()

    def is_constant(self):
        return False

    def repr(self):
        raise TypeError("abstract base class")

    def compile(self, ctx, first_pass=False):
        if self.lineno != 0:
            ctx.set_lineno(self.lineno)
        self._compile(ctx)

    def can_compile_ptr(self):
        return False

    def compile_ptr(self, ctx, mode=READ):
        """For expressions, the regular compile() pushes the result on
        the regular stack.  This compile_ptr() on the other hand is for
        expressions used e.g. as targets of assignments: it causes a
        'BasePointer' subclass to be pushed on the 'ptrs' stack."""
        raise CompilerError("Cannot take a reference to a non-variable")

    def compile_ref(self, ctx):
        self.compile_ptr(ctx, mode=RW)
        ctx.emit(consts.RESOLVE_FOR_WRITING)

    def compile_unset(self, ctx):
        self.compile_ptr(ctx, mode=UNSET)
        ctx.emit(consts.PTR_UNSET)

    def compile_set(self, ctx):
        """Compile <self> =& <top of stack>"""
        self.compile_ptr(ctx, mode=WRITE)
        ctx.emit(consts.STORE_REF)

    def _compile(self, ctx):
        raise TypeError("abstract base class")

    def is_this(self):
        return False

    def is_unique_result(self):
        return False


class Block(Node):
    def __init__(self, stmts=None):
        if stmts is None:
            stmts = []
        if not we_are_translated():
            assert isinstance(stmts, list) and None not in stmts
        self.stmts = stmts
        self.lineno = 0

    def append_item(self, stmt):
        self.stmts.append(stmt)

    def extend_items(self, otherblock):
        assert isinstance(otherblock, Block)
        self.stmts.extend(otherblock.stmts)

    def getstmtlist(self):
        return self.stmts

    def unwrap_as_strings(self):
        result = []
        for conststr in self.stmts:
            assert isinstance(conststr, ConstantStr)
            result.append(conststr.strval)
        return result

    def repr(self):
        return "Block(" + ", ".join([i.repr() for i in self.stmts]) + ")"

    def _compile(self, ctx):
        for stmt in self.stmts:
            stmt.compile(ctx)


class LiteralBlock(Node):
    def __init__(self, literal_text, firstlineno):
        self.literal_text = literal_text
        self.lineno = firstlineno

    def repr(self):
        return "LiteralBlock(%d chars from line %d)" % (
            len(self.literal_text), self.lineno)

    def _compile(self, ctx):
        if len(self.literal_text) > 0:
            ctx.emit(consts.LOAD_NAME, ctx.create_name(self.literal_text))
            ctx.emit(consts.ECHO)


class TryBlock(Node):
    def __init__(self, block, catch_blocks, lineno=0):
        self.block = block
        self.catch_blocks = catch_blocks
        self.lineno = lineno

    def repr(self):
        return "TryBlock(%s, [%s])" % (self.block.repr(),
                                     ", ".join([b.repr()
                                                for b in self.catch_blocks]))

    def _compile(self, ctx):
        # load the catch blocks on the stack
        catch_block_positions = []
        n = len(self.catch_blocks)
        for i in range(n - 1, -1, -1):
            catch_block = self.catch_blocks[i]
            assert isinstance(catch_block, CatchBlock)
            ctx.emit(consts.LOAD_NAME,
                     ctx.create_name(catch_block.class_name))
            ctx.emit(consts.PUSH_CATCH_BLOCK, PLACEHOLDER)
            catch_block_positions.append(ctx.get_pos())
        self.block.compile(ctx)
        ctx.emit(consts.JUMP_FORWARD, PLACEHOLDER)
        positions = [ctx.get_pos()]
        for i, catch_block in enumerate(self.catch_blocks):
            assert isinstance(catch_block, CatchBlock)
            ctx.patch_pos(catch_block_positions[n - 1 - i])
            # to record we have one extra item on the stack
            ctx.emit(consts.DUMMY_STACK_PUSH)
            ctx.emit(consts.VAR_PTR, ctx.create_var_name(catch_block.varname))
            ctx.emit(consts.STORE)
            ctx.emit(consts.DISCARD_TOP)
            catch_block.compile(ctx)
            if i != len(self.catch_blocks) - 1:
                ctx.emit(consts.JUMP_FORWARD, PLACEHOLDER)
                positions.append(ctx.get_pos())
        for pos in positions:
            ctx.patch_pos(pos)


class CatchBlock(Node):
    def __init__(self, class_name, varname, block, lineno=0):
        self.class_name = class_name
        self.varname = varname
        self.block = block
        self.lineno = lineno

    def repr(self):
        return 'CatchBlock(%s, %s, %s)' % (self.class_name, self.varname,
                                           self.block.repr())

    def _compile(self, ctx):
        self.block.compile(ctx)


class ConstDecl(Node):
    def __init__(self, name, const_expr, lineno=0):
        self.name = name
        self.const_expr = const_expr
        self.lineno = lineno

    def repr(self):
        return "ConstDecl(%r, %s, %d)" % (self.name, self.const_expr.repr(),
                                          self.lineno)

    def _compile(self, ctx):
        ctx.emit(consts.LOAD_NAME, ctx.create_name("define"))
        ctx.emit(consts.GETFUNC)
        ctx.compile_call([ConstantStr(self.name),
                          self.const_expr])
        ctx.emit(consts.DISCARD_TOP)


class ClassConstant(Node):
    def __init__(self, classexpr, name, lineno=0):
        self.classexpr = classexpr
        self.name = name
        self.lineno = lineno

    def repr(self):
        return "ClassConstant(%s, %r, %d)" % (self.classexpr.repr(),
                                              self.name, self.lineno)

    def wrap(self, ctx, space):
        from hippy.klass import UserClass, DelayedClassConstant

        classexpr = self.classexpr
        if not isinstance(classexpr, ConstantStr):
            raise CompilerError("Non constant class expression in "
                                "constant initializer")
        cls_name = classexpr.strval
        cls_id = cls_name.lower()
        if cls_id == 'self':
            klass = ctx.current_class
            cls_name = klass.name
        elif cls_id == 'static':
            raise CompilerError(
                '"static::" is not allowed in compile-time constants')
        else:
            if cls_id == 'parent':
                cls_name = ctx.current_class.extends_name
            klass = ctx.find_class_or_function(cls_name.lower())
            if klass is None:
                klass = space.ec.interpreter._lookup_class(cls_name)
            if klass is None or not isinstance(klass, UserClass):
                return DelayedClassConstant(cls_name, self.name)
        try:
            return klass.constants_w[self.name]
        except KeyError:
            return DelayedClassConstant(cls_name, self.name)

    def _compile(self, ctx):
        self.classexpr.compile(ctx)
        ctx.emit(consts.CLASSCONST, ctx.create_name(self.name))


class GetClass(Node):
    def __init__(self, subexpr, lineno=0, complain=True):
        self.subexpr = subexpr
        self.lineno = lineno
        self.complain = complain

    def repr(self):
        return "GetClass(%s, %d)" % (self.subexpr.repr(), self.lineno)

    def _compile(self, ctx):
        self.subexpr.compile(ctx)
        ctx.emit(consts.GETCLASS, int(self.complain))


class Stmt(Node):
    def __init__(self, expr, lineno=0):
        self.expr = expr
        self.lineno = lineno

    def repr(self):
        return "Stmt(%s, %d)" % (self.expr.repr(), self.lineno)

    def _compile(self, ctx):
        self.expr.compile(ctx)
        if ctx.print_exprs:
            # special mode used for interactive usage: print all expressions
            # instead of discarding them.
            ctx.emit(consts.PRINT_EXPR)
        else:
            ctx.emit(consts.DISCARD_TOP)


class CommaStmt(Node):
    def __init__(self, left, right, lineno=0):
        self.left = left
        self.right = right
        self.lineno = lineno

    def repr(self):
        return "CommaStmt(%s, %s)" % (self.left.repr(), self.right.repr())

    def _compile(self, ctx):
        self.left.compile(ctx)
        ctx.emit(consts.DISCARD_TOP)
        self.right.compile(ctx)


class Silence(Node):
    def __init__(self, expr, lineno=0):
        self.expr = expr
        self.lineno = lineno

    def repr(self):
        return "Silence(%s, %d)" % (self.expr.repr(), self.lineno)

    def _compile(self, ctx):
        ctx.emit(consts.SILENCE)
        self.expr.compile(ctx)
        ctx.emit(consts.UNSILENCE)

    def can_compile_ptr(self):
        return False


class Assignment(Node):
    """ Assignment by value, i.e. '=', not '=&'.
    """
    def __init__(self, var, expr, lineno=0):
        self.var = var
        self.expr = expr
        self.lineno = lineno

    def repr(self):
        return "Assign(%s, %s, %d)" % (self.var.repr(),
                                       self.expr.repr(),
                                       self.lineno)

    def _compile(self, ctx):
        self.var.compile_ptr(ctx, mode=WRITE)
        self.expr.compile(ctx)
        if self.expr.is_unique_result():
            ctx.emit(consts.STORE_UNIQUE)
        else:
            ctx.emit(consts.STORE)


class ListAssignment(Node):
    """ Assignment by list, i.e. list($a) = ...
    """
    def __init__(self, varlist, expr):
        self.list_of_vars = varlist
        self.expr = expr

    def repr(self):
        return "ListAssign(%s, %s)" % (self.list_of_vars.repr(),
                                       self.expr.repr())

    def _compile(self, ctx):
        self.expr.compile(ctx)
        self.list_of_vars.compile(ctx)


class ListOfVars(Node):
    def __init__(self, varlist):
        self.varlist = varlist

    def repr(self):
        return "[%s]" % (", ".join([var.repr() for var in self.varlist]),)

    def _compile(self, ctx):
        varlist = self.varlist
        for i in range(len(varlist) - 1, -1, -1):
            var = varlist[i]
            if var is None:
                continue
            if isinstance(var, ListOfVars):
                ctx.emit(consts.LOAD_CONST, ctx.create_int_const(i))
                ctx.emit(consts.GETITEM_NOPOP)
                var.compile(ctx)
                ctx.emit(consts.DISCARD_TOP)
                continue
            var.compile_ptr(ctx, mode=WRITE)
            ctx.emit(consts.LOAD_CONST, ctx.create_int_const(i))
            ctx.emit(consts.GETITEM_NOPOP)
            ctx.emit(consts.STORE)
            ctx.emit(consts.DISCARD_TOP)


class Throw(Node):
    def __init__(self, expr, lineno=0):
        self.expr = expr

    def repr(self):
        return "Throw(%s)" % (self.expr.repr(),)

    def _compile(self, ctx):
        self.expr.compile(ctx)
        ctx.emit(consts.THROW)

class RefAssignment(Node):
    """ Assignment by reference, for '=&'.
    """
    def __init__(self, var, ref, lineno=0):
        self.var = var
        self.ref = ref
        self.lineno = lineno

    def repr(self):
        return "RefAssign(%s, %s, %d)" % (self.var.repr(),
                                       self.ref.repr(),
                                       self.lineno)

    def _compile(self, ctx):
        if isinstance(self.var, _BaseCall):
            raise CompilerError(
                "Can't use function return value in write context")
        self.ref.compile_ref(ctx)
        self.var.compile_set(ctx)


class InplaceOp(Node):
    """ In-place assignment operators: '+=' and friends.
    """
    def __init__(self, op, var, expr, lineno=0):
        self.op = op
        self.var = var
        self.expr = expr
        self.lineno = lineno

    def repr(self):
        return "InplaceOp(%s, %s, %s)" % (self.op, self.var.repr(),
                                          self.expr.repr())

    def _compile(self, ctx):
        assert self.op.endswith('=')
        op = self.op[:-1]
        self.var.compile_ptr(ctx)
        ctx.emit(consts.PTR_DEREF)
        self.expr.compile(ctx)
        ctx.emit(consts.BIN_OP_TO_BC[op.lower()])
        ctx.emit(consts.STORE)


class Const(Node):
    def is_constant(self):
        return True

    def uminus(self):
        raise NotImplementedError


class ConstantInt(Const):
    def __init__(self, intval, lineno=0):
        self.intval = intval
        self.lineno = lineno

    def uminus(self):
        return ConstantInt(-self.intval, self.lineno)

    def repr(self):
        return "ConstantInt(%d, %d)" % (self.intval, self.lineno)

    def _compile(self, ctx):
        ctx.emit(consts.LOAD_CONST, ctx.create_int_const(self.intval))

    def wrap(self, ctx, space):
        return space.wrap(self.intval)


class ConstantStr(Const):
    def __init__(self, strval, lineno=0):
        assert strval is not None
        self.strval = strval
        self.lineno = lineno

    def repr(self):
        return "ConstantStr(%s, %d)" % (self.strval, self.lineno)

    def _compile(self, ctx):
        strval = self.strval
        ctx.emit(consts.LOAD_NAME, ctx.create_name(strval))

    def wrap(self, ctx, space):
        return space.newstr(self.strval)

class LinkedList(Node):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def flatten(self, l):
        for x in [self.left, self.right]:
            if isinstance(x, LinkedList):
                x.flatten(l)
            else:
                l.append(x)

class DoubleQuotedStr(Node):
    def __init__(self, pieces, lineno=0):
        self.pieces = pieces
        self.lineno = lineno

    def repr(self):
        r1 = ', '.join([x.repr() for x in self.pieces])
        return "DoubleQuotedStr([%s], %d)" % (r1, self.lineno)

    def wrap(self, ctx, space):
        raise ParseError("Encapsed string cannot be used as a class constant",
                         self.lineno)

    def _compile(self, ctx):
        to_pop = 0
        strpieces = []
        for expr in self.pieces:
            if isinstance(expr, ConstantStr):
                strpieces.append(expr.strval)
                continue
            else:
                strpieces.append(None)
            to_pop += 1
            expr.compile(ctx)
        ctx.emit(consts.LOAD_CONST,
                 ctx.create_interpolation_const(strpieces))
        ctx.emit(consts.INTERPOLATE, to_pop)


class ConstantFloat(Const):
    def __init__(self, floatval, lineno=0):
        self.floatval = floatval
        self.lineno = lineno

    def uminus(self):
        return ConstantFloat(-self.floatval, self.lineno)

    def repr(self):
        return str(self.floatval)

    def _compile(self, ctx):
        ctx.emit(consts.LOAD_CONST, ctx.create_float_const(self.floatval))

    def wrap(self, ctx, space):
        return space.wrap(self.floatval)


def compile_two_arguments(ctx, left, right):
    if isinstance(left, NamedVariable):
        right.compile(ctx)
        ctx.emit(consts.LOAD_VAR_SWAP, ctx.create_var_name(left.name))
        return
    left.compile(ctx)
    right.compile(ctx)

class BinOp(Node):
    def __init__(self, op, left, right, lineno=0):
        self.op = op
        self.left = left
        self.right = right
        self.lineno = lineno

    def repr(self):
        return "BinOp(%s %s %s, %d)" % (
            self.left.repr(),
            self.op,
            self.right.repr(),
            self.lineno)

    def _compile(self, ctx):
        compile_two_arguments(ctx, self.left, self.right)
        ctx.emit(consts.BIN_OP_TO_BC[self.op.lower()])


class InstanceOf(BinOp):
    op = 'instanceof'

    def __init__(self, left, right, lineno=0):
        self.left = left
        self.right = right
        self.lineno = lineno


def _compile_suffix_or_prefix(ctx, val, op, mapping):
    if op == '++' or op == '--':
        val.compile_ptr(ctx)
    else:
        val.compile(ctx)
    ctx.emit(mapping[op])

class PrefixOp(Node):
    def __init__(self, op, val, lineno=0):
        self.op = op
        self.val = val
        self.lineno = lineno

    def repr(self):
        return "PrefixOp(%s,%s)" % (self.op, self.val.repr())

    def _compile(self, ctx):
        _compile_suffix_or_prefix(ctx, self.val, self.op,
                                  consts.PREFIX_OP_TO_BC)


class SuffixOp(Node):
    def __init__(self, op, val, lineno=0):
        self.op = op
        self.val = val
        self.lineno = lineno

    def repr(self):
        return "%s%s" % (self.val.repr(), self.op)

    def _compile(self, ctx):
        _compile_suffix_or_prefix(ctx, self.val, self.op,
                                  consts.SUFFIX_OP_TO_BC)


class Variable(Node):
    def __init__(self, node, lineno=0):
        self.node = node
        self.lineno = lineno

    def repr(self):
        return "Variable(%s, %d)" % (self.node.repr(), self.lineno)

    def _compile(self, ctx):
        node = self.node
        node.compile(ctx)
        ctx.emit(consts.LOAD_VAR_INDIRECT)

    def can_compile_ptr(self):
        return True

    def compile_ptr(self, ctx, mode=READ):
        node = self.node
        node.compile(ctx)
        ctx.emit(consts.VAR_INDIRECT_PTR)

    def compile_unset(self, ctx):
        node = self.node
        node.compile(ctx)
        ctx.emit(consts.UNSET_VAR_INDIRECT)

    def compile_set(self, ctx):
        node = self.node
        node.compile(ctx)
        ctx.emit(consts.SET_REF_INDIRECT)


class NamedVariable(Variable):
    def __init__(self, strval, lineno=0):
        self.name = strval
        self.node = ConstantStr(strval, lineno)
        self.lineno = lineno

    def repr(self):
        return "$%s" % self.name

    def is_this(self):
        return self.name == 'this'

    def _compile(self, ctx):
        ctx.emit(consts.LOAD_VAR, ctx.create_var_name(self.name))

    def compile_ptr(self, ctx, mode=READ):
        if self.name == 'this' and mode == WRITE:
            raise CompilerError("Cannot re-assign $this")
        ctx.emit(consts.VAR_PTR, ctx.create_var_name(self.name))

    def compile_unset(self, ctx):
        ctx.emit(consts.UNSET_FAST, ctx.create_var_name(self.name))

    def compile_set(self, ctx):
        if self.name == 'this':
            raise CompilerError("Cannot re-assign $this")
        ctx.emit(consts.SET_FAST, ctx.create_var_name(self.name))


class UninitializedVariable(Node):
    def __init__(self, name, lineno=0):
        self.name = name
        self.lineno = lineno

    def repr(self):
        return "$" + self.name


class InitializedVariable(Node):
    def __init__(self, name, expr, lineno=0):
        self.name = name
        self.expr = expr
        self.lineno = lineno

    def repr(self):
        return "$" + self.name + " = " + self.expr.repr()


class PropertyDecl(Node):
    def __init__(self, name, expr, access_flags=0, lineno=0):
        self.name = name
        self.expr = expr
        self.lineno = lineno
        self.access_flags = access_flags

    def set_access_flags(self, af):
        self.access_flags = af

    def repr(self):
        expr = self.expr.repr() if self.expr is not None else "None"
        return "PropertyDecl(%s, %s, %d)" % (self.name, expr, self.lineno)


class StaticMember(Node):
    def __init__(self, classexpr, varnode, lineno=0):
        self.classexpr = classexpr
        self.varnode = varnode
        self.lineno = lineno

    def repr(self):
        return "StaticMember(%s, %s, %d)" % (self.classexpr.repr(),
                                             self.varnode.repr(),
                                             self.lineno)

    def _compile(self, ctx):
        self.classexpr.compile(ctx)
        self.varnode.compile(ctx)
        ctx.emit(consts.STATICMEMBER)

    def can_compile_ptr(self):
        return True

    def compile_ptr(self, ctx, mode=READ):
        self.classexpr.compile(ctx)
        self.varnode.compile(ctx)
        ctx.emit(consts.STATICMEMBER_PTR)


class Echo(Node):
    def __init__(self, exprlist, lineno=0):
        self.exprlist = exprlist
        self.lineno = lineno

    def repr(self):
        return "Echo(%s)" % ", ".join([i.repr() for i in self.exprlist])

    def _compile(self, ctx):
        for expr in self.exprlist:
            expr.compile(ctx)
            ctx.emit(consts.ECHO)


class Print(Node):
    def __init__(self, expr, lineno=0):
        self.expr = expr
        self.lineno = lineno

    def repr(self):
        return "Print(%s)" % (self.expr.repr(),)

    def _compile(self, ctx):
        self.expr.compile(ctx)
        ctx.emit(consts.ECHO)
        ctx.emit(consts.LOAD_CONST, ctx.create_int_const(1))


class Return(Stmt):

    def repr(self):
        if self.expr is None:
            return "return;"
        return "return " + self.expr.repr() + ";"

    def _compile(self, ctx):
        if self.expr is None:
            ctx.emit(consts.LOAD_NULL)
        else:
            if ctx.returns_reference and self.expr.can_compile_ptr():
                self.expr.compile_ref(ctx)
            else:
                self.expr.compile(ctx)
                ctx.emit(consts.DEREF)
        ctx.emit(consts.RETURN)


class Require(Node):
    def __init__(self, expr, lineno=0):
        self.expr = expr
        self.lineno = lineno

    def repr(self):
        return 'require %s' % self.expr.repr()

    def _compile(self, ctx):
        self.expr.compile(ctx)
        ctx.emit(consts.REQUIRE)


class RequireOnce(Node):
    def __init__(self, expr, lineno=0):
        self.expr = expr
        self.lineno = lineno

    def repr(self):
        return 'require_once %s' % self.expr.repr()

    def _compile(self, ctx):
        self.expr.compile(ctx)
        ctx.emit(consts.REQUIRE_ONCE)


class Include(Node):
    def __init__(self, expr, lineno=0):
        self.expr = expr
        self.lineno = lineno

    def repr(self):
        return 'include %s' % self.expr.repr()

    def _compile(self, ctx):
        self.expr.compile(ctx)
        ctx.emit(consts.INCLUDE)


class IncludeOnce(Node):
    def __init__(self, expr, lineno=0):
        self.expr = expr
        self.lineno = lineno

    def repr(self):
        return 'include_once %s' % self.expr.repr()

    def _compile(self, ctx):
        self.expr.compile(ctx)
        ctx.emit(consts.INCLUDE_ONCE)


class While(Node):
    def __init__(self, expr, body, lineno=0):
        self.expr = expr
        assert body is not None
        self.body = body
        self.lineno = lineno

    def repr(self):
        return "While(%s, %s)" % (self.expr.repr(), self.body.repr())

    def _compile(self, ctx):
        pos = ctx.enter_loop()
        ctx.register_continue_target()
        self.expr.compile(ctx)
        ctx.emit(consts.JUMP_IF_FALSE, PLACEHOLDER)
        ctx.register_break()
        self.body.compile(ctx)
        ctx.emit(consts.JUMP_BACKWARD, pos)
        ctx.leave_loop()


class DoWhile(Node):
    def __init__(self, body, expr, lineno=0):
        self.expr = expr
        self.body = body
        self.lineno = lineno

    def repr(self):
        return "DoWhile(%s, %s)" % (self.body.repr(), self.expr.repr())

    def _compile(self, ctx):
        jmp_pos = ctx.enter_loop()
        ctx.register_continue_target()
        self.body.compile(ctx)
        self.expr.compile(ctx)
        ctx.emit(consts.JUMP_BACK_IF_TRUE, jmp_pos)
        ctx.leave_loop()


class For(Node):
    def __init__(self, start, cond, step, body, lineno=0):
        self.start = start
        self.cond = cond
        self.step = step
        self.body = body
        self.lineno = lineno

    def repr(self):
        if self.step:
            return "For(%s, %s, %s, %s)" % (self.start.repr(),
                                            self.cond.repr(), self.step.repr(),
                                            self.body.repr())
        else:
            return "For(%s, %s, empty, %s)" % (self.start.repr(),
                                               self.cond.repr(),
                                               self.body.repr())

    def _compile(self, ctx):
        if self.start is not None:
            self.start.compile(ctx)
            ctx.emit(consts.DISCARD_TOP)
        pos = ctx.enter_loop()
        if self.cond is not None:
            self.cond.compile(ctx)
            ctx.emit(consts.JUMP_IF_FALSE, PLACEHOLDER)
            ctx.register_break()
        self.body.compile(ctx)
        ctx.register_continue_target()
        if self.step is not None:
            self.step.compile(ctx)
            ctx.emit(consts.DISCARD_TOP)
        ctx.emit(consts.JUMP_BACKWARD, pos)
        ctx.leave_loop()


class If(Node):
    def __init__(self, cond, body, elseiflist=[], elseclause=None,
                 lineno=0):
        self.cond = cond
        assert body is not None
        self.body = body
        assert isinstance(elseiflist, list)
        self.elseiflist = elseiflist
        self.elseclause = elseclause
        self.lineno = lineno

    def repr(self):
        if self.elseiflist is not None:
            elseif = ", [" + ", ".join(
                [i.repr() for i in self.elseiflist]) + "]"
        else:
            elseif = ""
        if self.elseclause is not None:
            elseclause = ", " + self.elseclause.repr()
        else:
            elseclause = ""
        return "If(%s, %s%s%s, %d)" % (self.cond.repr(), self.body.repr(),
                                       elseif, elseclause, self.lineno)

    def _compile(self, ctx):
        self.cond.compile(ctx)
        ctx.emit(consts.JUMP_IF_FALSE, PLACEHOLDER)
        pos = ctx.get_pos()
        self.body.compile(ctx)
        jump_after_list = []

        for elem in self.elseiflist:
            ctx.emit(consts.JUMP_FORWARD, PLACEHOLDER)
            jump_after_list.append(ctx.get_pos())
            ctx.patch_pos(pos)
            assert isinstance(elem, If)
            elem.cond.compile(ctx)
            ctx.emit(consts.JUMP_IF_FALSE, PLACEHOLDER)
            pos = ctx.get_pos()
            elem.body.compile(ctx)

        if self.elseclause is not None:
            ctx.emit(consts.JUMP_FORWARD, PLACEHOLDER)
            jump_after_list.append(ctx.get_pos())
        ctx.patch_pos(pos)
        if self.elseclause is not None:
            self.elseclause.compile(ctx)
        for pos in jump_after_list:
            ctx.patch_pos(pos)


class _BaseCall(Node):
    def can_compile_ptr(self):
        return True

    def compile_ptr(self, ctx, mode=READ):
        if mode in (WRITE, UNSET):
            raise CompilerError(
                "Can't use function return value in write context")
        self.compile(ctx)
        ctx.emit(consts.REF_PTR)


class SimpleCall(_BaseCall):
    def __init__(self, name, args, lineno=0):
        self.name = name
        self.args = args
        self.lineno = lineno

    def repr(self):
        argrepr = ", ".join([i.repr() for i in self.args])
        return "SimpleCall(%s, %s, %d)" % (self.name.repr(), argrepr,
                                           self.lineno)

    def _compile(self, ctx):
        name = self.name
        if isinstance(name, GetAttr):
            this = name.node
            if this.is_this():
                ctx.emit(consts.THIS_PTR)
            else:
                this.compile_ptr(ctx)
            name.attr.compile(ctx)
            ctx.emit(consts.GETMETH)
        else:
            name.compile(ctx)
            ctx.emit(consts.GETFUNC)
        ctx.compile_call(self.args)


class DynamicCall(_BaseCall):
    def __init__(self, node, args, lineno=0):
        self.node = node
        self.args = args
        self.lineno = lineno

    def repr(self):
        argrepr = ", ".join([i.repr() for i in self.args])
        return "DynamicCall(%s, %s, %d)" % (self.node.repr(), argrepr,
                                            self.lineno)

    def _compile(self, ctx):
        self.node.compile(ctx)
        ctx.emit(consts.GETFUNC)
        ctx.compile_call(self.args)


class StaticMethodCall(_BaseCall):
    def __init__(self, classexpr, methnode, args, lineno=0):
        self.classexpr = classexpr
        self.methnode = methnode
        self.args = args
        self.lineno = lineno

    def repr(self):
        argrepr = ", ".join([i.repr() for i in self.args])
        return "StaticMethodCall(%s, %s, %s, %d)" % (
            self.classexpr.repr(), self.methnode.repr(), argrepr, self.lineno)

    def _compile(self, ctx):
        self.classexpr.compile(ctx)
        self.methnode.compile(ctx)
        ctx.emit(consts.GETSTATICMETH)
        ctx.compile_call(self.args)


class FunctionDecl(Node):
    def __init__(self, name, returns_reference, argdecls, body, lineno):
        self.name = name
        self.returns_reference = returns_reference
        assert isinstance(argdecls, list)
        self.argdecls = argdecls
        self.body = body
        self.lineno = lineno

    def repr(self):
        argsrepr = "[" + ", ".join([i.repr() for i in self.argdecls]) + "]"
        bodyrepr = self.body.repr() if self.body is not None else 'None'
        return "FunctionDecl(%s, %s, %s, %d)" % (self.name, argsrepr,
                                                 bodyrepr, self.lineno)

    def prepare_function(self, ctx, is_method_of=None, static=False):
        return ctx.prepare_function(self.name, self.argdecls, [], self.lineno,
            self.returns_reference, self.body, is_method_of=is_method_of,
            static=static)

    def _compile(self, ctx):
        function = self.prepare_function(ctx)
        num = ctx.register_function_or_class(function)
        ctx.emit(consts.DECLARE_FUNC, num)


class MethodDecl(FunctionDecl):
    def __init__(self, name, byref, argdecls, body, access_flags, lineno):
        FunctionDecl.__init__(self, name, byref, argdecls, body, lineno)
        assert isinstance(access_flags, ConstantInt)
        self.access_flags = access_flags.intval

    def set_access_flags(self, af):
        self.access_flags = af

    def repr(self):
        argsrepr = "[" + ", ".join([i.repr() for i in self.argdecls]) + "]"
        bodyrepr = self.body.repr() if self.body is not None else 'None'
        return "MethodDecl(%s, %s, %s, %d)" % (self.name, argsrepr, bodyrepr,
                                               self.lineno)


class LambdaDecl(Node):
    def __init__(self, returns_reference, argdecls, closure, body, static,
                 lineno):
        self.returns_reference = returns_reference
        self.argdecls = argdecls
        self.body = body
        self.lineno = lineno
        self.closure = closure
        self.static = static

    def repr(self):
        argsrepr = "[" + ", ".join([i.repr() for i in self.argdecls]) + "]"
        bodyrepr = self.body.repr() if self.body is not None else 'None'
        closurerepr = (self.closure.repr() if self.closure is not None
                       else "None")
        return "LambdaDecl(%s, %s, %s, %d)" % (argsrepr, closurerepr,
                                               bodyrepr, self.lineno)

    def _compile(self, ctx):
        if self.closure is not None:
            clos = self.closure
            assert isinstance(clos, ListOfVars)
        else:
            clos = None
        closuredecls = []
        if clos is not None:
            for v in clos.varlist:
                byref = False
                if isinstance(v, Reference):
                    v = v.item
                    byref = True
                assert isinstance(v, Variable)
                val = v.node
                assert isinstance(val, ConstantStr)
                closuredecls.append(ClosureArgDesc(val.strval, byref))
        function = ctx.prepare_function('lambda', self.argdecls, closuredecls,
                                        self.lineno, self.returns_reference,
                                        self.body, ctx.current_class,
                                        self.static)
        num = ctx.register_function_or_class(function)
        if self.static:
            ctx.emit(consts.LOAD_STATIC_CLOSURE, num)
        else:
            ctx.emit(consts.LOAD_CLOSURE, num)
        if clos is not None:
            for v in clos.varlist:
                v.compile(ctx)
                if not isinstance(v, Reference):
                    ctx.emit(consts.DEREF)
            ctx.emit(consts.PUT_CLOSURE_VARS, len(clos.varlist))


class Argument(Node):
    def __init__(self, name, typehint=None, is_reference=False,
                 defaultvalue=None, lineno=0):
        self.name = name
        self.typehint = typehint
        self.is_reference = is_reference
        self.defaultvalue = defaultvalue
        self.lineno = lineno

    def repr(self):
        if self.defaultvalue is None:
            defaultrepr = ""
        else:
            defaultrepr = " = " + self.defaultvalue.repr()
        if self.is_reference:
            refrepr = "&"
        else:
            refrepr = ""
        if self.typehint is None:
            typehintrepr = ""
        else:
            typehintrepr = self.typehint + " "
        return "Argument(%s%s%s%s, %d)" % (typehintrepr, refrepr, self.name,
                                           defaultrepr, self.lineno)


class ClassBlock(Node):
    def __init__(self, name, access_flags=0, extends=None, baseinterfaces=[],
                 body=None, lineno=0):
        assert extends is None or isinstance(extends, str)
        for intf in baseinterfaces:
            assert isinstance(intf, str)
        self.name = name
        self.access_flags = access_flags
        self.extends = extends
        self.baseinterfaces = baseinterfaces
        self.body = body or Block()
        self.lineno = lineno

    def set_access_flags(self, af):
        self.access_flags = af

    def repr(self):
        extendsrepr = self.extends
        if extendsrepr is None:
            extendsrepr = "None"
        implementsrepr = ', '.join(self.baseinterfaces)
        return "ClassBlock(%s, 0x%x, %s, [%s], %s, %d)" % (
            self.name, self.access_flags, extendsrepr, implementsrepr,
            self.body.repr(), self.lineno)

    def can_declare_early(self, ctx):
        if self.extends is not None:
            parent_id = self.extends.lower()
            if ctx.find_class_or_function(parent_id) is None:
                return False
        for name in self.baseinterfaces:
            if ctx.find_class_or_function(name.lower()) is None:
                return False
        return True

    def compile(self, ctx, first_pass=False):
        if first_pass and not self.can_declare_early(ctx):
            raise CannotCompileYet
        if self.lineno != 0:
            ctx.set_lineno(self.lineno)
        from hippy.klass import UserClass
        prev_class = ctx.current_class
        klass = UserClass(self.name)
        ctx.current_class = klass
        num = ctx.register_function_or_class(klass)
        klass.initialize(self, ctx)
        ctx.current_class = prev_class
        ctx.emit(consts.DECLARE_CLASS, num)


class New(Node):
    def __init__(self, classexpr, ctorargs=[], lineno=0):
        self.classexpr = classexpr
        self.ctorargs = ctorargs
        self.lineno = lineno

    def repr(self):
        argsrepr = "[" + ", ".join([i.repr() for i in self.ctorargs]) + "]"
        return "New(%s, %s, %d)" % (self.classexpr.repr(), argsrepr,
                                    self.lineno)

    def _compile(self, ctx):
        self.classexpr.compile(ctx)
        ctx.emit(consts.GETCLASS, 1)
        ctx.compile_call(self.ctorargs)

    def compile_ptr(self, ctx, mode=READ):
        # only for when 'new xyz' is used directly as argument to a func call
        self.compile(ctx)
        ctx.emit(consts.MAKE_REF_PTR)


class Clone(Node):
    def __init__(self, objexpr, lineno=0):
        self.objexpr = objexpr
        self.lineno = lineno

    def repr(self):
        return "Clone(%s, %d)" % (self.objexpr.repr(), self.lineno)

    def _compile(self, ctx):
        self.objexpr.compile(ctx)
        ctx.emit(consts.CLONE)


class GetItem(Node):
    def __init__(self, node, item, lineno=0):
        self.node = node
        self.item = item     # or None to stand for 'node[]'
        self.lineno = lineno

    def repr(self):
        if self.item is None:
            itemrepr = 'None'
        else:
            itemrepr = self.item.repr()
        return 'GetItem(%s, %s)' % (self.node.repr(), itemrepr)

    def _compile(self, ctx):
        if self.item is None:
            raise CompilerError("Cannot use [] for reading")
        left = self.node
        right = self.item
        if isinstance(left, NamedVariable):
            right.compile(ctx)
            ctx.emit(consts.GETITEM_VAR, ctx.create_var_name(left.name))
            return
        left.compile(ctx)
        right.compile(ctx)
        ctx.emit(consts.GETITEM)

    def can_compile_ptr(self):
        return True

    def compile_ptr(self, ctx, mode=READ):
        self.node.compile_ptr(ctx, mode=RW)
        if self.item is None:
            if mode == READ:
                raise CompilerError("Cannot use [] for reading")
            elif mode == UNSET:
                raise CompilerError("Cannot use [] for unsetting")
            ctx.emit(consts.APPEND_PTR)
        else:
            left = self.item
            if isinstance(left, NamedVariable):
                ctx.emit(consts.LOAD_VAR_ITEM_PTR,
                            ctx.create_var_name(left.name))
                return
            left.compile(ctx)
            ctx.emit(consts.ITEM_PTR)


class GetAttr(Node):
    def __init__(self, node, attr, lineno=0):
        self.node = node
        self.attr = attr
        self.lineno = lineno

    def repr(self):
        return 'GetAttr(%s, %s)' % (self.node.repr(), self.attr.repr())

    def _compile(self, ctx):
        node = self.node
        if node.is_this():
            self.attr.compile(ctx)
            ctx.emit(consts.THIS_ATTR)
        else:
            compile_two_arguments(ctx, self.node, self.attr)
            ctx.emit(consts.GETATTR)

    def can_compile_ptr(self):
        return True

    def compile_ptr(self, ctx, mode=READ):
        node = self.node
        if node.is_this():
            ctx.emit(consts.THIS_PTR)
        else:
            if mode in (WRITE, UNSET):
                mode = RW
            self.node.compile_ptr(ctx, mode=mode)
        self.attr.compile(ctx)
        ctx.emit(consts.ATTR_PTR)


class ObjectDimList(Node):
    def __init__(self, head, tail, lineno=0):
        self.head = head
        self.tail = tail
        self.lineno = lineno

    def repr(self):
        return 'ObjectDimList(%s, %r)' % (self.head.repr(), self.tail)


class ChainingStuff(Node):
    def __init__(self, indices, props):
        self.indices = indices
        self.props = props

    def repr(self):
        return 'ChainingStuff(%r, %r)' % (self.indices, self.props)


class Unset(Node):
    def __init__(self, nodes, lineno=0):
        self.nodes = nodes
        self.lineno = lineno

    def repr(self):
        return 'Unset([%s])' % ', '.join([node.repr() for node in self.nodes])

    def _compile(self, ctx):
        for node in self.nodes:
            node.compile_unset(ctx)


class IsSet(Node):
    def __init__(self, node, lineno=0):
        self.node = node
        self.lineno = lineno

    def repr(self):
        return 'IsSet(%s, %d)' % (self.node.repr(), self.lineno)

    def _compile(self, ctx):
        self.node.compile_ptr(ctx, mode=READ)
        ctx.emit(consts.PTR_ISSET)


class Empty(Node):
    def __init__(self, node, lineno=0):
        self.node = node
        self.lineno = lineno

    def repr(self):
        return 'Empty(%s, %d)' % (self.node.repr(), self.lineno)

    def _compile(self, ctx):
        self.node.compile_ptr(ctx, mode=READ)
        ctx.emit(consts.PTR_EMPTY)


class Hash(Node):
    def __init__(self, initializers, lineno=0):
        self.initializers = initializers
        self.lineno = lineno

    def repr(self):
        arg_repr = ["(%s => %s)" % (k, v.repr()) for k, v in self.initializers]
        return 'Hash([%s])' % ', '.join(arg_repr)

    def is_array(self):
        """
        Check whether this is a simple array (list).

        Otherwise, this is a full-blown hash (i.e. OrderedDict).
        """
        for key, value in self.initializers:
            if key is not None:
                return False
        else:
            return True

    def _compile(self, ctx):
        if self.is_constant():
            w_array = self.wrap(ctx, ctx.space)
            ctx.emit(consts.LOAD_CONST, ctx.create_other_const(w_array))
        elif self.is_array():
            self._compile_array(ctx)
        else:
            self._compile_hash(ctx)

    def is_constant(self):
        # All keys and values are constant => it's a constant array
        for key, value in self.initializers:
            if key is not None and not key.is_constant():
                return False
            if not value.is_constant():
                return False
        return True

    def _generate_code(self, ctx, value):
        assert value is not None
        value.compile(ctx)
        if not isinstance(value, Reference):
            ctx.emit(consts.DEREF)

    def _compile_array(self, ctx):
        # Generate for "array($a, &$b, $c)":
        #        ...load $a...
        #        DEREF
        #        ...load $b as a W_Reference...
        #        ...load $c...
        #        DEREF
        #        MAKE_ARRAY 3
        for key, value in self.initializers:
            self._generate_code(ctx, value)
        ctx.emit(consts.MAKE_ARRAY, len(self.initializers))

    def _compile_hash(self, ctx):
        # For every item:
        #     Load the key and the value as a pair of items
        #     DEREF the value unless the syntax uses '&'
        #     SWAP
        #     DEREF
        for key, value in self.initializers:
            if key is None:
                self._generate_code(ctx, value)
                ctx.emit(consts.LOAD_NONE)
            else:
                compile_two_arguments(ctx, key, value)
                if not isinstance(value, Reference):
                    ctx.emit(consts.DEREF)
                ctx.emit(consts.SWAP)
                ctx.emit(consts.DEREF)
        ctx.emit(consts.MAKE_HASH, len(self.initializers))

    def is_unique_result(self):
        """Return True if we're emitted with a MAKE_ARRAY or MAKE_HASH.
        Return False if we're emitted with a LOAD_CONST."""
        return not self.is_constant()

    def wrap(self, ctx, space):
        if self.is_array():
            return self._wrap_array(ctx, space)
        else:
            return self._wrap_hash(ctx, space)

    def _wrap_array(self, ctx, space):
        values = [value.wrap(ctx, space) for key, value in self.initializers]
        for w_val in values:
            if not isinstance(w_val, W_Object):
                break
        else:
            return space.new_array_from_list(values)
        return DelayedArray(values)

    def _wrap_hash(self, ctx, space):
        pairs_ww = []
        for key, value in self.initializers:
            if key is not None:
                w_key = key.wrap(ctx, space)
            else:
                w_key = None
            w_value = value.wrap(ctx, space)
            pairs_ww.append((w_key, w_value))
        for w_key, w_value in pairs_ww:
            if not (w_key is None or isinstance(w_key, W_Object) and
                    isinstance(w_value, W_Object)):
                break
        else:
            return space.new_array_from_pairs(pairs_ww)
        return DelayedHash(pairs_ww)


class And(Node):
    def __init__(self, left, right, lineno=0):
        self.left = left
        self.right = right
        self.lineno = lineno

    def repr(self):
        return 'And(%s, %s)' % (self.left.repr(), self.right.repr())

    def _compile(self, ctx):
        self.left.compile(ctx)
        ctx.emit(consts.IS_TRUE)
        ctx.emit(consts.JUMP_IF_FALSE_NO_POP, PLACEHOLDER)
        jmp_pos = ctx.get_pos()
        ctx.emit(consts.DISCARD_TOP)
        self.right.compile(ctx)
        ctx.emit(consts.IS_TRUE)
        ctx.patch_pos(jmp_pos)


class Or(Node):
    def __init__(self, left, right, lineno=0):
        self.left = left
        self.right = right
        self.lineno = lineno

    def repr(self):
        return 'Or(%s, %s)' % (self.left.repr(), self.right.repr())

    def _compile(self, ctx):
        self.left.compile(ctx)
        ctx.emit(consts.IS_TRUE)
        ctx.emit(consts.JUMP_IF_TRUE_NO_POP, PLACEHOLDER)
        jmp_pos = ctx.get_pos()
        ctx.emit(consts.DISCARD_TOP)
        self.right.compile(ctx)
        ctx.emit(consts.IS_TRUE)
        ctx.patch_pos(jmp_pos)


class Global(Node):
    def __init__(self, names, lineno=0):
        self.names = names
        self.lineno = lineno

    def repr(self):
        return 'Global(%s)' % ', '.join(self.names)

    def _compile(self, ctx):
        for name in self.names:
            if name == 'this':
                raise CompilerError("Cannot re-assign $this")
            ctx.emit(consts.DECLARE_GLOBAL, ctx.create_var_name(name))


class StaticDecl(Node):
    def __init__(self, vars, lineno=0):
        self.vars = vars
        self.lineno = lineno

    def repr(self):
        return 'StaticDecl([%s])' % ', '.join([v.repr() for v in self.vars])

    def _compile(self, ctx):
        for var in self.vars:
            if isinstance(var, UninitializedVariable):
                name = var.name
                w_initial_value = ctx.space.w_Null
            else:
                assert isinstance(var, InitializedVariable)
                name = var.name
                w_initial_value = var.expr.wrap(ctx, ctx.space)
            if name == 'this':
                raise CompilerError("Cannot re-assign $this")
            if name in ctx.static_vars:
                # generate a warning --- it's nonsense code
                ctx.warn("Static variable '%s' declared twice, ignoring "
                         "previous declaration" % (name,))
                w_ref = ctx.static_vars[name]
                w_ref.store(w_initial_value)
            else:
                w_ref = W_Reference(w_initial_value)
                ctx.static_vars[name] = w_ref
            ctx.emit(consts.LOAD_CONST, ctx.create_other_const(w_ref))
            NamedVariable(name).compile_set(ctx)
            ctx.emit(consts.DISCARD_TOP)


class NamedConstant(Node):
    def __init__(self, name, lineno=0):
        self.name = name
        self.lineno = lineno

    def is_constant(self):
        # only prebuilt ones
        if self.name.lower() in ['true', 'false', 'null']:
            return True
        return False

    def repr(self):
        return 'NamedConstant(%s)' % self.name

    def _compile(self, ctx):
        ctx.emit(consts.LOAD_NAMED_CONSTANT, ctx.create_name(self.name))

    def wrap(self, ctx, space):
        name = self.name.lower()
        if name == 'null':
            return space.w_Null
        elif name == 'true':
            return space.w_True
        elif name == 'false':
            return space.w_False
        else:
            return W_Constant(self.name)


class MagicConstant(Node):
    def __init__(self, lineno=0):
        self.lineno = lineno

    def compile(self, ctx, first_pass=False):
        ConstantStr(self.eval(ctx), self.lineno).compile(ctx)

    def wrap(self, ctx, space):
        return W_ConstStringObject(self.eval(ctx))

    def eval(self, ctx):
        raise NotImplementedError('Abstract base class')

    def repr(self):
        return '%s()' % self.__class__.__name__


class FileMagic(MagicConstant):
    def eval(self, ctx):
        return ctx.filename


class DirMagic(MagicConstant):
    def eval(self, ctx):
        dirname = rpath.dirname(ctx.filename)
        if not dirname:
            dirname = '.'
        return dirname


class MethodMagic(MagicConstant):
    def eval(self, ctx):
        if ctx.is_global:
            if ctx.current_class:
                return ctx.current_class.name
            else:
                return ''
        if ctx.method_of_class:
            cls_prefix = ctx.method_of_class.name + '::'
        else:
            cls_prefix = ''
        return cls_prefix + ctx.name


class ClassMagic(MagicConstant):
    def eval(self, ctx):
        if ctx.current_class:
            return ctx.current_class.name
        else:
            return ''


class FunctionMagic(MagicConstant):
    def eval(self, ctx):
        return ctx.name if not ctx.is_global else ''


class Reference(Node):
    def __init__(self, item=None, lineno=0):
        self.item = item
        self.lineno = lineno

    def repr(self):
        if self.item is not None:
            itemrepr = self.item.repr()
        else:
            itemrepr = ""
        return 'Reference(%s)' % itemrepr

    def _compile(self, ctx):
        self.item.compile_ref(ctx)


class Break(Node):
    def __init__(self, levels=1, lineno=0):
        self.levels = levels
        self.lineno = lineno

    def repr(self):
        return "Break(%d, %d)" % (self.levels, self.lineno)

    def _compile(self, ctx):
        ctx.emit_break(self.levels)


class Continue(Node):
    def __init__(self, levels=1, lineno=0):
        self.levels = levels
        self.lineno = lineno

    def repr(self):
        return "Continue(%d, %d)" % (self.levels, self.lineno)

    def _compile(self, ctx):
        ctx.emit_continue(self.levels)


class IfExpr(Node):
    def __init__(self, cond, left, right, lineno=0):
        self.cond = cond
        self.left = left
        self.right = right
        self.lineno = lineno

    def repr(self):
        return "IfExpr(%s, %s, %s)" % (self.cond.repr(), self.left.repr(),
                                       self.right.repr())

    def _compile(self, ctx):
        self.cond.compile(ctx)
        ctx.emit(consts.JUMP_IF_FALSE, PLACEHOLDER)
        jmp_if_false_pos = ctx.get_pos()
        self.left.compile(ctx)
        ctx.emit(consts.JUMP_FORWARD, PLACEHOLDER)
        jmp_forward_pos = ctx.get_pos()
        ctx.emit(consts.DISCARD_TOP)   # dead code, to fix the stack depth
        ctx.patch_pos(jmp_if_false_pos)
        self.right.compile(ctx)
        ctx.patch_pos(jmp_forward_pos)


class ForEach(Node):
    def __init__(self, expr, valuevar, body, lineno=0):
        self.expr = expr
        self.valuevar = valuevar
        self.body = body
        self.lineno = lineno

    def repr(self):
        return 'ForEach(%s, %s, %s)' % (self.expr.repr(), self.valuevar.repr(),
                                        self.body.repr())

    def _compile(self, ctx):
        if not isinstance(self.valuevar, Reference):
            self.expr.compile(ctx)
            ctx.emit(consts.CREATE_ITER)
        else:
            self.expr.compile_ref(ctx)
            ctx.emit(consts.CREATE_ITER_REF)
        jmp_back_pos = ctx.enter_loop(extra_stack=1)
        ctx.register_continue_target()
        ctx.emit(consts.NEXT_VALUE_ITER, PLACEHOLDER)
        ctx.register_break()
        ctx.compile_assignment(self.valuevar)
        if self.body is not None:
            self.body.compile(ctx)
        ctx.emit(consts.JUMP_BACKWARD, jmp_back_pos)
        ctx.leave_loop()
        ctx.emit(consts.DISCARD_TOP)


class ForEachKey(Node):
    def __init__(self, expr, keyvar, valuevar, body, lineno=0):
        self.expr = expr
        self.keyvar = keyvar
        self.valuevar = valuevar
        self.body = body
        self.lineno = lineno

    def repr(self):
        return 'ForEachKey(%s, %s, %s, %s)' % (self.expr.repr(),
                                               self.keyvar.repr(),
                                               self.valuevar.repr(),
                                               self.body.repr())

    def _compile(self, ctx):
        if not isinstance(self.valuevar, Reference):
            self.expr.compile(ctx)
            ctx.emit(consts.CREATE_ITER)
        else:
            self.expr.compile_ref(ctx)
            ctx.emit(consts.CREATE_ITER_REF)
        jmp_back_pos = ctx.enter_loop(extra_stack=1)
        ctx.register_continue_target()
        ctx.emit(consts.NEXT_ITEM_ITER, PLACEHOLDER)
        ctx.register_break()
        ctx.compile_assignment(self.valuevar)
        ctx.compile_assignment(self.keyvar)
        self.body.compile(ctx)
        ctx.emit(consts.JUMP_BACKWARD, jmp_back_pos)
        ctx.leave_loop()
        ctx.emit(consts.DISCARD_TOP)


class Cast(Node):
    def __init__(self, to, expr, lineno=0):
        self.to = to
        self.expr = expr
        self.lineno = lineno

    def repr(self):
        return 'Cast(%s, %s)' % (self.to, self.expr.repr())

    def _compile(self, ctx):
        self.expr.compile(ctx)
        ctx.emit(consts.CAST_TO_BC[self.to])


class Switch(Node):
    def __init__(self, expr, casesblock, lineno=0):
        self.expr = expr
        self.casesblock = casesblock
        self.lineno = lineno

    def repr(self):
        return 'Switch(%s, %s, %d)' % (self.expr.repr(),
                                       self.casesblock.repr(),
                                       self.lineno)

    def _compile(self, ctx):
        self.expr.compile(ctx)
        ctx.enter_loop()
        default_case = None
        cases_pos = []
        caselist = self.casesblock.getstmtlist()
        for case in caselist:
            assert isinstance(case, Case)
            ctx.set_lineno(case.lineno)
            if case.expr is None:
                # xxx warn if several 'default:'
                default_case = case
                pos = sys.maxint
            else:
                case.expr.compile(ctx)
                ctx.emit(consts.CASE_IF_EQ, PLACEHOLDER)
                pos = ctx.get_pos()
            cases_pos.append(pos)
        ctx.emit(consts.DISCARD_TOP)
        ctx.emit(consts.JUMP_FORWARD, PLACEHOLDER)
        if default_case is None:
            ctx.register_break()
            final_jump_pos = -1  # please the annotator
        else:
            final_jump_pos = ctx.get_pos()
        #
        for i in range(len(caselist)):
            case = caselist[i]
            assert isinstance(case, Case)
            ctx.set_lineno(case.lineno)
            if case is default_case:
                ctx.patch_pos(final_jump_pos)
            elif case.expr is not None:
                ctx.patch_pos(cases_pos[i])
            case.block.compile(ctx)
        ctx.register_continue_target()
        ctx.leave_loop()


class Case(Node):
    def __init__(self, expr, block, lineno=0):
        self.expr = expr    # or None for 'default:'
        self.block = block
        self.lineno = lineno

    def repr(self):
        if self.expr is not None:
            exprrepr = self.expr.repr()
        else:
            exprrepr = 'None'
        return 'Case(%s, %s, %d)' % (exprrepr, self.block.repr(), self.lineno)


class Exit(Node):
    def __init__(self, expr, lineno=0):
        self.expr = expr

    def repr(self):
        return 'Exit(%s, %d)' % (self.expr.repr(), self.lineno)

    def _compile(self, ctx):
        ctx.emit(consts.LOAD_NAME, ctx.create_name("___exit"))
        ctx.emit(consts.GETFUNC)
        ctx.compile_call([self.expr])


class TupleWrapper(Node):
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2


class GotoLabel(Node):
    def __init__(self, label, lineno=0):
        self.label = label
        self.lineno = lineno

    def repr(self):
        return 'GotoLabel(%s, %d)' % (self.label, self.lineno)

    def _compile(self, ctx):
        if self.label in ctx.goto_labels:
            raise CompilerError("Label '%s' already defined" % (self.label,))
        looplabel = ctx.get_innermost_loop()
        if looplabel is not None:
            looplabel.labels_inside_loop.append(self.label)
            start = looplabel.start_pos
            current_extra = looplabel.extra_stack_total
        else:
            start = -1
            current_extra = 0
        ctx.goto_labels[self.label] = ctx.get_pos(), current_extra
        try:
            lst = ctx.pending_gotos.pop(self.label)
        except KeyError:
            pass
        else:
            for pos1, pos2, extra in lst:
                if pos2 <= start:
                    raise CompilerError("'goto' into loop or switch statement"
                                        " is disallowed")
                ctx.patch_pos(pos2)
                n = extra - current_extra
                assert n >= 0
                ctx.patch_with(pos1, n)


class Goto(GotoLabel):
    def repr(self):
        return 'Goto(%s, %d)' % (self.label, self.lineno)

    def _compile(self, ctx):
        looplabel = ctx.get_innermost_loop()
        if looplabel is not None:
            current_extra = looplabel.extra_stack_total
        else:
            current_extra = 0
        try:
            pos, extra = ctx.goto_labels[self.label]
        except KeyError:
            ctx.emit(consts.BREAK_CONTINUE_POP, PLACEHOLDER)
            p1 = ctx.get_pos()
            ctx.emit(consts.JUMP_FORWARD, PLACEHOLDER)
            p2 = ctx.get_pos()
            lst = ctx.pending_gotos.setdefault(self.label, [])
            lst.append((p1, p2, current_extra))
        else:
            if pos < 0:
                raise CompilerError("'goto' into loop or switch statement"
                                    " is disallowed")
            n = current_extra - extra
            assert n >= 0
            if n > 0:
                ctx.emit(consts.BREAK_CONTINUE_POP, n)
            ctx.emit(consts.JUMP_BACKWARD, pos)


class BackTick(Node):
    def __init__(self, cmd, lineno=0):
        self.cmd = cmd
        self.lineno = lineno

    def repr(self):
        return 'Popen(%s, %d)' % (self.cmd.repr(), self.lineno)

    def _compile(self, ctx):
        self.cmd.compile(ctx)
        ctx.emit(consts.POPEN)
