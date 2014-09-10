from rply import ParserGenerator
from hippy.lexer import PRECEDENCES, ALL_RULES, BaseLexer, Lexer
from hippy import consts
from rpython.rlib.objectmodel import specialize, we_are_translated
from hippy.ast import (
    Block, Assignment, RefAssignment, Stmt, ConstantInt, BinOp, Variable,
    NamedVariable, ConstantStr, Echo, ConstantFloat, If, SuffixOp, PrefixOp,
    While, SimpleCall, For, GetItem, FunctionDecl, LambdaDecl, Argument,
    Return, And, Or, InplaceOp, Global, NamedConstant, DoWhile, Reference,
    Break, Hash, IfExpr, DoubleQuotedStr, ForEach, ForEachKey, Cast, Continue,
    DynamicCall, StaticDecl, UninitializedVariable, InitializedVariable,
    LiteralBlock, Unset, Print, ConstDecl, ClassBlock, New, GetAttr,
    StaticMember, StaticMethodCall, GetClass, ClassConstant, Clone, IsSet,
    Empty, Silence, Switch, Case, Require, RequireOnce, Include, IncludeOnce,
    Exit, GotoLabel, Goto, ListAssignment, ListOfVars, TryBlock, CatchBlock,
    Throw, CommaStmt, ChainingStuff, TupleWrapper, LinkedList, FileMagic,
    DirMagic, ClassMagic, MethodMagic, FunctionMagic, NamespaceMagic,
    ObjectDimList, PropertyDecl, MethodBlock, ParseError, BackTick,
    InstanceOf, Eval, BeginNamespace, NameBase, RelativeName, AbsoluteName,
    Static, Use, UseDeclaration, NamespaceBlock)


def is_hexdigit(c):
    return '0' <= c <= '9' or 'A' <= c <= 'F' or 'a' <= c <= 'f'


def hexdigit(c):
    if '0' <= c <= '9':
        return ord(c) - ord('0')
    if 'A' <= c <= 'F':
        return ord(c) - ord('A') + 10
    if 'a' <= c <= 'f':
        return ord(c) - ord('a') + 10
    raise AssertionError


class LexerWrapper(BaseLexer):
    def __init__(self, lexer):
        self.lexer = lexer

    def next(self):
        for token in self.lexer.token():
            return token


class BaseParser(object):
    pass


class SourceParser(BaseParser):

    def __init__(self, space, lexer, filename):
        self.space = space
        self.lexer = lexer
        self.filename = filename

    def parse(self):
        l = LexerWrapper(self.lexer)
        return self.parser.parse(l, state=self)

    pg = ParserGenerator([d for (r, d) in ALL_RULES],
                         precedence=PRECEDENCES,
                         cache_id="hippy")

    @pg.production("main : top_statement_list")
    def main_top_statement_list(self, p):
        return p[0]

    @pg.production("top_statement_list : top_statement_list top_statement")
    def top_statement_list_top_statement(self, p):
        if p[1] is not None:
            p[0].append_item(p[1])
        return p[0]

    @pg.production("top_statement_list : empty")
    def top_statatement_list(self, p):
        blk = Block()
        return blk

    @pg.production("top_statement : statement")
    def top_statement(self, p):
        return p[0]

    @pg.production("top_statement : function_declaration_statement")
    def top_statement_function_declaration_statement(self, p):
        return p[0]

    @pg.production("top_statement : class_declaration_statement")
    def top_statement_class_declaration_statement(self, p):
        return p[0]

    @pg.production("top_statement : constant_declaration")
    def top_statement_constant_declaration(self, p):
        return p[0]

    @pg.production("top_statement : T_NAMESPACE namespace_name ;")
    def top_statement_namespace(self, p):
        return BeginNamespace(p[1], p[1].lineno)

    @pg.production("top_statement : T_NAMESPACE namespace_name { top_statement_list }")
    def top_statement_namespace_block(self, p):
        return NamespaceBlock(p[1], p[3], lineno=p[1].lineno)

    @pg.production("top_statement : T_NAMESPACE { top_statement_list }")
    def top_statement_namespace_block(self, p):
        return NamespaceBlock(RelativeName([]), p[2],
                              lineno=p[0].getsourcepos())

    @pg.production("top_statement : T_USE use_declarations ;")
    def use_statement(self, p):
        use_decls = p[1]
        assert isinstance(use_decls, Block)
        return Use(use_decls.stmts, lineno=p[0].getsourcepos())

    @pg.production("use_declarations : use_declarations , use_declaration")
    def use_declarations_many(self, p):
        p[0].append_item(p[2])
        return p[0]

    @pg.production("use_declarations : use_declaration")
    def use_declarations_many(self, p):
        return Block([p[0]])

    @pg.production("use_declaration : namespace_name")
    def use_relative_name(self, p):
        return UseDeclaration(p[0], lineno=p[0].lineno)

    @pg.production("use_declaration : namespace_name T_AS T_STRING")
    def use_relative_name_as(self, p):
        return UseDeclaration(p[0], p[2].getstr(), lineno=p[0].lineno)

    @pg.production("use_declaration : T_NS_SEPARATOR namespace_name")
    def use_absolute_name(self, p):
        return UseDeclaration(p[1], lineno=p[1].lineno)

    @pg.production("use_declaration : "
                   "T_NS_SEPARATOR namespace_name T_AS T_STRING")
    def use_absolute_name_as(self, p):
        return UseDeclaration(p[1], p[3].getstr(), lineno=p[1].lineno)

    @pg.production("top_statement : constant_declaration")
    def top_statement_constant_declaration(self, p):
        return p[0]

    @pg.production("constant_declaration : "
                   "constant_declaration , T_STRING = static_scalar")
    @pg.production("class_constant_declaration : "
                   "class_constant_declaration , T_STRING = static_scalar")
    def constant_declaration_more(self, p):
        cdecl = ConstDecl(p[2].getstr(), p[4], lineno=p[2].getsourcepos())
        p[0].append_item(cdecl)
        return p[0]

    @pg.production("constant_declaration : "
                   "T_CONST T_STRING = static_scalar")
    @pg.production("class_constant_declaration : "
                   "T_CONST T_STRING = static_scalar")
    def constant_declaration_first(self, p):
        cdecl = ConstDecl(p[1].getstr(), p[3], lineno=p[1].getsourcepos())
        return Block([cdecl])

    @pg.production("inner_statement_list : "
                   "inner_statement_list inner_statement")
    def inner_statement_list_inner_statement_list_inner_statement(self, p):
        if p[1] is not None:
            p[0].append_item(p[1])
        return p[0]

    @pg.production("inner_statement_list : empty")
    def inner_statement_list_empty(self, p):
        return Block()

    @pg.production("inner_statement : statement")
    def inner_statement_statement(self, p):
        return p[0]

    @pg.production("inner_statement : function_declaration_statement")
    def inner_statement_function_declaration_statement(self, p):
        return p[0]

    @pg.production("inner_statement : class_declaration_statement")
    def inner_statement_class_declaration_statement(self, p):
        return p[0]

    @pg.production("statement : unticked_statement")
    def statement(self, p):
        return p[0]

    @pg.production("statement : T_STRING :")
    def label_statement(self, p):
        return GotoLabel(p[0].getstr(), p[0].getsourcepos())

    @pg.production("statement : B_LITERAL_BLOCK")
    def statement_b_literal_block(self, p):
        return LiteralBlock(p[0].getstr(), p[0].getsourcepos())

    @pg.production("unticked_statement : expr ;")
    def unticked_statement_expr(self, p):
        return Stmt(p[0], lineno=p[0].lineno)

    @pg.production("unticked_statement : { inner_statement_list }")
    def unticked_statement_inner_statement_list(self, p):
        return p[1]

    @pg.production("unticked_statement : T_UNSET "
                   "( unset_variables ) ;")
    def unticked_statement_t_unset_variables(self, p):
        return Unset(p[2].getstmtlist(), lineno=p[0].getsourcepos())

    @pg.production("unticked_statement : T_TRY { inner_statement_list }"
    " T_CATCH ( fully_qualified_class_name T_VARIABLE ) "
    "{ inner_statement_list } "
    "additional_catches")
    def unticked_statement_t_try(self, p):
        cstr = p[6]
        assert isinstance(cstr, NameBase)
        additional_catches = p[12]
        assert isinstance(additional_catches, Block)
        catches = additional_catches.getstmtlist()
        catches = [CatchBlock(cstr.getstr(), p[7].getstr()[1:], p[10],
                              lineno=p[4].getsourcepos())] + catches
        return TryBlock(p[2], catches, lineno=p[0].getsourcepos())

    @pg.production("additional_catches : non_empty_additional_catches")
    def non_empty_additional_catches(self, p):
        return p[0]

    @pg.production("additional_catches : empty")
    def empty_additional_catches(self, p):
        return Block()

    @pg.production("non_empty_additional_catches : additional_catch")
    def single_additional_catch(self, p):
        return Block([p[0]])

    @pg.production("non_empty_additional_catches : "
                   "non_empty_additional_catches additional_catch")
    def multiple_additional_catches(self, p):
        p[0].append_item(p[1])
        return p[0]

    @pg.production("additional_catch : T_CATCH "
                   "( fully_qualified_class_name T_VARIABLE ) "
                   "{ inner_statement_list }")
    def additional_catch_def(self, p):
        fqcn = p[2]
        assert isinstance(fqcn, NameBase)
        return CatchBlock(fqcn.getstr(), p[3].getstr()[1:], p[6],
                          lineno=p[0].getsourcepos())

    @pg.production("unticked_statement : T_THROW expr ;")
    def unticked_statement_t_throw(self, p):
        return Throw(p[1])

    @pg.production("unset_variables : unset_variables , unset_variable")
    def unset_vars_unset_vars_unset_var(self, p):
        p[0].append_item(p[2])
        return p[0]

    @pg.production("unset_variables : unset_variable")
    def unset_vars_unset_var(self, p):
        return Block([p[0]])

    @pg.production("unset_variable : variable")
    def unset_var_var(self, p):
        return p[0]

    @pg.production("unticked_statement : ;")
    def unticked_statement_empty(self, p):
        return None

    @pg.production("expr : r_variable")
    def expr_expr_r_variable(self, p):
        return p[0]

    @pg.production("expr : expr_without_variable")
    def expr_expr_without_variable(self, p):
        return p[0]

    @pg.production("expr_without_variable : scalar")
    def expr_expr_without_variable_scalar(self, p):
        return p[0]

    @pg.production("backticks_expr : ` encaps_list `")
    def backticks_expr_encaps_list(self, p):
        lst = p[1]
        l = []
        if isinstance(lst, LinkedList):
            lst.flatten(l)
        else:
            l.append(p[1])
        return DoubleQuotedStr(l, lineno=p[0].getsourcepos())

    @pg.production("backticks_expr : ` T_ENCAPSED_AND_WHITESPACE `")
    def backticks_expr_t_encapsed(self, p):
        return ConstantStr(p[1].getstr(), lineno=p[1].getsourcepos())

    @pg.production("expr_without_variable : backticks_expr")
    def expr_expr_without_variable_backticks(self, p):
        return BackTick(p[0], lineno=p[0].lineno)

    @pg.production("expr_without_variable : variable = expr")
    def expr_without_variable_variable_eq_expr(self, p):
        return Assignment(p[0], p[2], lineno=p[0].lineno)

    @pg.production("expr_without_variable : rw_variable T_INC")
    @pg.production("expr_without_variable : rw_variable T_DEC")
    def expr_without_variable_variable_rw_var_t_inc_dec(self, p):
        return SuffixOp(p[1].getstr(), p[0], lineno=p[1].getsourcepos())

    @pg.production("expr_without_variable : T_INC rw_variable")
    @pg.production("expr_without_variable : T_DEC rw_variable")
    def expr_without_variable_variable_t_inc_dec_rw_var(self, p):
        return PrefixOp(p[0].getstr(), p[1], lineno=p[0].getsourcepos())

    @pg.production("expr_without_variable : expr + expr")
    @pg.production("expr_without_variable : expr - expr")
    @pg.production("expr_without_variable : expr * expr")
    @pg.production("expr_without_variable : expr / expr")
    @pg.production("expr_without_variable : expr > expr")
    @pg.production("expr_without_variable : expr < expr")
    @pg.production("expr_without_variable : expr . expr")
    @pg.production("expr_without_variable : expr | expr")
    @pg.production("expr_without_variable : expr % expr")
    @pg.production("expr_without_variable : expr & expr")
    @pg.production("expr_without_variable : expr ^ expr")
    @pg.production("expr_without_variable : expr T_LOGICAL_XOR expr")
    @pg.production("expr_without_variable : expr T_IS_EQUAL expr")
    @pg.production("expr_without_variable : expr T_IS_NOT_EQUAL expr")
    @pg.production("expr_without_variable : expr T_IS_IDENTICAL expr")
    @pg.production("expr_without_variable : expr T_IS_NOT_IDENTICAL expr")
    @pg.production("expr_without_variable : expr T_SL expr")
    @pg.production("expr_without_variable : expr T_SR expr")
    @pg.production("expr_without_variable : expr T_IS_GREATER_OR_EQUAL expr")
    @pg.production("expr_without_variable : expr T_IS_SMALLER_OR_EQUAL expr")
    def expr_oper_expr(self, p):
        return BinOp(p[1].getstr(), p[0], p[2], lineno=p[1].getsourcepos())

    @pg.production("expr_without_variable : "
                   "expr T_INSTANCEOF class_name_reference")
    def expr_oper_expr_instanceof(self, p):
        right = p[2]
        return InstanceOf(p[0],
            GetClass(right, lineno=p[2].lineno, complain=False),
                          lineno=p[1].getsourcepos())

    @pg.production("expr_without_variable : expr T_BOOLEAN_OR expr")
    def expr_or_expr(self, p):
        return Or(p[0], p[2], lineno=p[1].getsourcepos())

    @pg.production("expr_without_variable : expr T_BOOLEAN_AND expr")
    def expr_and_expr(self, p):
        return And(p[0], p[2], lineno=p[1].getsourcepos())

    @pg.production("expr_without_variable : expr T_LOGICAL_OR expr")
    def expr_logical_or_expr(self, p):
        return Or(p[0], p[2], lineno=p[1].getsourcepos())

    @pg.production("expr_without_variable : expr T_LOGICAL_AND expr")
    def expr_logical_and_expr(self, p):
        return And(p[0], p[2], lineno=p[1].getsourcepos())

    @pg.production("expr_without_variable : expr T_MINUS_EQUAL expr")
    @pg.production("expr_without_variable : expr T_PLUS_EQUAL expr")
    @pg.production("expr_without_variable : expr T_MUL_EQUAL expr")
    @pg.production("expr_without_variable : expr T_DIV_EQUAL expr")
    @pg.production("expr_without_variable : expr T_SR_EQUAL expr")
    @pg.production("expr_without_variable : expr T_SL_EQUAL expr")
    @pg.production("expr_without_variable : expr T_CONCAT_EQUAL expr")
    @pg.production("expr_without_variable : expr T_MOD_EQUAL expr")
    @pg.production("expr_without_variable : expr T_AND_EQUAL expr")
    @pg.production("expr_without_variable : expr T_OR_EQUAL expr")
    @pg.production("expr_without_variable : expr T_XOR_EQUAL expr")
    def expr_inplace_op_expr(self, p):
        return InplaceOp(p[1].getstr(), p[0], p[2], lineno=p[1].getsourcepos())

    @pg.production("expr_without_variable : expr ? expr : expr")
    def expr_if_expr_or_expr(self, p):
        return IfExpr(p[0], p[2], p[4], lineno=p[1].getsourcepos())

    @pg.production("expr_without_variable : variable T_PLUS_EQUAL expr")
    def expr_wo_variable_variable_inplaceop_expr(self, p):
        return InplaceOp(p[1].getstr(), p[0], p[2])

    @pg.production("expr_without_variable : - expr", precedence="T_DEC")
    @pg.production("expr_without_variable : + expr", precedence="T_INC")
    def expr_h_minus_expr(self, p):
        return PrefixOp(p[0].getstr(), p[1], lineno=p[0].getsourcepos())

    @pg.production("expr_without_variable : ! expr")
    @pg.production("expr_without_variable : ~ expr")
    def expr_excl_tilde_expr(self, p):
        return PrefixOp(p[0].getstr(), p[1], lineno=p[0].getsourcepos())

    @pg.production("expr_without_variable : internal_functions_in_yacc")
    def expr_internal_functions(self, p):
        return p[0]

    @pg.production("expr_without_variable : T_INT_CAST expr")
    @pg.production("expr_without_variable : T_DOUBLE_CAST expr")
    @pg.production("expr_without_variable : T_STRING_CAST expr")
    @pg.production("expr_without_variable : T_ARRAY_CAST expr")
    @pg.production("expr_without_variable : T_OBJECT_CAST expr")
    @pg.production("expr_without_variable : T_BOOL_CAST expr")
    @pg.production("expr_without_variable : T_UNSET_CAST expr")
    def cast_expr(self, p):
        s = p[0].getstr()
        stop = len(s) - 1
        assert stop >= 1
        return Cast(s[1:stop], p[1], lineno=p[0].getsourcepos())

    @pg.production("expr_without_variable : @ expr")
    def expr_at_sign(self, p):
        return Silence(p[1], lineno=p[0].getsourcepos())

    @pg.production("expr_without_variable : parenthesis_expr")
    def expr_without_variable_parenthesis_expr(self, p):
        return p[0]

    @pg.production("expr_without_variable : T_EXIT exit_expr")
    def expr_without_variable_exit(self, p):
        return Exit(p[1], lineno=p[0].getsourcepos())

    @pg.production("parenthesis_expr : ( expr )")
    def parenthesis_expr_expr(self, p):
        return p[1]

    @pg.production("expr_without_variable : variable = & variable")
    def expr_variable_is_ref_variable(self, p):
        return RefAssignment(p[0], p[3], lineno=p[1].getsourcepos())

    @pg.production("expr_without_variable : new_expr")
    def expr_without_variable_new(self, p):
        return p[0]

    @pg.production("expr_without_variable : ( new_expr )")
    def expr_without_variable_new_with_par(self, p):
        return p[1]

    @pg.production("expr_without_variable : "
                   "( new_expr ) chaining_instance_call")
    def expr_without_variable_chaining(self, p):
        container = p[3]
        assert isinstance(container, ChainingStuff)
        res = p[1]
        for item in container.indices:
            res = GetItem(res, item, lineno=res.lineno)
        for prop in container.props:
            assert isinstance(prop, TupleWrapper)
            prop, arguments = prop.p1, prop.p2
            res = self._apply_objprop(res, prop, arguments, res.lineno)
        return res

    @pg.production("expr_without_variable : T_CLONE expr")
    def expr_without_variable_clone(self, p):
        return Clone(p[1], lineno=p[0].getsourcepos())

    @pg.production("expr_without_variable : T_LIST ( assignment_list ) = expr")
    def expr_without_variable_t_list(self, p):
        return ListAssignment(p[2], p[5])

    @pg.production("expr_without_variable : function is_reference ( "
                   "parameter_list ) lexical_vars { inner_statement_list }")
    def expr_without_variable_lambda_function(self, p):
        return LambdaDecl(p[1] is not None, p[3].getstmtlist(), p[5], p[7],
                          static=False,
                          lineno=p[0].getsourcepos())

    @pg.production("expr_without_variable : T_STATIC function is_reference ( "
                   "parameter_list ) lexical_vars { inner_statement_list }")
    def expr_without_variable_static_lambda(self, p):
        return LambdaDecl(p[2] is not None, p[4].getstmtlist(), p[6], p[8],
                          static=True,
                          lineno=p[0].getsourcepos())

    @pg.production("chaining_method_or_property : "
                "chaining_method_or_property variable_property")
    def chaining_meth(self, p):
        lst = p[0]
        assert isinstance(lst, ChainingStuff)
        lst.props.append(p[1])
        return lst

    @pg.production("chaining_method_or_property : variable_property")
    def chaining_meth_base(self, p):
        return ChainingStuff([], [p[0]])

    @pg.production("chaining_dereference : "
                   "chaining_dereference [ dim_offset ]")
    def chaining_index(self, p):
        lst = p[0]
        assert isinstance(lst, ChainingStuff)
        lst.indices.append(p[2])
        return lst

    @pg.production("chaining_dereference : [ dim_offset ]")
    def chaining_index_base(self, p):
        return ChainingStuff([p[1]], [])

    @pg.production("chaining_instance_call : "
                   "chaining_dereference chaining_method_or_property")
    def chaining_both(self, p):
        index_list = p[0]
        prop_list = p[1]
        assert isinstance(index_list, ChainingStuff)
        assert isinstance(prop_list, ChainingStuff)
        return ChainingStuff(index_list.indices, prop_list.props)

    @pg.production("chaining_instance_call : chaining_dereference")
    @pg.production("chaining_instance_call : chaining_method_or_property")
    def chaining_instance_call(self, p):
        return p[0]

    @pg.production("new_expr : T_NEW class_name_reference ctor_arguments")
    def new_expr(self, p):
        return New(p[1], p[2].getstmtlist(), lineno=p[0].getsourcepos())

    @pg.production("lexical_vars : empty")
    def lexical_vars_empty(self, p):
        return None

    @pg.production("lexical_vars : T_USE ( lexical_var_list )")
    def lexical_vars_use_lexical_var_list(self, p):
        return p[2]

    @pg.production("lexical_var_list : lexical_var")
    def lexical_var_list_lexical_var(self, p):
        return ListOfVars([p[0]])

    @pg.production("lexical_var_list : & lexical_var")
    def lexical_var_list_ref(self, p):
        return ListOfVars([Reference(p[1])])

    @pg.production("lexical_var_list : lexical_var_list , lexical_var")
    def lexical_var_list_more_vars(self, p):
        varlist = p[0]
        assert isinstance(varlist, ListOfVars)
        return ListOfVars(varlist.varlist + [p[2]])

    @pg.production("lexical_var_list : lexical_var_list , & lexical_var")
    def lexical_var_list_more_refs(self, p):
        varlist = p[0]
        assert isinstance(varlist, ListOfVars)
        return ListOfVars(varlist.varlist + [Reference(p[3])])

    @pg.production("lexical_var : T_VARIABLE")
    def lexical_var_variable(self, p):
        return NamedVariable(p[0].getstr()[1:])

    @pg.production("assignment_list : "
                   "assignment_list , assignment_list_element")
    def assignment_list_assignment_list_assignment_list_element(self, p):
        x = p[0]
        assert isinstance(x, ListOfVars)
        return ListOfVars(x.varlist + [p[2]])

    @pg.production("assignment_list : assignment_list_element")
    def assignment_list_assignment_list_element(self, p):
        return ListOfVars(p)

    @pg.production("assignment_list_element : variable")
    def assignment_list_element_variable(self, p):
        return p[0]

    @pg.production("assignment_list_element : T_LIST ( assignment_list )")
    def assignment_list_element_t_list_assignment_list(self, p):
        return p[2]

    @pg.production("assignment_list_element : empty")
    def assignment_list_element_empty(self, p):
        return None

    @pg.production("internal_functions_in_yacc : T_ISSET ( isset_variables )")
    def internal_f_isset(self, p):
        return p[2]

    @pg.production("internal_functions_in_yacc : T_EMPTY ( variable )")
    #@pg.production("internal_functions_in_yacc : "
    #               "T_EMPTY ( expr_without_variable )")
    def internal_f_empty(self, p):
        return Empty(p[2], lineno=p[0].getsourcepos())

    @pg.production("isset_variables : isset_variables , isset_variable")
    def issetvs_issetvs_issetv(self, p):
        return And(p[0], p[2], lineno=p[1].getsourcepos())

    @pg.production("isset_variables : isset_variable")
    def issetvs_issetv(self, p):
        return p[0]

    @pg.production("isset_variable : variable")
    #@pg.production("isset_variable : expr_without_variable")
    def isset_variable(self, p):
        return IsSet(p[0], lineno=p[0].lineno)

    @pg.production("expr : T_PRINT expr")
    def expr_t_print_expr(self, p):
        return Print(p[1], lineno=p[0].getsourcepos())

    # what's that?
    # we are missing
    # http://php.net/manual/en/language.types.string.php#language.types.string.parsing.complex
    #@pg.production("scalar : T_STRING_VARNAME")
    #def scalar_t_string_varname(self, p):
    #    raise NotImplementedError(p)

    @pg.production("scalar : class_constant")
    def scalar_class_constant(self, p):
        return p[0]

    @pg.production("scalar : namespace_name")
    def scalar_namespace_name(self, p):
        return NamedConstant(p[0], p[0].getsourcepos())

    @pg.production("scalar : T_NAMESPACE T_NS_SEPARATOR namespace_name")
    def scalar_namespace_sep_namespace(self, p):
        return NamedConstant(p[2].as_absolute(from_root=False),
                             p[2].getsourcepos())

    @pg.production("scalar : T_NS_SEPARATOR namespace_name")
    def scalar_sep_namespace(self, p):
        return NamedConstant(p[1].as_absolute(from_root=True),
                             p[1].getsourcepos())

    @pg.production("scalar : common_scalar")
    def scalar_common_scalar(self, p):
        return p[0]

    @pg.production("scalar : T_START_HEREDOC encaps_list T_END_HEREDOC")
    def scalar_heredoc_encaps_list(self, p):
        lst = p[1]
        l = []
        if isinstance(lst, LinkedList):
            lst.flatten(l)
        else:
            l.append(p[1])
        return DoubleQuotedStr(l, lineno=p[0].getsourcepos())

    @pg.production('scalar : " encaps_list "')
    def scalar_encaps_list(self, p):
        lst = p[1]
        l = []
        if isinstance(lst, LinkedList):
            lst.flatten(l)
        else:
            l.append(p[1])
        return DoubleQuotedStr(l, lineno=p[0].getsourcepos())

    @pg.production('encaps_list : encaps_list encaps_var')
    def encaps_list_encaps_list_encaps_var(self, p):
        return LinkedList(p[0], p[1])

    @pg.production('encaps_list : encaps_list T_ENCAPSED_AND_WHITESPACE')
    def encaps_list_encaps_list_encapsed_and_whitespace(self, p):
        v = self._parse_doublequoted(p[1].getstr(), False)
        return LinkedList(p[0], v)

    @pg.production('encaps_list : encaps_list T_DOLLAR')
    def encaps_list_encaps_list_dolar(self, p):
        return LinkedList(p[0], ConstantStr("$"))

    @pg.production('encaps_list : encaps_list T_ENCAPSED_AND_WHITESPACE T_DOLLAR')
    def encaps_list_encaps_list_encapsed_and_whitespace_dollar(self, p):
        v = self._parse_doublequoted("%s$" % p[1].getstr(), False)
        return LinkedList(p[0], v)

    @pg.production('encaps_list : encaps_list T_CONSTANT_ENCAPSED_STRING')
    def encaps_list_encaps_list_encapsed_and_t_constant_encapsed(self, p):
        v = self._parse_doublequoted(p[1].getstr(), False)
        return LinkedList(p[0], v)

    @pg.production('encaps_list : encaps_var')
    def encaps_list_encaps_var(self, p):
        return p[0]

    @pg.production('encaps_list : T_ENCAPSED_AND_WHITESPACE encaps_var')
    def encaps_list_encaps_list_encapsed_and_whitespce_encaps_var(self, p):
        v = self._parse_doublequoted(p[0].getstr(), p[0].getsourcepos())
        return LinkedList(v, p[1])

    @pg.production('encaps_list : T_STRING encaps_var')
    def encaps_list_encaps_list_string(self, p):
        v = self._parse_doublequoted(p[0].getstr(), False)
        return LinkedList(v, p[1])

    @pg.production('encaps_list : T_CONSTANT_ENCAPSED_STRING encaps_var')
    def encaps_list_encaps_list_encapsed_and_t_constant_encapsed_encaps_var(self, p):
        v = self._parse_doublequoted(p[0].getstr(), False)
        return LinkedList(v, p[1])

    @pg.production('encaps_var : T_VARIABLE')
    def encaps_var_variable(self, p):
        parts = p[0].getstr().split("->")

        assert len(parts) <= 2

        if len(parts) == 1:
            return NamedVariable(p[0].getstr()[1:])

        elif len(parts) == 2:
            obj, variable = parts
            return GetAttr(
                NamedVariable(obj[1:]),
                ConstantStr(variable),
                lineno=p[0].getsourcepos())

    @pg.production('encaps_var : T_VARIABLE T_OBJECT_OPERATOR T_STRING')
    def encaps_var_obj_operator(self, p):
        return GetAttr(NamedVariable(p[0].getstr()[1:]),
                       ConstantStr(p[2].getstr()), lineno=p[0].getsourcepos())

    @pg.production('encaps_var : T_VARIABLE [ encaps_var_offset ]')
    def encaps_var_variable_brackets(self, p):
        return GetItem(NamedVariable(p[0].getstr()[1:]), p[2])

    @pg.production('encaps_var_offset : T_STRING')
    def encaps_var_offset_string(self, p):
        return ConstantStr(p[0].getstr())

    @pg.production('encaps_var_offset : T_NUM_STRING')
    def encaps_var_offset_numeric(self, p):
        return ConstantStr(p[0].getstr())

    @pg.production('encaps_var_offset : T_VARIABLE')
    def encaps_var_offset_variable(self, p):
        return NamedVariable(p[0].getstr()[1:])

    @pg.production('encaps_var : T_DOLLAR_OPEN_CURLY_BRACES variable }')
    def encaps_var_curly_braces(self, p):
        return p[1]

    @pg.production("common_scalar : T_LNUMBER")
    def common_scalar_lnumber(self, p):
        from hippy.objects.convert import convert_string_to_number
        lineno = p[0].getsourcepos()
        num_str = p[0].getstr()
        w_num, _ = convert_string_to_number(num_str, can_be_octal=True)
        if w_num.tp == self.space.tp_int:
            return ConstantInt(self.space.int_w(w_num), lineno=lineno)
        else:
            return ConstantFloat(self.space.float_w(w_num), lineno=lineno)

    @pg.production("common_scalar : T_DNUMBER")
    def common_scalar_dnumber(self, p):
        lineno = p[0].getsourcepos()
        return ConstantFloat(float(p[0].getstr()), lineno=lineno)

    @staticmethod
    def _parse_doublequoted(s, lineno, escape_quotes=True, skip_borders=False):
        if skip_borders:
            i = 1
            end = len(s) - 1
        else:
            i = 0
            end = len(s)
        r = []
        while i < end:
            c = s[i]
            if c == '\\':
                if i == end - 1:
                    r.append(c)
                    break
                next = s[i + 1]
                if next == 'n':
                    r.append('\n')   # \x0A
                elif next == 'r':
                    r.append('\r')   # \x0D
                elif next == 't':
                    r.append('\t')   # \x09
                elif next == 'v':
                    r.append('\v')   # \x0B
                elif next == 'e':
                    r.append('\x1B')
                elif next == 'f':
                    r.append('\f')   # \x0C
                elif next == '\\' or next == '$' or (
                        escape_quotes and next == '"'):
                    r.append(next)
                elif next == 'x' and i < end - 2 and is_hexdigit(s[i + 2]):
                    charvalue = hexdigit(s[i + 2])
                    if i < end - 3 and is_hexdigit(s[i + 3]):
                        charvalue <<= 4
                        charvalue |= hexdigit(s[i + 3])
                        i += 1
                    i += 1
                    r.append(chr(charvalue))
                elif '0' <= next <= '7':
                    charvalue = ord(next) - ord('0')
                    if i < end - 2 and '0' <= s[i + 2] <= '7':
                        charvalue <<= 3
                        charvalue |= (ord(s[i + 2]) - ord('0'))
                        i += 1
                        if i < end - 2 and '0' <= s[i + 2] <= '7':
                            charvalue <<= 3
                            charvalue &= 0xFF
                            charvalue |= (ord(s[i + 2]) - ord('0'))
                            i += 1
                    r.append(chr(charvalue))
                else:
                    r.append('\\')
                    r.append(next)
                i += 2
            else:
                r.append(c)
                i += 1
        return ConstantStr(''.join(r), lineno=lineno)

    @pg.production("common_scalar : T_CONSTANT_ENCAPSED_STRING")
    def common_scalar_constant_escaped_string(self, p):
        lineno = p[0].getsourcepos()
        s = p[0].getstr()
        #
        if s[0] == 'b':
            s = s[1:]
        last = len(s) - 1
        assert last >= 0
        got = []
        if s[0] == "'":
            assert s[last] == "'"
            i = 1
            while i < last:
                if s[i] == "\\" and (s[i + 1] == "\\" or s[i + 1] == "'"):
                    got.append(s[i + 1])
                    i += 2
                else:
                    got.append(s[i])
                    i += 1
        #
        if s[0] == '"':
            assert s[last] == '"'
            return self._parse_doublequoted(s, lineno, True, True)
        # remove "\'" and "\\"
        return ConstantStr(''.join(got), lineno=lineno)
        #

    @pg.production("common_scalar : T_LINE")
    def magic_line(self, p):
        lineno = p[0].getsourcepos()
        return ConstantInt(lineno, lineno=lineno)

    @pg.production("common_scalar : T_FILE")
    def magic_file(self, p):
        return FileMagic(lineno=p[0].getsourcepos())

    @pg.production("common_scalar : T_DIR")
    def magic_dir(self, p):
        return DirMagic(lineno=p[0].getsourcepos())

    @pg.production("common_scalar : T_CLASS_C")
    def magic_class(self, p):
        return ClassMagic(lineno=p[0].getsourcepos())

    @pg.production("common_scalar : T_METHOD_C")
    def magic_method(self, p):
        return MethodMagic(lineno=p[0].getsourcepos())

    @pg.production("common_scalar : T_FUNC_C")
    def magic_func(self, p):
        return FunctionMagic(lineno=p[0].getsourcepos())

    @pg.production("common_scalar : T_NS_C")
    def common_scalar_nsmagic(self, p):
        return NamespaceMagic(lineno=p[0].getsourcepos())

    @pg.production("common_scalar : T_START_HEREDOC "
                   "T_ENCAPSED_AND_WHITESPACE T_END_HEREDOC")
    def heredoc(self, p):
        lineno = p[1].getsourcepos()
        return self._parse_doublequoted(p[1].getstr(), lineno, False)

    @pg.production("common_scalar : T_START_HEREDOC T_END_HEREDOC")
    def heredoc_empty(self, p):
        return ConstantStr("")

    @pg.production("static_scalar : common_scalar")
    def static_scalar_common_scalar(self, p):
        return p[0]

    @pg.production("static_scalar : namespace_name")
    def static_scalar_namespace_name(self, p):
        return NamedConstant(p[0], lineno=p[0].getsourcepos())

    @pg.production("static_scalar : T_NAMESPACE T_NS_SEPARATOR namespace_name")
    def static_scalar_namespace_sep_namespace(self, p):
        return NamedConstant(p[2].as_absolute(from_root=False),
                             p[2].getsourcepos())

    @pg.production("static_scalar : T_NS_SEPARATOR namespace_name")
    def static_scalar_sep_namespace(self, p):
        return NamedConstant(p[1].as_absolute(from_root=True),
                             p[1].getsourcepos())

    @pg.production("static_scalar : static_class_constant")
    def static_scalar_static_class_constant(self, p):
        return p[0]

    @pg.production("static_scalar : - static_scalar")
    def static_scalar_minus_static_scalar(self, p):
        return p[1].uminus()

    @pg.production("static_scalar : + static_scalar")
    def static_scalar_plus_static_scalar(self, p):
        return p[1]

    @pg.production("static_class_constant : class_name "
                   "T_PAAMAYIM_NEKUDOTAYIM T_STRING")
    def static_class_constant_class_name(self, p):
        return ClassConstant(p[0], p[2].getstr())

    @pg.production('static_scalar : T_ARRAY ( static_array_pair_list )')
    def static_array(self, p):
        hash = p[2]
        hash.lineno = p[0].getsourcepos()
        return hash

    @pg.production('static_array_pair_list : empty')
    def empty_static_array_pl(self, p):
        return Hash([])

    @pg.production('static_array_pair_list : non_empty_array_pair_list '
                   'possible_comma')
    def nonempty_static_array_pl(self, p):
        return p[0]

    @pg.production("variable : "
                   "base_variable_with_function_calls T_OBJECT_OPERATOR "
                   "object_property method_or_not variable_properties")
    def variable_object_operator(self, p):
        result = p[0]
        lineno = p[1].getsourcepos()
        result = self._apply_objprop(p[0], p[2], p[3], lineno)
        for x in p[4].getstmtlist():
            assert isinstance(x, TupleWrapper)
            prop, arguments = x.p1, x.p2
            result = self._apply_objprop(result, prop, arguments, lineno)
        return result

    def _apply_objprop(self, base, prop, arguments, lineno):
        if isinstance(prop, ObjectDimList):
            result = GetAttr(base, prop.head, lineno=prop.lineno)
            for index in prop.tail:
                result = GetItem(result, index, lineno=prop.lineno)
        else:
            result = GetAttr(base, prop, lineno=prop.lineno)
        if arguments is not None:
            assert isinstance(arguments, ObjectDimList)
            result = SimpleCall(result, arguments.head.getstmtlist(),
                                result.lineno)
            for index in arguments.tail:
                result = GetItem(result, index, lineno=prop.lineno)
        return result

    @pg.production("array_function_dereference : "
                   "function_call [ dim_offset ]")
    @pg.production("array_function_dereference : "
                   "array_function_dereference [ dim_offset ]")
    def array_function_dereference_def(self, p):
        return GetItem(p[0], p[2], lineno=p[1].getsourcepos())

    @pg.production("variable : base_variable_with_function_calls")
    def variable_base_variable_with_function_calls(self, p):
        return p[0]

    @pg.production("base_variable_with_function_calls : base_variable")
    def base_variable_with_function_calls_base_variable(self, p):
        return p[0]

    @pg.production("base_variable_with_function_calls : "
                   "array_function_dereference")
    def base_variable_with_function_calls_array(self, p):
        return p[0]

    @pg.production("base_variable_with_function_calls : function_call")
    def base_variable_with_function_calls_function_call(self, p):
        return p[0]

    @pg.production("base_variable : reference_variable")
    def base_variable_reference_variable(self, p):
        return p[0]

    @pg.production("base_variable : simple_indirect_reference "
                   "reference_variable")
    def base_variable_simple_indirect_reference_variable(self, p):
        counter = p[0]
        assert isinstance(counter, ConstantInt)
        var = p[1]
        for i in range(counter.intval):
            var = Variable(var, lineno=var.lineno)
        return var

    @pg.production("base_variable : static_member")
    def base_variable_static_method(self, p):
        return p[0]

    @pg.production("reference_variable : compound_variable")
    def reference_variable_compound_variable(self, p):
        return p[0]

    @pg.production("reference_variable : "
                   "reference_variable [ dim_offset ]")
    def reference_variable_reference_variable_offset(self, p):
        return GetItem(p[0], p[2], lineno=p[1].getsourcepos())

    @pg.production("reference_variable : "
                   "reference_variable { expr }")
    def reference_variable_reference_variable_expr(self, p):
        return GetItem(p[0], p[2], lineno=p[1].getsourcepos())

    @pg.production("dim_offset : empty")
    def dim_offset_empty(self, p):
        return p[0]

    @pg.production("dim_offset : expr")
    def dim_offset_expr(self, p):
        return p[0]

    @pg.production("compound_variable : T_VARIABLE")
    def compound_variable_t_variable(self, p):
        return NamedVariable(p[0].getstr().lstrip('$'), lineno=p[0].getsourcepos())

    @pg.production("compound_variable : $ { expr }")
    def compound_variable_expr(self, p):
        expr = p[2]
        if isinstance(expr, ConstantStr):
            return NamedVariable(expr.strval, lineno=p[0].getsourcepos())
        return Variable(p[2], lineno=p[0].getsourcepos())

    @pg.production("r_variable : variable")
    def variable_r_variable(self, p):
        return p[0]

    @pg.production("rw_variable : variable")
    def variable_rw_variable(self, p):
        return p[0]

    @pg.production("w_variable : variable")
    def variable_w_variable(self, p):
        return p[0]

    @pg.production("unticked_statement : T_ECHO echo_expr_list ;")
    def unticked_statement_t_echo_expr_list(self, p):
        return Echo(p[1].getstmtlist(), lineno=p[0].getsourcepos())

    @pg.production("unticked_statement : T_SWITCH parenthesis_expr "
                   "switch_case_list")
    def unticked_statement_t_switch(self, p):
        return Switch(p[1], p[2], lineno=p[0].getsourcepos())

    @pg.production("unticked_statement : T_BREAK expr ;")
    def unticked_statement_t_break_expr(self, p):
        levels = p[1]
        if not isinstance(levels, ConstantInt):
            raise ParseError("'break' operator accepts only positive numbers",
                             p[0].getsourcepos())
        return Break(levels=levels.intval, lineno=p[0].getsourcepos())

    @pg.production("unticked_statement : T_BREAK ;")
    def unticked_statement_t_break(self, p):
        return Break(lineno=p[0].getsourcepos())

    @pg.production("unticked_statement : T_CONTINUE expr ;")
    def unticked_statement_t_continue_expr(self, p):
        levels = p[1]
        if not isinstance(levels, ConstantInt):
            raise ParseError(
                "'continue' operator accepts only positive numbers",
                p[0].getsourcepos())
        return Continue(levels=levels.intval, lineno=p[0].getsourcepos())

    @pg.production("unticked_statement : T_CONTINUE ;")
    def unticked_statement_t_continue(self, p):
        return Continue(lineno=p[0].getsourcepos())

    @pg.production("unticked_statement : T_DO statement "
                   "T_WHILE parenthesis_expr ;")
    def unticked_statement_t_do(self, p):
        return DoWhile(p[1], p[3], lineno=p[0].getsourcepos())

    @pg.production("echo_expr_list : echo_expr_list , expr")
    def echo_expr_list_echo_expr_list_expr(self, p):
        p[0].append_item(p[2])
        return p[0]

    @pg.production("echo_expr_list : expr")
    def echo_expr_list_expr(self, p):
        return Block([p[0]])

    @pg.production("unticked_statement : T_RETURN ;")
    def unticked_statement_t_return(self, p):
        return Return(None, lineno=p[0].getsourcepos())

    @pg.production("unticked_statement : T_RETURN expr_without_variable ;")
    def unticked_statement_t_return_expr_wo_variable(self, p):
        return Return(p[1], lineno=p[0].getsourcepos())

    @pg.production("unticked_statement : T_RETURN variable ;")
    def unticked_statement_t_return_variable(self, p):
        return Return(p[1], lineno=p[0].getsourcepos())

    @pg.production("unticked_statement : T_FOREACH "
                   "( variable T_AS foreach_variable "
                   "foreach_optional_arg ) foreach_statement")
    def unticked_statement_t_for_each_variable(self, p):
        if p[5] is None:
            return ForEach(p[2], p[4], p[7], lineno=p[0].getsourcepos())
        return ForEachKey(p[2], p[4], p[5], p[7], lineno=p[0].getsourcepos())

    @pg.production("unticked_statement : T_FOREACH ( expr_without_variable"
                   " T_AS foreach_variable foreach_optional_arg ) "
                   "foreach_statement")
    def unticket_statement_t_for_each_variable_expr(self, p):
        if p[5] is None:
            return ForEach(p[2], p[4], p[7], lineno=p[0].getsourcepos())
        return ForEachKey(p[2], p[4], p[5], p[7], lineno=p[0].getsourcepos())

    @pg.production("unticked_statement : T_GOTO T_STRING ;")
    def unticked_statement_t_goto(self, p):
        return Goto(p[1].getstr(), p[1].getsourcepos())

    @pg.production("foreach_variable : variable")
    def foreach_variable_variable(self, p):
        return p[0]

    @pg.production("foreach_variable : & variable")
    def foreach_variable_ref_variable(self, p):
        return Reference(p[1])

    @pg.production("foreach_optional_arg : T_DOUBLE_ARROW foreach_variable")
    def foreach_opt_arg_t_d_arrow_foreach_var(self, p):
        return p[1]

    @pg.production("foreach_optional_arg : empty")
    def foreach_opt_arg_empty(self, p):
        return None

    @pg.production("foreach_statement : statement")
    def foreach_statement_statement(self, p):
        return p[0]

    @pg.production("foreach_statement : "
                   ": inner_statement_list T_ENDFOREACH ;")
    def foreach_statement_inner_statement_list(self, p):
        return p[1]

    @pg.production("unticked_statement : T_GLOBAL global_var_list ;")
    def unticked_statement_t_global_global_var_list(self, p):
        return Global(p[1], lineno=p[0].getsourcepos())

    @pg.production("global_var_list : global_var_list , global_var")
    def global_var_list_global_var_list_global_var(self, p):
        p[0].append_item(p[2])
        return p[0]

    @pg.production("global_var_list : global_var")
    def global_var_list_global_var(self, p):
        return Block([p[0]])

    @pg.production("global_var : T_VARIABLE")
    def global_var_t_variable(self, p):
        return NamedVariable(p[0].getstr()[1:])

    @pg.production("global_var : $ r_variable")
    def global_var_dollar_r_variable(self, p):
        return Variable(p[1], p[1].getsourcepos())

    @pg.production("global_var : $ { expr }")
    def global_var_expr(self, p):
        raise ParseError("not implemented", p[0].getsourcepos())

    @pg.production("unticked_statement : T_STATIC static_var_list ;")
    def unticked_statement_t_static_static_var_list(self, p):
        return StaticDecl(p[1].getstmtlist(), lineno=p[0].getsourcepos())

    @pg.production("static_var_list : static_var_list , T_VARIABLE")
    def static_var_list_static_var_list_t_variable(self, p):
        p[0].append_item(UninitializedVariable(p[2].getstr()[1:],
                                               lineno=p[2].getsourcepos()))
        return p[0]

    @pg.production("static_var_list : static_var_list"
                   " , T_VARIABLE = static_scalar")
    def static_var_list_static_var_list_t_variable_t_eq_static_scalar(self, p):
        p[0].append_item(InitializedVariable(p[2].getstr()[1:], p[4],
                                             lineno=p[2].getsourcepos()))
        return p[0]

    @pg.production("static_var_list : T_VARIABLE")
    def static_var_list_t_variable(self, p):
        v = UninitializedVariable(p[0].getstr()[1:],
                                  lineno=p[0].getsourcepos())
        return Block([v])

    @pg.production("static_var_list : T_VARIABLE = static_scalar")
    def static_var_list_t_variable_t_eq_static_scalar(self, p):
        v = InitializedVariable(p[0].getstr()[1:], p[2],
                                lineno=p[0].getsourcepos())
        return Block([v])

    @pg.production("unticked_statement : T_IF parenthesis_expr "
                   "statement elseif_list else_single")
    def unticked_statement_if_statement_elseif_else_single(self, p):
        if_block = p[2]
        if if_block is None:
            if_block = Block([])
        return If(p[1],
                  if_block,
                  elseiflist=p[3].getstmtlist(),
                  elseclause=p[4],
                  lineno=p[0].getsourcepos())

    @pg.production("unticked_statement : T_IF parenthesis_expr : "
                   "inner_statement_list new_elseif_list "
                   "new_else_single T_ENDIF ;")
    def unticked_statement_if_inner_statement_elseif_else_single(self, p):
        return If(p[1],
                  p[3],
                  elseiflist=p[4].getstmtlist(),
                  elseclause=p[5],
                  lineno=p[0].getsourcepos())

    @pg.production("elseif_list : empty")
    def elseif_list_empty(self, p):
        return Block()

    @pg.production("elseif_list : elseif_list T_ELSEIF parenthesis_expr "
                   "statement")
    def elseif_list_elseif_list(self, p):
        _if = If(p[2], p[3], lineno=p[1].getsourcepos())
        p[0].append_item(_if)
        return p[0]

    @pg.production("new_elseif_list : new_elseif_list "
                   "T_ELSEIF parenthesis_expr : inner_statement_list")
    def new_elseif_list_new_elseif_list(self, p):
        _if = If(p[2], p[4], lineno=p[1].getsourcepos())
        p[0].append_item(_if)
        return p[0]

    @pg.production("new_elseif_list : empty")
    def new_elseif_list_empty(self, p):
        return Block()

    @pg.production("else_single : T_ELSE statement")
    def else_single_t_else_statement(self, p):
        return p[1]

    @pg.production("else_single : empty")
    def else_single_empty(self, p):
        return p[0]

    @pg.production("new_else_single : T_ELSE : inner_statement_list")
    def new_else_single_t_else(self, p):
        return p[2]

    @pg.production("new_else_single : empty")
    def new_else_single_empty(self, p):
        return p[0]

    @pg.production("unticked_statement : T_WHILE "
                   "parenthesis_expr while_statement")
    def unticked_statement_t_while(self, p):
        body = p[2]
        if body is None:
            body = Block([])
        return While(p[1], body, lineno=p[0].getsourcepos())

    @pg.production("while_statement : statement")
    def while_stmt_stmt(self, p):
        return p[0]

    @pg.production("while_statement : "
                   ": inner_statement_list T_ENDWHILE ;")
    def while_stmt_inner_stmt_list(self, p):
        return p[1]

    @pg.production("unticked_statement : T_FOR "
                   "( for_expr ; "
                   "for_expr ; for_expr ) for_statement")
    def unticked_statement_t_for(self, p):
        return For(p[2], p[4], p[6], p[8], lineno=p[0].getsourcepos())

    @pg.production("for_expr : non_empty_for_expr")
    def for_expr_non_empty_for_expr(self, p):
        return p[0]

    @pg.production("for_expr : empty")
    def for_expr_empty(self, p):
        return

    @pg.production("non_empty_for_expr : non_empty_for_expr , expr")
    def non_empty_for_expr_non_empty_for_expr_expr(self, p):
        return CommaStmt(p[0], p[2])

    @pg.production("non_empty_for_expr : expr")
    def non_empty_for_expr_expr(self, p):
        return p[0]

    @pg.production("for_statement : statement")
    def for_stmt_stmt(self, p):
        return p[0]

    @pg.production("for_statement : "
                   ": inner_statement_list T_ENDFOR ;")
    def for_stmt_inner_stmt_list(self, p):
        return p[1]

    @pg.production("simple_indirect_reference : $")
    def simple_indirect_reference(self, p):
        return ConstantInt(1)

    @pg.production("simple_indirect_reference : "
                   "simple_indirect_reference $")
    def simple_indirect_reference_simple_indirect_reference(self, p):
        counter = p[0]
        assert isinstance(counter, ConstantInt)
        return ConstantInt(counter.intval + 1)

    @pg.production("function_call : "
                   "namespace_name ( function_call_parameter_list )")
    def function_call_namespace(self, p):
        return SimpleCall(p[0], p[2].getstmtlist(), p[0].getsourcepos())

    @pg.production("function_call : "
                   "T_NAMESPACE T_NS_SEPARATOR namespace_name "
                   "( function_call_parameter_list )")
    def function_call_rel2abs(self, p):
        name = p[2].as_absolute(from_root=False)
        return SimpleCall(name, p[4].getstmtlist(), name.getsourcepos())

    @pg.production("function_call : "
                   "T_NS_SEPARATOR namespace_name "
                   "( function_call_parameter_list )")
    def function_call_absolute(self, p):
        name = p[1].as_absolute(from_root=True)
        return SimpleCall(name, p[3].getstmtlist(), name.getsourcepos())

    @pg.production("function_call : "
                   "class_name T_PAAMAYIM_NEKUDOTAYIM T_STRING "
                   "( function_call_parameter_list )")
    @pg.production("function_call : "
                   "variable_class_name T_PAAMAYIM_NEKUDOTAYIM T_STRING "
                   "( function_call_parameter_list )")
    def function_call_class_colon_str(self, p):
        return StaticMethodCall(p[0], ConstantStr(p[2].getstr()),
                                p[4].getstmtlist(),
                                lineno=p[1].getsourcepos())

    @pg.production("function_call : "
                   "class_name T_PAAMAYIM_NEKUDOTAYIM variable_without_objects"
                   " ( function_call_parameter_list )")
    @pg.production("function_call : "
                   "variable_class_name T_PAAMAYIM_NEKUDOTAYIM "
                   "variable_without_objects ( function_call_parameter_list )")
    def function_call_class_colon_var(self, p):
        return StaticMethodCall(p[0], p[2], p[4].getstmtlist(),
                                lineno=p[1].getsourcepos())

    @pg.production("function_call : "
                   "variable_without_objects "
                   "( function_call_parameter_list )")
    def function_call_variable(self, p):
        return DynamicCall(p[0], p[2].getstmtlist(),
                           lineno=p[1].getsourcepos())

    @pg.production("variable_without_objects : reference_variable")
    def variable_without_objects_reference_variable(self, p):
        return p[0]

    @pg.production("variable_without_objects : "
                   "simple_indirect_reference reference_variable")
    def variable_without_objects_simple_i_ref_reference_variable(self, p):
        counter = p[0]
        assert isinstance(counter, ConstantInt)
        var = p[1]
        for i in range(counter.intval):
            var = Variable(var, lineno=var.lineno)
        return var

    @pg.production("namespace_name : T_STRING")
    def namespace_name_t_string(self, p):
        return RelativeName([p[0].getstr()], p[0].getsourcepos())

    @pg.production("namespace_name :  namespace_name T_NS_SEPARATOR T_STRING")
    def namespace_name_namespace_name_t_ns_sep_t_string(self, p):
        ns = p[0]
        assert isinstance(ns, RelativeName)
        ns.parts.append(p[2].getstr())
        return ns

    @pg.production("function_call_parameter_list : "
                   "non_empty_function_call_parameter_list")
    def function_call_parameter_list_non_empty_function(self, p):
        return p[0]

    @pg.production("function_call_parameter_list : empty")
    def function_call_parameter_list_empty(self, p):
        return Block()

    @pg.production("non_empty_function_call_parameter_list : "
                   "expr_without_variable")
    def non_empty_function_call_parameter_list_expr_wo_variable(self, p):
        return Block([p[0]])

    @pg.production("non_empty_function_call_parameter_list : "
                   "variable")
    def non_empty_function_call_parameter_list_variable(self, p):
        return Block([p[0]])

    @pg.production("non_empty_function_call_parameter_list : "
                   "& w_variable")
    def non_empty_function_call_parameter_list_reference_variable(self, p):
        return Block([Reference(p[1], lineno=p[0].getsourcepos())])

    @pg.production("non_empty_function_call_parameter_list : "
                   "non_empty_function_call_parameter_list , variable")
    @pg.production("non_empty_function_call_parameter_list : "
                   "non_empty_function_call_parameter_list , "
                   "expr_without_variable")
    def non_empty_function_call_parameter_list_list_expr_wo_variable(self, p):
        p[0].append_item(p[2])
        return p[0]

    @pg.production("non_empty_function_call_parameter_list : "
                   "non_empty_function_call_parameter_list , "
                   "& w_variable")
    def non_empty_function_call_parameter_list_list_ref_variable(self, p):
        p[0].append_item(Reference(p[3], lineno=p[2].getsourcepos()))
        return p[0]

    @pg.production("function : T_FUNCTION")
    def function_t_function(self, p):
        return p[0]

    @pg.production("function_declaration_statement : "
                   "unticked_function_declaration_statement")
    def function_declaration_statement_unticked_f_decl_stmt(self, p):
        return p[0]

    @pg.production("unticked_function_declaration_statement : "
                   "function is_reference T_STRING ( parameter_list ) "
                   " { inner_statement_list }")
    def unticked_func_decl_stmt_f_is_ref_param_list_inner_stmt_lst(self, p):
        return FunctionDecl(p[2].getstr(), p[1] is not None,
                            p[4].getstmtlist(), p[7],
                            lineno=p[0].getsourcepos())

    @pg.production("is_reference : &")
    def is_reference_reference(self, p):
        return Reference()

    @pg.production("is_reference : empty")
    def is_reference_empty(self, p):
        return None

    @pg.production("parameter_list : non_empty_parameter_list")
    def parameter_list_non_empty_parameter_list(self, p):
        return p[0]

    @pg.production("parameter_list : empty")
    def parameter_list_empty(self, p):
        return Block()

    def _new_argument(self, opt_class_type, is_reference, t_variable,
                      static_scalar=None):
        if opt_class_type is not None:
            assert isinstance(opt_class_type, NameBase)
            typehint = opt_class_type
        else:
            typehint = None
        return Argument(t_variable.getstr()[1:],
                        defaultvalue=static_scalar,
                        is_reference=is_reference,
                        typehint=typehint,
                        lineno=t_variable.getsourcepos())

    @pg.production("non_empty_parameter_list : "
                   "optional_class_type T_VARIABLE")
    def nepl_optional_class_type_t_var(self, p):
        return Block([self._new_argument(p[0], False, p[1])])

    @pg.production("non_empty_parameter_list : "
                   "optional_class_type & T_VARIABLE")
    def nepl_optional_class_type_h_ref_t_var(self, p):
        return Block([self._new_argument(p[0], True, p[2])])

    @pg.production("non_empty_parameter_list : "
                   "optional_class_type & T_VARIABLE = static_scalar")
    def nepl_optional_class_type_h_ref_t_var_static_scalar(self, p):
        return Block([self._new_argument(p[0], True, p[2], p[4])])

    @pg.production("non_empty_parameter_list : "
                   "optional_class_type T_VARIABLE = static_scalar")
    def nepl_optional_class_type_t_var_static_scalar(self, p):
        return Block([self._new_argument(p[0], False, p[1], p[3])])

    @pg.production("non_empty_parameter_list : "
                   "non_empty_parameter_list , "
                   "optional_class_type T_VARIABLE")
    def nepl_nepl_optional_class_type_t_var(self, p):
        p[0].append_item(self._new_argument(p[2], False, p[3]))
        return p[0]

    @pg.production("non_empty_parameter_list : "
                   "non_empty_parameter_list , "
                   "optional_class_type & T_VARIABLE")
    def nepl_nepl_optional_class_type_h_ref_t_var(self, p):
        p[0].append_item(self._new_argument(p[2], True, p[4]))
        return p[0]

    @pg.production("non_empty_parameter_list : "
                   "non_empty_parameter_list , "
                   "optional_class_type & T_VARIABLE = static_scalar")
    def nepl_nepl_optional_class_type_h_ref_t_var_static_scalar(self, p):
        p[0].append_item(self._new_argument(p[2], True, p[4], p[6]))
        return p[0]

    @pg.production("non_empty_parameter_list : "
                   "non_empty_parameter_list , optional_class_type"
                   " T_VARIABLE = static_scalar")
    def nepl_nepl_optional_class_type_t_var_static_scalar(self, p):
        p[0].append_item(self._new_argument(p[2], False, p[3], p[5]))
        return p[0]

    @pg.production("optional_class_type : fully_qualified_class_name")
    def optional_class_type_fqcn(self, p):
        return p[0]

    @pg.production("optional_class_type : T_ARRAY")
    def optional_class_type_t_array(self, p):
        return AbsoluteName(["array"])

    @pg.production("optional_class_type : empty")
    def optional_class_type_empty(self, p):
        return None

    @pg.production("fully_qualified_class_name : namespace_name")
    def fqcn_namespace_name(self, p):
        return p[0]

    @pg.production("fully_qualified_class_name : "
                   "T_NAMESPACE T_NS_SEPARATOR namespace_name")
    def fqcn_t_namespace_t_ns_sep_namespace_name(self, p):
        return p[2].as_absolute(from_root=False)

    @pg.production("fully_qualified_class_name : "
                   "T_NS_SEPARATOR namespace_name")
    def fqcn_t_ns_sep_namespace_name(self, p):
        return p[1].as_absolute()

    @pg.production("expr_without_variable : combined_scalar")
    def expr_expr_without_variable_array(self, p):
        return p[0]

    @pg.production("combined_scalar : T_ARRAY ( array_pair_list )")
    def combined_scalar_t_array_array_pair_list(self, p):
        hash = p[2]
        hash.lineno = p[0].getsourcepos()
        return hash

    @pg.production("combined_scalar : [ array_pair_list ]")
    def combined_scalar_square_bracket_array_pair_list(self, p):
        hash = p[1]
        hash.lineno = p[0].getsourcepos()
        return hash

    @pg.production("array_pair_list : "
                   "non_empty_array_pair_list possible_comma")
    def array_pair_list_non_empty(self, p):
        return p[0]

    @pg.production("array_pair_list : empty")
    def array_pair_list_empty(self, p):
        return Hash([])

    @pg.production("non_empty_array_pair_list : "
                   "non_empty_array_pair_list , expr T_DOUBLE_ARROW expr")
    def non_empty_array_pair_list_list_expr_da_expr(self, p):
        hash = p[0]
        assert isinstance(hash, Hash)
        hash.initializers.append((p[2], p[4]))
        return hash

    @pg.production("non_empty_array_pair_list : "
                   "expr T_DOUBLE_ARROW expr")
    def non_empty_array_pair_list_expr_da_expr(self, p):
        return Hash([(p[0], p[2])])

    @pg.production("non_empty_array_pair_list : "
                   "non_empty_array_pair_list , expr")
    def non_empty_array_pair_list_list_expr(self, p):
        hash = p[0]
        assert isinstance(hash, Hash)
        hash.initializers.append((None, p[2]))
        return hash

    @pg.production("non_empty_array_pair_list : expr")
    def non_empty_array_pair_list_expr(self, p):
        return Hash([(None, p[0])])

    @pg.production("non_empty_array_pair_list : "
                   "non_empty_array_pair_list , expr T_DOUBLE_ARROW "
                   "& w_variable")
    def non_empty_array_pair_list_list_expr_da_ref_w_variable(self, p):
        hash = p[0]
        assert isinstance(hash, Hash)
        ref = Reference(p[5], lineno=p[0].getsourcepos())
        hash.initializers.append((p[2], ref))
        return hash

    @pg.production("non_empty_array_pair_list : "
                   "non_empty_array_pair_list , & w_variable")
    def non_empty_array_pair_list_list_ref_w_variable(self, p):
        hash = p[0]
        assert isinstance(hash, Hash)
        ref = Reference(p[3], lineno=p[0].lineno)
        hash.initializers.append((None, ref))
        return hash

    @pg.production("non_empty_array_pair_list : "
                   "expr T_DOUBLE_ARROW & w_variable")
    def non_empty_array_pair_list_expr_da_ref_w_variable(self, p):
        return Hash([(p[0], Reference(p[3], lineno=p[1].getsourcepos()))])

    @pg.production("non_empty_array_pair_list : & w_variable")
    def non_empty_array_pair_list_ref_w_variable(self, p):
        return Hash([(None, Reference(p[1], lineno=p[0].getsourcepos()))])

    @pg.production("possible_comma : empty")
    @pg.production("possible_comma : ,")
    def possible_comma_empty(self, p):
        return None

    @pg.production("empty :")
    def empty(self, p):
        return None

    @pg.production("class_declaration_statement : "
                   "unticked_class_declaration_statement")
    def class_declaration_statement_unticked_cls_decl_stmt(self, p):
        return p[0]

    @pg.production("unticked_class_declaration_statement : "
                   "class_entry_type T_STRING extends_from "
                   "implements_list { class_statement_list }")
    def unticked_cls_decl_stmt_class_entry_type(self, p):
        c = p[0]
        assert isinstance(c, ConstantInt)
        x = p[2]
        if x is None:
            extends = None
        else:
            assert isinstance(x, NameBase)
            extends = x
        lineno = p[1].getsourcepos()
        from hippy.module.reflections import ReflectionData
        reflection = ReflectionData(
            filename=self.filename,
            startline=lineno, endline=p[-1].getsourcepos() + 1)
        return ClassBlock(p[1].getstr(), c.intval, extends=extends,
                         baseinterfaces=p[3].getstmtlist(), body=p[5],
                         lineno=p[1].getsourcepos(), reflection=reflection)

    @pg.production("unticked_class_declaration_statement : "
                   "interface_entry T_STRING interface_extends_list "
                   "{ class_statement_list }")
    def unticked_cls_decl_stmt_interface_entry(self, p):
        return ClassBlock(p[1].getstr(),
                         consts.ACC_INTERFACE | consts.ACC_ABSTRACT,
                         baseinterfaces=p[2].getstmtlist(), body=p[4],
                         lineno=p[1].getsourcepos())

    @pg.production("class_entry_type : T_CLASS")
    def class_entry_type_class(self, p):
        return ConstantInt(0)

    @pg.production("class_entry_type : T_ABSTRACT T_CLASS")
    def class_entry_type_abstract_class(self, p):
        return ConstantInt(consts.ACC_ABSTRACT)

    @pg.production("class_entry_type : T_FINAL T_CLASS")
    def class_entry_type_final_class(self, p):
        return ConstantInt(consts.ACC_FINAL)

    @pg.production("interface_entry : T_INTERFACE")
    def interface_entry(self, p):
        return None

    @pg.production("extends_from : ")
    def extends_from_empty(self, p):
        return None

    @pg.production("extends_from : T_EXTENDS fully_qualified_class_name")
    def extends_from_class(self, p):
        return p[1]

    @pg.production("interface_extends_list : ")
    def interface_extends_list_empty(self, p):
        return Block()

    @pg.production("interface_extends_list : T_EXTENDS interface_list")
    def interface_extends_list_interface_list(self, p):
        return p[1]

    @pg.production("interface_list : fully_qualified_class_name")
    def interface_list_class_name(self, p):
        return Block([p[0]])

    @pg.production("interface_list : "
                   "interface_list , fully_qualified_class_name")
    def interface_list_more(self, p):
        p[0].append_item(p[2])
        return p[0]

    @pg.production("class_statement_list : "
                   "class_statement_list class_statement")
    def class_statement_list_class_statement(self, p):
        p[0].extend_items(p[1])
        return p[0]

    @pg.production("class_statement_list :")
    def class_statement_list_empty(self, p):
        return Block()

    @pg.production("class_statement : "
                   "variable_modifiers class_variable_declaration ;")
    def class_statement_variable_decl(self, p):
        lst = p[1].getstmtlist()
        access_flags = p[0]
        assert isinstance(access_flags, ConstantInt)
        for initializer in lst:
            initializer.set_access_flags(access_flags.intval)
        return Block(lst)

    @pg.production("class_statement : class_constant_declaration ;")
    def class_statement_const_decl(self, p):
        return p[0]   # Block list of ConstDecl

    @pg.production("class_statement : "
                   "method_modifiers function is_reference T_STRING "
                   "( parameter_list ) method_body")
    def class_statement_method(self, p):
        lineno = p[3].getsourcepos()
        decl = MethodBlock(p[3].getstr(), p[2] is not None,
                           p[5].getstmtlist(), p[7], p[0], lineno=lineno)
        return Block([decl])

    @pg.production("method_body : ;")   # abstract method
    def method_body_abstract(self, p):
        return None

    @pg.production("method_body : { inner_statement_list }")
    def method_body_stmts(self, p):
        return p[1]

    @pg.production("variable_modifiers : non_empty_member_modifiers")
    def variable_modifiers_non_empty_member_modifiers(self, p):
        return p[0]

    @pg.production("variable_modifiers : T_VAR")
    def variable_modifiers_var(self, p):
        return ConstantInt(consts.ACC_PUBLIC,
                           lineno=p[0].getsourcepos())

    @pg.production("method_modifiers : ")   # empty
    def method_modifiers_empty(self, p):
        return ConstantInt(0)

    @pg.production("method_modifiers : non_empty_member_modifiers")
    def method_modifiers_non_empty(self, p):
        return p[0]

    @pg.production("non_empty_member_modifiers : member_modifier")
    def non_empty_member_modifiers_member_modifier(self, p):
        return p[0]

    @pg.production("non_empty_member_modifiers : "
                   "non_empty_member_modifiers member_modifier")
    def non_empty_member_modifiers_list(self, p):
        p0, p1 = p
        assert isinstance(p0, ConstantInt)
        assert isinstance(p1, ConstantInt)
        if ((p0.intval & consts.ACCMASK_VISIBILITY) != 0 and
                (p1.intval & consts.ACCMASK_VISIBILITY) != 0):
            raise ParseError("Multiple access type modifiers are "
                             "not allowed", p1.lineno)
        if p0.intval & p1.intval:
            raise ParseError("Duplicate modifiers are not allowed", p1.lineno)
        return ConstantInt(p0.intval | p1.intval, p1.lineno)

    @pg.production("member_modifier : T_PUBLIC")
    def member_modifier_public(self, p):
        return ConstantInt(consts.ACC_PUBLIC,
                           lineno=p[0].getsourcepos())

    @pg.production("member_modifier : T_PROTECTED")
    def member_modifier_protected(self, p):
        return ConstantInt(consts.ACC_PROTECTED,
                           lineno=p[0].getsourcepos())

    @pg.production("member_modifier : T_PRIVATE")
    def member_modifier_private(self, p):
        return ConstantInt(consts.ACC_PRIVATE,
                           lineno=p[0].getsourcepos())

    @pg.production("member_modifier : T_STATIC")
    def member_modifier_static(self, p):
        return ConstantInt(consts.ACC_STATIC,
                           lineno=p[0].getsourcepos())

    @pg.production("member_modifier : T_ABSTRACT")
    def member_modifier_abstract(self, p):
        return ConstantInt(consts.ACC_ABSTRACT,
                           lineno=p[0].getsourcepos())

    @pg.production("member_modifier : T_FINAL")
    def member_modifier_final(self, p):
        return ConstantInt(consts.ACC_FINAL,
                           lineno=p[0].getsourcepos())

    @pg.production("class_variable_declaration : "
                   "class_variable_declaration , T_VARIABLE")
    def class_variable_declaration_more(self, p):
        p[0].append_item(PropertyDecl(p[2].getstr()[1:], None,
                                      lineno=p[2].getsourcepos()))
        return p[0]

    @pg.production("class_variable_declaration : "
                   "class_variable_declaration , T_VARIABLE = static_scalar")
    def class_variable_declaration_more_scalar(self, p):
        p[0].append_item(PropertyDecl(p[2].getstr()[1:], p[4],
                                      lineno=p[2].getsourcepos()))
        return p[0]

    @pg.production("class_variable_declaration : T_VARIABLE")
    def class_variable_declaration_variable(self, p):
        return Block([PropertyDecl(p[0].getstr()[1:], None,
                                   lineno=p[0].getsourcepos())])

    @pg.production("class_variable_declaration : T_VARIABLE = static_scalar")
    def class_variable_declaration_variable_scalar(self, p):
        return Block([PropertyDecl(p[0].getstr()[1:], p[2],
                                   lineno=p[0].getsourcepos())])

    @pg.production("implements_list : ")
    def implements_list_empty(self, p):
        return Block()

    @pg.production("implements_list : T_IMPLEMENTS interface_list")
    def implements_list_interface_list(self, p):
        return p[1]

    @pg.production("class_name_reference : class_name")
    def class_name_reference_class_name(self, p):
        return p[0]

    @pg.production("class_name_reference : dynamic_class_name_reference")
    def class_name_reference_dynamic(self, p):
        return p[0]

    @pg.production("dynamic_class_name_reference : base_variable")
    def dynamic_class_name_reference_base_variable(self, p):
        return p[0]

    @pg.production("dynamic_class_name_reference : "
                   "base_variable T_OBJECT_OPERATOR object_property "
                   "dynamic_class_name_variable_properties")
    def dynamic_class_name_reference(self, p):
        base = p[0]
        lineno = p[1].getsourcepos()
        odl = p[2]
        assert isinstance(odl, ObjectDimList)
        result = GetAttr(base, odl.head, lineno=lineno)
        for index in odl.tail:
            result = GetItem(result, index, lineno=lineno)
        for odl in p[3].getstmtlist():
            assert isinstance(odl, ObjectDimList)
            result = GetAttr(result, odl.head, lineno=lineno)
            for index in odl.tail:
                result = GetItem(result, index, lineno=lineno)
        return result

    @pg.production("dynamic_class_name_variable_properties : empty")
    def empty_dcnvp(self, p):
        return Block()

    @pg.production("dynamic_class_name_variable_properties : "
                   "dynamic_class_name_variable_properties "
                   "dynamic_class_name_variable_property")
    def multiple_dcnvp(self, p):
        block = p[0]
        assert isinstance(block, Block)
        block.append_item(p[1])
        return block

    @pg.production("dynamic_class_name_variable_property : "
            "T_OBJECT_OPERATOR object_property")
    def dcnvp(self, p):
        return p[1]

    @pg.production("class_name : T_STATIC")
    def class_name_static(self, p):
        return Static(lineno=p[0].getsourcepos())

    @pg.production("class_name : namespace_name")
    def class_name_relative(self, p):
        return p[0]

    @pg.production("class_name : T_NAMESPACE T_NS_SEPARATOR namespace_name")
    def class_name_T_NAMESPACE(self, p):
        return p[2].as_absolute(from_root=False)

    @pg.production("class_name : T_NS_SEPARATOR namespace_name")
    def class_name_absolute(self, p):
        return p[1].as_absolute(from_root=True)

    @pg.production("ctor_arguments : ")
    def ctor_arguments_empty(self, p):
        return Block()

    @pg.production("ctor_arguments : ( function_call_parameter_list )")
    def ctor_arguments_nonempty(self, p):
        return p[1]

    @pg.production("object_property : object_dim_list")
    def object_property_object_dim_list(self, p):
        return p[0]

    @pg.production("object_property : variable_without_objects")
    def object_property_variable_without_objects(self, p):
        return p[0]

    @pg.production("object_dim_list : object_dim_list [ dim_offset ]")
    def object_dim_list_dim_offset(self, p):
        lst = p[0]
        assert isinstance(lst, ObjectDimList)
        lst.tail.append(p[2])
        return lst

    @pg.production("object_dim_list : object_dim_list { expr }")
    def object_dim_list_expr(self, p):
        raise ParseError("not implemented", p[0].getsourcepos())

    @pg.production("object_dim_list : variable_name")
    def object_dim_list_variable_name(self, p):
        return ObjectDimList(p[0], [], p[0].lineno)

    @pg.production("variable_name : T_STRING")
    def variable_name_t_string(self, p):
        return ConstantStr(p[0].getstr(), lineno=p[0].getsourcepos())

    @pg.production("variable_name : { expr }")
    def variable_name_expr(self, p):
        return p[1]

    @pg.production("method : ( function_call_parameter_list )")
    def method_params(self, p):
        return p[1]

    @pg.production("array_method_dereference : "
                   "method [ dim_offset ]")
    def array_method_dereference_base(self, p):
        return ObjectDimList(p[0], [p[2]], lineno=p[1].getsourcepos())

    @pg.production("array_method_dereference : "
                   "array_method_dereference [ dim_offset ]")
    def array_method_dereference_def(self, p):
        lst = p[0]
        assert isinstance(lst, ObjectDimList)
        lst.tail.append(p[2])
        return lst

    @pg.production("method_or_not : method")
    def method_or_not_method(self, p):
        return ObjectDimList(p[0], [], lineno=p[0].lineno)

    @pg.production("method_or_not : array_method_dereference")
    def method_or_not_indexed_method(self, p):
        return p[0]

    @pg.production("method_or_not : ")
    def method_or_not_property(self, p):
        return None

    @pg.production("variable_properties : "
                   "variable_properties variable_property")
    def variable_properties_nonempty(self, p):
        p[0].append_item(p[1])
        return p[0]

    @pg.production("variable_properties : ")   # empty
    def variable_properties_empty(self, p):
        return Block()

    @pg.production("variable_property : "
            "T_OBJECT_OPERATOR object_property method_or_not")
    def variable_property(self, p):
        return TupleWrapper(p[1], p[2])

    def _make_static_member(self, cls_name, v, lineno):
        if isinstance(v, Variable):
            return StaticMember(cls_name, v.node, lineno=lineno)
        elif isinstance(v, GetItem):
            node = v.node
            parent_node = v
            while isinstance(node, GetItem):
                parent_node = node
                node = node.node
            assert isinstance(node, Variable)
            assert isinstance(parent_node, GetItem)
            parent_node.node = StaticMember(cls_name, node.node, lineno=lineno)
            return v
        else:
            raise ParseError("Unexpected T_PAAMAYIM_NEKUDOTAYIM", lineno)

    @pg.production("static_member : "
                   "class_name T_PAAMAYIM_NEKUDOTAYIM "
                   "variable_without_objects")
    def static_member_class_name(self, p):
        return self._make_static_member(p[0], p[2], p[1].getsourcepos())

    @pg.production("static_member : "
                   "variable_class_name T_PAAMAYIM_NEKUDOTAYIM "
                   "variable_without_objects")
    def static_member_variable_class_name(self, p):
        return self._make_static_member(p[0], p[2], p[1].getsourcepos())

    @pg.production("variable_class_name : reference_variable")
    def variable_class_name(self, p):
        return p[0]

    @pg.production("class_constant : "
                   "class_name T_PAAMAYIM_NEKUDOTAYIM T_STRING")
    @pg.production("class_constant : "
                   "variable_class_name T_PAAMAYIM_NEKUDOTAYIM T_STRING")
    def class_constant_name(self, p):
        return ClassConstant(p[0], p[2].getstr(), lineno=p[1].getsourcepos())

    @pg.production("switch_case_list : { case_list }")
    @pg.production("switch_case_list : : case_list T_ENDSWITCH ;")
    def switch_case_list_1(self, p):
        return p[1]

    @pg.production("switch_case_list : { ; case_list }")
    @pg.production("switch_case_list : : ; case_list T_ENDSWITCH ;")
    def switch_case_list_2(self, p):
        return p[2]

    @pg.production("case_list : ")   # empty
    def case_list_empty(self, p):
        return Block()

    @pg.production("case_list : "
                   "case_list T_CASE expr case_separator inner_statement_list")
    def case_list_case(self, p):
        lst = p[0]
        lst.append_item(Case(p[2], p[4], lineno=p[1].getsourcepos()))
        return lst

    @pg.production("case_list : "
                   "case_list T_DEFAULT case_separator inner_statement_list")
    def case_list_default(self, p):
        lst = p[0]
        lst.append_item(Case(None, p[3], lineno=p[1].getsourcepos()))
        return lst

    @pg.production("case_separator : :")
    @pg.production("case_separator : ;")
    def case_separator(self, p):
        return None

    @pg.production("exit_expr : ")   # empty
    @pg.production("exit_expr : ( )")
    def exit_expr_empty(self, p):
        return ConstantInt(0)

    @pg.production("exit_expr : parenthesis_expr")
    def exit_expr_expr(self, p):
        return p[0]

    @pg.production("internal_functions_in_yacc : T_REQUIRE expr")
    def require_statement(self, p):
        return Require(p[1], lineno=p[1].lineno)

    @pg.production("internal_functions_in_yacc : T_REQUIRE_ONCE expr")
    def require_once_statement(self, p):
        return RequireOnce(p[1], lineno=p[1].lineno)

    @pg.production("internal_functions_in_yacc : T_INCLUDE expr")
    def include_statement(self, p):
        return Include(p[1], lineno=p[1].lineno)

    @pg.production("internal_functions_in_yacc : T_INCLUDE_ONCE expr")
    def include_once(self, p):
        return IncludeOnce(p[1], lineno=p[1].lineno)

    @pg.production("internal_functions_in_yacc : T_EVAL parenthesis_expr")
    def eval(self, p):
        return Eval(p[1], lineno=p[1].lineno)

    @pg.error
    def error_handler(self, token):
        s = token.getstr()
        pos = s.find('\n')
        if pos >= 0:
            s = s[:pos]
        if len(s) > 20:
            s = s[:17] + "..."
        if token.name == s:
            message = ("syntax error, unexpected \'%s\' in %s" %
                          (s, self.filename))
        else:
            message = ("syntax error, unexpected \'%s\' (%s) in %s" %
                          (s, token.name, self.filename))
        raise ParseError(message, token.getsourcepos())


    parser = pg.build()


@specialize.memo()
def get_lexer(are_we_translated):
    return Lexer()


def parse(space, _source, startlineno, filename):
    lx = get_lexer(we_are_translated())
    lx.input(_source + ';', 0, startlineno)
    parser = SourceParser(space, lx, filename)
    return parser.parse()
