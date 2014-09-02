from pytest import raises
from hippy import sourceparser
from hippy.ast import (
    Block, Stmt, Assignment, RefAssignment, ConstantInt, Variable, Echo,
    Return, If, PrefixOp, SuffixOp, While, For, ConstantStr, SimpleCall,
    DynamicCall, FunctionDecl, Argument, BinOp, ConstantFloat, GetItem, And,
    Or, InplaceOp, Global, DoubleQuotedStr, NamedConstant, DoWhile, Reference,
    Hash, ForEach, ForEachKey, Cast, StaticDecl, InitializedVariable,
    UninitializedVariable, Break, Continue, Unset, Print, ConstDecl,
    ClassBlock, New, GetAttr, StaticMember, StaticMethodCall, ClassConstant,
    Clone, IsSet, Empty, Silence, Switch, Case, Exit, GotoLabel, Goto,
    PropertyDecl, ListOfVars, ListAssignment, TryBlock, CatchBlock, Throw,
    LambdaDecl, MethodBlock, NamedVariable, GetClass, ParseError, InstanceOf,
    BeginNamespace, RelativeName, AbsoluteName, Rel2AbsName,
    Use, UseDeclaration)

from hippy import consts
from hippy.objspace import getspace


def parse(source):
    return sourceparser.parse(getspace(), source, 0, '<input>')

def parse_doublequoted(src):
    return parse('"' + src + '"').stmts[0].expr

class TestParseDoubleQuote(object):
    def test_basic(self):
        assert parse_doublequoted("xyz") == ConstantStr("xyz")
        assert parse_doublequoted("\\n") == ConstantStr("\n")
        assert parse_doublequoted("\\\\") == ConstantStr("\\")
        assert parse_doublequoted("$") == ConstantStr("$")
        assert parse_doublequoted("$'") == ConstantStr("$'")
        assert parse_doublequoted("$[") == ConstantStr("$[")

    def test_variable(self):
        expected = DoubleQuotedStr([ConstantStr("a"),
                                   NamedVariable("xyz"),
                                   ConstantStr(" b")])
        assert parse_doublequoted("a$xyz b") == expected

    def test_variable_quoted(self):
        expected = DoubleQuotedStr([ConstantStr("a"),
                                    NamedVariable("xyz"),
                                    ConstantStr("b")])
        assert parse_doublequoted("a{$xyz}b") == expected

    def test_brackets(self):
        expected = DoubleQuotedStr([ConstantStr("a"),
                                    GetItem(NamedVariable("x"),
                                            ConstantInt(3))])
        assert parse_doublequoted("a{$x[3]}") == expected

    def test_interpolated_str_re(self):
        r = parse_doublequoted("^(?:$langtag|$privateUse)$")
        expected = DoubleQuotedStr([ConstantStr("^(?:"),
                                    NamedVariable("langtag"),
                                    ConstantStr("|"),
                                    NamedVariable("privateUse"),
                                    ConstantStr(")$")])
        assert r == expected

    def test_obj_access(self):
        assert parse_doublequoted("$this->aa") == DoubleQuotedStr([
            GetAttr(NamedVariable("this"), ConstantStr("aa"))])

    def test_strange_case(self):
        parse_doublequoted("""/(?:^|$space)({$attribFirst}{$attrib}*)
				  ($space*=$space*
					(?:
					 # The attribute value: quoted or alone
					  \\"([^<\\"]*)\\"
					 | '([^<']*)'
					 |  ([a-zA-Z0-9!#$%&()*,\\\\-.\\\\/:;<>?@[\\\\]^_`{|}~]+)
					 |  (\\#[0-9a-fA-F]+) # Technically wrong, but lots of
										 # colors are specified like this.
										 # We'll be normalizing it.
					)
				)?(?=$space|\\$)/sx""")
                # assert did not explode

    def test_parse_varia(self):
        assert parse_doublequoted("%.${acc}f") == DoubleQuotedStr([
            ConstantStr("%."), NamedVariable("acc"), ConstantStr("f")
        ])

    def test_parse_index(self):
        assert parse_doublequoted("$foo[id]") == DoubleQuotedStr([
            GetItem(NamedVariable('foo'), ConstantStr('id'))])


class TestParser(object):

    def test_parse_newlines(self):
        ret = parse("\n\n\n\n1;")
        assert ret == Block([Stmt(ConstantInt(1, lineno=4), lineno=4)])

        ret = parse("\n\n\n\n$v;")
        assert ret == Block([Stmt(NamedVariable('v', lineno=4), lineno=4)])

    def test_top_statement(self):
        r = parse("1;")
        assert r == Block([Stmt(ConstantInt(1))])
        r = parse("{1;}")
        assert r == Block([Block([Stmt(ConstantInt(1))])])

    def test_automatic_semicolon_at_the_end(self):
        r = parse("1")
        assert r == Block([Stmt(ConstantInt(1))])
        r = parse("{1;}")
        assert r == Block([Block([Stmt(ConstantInt(1))])])

    def test_assign(self):
        r = parse("$x = 3;")
        assert r == Block([Stmt(
            Assignment(NamedVariable('x'), ConstantInt(3)))])

    def test_refassign(self):
        r = parse("$x =& $y;")
        assert r == Block([Stmt(
            RefAssignment(NamedVariable('x'), NamedVariable('y')))])

    def test_assign_variation1(self):
        r = parse("$null = 3;")
        assert r == Block([Stmt(
            Assignment(NamedVariable('null'), ConstantInt(3)))])

        r = parse("$false = 3;")
        assert r == Block([Stmt(
            Assignment(NamedVariable('false'), ConstantInt(3)))])

        r = parse("$true = 3;")
        assert r == Block([Stmt(
            Assignment(NamedVariable('true'), ConstantInt(3)))])

        r = parse("${'true'} = 3;")
        assert r == Block([Stmt(
            Assignment(NamedVariable('true'), ConstantInt(3)))])

    def test_assign_error(self):
        with raises(ParseError):
            parse("$x$ = 3;")

    def test_add(self):
        r = parse("3 + 1;")
        assert r == Block([Stmt(BinOp("+", ConstantInt(3), ConstantInt(1)))])

    def test_add2(self):
        r = parse("3 + 1 + 5;")
        assert r == Block([Stmt(
            BinOp("+", BinOp("+", ConstantInt(3), ConstantInt(1)),
                  ConstantInt(5)))])

    def test_minus2(self):
        r = parse("1 - 2 - 3;")
        assert r == Block([Stmt(
            BinOp("-", BinOp("-", ConstantInt(1), ConstantInt(2)),
                  ConstantInt(3)))])

    def test_add_minus(self):
        r = parse("3 - 1 + 5;")
        assert r == Block([Stmt(
            BinOp("+", BinOp("-", ConstantInt(3), ConstantInt(1)),
                  ConstantInt(5)))])

    def test_operation_precedence(self):
        r = parse("5 + 1 * 3;")
        assert r == Block([Stmt(
            BinOp("+", ConstantInt(5),
                  BinOp("*", ConstantInt(1), ConstantInt(3))))])
        r = parse("5 - 1 * 3;")
        assert r == Block([Stmt(
            BinOp("-", ConstantInt(5),
                  BinOp("*", ConstantInt(1), ConstantInt(3))))])
        r = parse("5 + 1 / 3;")
        assert r == Block([Stmt(
            BinOp("+", ConstantInt(5),
                  BinOp("/", ConstantInt(1), ConstantInt(3))))])
        r = parse("5 - 1 / 3;")
        assert r == Block([Stmt(
            BinOp("-", ConstantInt(5),
                  BinOp("/", ConstantInt(1), ConstantInt(3))))])
        r = parse("(5 + 1) * 3;")
        assert r == Block([Stmt(
            BinOp("*", BinOp("+", ConstantInt(5), ConstantInt(1)),
                  ConstantInt(3)))])
        r = parse("(5 + 1) / 3;")
        assert r == Block([Stmt(
            BinOp("/", BinOp("+", ConstantInt(5), ConstantInt(1)),
                  ConstantInt(3)))])
        r = parse("5 * (1 + 3);")
        assert r == Block([Stmt(
            BinOp("*", ConstantInt(5),
                  BinOp("+", ConstantInt(1), ConstantInt(3))))])
        r = parse("5 / (1 + 3);")
        assert r == Block([Stmt(
            BinOp("/", ConstantInt(5),
                  BinOp("+", ConstantInt(1), ConstantInt(3))))])
        r = parse("5 * 1 + 3;")
        assert r == Block([Stmt(
            BinOp("+", BinOp("*", ConstantInt(5), ConstantInt(1)),
                  ConstantInt(3)))])
        r = parse("5 / 1 + 3;")
        assert r == Block([Stmt(
            BinOp("+", BinOp("/", ConstantInt(5), ConstantInt(1)),
                  ConstantInt(3)))])
        r = parse("5 + 1 / 3;")
        assert r == Block([Stmt(
            BinOp("+", ConstantInt(5),
                  BinOp("/", ConstantInt(1), ConstantInt(3))))])
        r = parse("5 + 1 * 3;")
        assert r == Block([Stmt(
            BinOp("+", ConstantInt(5),
                  BinOp("*", ConstantInt(1), ConstantInt(3))))])
        r = parse("5 || 1 && 3;")
        assert r == Block([Stmt(
            Or(ConstantInt(5), And(ConstantInt(1), ConstantInt(3))))])

    def test_multi(self):
        r = parse("1 * 2 - $x;")
        assert r == Block([Stmt(
            BinOp("-", BinOp("*", ConstantInt(1), ConstantInt(2)),
                  NamedVariable("x")))])

    def test_float_const(self):
        r = parse("$x = 3.5 + .2 + 2.;")
        assert r == Block([Stmt(
            Assignment(
                NamedVariable("x"),
                BinOp("+", BinOp("+", ConstantFloat(3.5), ConstantFloat(.2)),
                      ConstantFloat(2.))))])

    def test_paren_multi(self):
        r = parse("($x - 3) * 2;")
        assert r == Block([Stmt(
            BinOp("*", BinOp("-", NamedVariable("x"), ConstantInt(3)),
                  ConstantInt(2)))])

    def test_plusplus(self):
        r = parse("++$x;")
        assert r == Block([Stmt(PrefixOp("++", NamedVariable("x")))])
        r = parse("$x--;")
        assert r == Block([Stmt(SuffixOp("--", NamedVariable("x")))])

    def test_unary_minus(self):
        r = parse("-$x;")
        assert r == Block([Stmt(PrefixOp("-", NamedVariable("x")))])

    def test_multiple_stmts(self):
        r = parse("""
        $x = 3;
        $y = 4;
        $z;
        """)
        assert r == Block([
            Stmt(Assignment(NamedVariable("x", 1),
                            ConstantInt(3, 1), 1), 1),
            Stmt(Assignment(NamedVariable("y", 2),
                            ConstantInt(4, 2), 2), 2),
            Stmt(NamedVariable("z", 3), 3)])

    def test_echo(self):
        r = parse("echo $x;")
        assert r == Block([Echo([NamedVariable("x")])])

    def test_echo_list(self):
        r = parse("echo $x, 2, 3, 4;")
        assert r == Block([Echo([NamedVariable("x"), ConstantInt(2),
                                 ConstantInt(3), ConstantInt(4)])])

    def test_return(self):
        r = parse("return $y;")
        assert r == Block([Return(NamedVariable("y"))])

    def test_if(self):
        ret = parse("""
        if ($x)
           return $y;
        """)
        assert ret == Block([If(NamedVariable("x", 1), Return(NamedVariable("y", 2), 2), lineno=1)])

    def test_empty_if(self):
        r = parse("if ($x); {$y;}")
        assert r == Block([If(NamedVariable("x"), Block([])),
                           Block([Stmt(NamedVariable("y"))])])

    def test_if_brackets(self):
        r = parse("if ($x) { return $y; }")
        assert r == Block([If(NamedVariable("x"),
                              Block([Return(NamedVariable("y"))]))])
        assert r == parse("if ($x): return $y; endif;")

    def test_if_else(self):
        r = parse("if ($x) $y; else $z;")
        expected = Block([If(NamedVariable("x"),
                             Stmt(NamedVariable("y")),
                             elseclause=Stmt(NamedVariable("z")))])

        assert r == expected

    def test_if_else_if_oneline(self):
        r = parse("""if ($x) $y; elseif ($z) 3; else 4;""")
        expected = Block([If(NamedVariable("x"),
                             Stmt(NamedVariable("y")),
                             [If(NamedVariable("z"), Stmt(ConstantInt(3)))],
                             Stmt(ConstantInt(4)))])

        assert r == expected

    def test_if_else_if(self):
        r = parse("""
        if ($x)
          $y;
        elseif ($z)
          3;
        else
          4;
        """)
        expected = Block([
            If(NamedVariable("x", 1),
               Stmt(NamedVariable("y", 2), 2),
               [If(NamedVariable("z", 3),
                   Stmt(ConstantInt(3, 4), 4), lineno=3)],
               Stmt(ConstantInt(4, 6), 6), lineno=1)])

        assert r == expected

    def test_if_else_if_2(self):
        r = parse("""
        if ($x)
          $y;
        elseif ($z)
          3;
        elseif($y)
          7;
        else
          8;
        """)
        assert r == Block([
            If(NamedVariable("x", 1),
               Stmt(NamedVariable("y", 2), 2),
               [If(NamedVariable("z", 3),
                   Stmt(ConstantInt(3, 4), 4), lineno=3),
                If(NamedVariable("y", 5),
                   Stmt(ConstantInt(7, 6), 6), lineno=5)],
               Stmt(ConstantInt(8, 8), 8),
               lineno=1)])

    def test_if_else_if_3(self):
        r = parse("""
        if ($x)
          $y;
        elseif ($z)
          3;
        elseif($y)
          7;
        """)
        assert r == Block([If(NamedVariable("x", 1),
                              Stmt(NamedVariable("y", 2), 2),
                              [If(NamedVariable("z", 3),
                                  Stmt(ConstantInt(3, 4), 4), lineno=3),
                               If(NamedVariable("y", 5),
                                  Stmt(ConstantInt(7, 6), 6), lineno=5)],
                              lineno=1)])

    def test_if_else_if_brackets(self):
        r1 = parse("""
        if ($x) {
          $y; 3;
        } elseif ($z) {
          3; $x;
        } elseif($y) {
          7;
        } else {
          8; $x;
        }""")
        r2 = parse("""
        if ($x):
          $y; 3;
        elseif ($z):
          3; $x;
        elseif($y):
          7;
        else:
          8; $x;
        endif;""")
        assert r1 == r2

    def test_while(self):
        r = parse("while ($x) $x--;")
        assert r == Block([While(NamedVariable("x"),
                                 Stmt(SuffixOp("--", NamedVariable("x"))))])

    def test_empty_while(self):
        r = parse("while(f());")
        assert r == Block([While(SimpleCall(RelativeName(['f']), []),
                                 Block([]))])

    def test_while_brackets(self):
        r1 = parse("while ($x) { 5; 6; }")
        r2 = parse("while ($x): 5; 6; endwhile;")
        assert r1 == r2

    def test_for(self):
        r = parse("for ($i = 0; $i < 10; $i++) {}")
        expected = Block([For(Assignment(NamedVariable("i"), ConstantInt(0)),
                              BinOp("<", NamedVariable("i"), ConstantInt(10)),
                              SuffixOp("++", NamedVariable("i")),
                              Block([]))])

        assert r == expected

    def test_for_empty(self):
        r = parse("for ($i = 0; $i;) {}")
        expected = Block([For(Assignment(NamedVariable("i"), ConstantInt(0)),
                              NamedVariable("i"), None, Block([]))])
        assert r == expected

    def test_for_brackets(self):
        r1 = parse("for($x; $y; $z) { $u; $v; }")
        r2 = parse("for($x; $y; $z): $u; $v; endfor;")
        assert r1 == r2

    def test_dolar_var(self):
        r = parse("$$x;")
        assert r == Block([Stmt(Variable(NamedVariable("x")))])

        r = parse("$$$x;")
        assert r == Block([Stmt(Variable(Variable(NamedVariable("x"))))])

    def test_dynamic_var(self):
        r = parse('${"x" + 3};')
        assert r == Block([Stmt(Variable(BinOp("+", ConstantStr("x"),
                                               ConstantInt(3))))])

    def test_function_call(self):
        r = parse("3 + printf();")
        assert r == Block([Stmt(BinOp("+", ConstantInt(3),
                          SimpleCall(RelativeName(["printf"]), [])))])
        r = parse("printf(1, 2, 3);")
        assert r == Block([Stmt(SimpleCall(
            RelativeName(["printf"]),
            [ConstantInt(1), ConstantInt(2), ConstantInt(3)])
        )])
        r = parse("printf(1);")
        assert r == Block([Stmt(SimpleCall(RelativeName(["printf"]),
                                           [ConstantInt(1)]))])

    def test_dynamic_funccall(self):
        r = parse("3 + $x(3, 4);")
        assert r == Block([Stmt(BinOp("+", ConstantInt(3),
                    DynamicCall(NamedVariable("x"),
                                [ConstantInt(3), ConstantInt(4)])))])

    def test_function_declr(self):
        r = parse("""
        function f() {}
        f();
        """)
        assert r == Block([
            FunctionDecl("f", False, [], Block([]), 1),
            Stmt(SimpleCall(RelativeName(["f"], 2), [], 2), 2)])
        r = parse("function f($a, $b, $c) { 3; 4; }")
        assert r == Block([
            FunctionDecl("f", False,
                         [Argument("a"), Argument("b"), Argument("c")],
                         Block([Stmt(ConstantInt(3)),
                                Stmt(ConstantInt(4))]), 0)])

        r = parse("function f($a) { 3; 4; }")
        assert r == Block([
            FunctionDecl("f", False, [Argument("a")],
                         Block([Stmt(ConstantInt(3)),
                                Stmt(ConstantInt(4))]), 0)])
        r = parse("function f(&$a) {}")
        assert r == Block([
            FunctionDecl("f", False, [Argument("a", is_reference=True)],
                         Block([]), 0)])
        r = parse("function &f($a) {}")
        assert r == Block([
            FunctionDecl("f", True, [Argument("a")], Block([]), 0)])

    def test_multielem_echo(self):
        r = parse('''
        echo 1, 2, 3;
        ''')
        assert r == Block([Echo([ConstantInt(1, 1), ConstantInt(2, 1),
                                 ConstantInt(3, 1)], 1)])
        # print gramma is >T_PRING expr<, so we should see parse exception
        with raises(ParseError):
            parse('''print 1, 2, 3;''')

    def test_string_literal(self):
        r = parse(r'''
        $x = "\n";
        ''')
        expected = Block([Stmt(Assignment(NamedVariable("x", 1),
                                          ConstantStr('\n', 1), 1), 1)])
        assert r == expected

    def test_getitem(self):
        r = parse("$x[1];")
        assert r == Block([Stmt(GetItem(NamedVariable("x"), ConstantInt(1)))])

    def test_setitem_new_approach(self):
        r = parse("$x[1] = 3;")
        assert r == Block([Stmt(
            Assignment(GetItem(NamedVariable("x"), ConstantInt(1)),
                       ConstantInt(3)))])

    def test_inplacesetitem(self):
        r = parse("$x[1] += 3;")
        assert r == Block([Stmt(InplaceOp('+=',
                                        GetItem(NamedVariable("x"),
                                        ConstantInt(1)), ConstantInt(3)))])

    def test_array(self):
        # Now we use Hash instead Array
        r = parse("array();")
        assert r == Block([Stmt(Hash([]))])
        r = parse("array(1);")
        assert r == Block([Stmt(Hash([(None, ConstantInt(1))]))])
        r = parse("array(0 => &$x, 1=> $y);")
        assert r == Block([Stmt(
            Hash([
                (ConstantInt(0), Reference(NamedVariable('x'))),
                (ConstantInt(1), NamedVariable('y')), ]))])
        r = parse("array(1, 2, 3 + 4);")
        assert r == Block([Stmt(
            Hash([(None, ConstantInt(1)),
                  (None, ConstantInt(2)),
                  (None, BinOp("+", ConstantInt(3), ConstantInt(4)))]))])

    def test_array_append(self):
        r = parse("$a[] = 3;")
        expected = Block([Stmt(
            Assignment(GetItem(NamedVariable("a"), None),
                       ConstantInt(3)))])
        assert r == expected

    def test_and_or(self):
        r = parse("1 && 2 || 3;")
        assert r == Block([Stmt(Or(And(ConstantInt(1), ConstantInt(2)),
                                   ConstantInt(3)))])

    def test_and_or2(self):
        r = parse("2 || 3 && 1;")
        assert r == Block([Stmt(Or(ConstantInt(2),
                                   And(ConstantInt(3), ConstantInt(1))))])

    def test_xor(self):
        r = parse("3 ^ 5;")    # 6
        assert r == Block([Stmt(BinOp('^', ConstantInt(3), ConstantInt(5)))])
        r = parse("3 xor 5;")  # TRUE
        assert r == Block([Stmt(BinOp('xor', ConstantInt(3), ConstantInt(5)))])

    def test_inplace_oper(self):
        r = parse("$x += 2;")
        assert r == Block([Stmt(InplaceOp("+=", NamedVariable("x"),
                                          ConstantInt(2)))])

    def test_inplace_2(self):
        r = parse("($i = $j);")
        assert r == Block([Stmt(Assignment(NamedVariable("i"),
                                           NamedVariable("j")))])

    def test_global(self):
        r = parse("global $a, $b, $c;")
        assert r == Block([Global(Block([
            NamedVariable("a"), NamedVariable("b"), NamedVariable("c")]))])
        r = parse("global $a;")
        assert r == Block([Global(Block([NamedVariable("a")]))])

    def test_constant(self):
        r = parse("$x = c;")
        assert r == Block([Stmt(Assignment(NamedVariable("x"),
                                           NamedConstant(RelativeName(["c"]))))])

    def test_do_while(self):
        r = parse("do { 1; } while (TRUE);")
        assert r == Block([DoWhile(Block([Stmt(ConstantInt(1))]),
                                   NamedConstant(RelativeName(['TRUE'])))])

    def test_assign_array_element_2(self):
        r = parse("$x[0][0];")
        expected = Block([Stmt(
            GetItem(GetItem(NamedVariable("x"),
                            ConstantInt(0)),
                    ConstantInt(0)))])

        assert r == expected

        r = parse("$x[0][0] = 1;")
        assert r == Block([Stmt(
            Assignment(GetItem(GetItem(NamedVariable("x"),
                                       ConstantInt(0)),
                               ConstantInt(0)), ConstantInt(1)))])

        r = parse("$x[0][] = 1;")
        assert r == Block([Stmt(Assignment(
            GetItem(GetItem(NamedVariable("x"), ConstantInt(0)), None),
            ConstantInt(1)))])

    def test_hash_creation(self):
        r = parse("array('x' => 'y', 'b' => 'a', 'z' => 3);")
        assert r == Block([Stmt(Hash([(ConstantStr("x"), ConstantStr("y")),
                                      (ConstantStr("b"), ConstantStr("a")),
                                      (ConstantStr("z"), ConstantInt(3))]))])

    def test_array_mix_creation(self):
        r = parse("array(1, 'a'=>2, 3, 'b'=>'c');")
        expected = Block([Stmt(
            Hash([(None, ConstantInt(1)),
                  (ConstantStr("a"), ConstantInt(2)),
                  (None, ConstantInt(3)),
                  (ConstantStr('b'), ConstantStr('c'))]))])
        assert r == expected

        r = parse("array(14 => 'xcx', 'a'=>2, 3);")
        assert r == Block([Stmt(Hash([(ConstantInt(14), ConstantStr("xcx")),
                                      (ConstantStr("a"), ConstantInt(2)),
                                      (None, ConstantInt(3))
                                      ]))])

        r = parse("array(1, 2, 3, 4 => 5);")
        assert r == Block([Stmt(Hash([(None, ConstantInt(1)),
                                      (None, ConstantInt(2)),
                                      (None, ConstantInt(3)),
                                      (ConstantInt(4), ConstantInt(5))
                                      ]))])

    def test_iterator(self):
        r = parse("foreach ($x as $y) {}")
        assert r == Block([ForEach(NamedVariable("x"),
                                   NamedVariable('y'), Block([]))])

    def test_iterator_with_reference(self):
        r = parse("foreach ($x as $y => &$z) {}")
        assert r == Block([ForEachKey(NamedVariable("x"),
                                      NamedVariable('y'),
                                      Reference(NamedVariable("z")),
                                      Block([]))])

    def test_iterator_with_reference_2(self):
        r = parse("foreach ($x as $y => &$z[5]) {}")
        assert r == Block([ForEachKey(NamedVariable("x"),
                                      NamedVariable('y'),
                                      Reference(GetItem(
                                          NamedVariable("z"),
                                          ConstantInt(5))),
                                      Block([]))])

    def test_foreach_brackets(self):
        r1 = parse("foreach ($x as $y) { $z; $t; }")
        r2 = parse("foreach ($x as $y): $z; $t; endforeach;")
        assert r1 == r2

    def test_array_cast(self):
        r = parse('(array)3;')
        assert r == Block([Stmt(Cast("array", ConstantInt(3)))])

    def test_array_trailing_coma(self):
        # Now we use Hash instead of Array
        r = parse("array(1,);")
        assert r == Block([Stmt(Hash([(None, ConstantInt(1))]))])

    def test_array_single_elem(self):
        r = parse("array(1 => 2);")
        assert r == Block([Stmt(Hash([(ConstantInt(1), ConstantInt(2))]))])

    def test_comments(self):
        r = parse('''1; // comment
        2;''')
        assert r == Block([Stmt(ConstantInt(1)), Stmt(ConstantInt(2, 1), 1)])
        r = parse('''
        1;
        1 /* abc * / */ + /* abc */ 2;
        ''')
        expected = Block([
            Stmt(ConstantInt(1, 1), 1),
            Stmt(BinOp("+", ConstantInt(1, 2), ConstantInt(2, 2), 2), 2)])
        assert r == expected

    def test_comments_2(self):
        r = parse('''
        1;
        # some other comment
        2;
        ''')
        assert r == Block([Stmt(ConstantInt(1, 1), 1),
                           Stmt(ConstantInt(2, 3), 3)])

    def test_print_new(self):
        r = parse('''
        print 1;
        ''')
        assert r == Block([Stmt(Print(ConstantInt(1, 1), 1), 1)])

    def test_default_args(self):
        r = parse('''
        function f($a = 3)
        {
        }
        ''')
        assert r == Block([
            FunctionDecl("f", False,
                         [Argument("a", defaultvalue=ConstantInt(3, 1),
                                   lineno=1)],
                         Block([]), 1)])

    def test_array_default_args(self):
        r = parse('''
        function f($a = array(0, 1 => 2))
        {
        }
        ''')
        assert r == Block(
            [FunctionDecl(
                "f",
                False,
                [Argument(
                    "a",
                    defaultvalue=Hash([
                        (None, ConstantInt(0, 1)),
                        (ConstantInt(1, 1), ConstantInt(2, 1))], 1),
                    lineno=1)],
                Block([]),
                1)])

    def test_all_8_args_combinations(self):
        r = parse("function f($x, $y) {}")
        assert r == Block([
            FunctionDecl("f", False, [Argument("x"), Argument("y")],
                         Block([]), 0)])
        r = parse("function f($x=5, $y=5) {}")
        assert r == Block([FunctionDecl("f", False, [
            Argument("x", defaultvalue=ConstantInt(5)),
            Argument("y", defaultvalue=ConstantInt(5))], Block([]), 0)])
        r = parse("function f(&$x, &$y) {}")
        assert r == Block([FunctionDecl("f", False, [
            Argument("x", is_reference=True),
            Argument("y", is_reference=True)], Block([]), 0)])
        r = parse("function f(&$x=5, &$y=5) {}")
        assert r == Block([FunctionDecl("f", False,
            [Argument("x", is_reference=True, defaultvalue=ConstantInt(5)),
             Argument("y", is_reference=True, defaultvalue=ConstantInt(5))],
            Block([]), 0)])

    def test_static(self):
        ret = parse("""
           static $a = 0;
        """)
        assert ret == Block([
            StaticDecl(
                [InitializedVariable('a', ConstantInt(0, 1), lineno=1)],
                lineno=1
            )])

        r = parse('''
        static $a, $x = 0, $y, $z = 0;
        ''')
        assert r == Block([StaticDecl([UninitializedVariable("a", 1),
                                       InitializedVariable('x',
                                        ConstantInt(0, 1), 1),
                                       UninitializedVariable("y", 1),
                                       InitializedVariable('z',
                                       ConstantInt(0, 1), 1)], 1)])
        r = parse('''
        static $x = 0;
        ''')
        assert r == Block([StaticDecl([InitializedVariable('x',
                                           ConstantInt(0, 1), 1)], 1)])
        r = parse('''
        static $x;
        ''')
        assert r == Block([StaticDecl([UninitializedVariable('x', 1)], 1)])
        r = parse('''
        static $x = 3;
        ''')
        assert r == Block([StaticDecl(
            [InitializedVariable('x', ConstantInt(3, 1), 1)], 1)])

    def test_octal(self):
        r = parse('''
        027;
        ''')
        assert r == Block([Stmt(ConstantInt(23, 1), 1)])

    # def test_octal_overflow(self):
    #     r = parse('''
    #     0277777777777777777777;
    #     ''')
    #     assert r == Block([Stmt(ConstantFloat(3.4587645138205E+18, 1), 1)])

    def test_ill_octal(self):
        r = parse('''
        02792;
        ''')
        assert r == Block([Stmt(ConstantInt(23, 1), 1)])

    def test_more_ill_octal(self):
        r = parse('''
        -07182;
        ''')
        assert r == Block([Stmt(PrefixOp('-', ConstantInt(57, 1), 1), 1)])

    def test_hex(self):
        r = parse('''
        0xff;
        ''')
        assert r == Block([Stmt(ConstantInt(255, 1), 1)])

    def test_hex_overflow(self):
        r = parse('''
        0xff33ff33f23f0123;
        ''')
        assert r == Block([Stmt(ConstantFloat(18389322302056497443.0, 1), 1)])

    def test_exponent(self):
        r = parse('''
        10e1;
        ''')
        expected = Block([Stmt(ConstantFloat(float(100.0), 1), 1)])
        assert r == expected

    def test_exponent_float(self):
        r = parse('''
        10.3e1;
        ''')
        expected = Block([Stmt(ConstantFloat(float(103.0), 1), 1)])
        assert r == expected

    def test_exponent_float_plus(self):
        r = parse('''
        10.3e+1;
        ''')
        assert r == Block([Stmt(ConstantFloat(float('10.3e+1'), 1), 1)])

    def test_exponent_float_minus(self):
        r = parse('''
        10.3e-1;
        ''')
        assert r == Block([Stmt(ConstantFloat(float('10.3e-1'), 1), 1)])

    def test_exponent_simple(self):
        r = parse('''
        2.345e1;
        ''')
        assert r == Block([Stmt(ConstantFloat(23.45, 1), 1)])

    def test_exponent_simple_minus(self):
        r = parse('''
        -2.345e1;
        ''')
        assert r == Block([Stmt(PrefixOp('-', ConstantFloat(23.45, 1), 1), 1)])

    def test_minus_octal(self):
        r = parse('''
        -027;
        ''')
        assert r == Block([Stmt(PrefixOp('-', ConstantInt(23, 1), 1), 1)])

    def test_bug_1(self):
        r = parse('$i < $iter and $Tr;')
        expected = Block([Stmt(And(BinOp("<", NamedVariable("i"),
                                         NamedVariable("iter")),
                                   NamedVariable("Tr")))])
        assert r == expected

    def test_break_with_expr(self):
        with raises(ParseError):
            parse("break 1+1;")
        with raises(ParseError):
            parse("break 1+$x;")
        with raises(ParseError):
            parse("break $x;")
        with raises(ParseError):
            parse("break -1;")
        r = parse('''
        break 9;
        ''')
        assert r == Block([Break(levels=9, lineno=1)])

    def test_continue_with_expr(self):
        with raises(ParseError):
            parse("continue 1+1;")
        with raises(ParseError):
            parse("continue 1+$x;")
        with raises(ParseError):
            parse("continue $x;")
        with raises(ParseError):
            parse("continue -1;")
        r = parse('''
        continue 9;
        ''')
        assert r == Block([Continue(levels=9, lineno=1)])

    def test_uppercase_1E50(self):
        r = parse('1E50')
        assert r == Block([Stmt(ConstantFloat(1E50))])

    def test_unset(self):
        r = parse('unset($x, $y[$z]);')
        assert r == Block([Unset(
            [NamedVariable("x"),
             GetItem(NamedVariable("y"),
                     NamedVariable("z"))])])

    def test_isset(self):
        r = parse('isset($x, $y[$z]);')
        assert r == Block([Stmt(And(
            IsSet(NamedVariable("x")),
            IsSet(GetItem(NamedVariable("y"),
                          NamedVariable("z")))))])

    def test_empty(self):
        r = parse('empty($y[$z]);')
        assert r == Block([Stmt(Empty(
            GetItem(NamedVariable("y"),
                    NamedVariable("z"))))])

    def test_nothing(self):
        r = parse('')
        assert r == Block([])

    def test_comment(self):
        r = parse('/*****/')
        assert r == Block([])

    def test_variable(self):
        r = parse("$a0a0")
        assert r == Block([Stmt(NamedVariable("a0a0"))])

    def test_dynamic_variable(self):
        r = parse("${'a0a'}")
        assert r == Block([Stmt(NamedVariable("a0a"))])
        r = parse('${"a0a"}')
        assert r == Block([Stmt(NamedVariable("a0a"))])

    def test_multiline_comment(self):
        r = parse('\n$a = /*\nfoo\n   */ 3')
        assert r == Block([Stmt(
            Assignment(
                NamedVariable('a', lineno=1),
                ConstantInt(3, lineno=3),
                lineno=1),
            lineno=1)])
        r = parse('\n$a /*\nfoo\n   */ = 3')
        assert r == Block([Stmt(
            Assignment(
                NamedVariable('a', lineno=1),
                ConstantInt(3, lineno=3),
                lineno=1),
            lineno=1)])

    def test_toplevel_const(self):
        r = parse('const x = 42;')
        assert r == Block([Block([ConstDecl('x', ConstantInt(42))])])
        r = parse('const x = 42, y = 84, z = 41;')
        assert r == Block([Block([ConstDecl('x', ConstantInt(42)),
                                  ConstDecl('y', ConstantInt(84)),
                                  ConstDecl('z', ConstantInt(41))])])

    def test_class_minimal(self):
        r = parse('class A { };')
        assert r == Block([ClassBlock("A")])

    def test_null_caseinsensitive(self):
        r = parse('null')
        assert r == Block([Stmt(NamedConstant(RelativeName(["null"])))])
        r = parse('nulL')
        assert r == Block([Stmt(NamedConstant(RelativeName(["nulL"])))])
        r = parse('Null')
        assert r == Block([Stmt(NamedConstant(RelativeName(["Null"])))])
        r = parse('nuLl')
        assert r == Block([Stmt(NamedConstant(RelativeName(["nuLl"])))])
        r = parse('nULl')
        assert r == Block([Stmt(NamedConstant(RelativeName(["nULl"])))])

    def test_class_property(self):
        r = parse('class A { public $foo; };')
        assert r == Block([ClassBlock("A", body=Block([
            PropertyDecl('foo', None, consts.ACC_PUBLIC)]))])
        r2 = parse('class A { var $foo; };')
        assert r2 == r

    def test_class_property_value(self):
        r = parse('class A { public $foo = 42; };')
        assert r == Block([ClassBlock("A", body=Block([
            PropertyDecl('foo', ConstantInt(42), consts.ACC_PUBLIC)]))])

    def test_class_new(self):
        r = parse('$x = new AaA;')
        assert r == Block([Stmt(Assignment(NamedVariable('x'),
                                           New(RelativeName(['AaA']))))])
        r = parse('$x = new \\AaA;')
        assert r == Block([Stmt(Assignment(NamedVariable('x'),
                                           New(AbsoluteName(['AaA']))))])
        r = parse('$x = new namespace\\AaA;')
        assert r == Block([Stmt(Assignment(NamedVariable('x'),
                                           New(Rel2AbsName(['AaA']))))])
        r = parse('$x = new AaA();')
        assert r == Block([Stmt(Assignment(NamedVariable('x'),
                                           New(RelativeName(['AaA']))))])
        r = parse('$x = new AaA(5, $y);')
        assert r == Block([Stmt(Assignment(NamedVariable('x'),
                                           New(RelativeName(['AaA']),
                    [ConstantInt(5), NamedVariable('y')])))])
        r = parse('$x = new $foo;')
        assert r == Block([Stmt(Assignment(NamedVariable('x'),
                                          New(NamedVariable('foo'))))])

    def test_class_extends(self):
        r = parse('class A extends B { };')
        assert r == Block([ClassBlock("A", extends=RelativeName(["B"]))])

    def test_class_method(self):
        r = parse('class A { function foo($x) { } };')
        assert r == Block([ClassBlock("A", body=Block([
            MethodBlock("foo", False, [Argument("x")], Block([]),
                       ConstantInt(0), 0), ]))])
        r2 = parse('class A { public function foo($x) { } };')
        assert r2 == Block([ClassBlock("A", body=Block([
            MethodBlock("foo", False, [Argument("x")], Block([]),
                       ConstantInt(consts.ACC_PUBLIC), 0)]))])

    def test_class_const(self):
        r = parse('class A { const a=1, b=2; const c=3; }')
        assert r == Block([ClassBlock("A", body=Block([
            ConstDecl('a', ConstantInt(1)),
            ConstDecl('b', ConstantInt(2)),
            ConstDecl('c', ConstantInt(3))]))])

    def test_class_const_use(self):
        r = parse('A::x;')
        assert r == Block([Stmt(ClassConstant(RelativeName(['A']), 'x'))])
        r = parse('$y::x;')
        assert r == Block([Stmt(ClassConstant(NamedVariable('y'),
                                              'x'))])

    def test_function_call_reference(self):
        r = parse("foo(&$a);")
        exp = Block([Stmt(SimpleCall(RelativeName(["foo"]),
                             [Reference(NamedVariable("a"))]))])
        assert r == exp
        r = parse("foo($a, &$b);")
        exp = Block([Stmt(SimpleCall(RelativeName(["foo"]),
                             [NamedVariable("a"),
                              Reference(NamedVariable("b"))]))])
        assert r == exp

    def test_instance_property_simple(self):
        r = parse('$x->foo')
        assert r == Block([Stmt(GetAttr(NamedVariable("x"),
                                        ConstantStr("foo")))])

    def test_instance_property_array(self):
        r = parse('$x->foo[5]')
        assert r == Block([Stmt(GetItem(GetAttr(NamedVariable("x"),
                                                ConstantStr("foo")),
                                        ConstantInt(5)))])
        r = parse('$x->foo[]')
        assert r == Block([Stmt(GetItem(GetAttr(NamedVariable("x"),
                                                ConstantStr("foo")),
                                        None))])

    def test_instance_property_double_arrow(self):
        r = parse('$x->foo->bar')
        assert r == Block([Stmt(GetAttr(GetAttr(NamedVariable("x"),
                                                ConstantStr("foo")),
                                        ConstantStr("bar")))])
        r = parse('$x->foo[2][3]->bar->baz[4]')
        assert r == Block([Stmt(
            GetItem(
                GetAttr(
                    GetAttr(
                        GetItem(
                            GetItem(
                                GetAttr(NamedVariable("x"),
                                        ConstantStr("foo")),
                                ConstantInt(2)),
                            ConstantInt(3)),
                        ConstantStr("bar")),
                    ConstantStr("baz")),
                ConstantInt(4)))])

    def test_call_method(self):
        r = parse('$x->foo(42)')
        assert r == Block([Stmt(SimpleCall(
            GetAttr(
                NamedVariable("x"),
                ConstantStr("foo")),
            [ConstantInt(42)]))])
        r = parse('$x->$bar(42)')
        assert r == Block([Stmt(
            SimpleCall(
                GetAttr(
                    NamedVariable("x"),
                    NamedVariable("bar")),
                [ConstantInt(42)])
        )])
        r = parse('$x->foo[5]->bar(42)')
        assert r == Block([Stmt(
            SimpleCall(
                GetAttr(
                    GetItem(
                        GetAttr(
                            NamedVariable("x"),
                            ConstantStr("foo")),
                        ConstantInt(5)),
                    ConstantStr("bar")),
                [ConstantInt(42)])
        )])

    def test_complex_call(self):
        r = parse('$x->foo[5]();')
        assert r == Block([Stmt(
            SimpleCall(
                GetItem(
                    GetAttr(NamedVariable("x"), ConstantStr('foo')),
                    ConstantInt(5)),
                [])
        )])
        r = parse('$x->$foo[5]();')
        assert r == Block([Stmt(
            SimpleCall(GetAttr(
                NamedVariable('x'),
                GetItem(
                    NamedVariable('foo'),
                    ConstantInt(5))),
                [])
        )])

    def test_attr_visibility(self):
        with raises(ParseError):
            parse("class A { private public $x; }")
        with raises(ParseError):
            parse("class A { private private $x; }")
        with raises(ParseError):
            parse("class A { public public $x; }")
        with raises(ParseError):
            parse("class A { var public $x; }")
        with raises(ParseError):
            parse("class A { public var $x; }")
        with raises(ParseError):
            parse("class A { protected var $x; }")
        parse("class A { static $x; }")
        with raises(ParseError):
            parse("class A { var static $x; }")
        with raises(ParseError):
            parse("class A { static var $x; }")
        parse("class A { static protected $x; }")
        with raises(ParseError):
            parse("class A { static static $x; }")
        with raises(ParseError):
            parse("class A { public static static $x; }")

        r = parse("class A { protected static $x; }")
        assert r == Block([ClassBlock("A", body=Block([
            PropertyDecl('x', None, consts.ACC_STATIC | consts.ACC_PROTECTED)
        ]))])

    def test_static_member(self):
        r = parse("A::$x;")
        assert r == Block([Stmt(StaticMember(
            RelativeName(["A"]), ConstantStr("x")))])
        r = parse("\\A\\B::$x;")
        assert r == Block([Stmt(StaticMember(
            AbsoluteName(["A", "B"]), ConstantStr("x")))])
        r = parse("$x::$$y;")
        assert r == Block([Stmt(StaticMember(
            NamedVariable("x"), NamedVariable("y")))])

    def test_static_method(self):
        r = parse("A::f();")
        assert r == Block([Stmt(StaticMethodCall(
            RelativeName(["A"]), ConstantStr("f"), []))])
        r = parse("A::$y();")
        assert r == Block([Stmt(StaticMethodCall(
            RelativeName(["A"]), NamedVariable("y"), []))])
        r = parse("\\A\\B::f();")
        assert r == Block([Stmt(StaticMethodCall(
            AbsoluteName(["A", "B"]), ConstantStr("f"), []))])
        r = parse("$x::f();")
        assert r == Block([Stmt(StaticMethodCall(
            NamedVariable("x"), ConstantStr("f"), []))])
        r = parse("$x::$y();")
        assert r == Block([Stmt(StaticMethodCall(
            NamedVariable("x"), NamedVariable("y"), []))])

    def test_class_or_method_abstract(self):
        r = parse('abstract class A { }')
        assert r == Block([ClassBlock("A", consts.ACC_ABSTRACT)])
        r = parse('abstract class A { abstract function f($x); }')
        assert r == Block([ClassBlock("A", consts.ACC_ABSTRACT, body=Block([
            MethodBlock("f", False, [Argument("x")], None,
                       ConstantInt(consts.ACC_ABSTRACT), 0)]))])

    def test_clone_operator(self):
        r = parse('$x = clone $y;')
        assert r == Block([Stmt(Assignment(NamedVariable('x'),
                                          Clone(NamedVariable('y'))))])

    def test_interface(self):
        r = parse('interface c extends a, b { function f($x); }')
        flags = consts.ACC_INTERFACE | consts.ACC_ABSTRACT
        assert r == Block([
            ClassBlock("c", flags,
                       baseinterfaces=[RelativeName(['a']),
                                       RelativeName(['b'])],
                       body=Block([
                           MethodBlock("f", False, [Argument("x")], None,
                                       ConstantInt(0), 0)]))])
        r = parse('class c implements a, b { }')
        assert r == Block([
            ClassBlock("c", 0, baseinterfaces=[RelativeName(['a']),
                                               RelativeName(['b'])])])

    def test_at_sign(self):
        r = parse('@$x;')
        assert r == Block([Stmt(Silence(NamedVariable('x')))])
        r = parse('$x[@$z[$u]];')
        assert r == Block([Stmt(GetItem(
            NamedVariable('x'),
            Silence(GetItem(NamedVariable('z'),
                           NamedVariable('u')))))])
        r = parse('@$x = $y;')
        assert r == Block([Stmt(Silence(Assignment(
            NamedVariable('x'),
            NamedVariable('y'))))])

    def test_switch(self):
        r = parse('switch ($x) { case $y: 5; 6; default: 7; }')
        assert r == Block([Switch(NamedVariable('x'), Block([
            Case(NamedVariable('y'), Block([
                Stmt(ConstantInt(5)),
                Stmt(ConstantInt(6))])),
            Case(None, Block([
                Stmt(ConstantInt(7))]))]))])
        r2 = parse("switch ($x): case $y: 5; 6; default: 7; endswitch;")
        assert r == r2

    def test_typehint(self):
        r = parse('function f(Abc $x) { }')
        assert r == Block([
            FunctionDecl("f", False,
                         [Argument("x", typehint=RelativeName(["Abc"]))],
                         Block([]), 0)])
        r = parse('function f(array $x) { }')
        assert r == Block([
            FunctionDecl("f", False,
                         [Argument("x", typehint=AbsoluteName(["array"]))],
                         Block([]), 0)])
        r = parse('function f(Abc &$x=NULL) { }')
        assert r == Block([
            FunctionDecl("f", False,
                         [Argument("x", typehint=RelativeName(["Abc"]),
                                   is_reference=True,
                                   defaultvalue=NamedConstant(
                                       RelativeName(["NULL"])))],
                         Block([]), 0)])

    def test_escaping_single_quoted(self):
        r = parse(r"echo 'foo\'bar';")
        assert r == Block([Echo([ConstantStr("foo'bar")])])
        r = parse(r"echo 'foo\'bar\nbaz';")
        assert r == Block([Echo([ConstantStr("foo'bar\\nbaz")])])
        r = parse(r"echo 'foo\\';")
        assert r == Block([Echo([ConstantStr("foo\\")])])

    def test_escaping_double_quoted(self):
        r = parse(r'echo "foo\"bar";')
        assert r == Block([Echo([ConstantStr('foo"bar')])])
        r = parse(r'echo "foo\nbaz";')
        assert r == Block([Echo([ConstantStr("foo\nbaz")])])
        r = parse(r'echo "foo\\";')
        assert r == Block([Echo([ConstantStr('foo\\')])])
        r = parse(r'echo "foo\$x";')
        assert r == Block([Echo([ConstantStr('foo$x')])])
        r = parse(r'echo "***\y***";')
        assert r == Block([Echo([ConstantStr('***\\y***')])])

    def test_double_quoted_1(self):
        r = parse(r'echo "foo$x";')
        assert r == Block([Echo([DoubleQuotedStr(
            [ConstantStr('foo'), NamedVariable('x')])])])
        r = parse(r'echo "foo$xz...$Foo?";')
        assert r == Block([Echo([DoubleQuotedStr(
            [ConstantStr('foo'),
             NamedVariable('xz'), ConstantStr('...'),
             NamedVariable('Foo'),
             ConstantStr('?')])])])

    def test_double_quoted_2(self):
        def prepr_simple(string, expected):
            r = parse('echo "%s";' % string)
            assert r == Block([Echo([ConstantStr(expected)])])

        def prepr_complex(string, lst):
            r = parse('echo "%s";' % string)
            assert r == Block([Echo([DoubleQuotedStr(lst)])])
        #
        prepr_simple('\\\\', '\\')
        prepr_simple('\\n', '\n')
        prepr_simple("\\'", "\\'")

        prepr_complex('$x',
                      [NamedVariable('x')])
        prepr_complex('a $x $y b $z ',
                      [ConstantStr('a '),
                       NamedVariable('x'),
                       ConstantStr(' '),
                       NamedVariable('y'),
                       ConstantStr(' b '),
                       NamedVariable('z'),
                       ConstantStr(' ')])
        prepr_complex('\${x$x[$y]$x}',
                      [ConstantStr("${x"),
                       GetItem(NamedVariable('x'),
                               NamedVariable('y')),
                       NamedVariable('x'),
                       ConstantStr("}")])

    def test_double_quoted_hex(self):
        r = parse(r'echo "***\x9A***";')
        assert r == Block([Echo([ConstantStr('***\x9A***')])])
        r = parse(r'echo "***\xA9***";')
        assert r == Block([Echo([ConstantStr('***\xA9***')])])
        r = parse(r'echo "***\xab***";')
        assert r == Block([Echo([ConstantStr('***\xAB***')])])
        r = parse(r'echo "***\x9***";')
        assert r == Block([Echo([ConstantStr('***\x09***')])])
        r = parse(r'echo "***\xA***";')
        assert r == Block([Echo([ConstantStr('***\x0A***')])])
        r = parse(r'echo "***\x9G***";')
        assert r == Block([Echo([ConstantStr('***\x09G***')])])
        r = parse(r'echo "***\xag***";')
        assert r == Block([Echo([ConstantStr('***\x0Ag***')])])
        r = parse(r'echo "***\xA";')
        assert r == Block([Echo([ConstantStr('***\x0A')])])
        r = parse(r'echo "***\x3";')
        assert r == Block([Echo([ConstantStr('***\x03')])])
        r = parse(r'echo "***\x";')
        assert r == Block([Echo([ConstantStr('***\\x')])])

    def test_double_quote_oct(self):
        r = parse(r'echo "***\4***";')
        assert r == Block([Echo([ConstantStr('***\x04***')])])
        r = parse(r'echo "***\8***";')
        assert r == Block([Echo([ConstantStr('***\\8***')])])
        r = parse(r'echo "***\42***";')
        assert r == Block([Echo([ConstantStr('***\x22***')])])
        r = parse(r'echo "***\48***";')
        assert r == Block([Echo([ConstantStr('***\x048***')])])
        r = parse(r'echo "***\123***";')
        assert r == Block([Echo([ConstantStr('***\x53***')])])
        r = parse(r'echo "***\129***";')
        assert r == Block([Echo([ConstantStr('***\x0A9***')])])
        r = parse(r'echo "***\423***";')     # wrap-around! equal to \023
        assert r == Block([Echo([ConstantStr('***\x13***')])])
        r = parse(r'echo "***\777***";')     # wrap-around! equal to \377
        assert r == Block([Echo([ConstantStr('***\xFF***')])])
        r = parse(r'echo "***\778***";')
        assert r == Block([Echo([ConstantStr('***\x3F8***')])])

    def test_exit_or_die(self):
        for input in ['exit;', 'exit();', 'exit(0);',
                      'die;', 'die();', 'die(0);']:
            r = parse(input)
            assert r == Block([Stmt(Exit(ConstantInt(0)))])
        for input in ['exit($a);', 'die($a);']:
            r = parse(input)
            assert r == Block([Stmt(Exit(NamedVariable('a')))])

    def test_goto(self):
        r = parse(r'abc:')
        assert r == Block([GotoLabel('abc')])
        r = parse(r'goto abc;')
        assert r == Block([Goto('abc')])

    def test_list_syntax(self):
        r = parse("list($a) = $b;")
        assert r == Block([Stmt(
            ListAssignment(ListOfVars([NamedVariable("a", 0)]),
                           NamedVariable("b", 0)))])
        r = parse("list($a, $b) = 3;")
        assert r == Block([Stmt(ListAssignment(
            ListOfVars([NamedVariable("a"),
                        NamedVariable("b")]),
            ConstantInt(3)))])

    def test_try_catch(self):
        r = parse("try { } catch (Exception $e) {}")
        assert r == Block([
            TryBlock(Block([]), [CatchBlock("Exception", "e", Block([]))])])

    def test_throw(self):
        r = parse("throw 0;")
        assert r == Block([Throw(ConstantInt(0))])

    def test_variable_with_numbers(self):
        r = parse("V4_V5")
        assert r == Block([Stmt(NamedConstant(RelativeName(["V4_V5"])))])

    def test_minus_static_decl(self):
        r = parse("class A { var $x = -1; }")
        assert r == Block([ClassBlock('A', 0x0, None, [], Block([
            PropertyDecl("x", ConstantInt(-1))]))])

    def test_lambda_function(self):
        r = parse("$x = function($a) {};")
        assert r == Block([Stmt(Assignment(NamedVariable("x"),
                                           LambdaDecl(False, [Argument("a")],
                                                      None, Block([]), False,
                                                      0)))])

    def test_lambda_function_closure(self):
        r = parse("$x = function($a) use ($c, $b) {};")
        assert r == Block([Stmt(Assignment(
            NamedVariable("x"),
            LambdaDecl(
                False, [Argument("a")],
                ListOfVars([
                    NamedVariable("c"),
                    NamedVariable("b")]),
                Block([]), False,
                0)))])

    def test_closure_with_ref(self):
        r = parse("$x = function($a) use ($c, &$b) {};")
        assert r == Block([Stmt(
            Assignment(
                NamedVariable("x"),
                LambdaDecl(
                    False,
                    [Argument("a")],
                    ListOfVars([NamedVariable("c"),
                                Reference(NamedVariable("b"))]),
                    Block([]), False,
                    0)))])

    def test_static_member_double_getitem(self):
        r = parse("$x::$xyz[$a][$b];")
        expected = Block([Stmt(GetItem(
            GetItem(
                StaticMember(NamedVariable("x"), ConstantStr("xyz")),
                NamedVariable("a")),
            NamedVariable("b")))])
        assert r == expected

    def test_reserved_names_in_properties(self):
        r = parse("$x->interface")
        assert r == Block([Stmt(GetAttr(NamedVariable("x"),
                                        ConstantStr("interface")))])

    def test_heredoc(self):
        r = parse("""print <<<ENDOFHEREDOC
This is a heredoc test.
ENDOFHEREDOC;
""")
        assert r == Block([Stmt(Print(
            ConstantStr("This is a heredoc test.", 1)))])

    def test_heredoc_with_dollar(self):
        r = parse("""print <<<ENDOFHEREDOC
This is a heredoc with quoted dollar "$".
ENDOFHEREDOC;
""")
        assert r == Block([Stmt(Print(
            ConstantStr("This is a heredoc with quoted dollar \"$\".", 1)))])

    def test_index_function_result(self):
        r = parse('f()[0][1];')
        assert r == Block([Stmt(GetItem(GetItem(
            SimpleCall(RelativeName(['f']), []),
            ConstantInt(0)), ConstantInt(1)))])

    def test_index_method_result(self):
        r = parse('$x->f()[0][1];')
        assert r == Block([Stmt(GetItem(GetItem(
            SimpleCall(
                GetAttr(NamedVariable('x'), ConstantStr('f')), []),
            ConstantInt(0)), ConstantInt(1)))])

    def test_new_in_parenthesis(self):
        r = parse('(new Foo())->method();')
        assert r == Block([Stmt(
            SimpleCall(
                GetAttr(
                    New(RelativeName(['Foo']), []),
                    ConstantStr('method')),
                [])
        )])

    def test_indexed_new(self):
        r = parse('(new Foo())[1][2];')
        assert r == Block([Stmt(
            GetItem(
                GetItem(
                    New(RelativeName(['Foo']), []),
                    ConstantInt(1)),
                ConstantInt(2))
        )])

    def test_new_something(self):
        r = parse('$x->a()->x = 3')
        assert r == Block([Stmt(
            Assignment(
                GetAttr(
                    SimpleCall(GetAttr(NamedVariable("x"), ConstantStr("a")),
                               []),
                    ConstantStr("x")),
                ConstantInt(3)))])

    def test_logical_not(self):
        r = parse("!1 && 2;")
        assert r == Block([Stmt(
            And(PrefixOp("!", ConstantInt(1)), ConstantInt(2)))])

    def test_lineno_multiline_string(self):
        r = parse("'string\nstring' + 3;")
        assert r.stmts[0].expr.right.lineno == 1

    def test_instanceof(self):
        r = parse("$x instanceof $y")
        assert r == Block([Stmt(
            InstanceOf(NamedVariable('x'),
                       GetClass(NamedVariable('y'), complain=False)))])

    def test_instanceof_2(self):
        r = parse("$x instanceof $y->name")
        assert r == Block([Stmt(
            InstanceOf(
                NamedVariable('x'),
                GetClass(GetAttr(NamedVariable('y'), ConstantStr('name')),
                         complain=False)))])

    def test_namespace_statement(self):
        r = parse("namespace Foo\\Bar;")
        assert r == Block([BeginNamespace(RelativeName(['Foo', 'Bar']))])

    def test_use(self):
        r = parse("use A\\B, C;")
        assert r == Block([Use([
            UseDeclaration(RelativeName(["A", "B"])),
            UseDeclaration(RelativeName(["C"]))])])
        r = parse("use A\\B as C;")
        assert r == Block([Use([
            UseDeclaration(RelativeName(["A", "B"]), "C")])])
        r = parse("use \\A\\B, C;")
        assert r == Block([Use([
            UseDeclaration(AbsoluteName(["A", "B"])),
            UseDeclaration(RelativeName(["C"]))])])
        r = parse("use \\A\\B as C;")
        assert r == Block([Use([
            UseDeclaration(AbsoluteName(["A", "B"]), "C")])])

    def test_dollar_at_the_end(self):

        r = parse_doublequoted("xyz $a $")
        assert r == DoubleQuotedStr([ConstantStr("xyz "), NamedVariable("a"), ConstantStr(" $")])

        r = parse_doublequoted("xyz $a asd$")
        assert r == DoubleQuotedStr([ConstantStr("xyz "), NamedVariable("a"), ConstantStr(" asd$")])

        r = parse_doublequoted("xyz $a asd$")
        assert r == DoubleQuotedStr([ConstantStr("xyz "), NamedVariable("a"), ConstantStr(" asd$")])

        r = parse_doublequoted("xyz ${a} $")
        assert r == DoubleQuotedStr([ConstantStr("xyz "), NamedVariable("a"), ConstantStr(" $")])

        r = parse_doublequoted("xyz ${a}$")
        assert r == DoubleQuotedStr([ConstantStr("xyz "), NamedVariable("a"), ConstantStr("$")])

        r = parse_doublequoted("xyz ${a} asd$")
        assert r == DoubleQuotedStr([ConstantStr("xyz "), NamedVariable("a"), ConstantStr(" asd$")])

    def test_parse_error_no_token_name(self):
        with raises(ParseError) as excinfo:
            parse('$foo=;')
        assert excinfo.value.message == "syntax error, unexpected ';' in <input>"

    def test_parse_error_with_token_name(self):
        with raises(ParseError) as excinfo:
            parse('1->2;')
        assert excinfo.value.message == "syntax error, unexpected '->' (T_OBJECT_OPERATOR) in <input>"
