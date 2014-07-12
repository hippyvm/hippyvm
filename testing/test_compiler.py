from py.test import raises
import py
from hippy.objects.intobject import W_IntObject
from hippy.sourceparser import parse
from hippy.astcompiler import compile_ast, bc_preprocess, CompilerContext
from hippy.ast import CompilerError, PLACEHOLDER, DelayedHash
from hippy.objspace import ObjSpace, getspace, ExecutionContext
from hippy.constants import E_HIPPY_WARN
from hippy.objects import reference, floatobject
from hippy.objects.strobject import W_ConstStringObject
from hippy import consts, klass, function


def test_encoding_decoding_arg():
    one_byte = [0, 1, 37, 127]
    two_bytes = [128, 278, 8941, 16383]
    three_bytes = [16384, 893478, 2097151]
    four_bytes = [2097152, 268435455]
    five_bytes = [268435456, 2147483647]
    for length, tests in [(1, one_byte), (2, two_bytes), (3, three_bytes),
                          (4, four_bytes), (5, five_bytes)]:
        for arg in tests:
            ctx = CompilerContext('fname', [], 0, None)
            ctx.emit(consts.LOAD_CONST, arg)
            assert ctx.data[0] == chr(consts.LOAD_CONST)
            assert len(ctx.data) == 1 + length
            ctx.emit(consts.RETURN)   # to fix the stack in this test
            bc = ctx.create_bytecode()
            pc, value = bc.next_arg(1)
            assert pc == 1 + length
            assert value == arg

def test_patch_pos():
    ctx = CompilerContext('fname', [], 0, None)
    ctx.emit(consts.JUMP_FORWARD, PLACEHOLDER)
    assert ctx.data[0] == chr(consts.JUMP_FORWARD)
    assert len(ctx.data) == 1 + 3
    pos = ctx.get_pos()
    ctx.emit(consts.JUMP_FORWARD, 12)
    assert len(ctx.data) == 1 + 3 + 2
    ctx.patch_pos(pos)
    assert ctx.data == list(chr(consts.JUMP_FORWARD) + '\x86\x81\x01' +
                            chr(consts.JUMP_FORWARD) + '\x0C')

class FakeInterpreter(object):
    def __init__(self, log):
        self.msgs = log

    def log_error(self, level, msg):
        assert level == E_HIPPY_WARN
        self.msgs.append(("HIPPY WARNING", msg))

class TestCompiler(object):
    def check_compile(self, source, expected=None, expected_warnings=[],
                      **kwds):

        self.space = ObjSpace()
        self.log = []
        self.space.ec = ExecutionContext(self.space)
        self.space.ec.interpreter = FakeInterpreter(self.log)
        ast = parse(self.space, source, startlineno=1, filename='<input>')
        bc = compile_ast('<input>', source, ast, self.space, **kwds)
        assert self.log == expected_warnings
        if expected is not None:
            self.compare(bc, expected)
        return bc

    def compare(self, bc, expected):
        expected = bc_preprocess(expected)
        bcdump = bc.dump()
        bcdump = bcdump.splitlines()
        expected = expected.splitlines()
        maxlen = max(len(expected), len(bcdump))
        expected += ['' * (maxlen - len(expected))]
        bcdump += ['' * (maxlen - len(bcdump))]
        print "Got:" + " "*26 + "Expected:"
        for bcline, expline in zip(bcdump, expected):
            print "%s%s %s" % (bcline, " " * (30 - len(bcline)),
                                expline)
            bcline = bcline.split()
            expline = expline.split()
            # we fail if the line we got is different than the expected line,
            # possibly after removing the first word (the index number)
            if bcline != expline and bcline[1:] != expline:
                assert False

    def test_assign(self):
        bc = self.check_compile("$x = 3;", """
        VAR_PTR 0
        LOAD_CONST 0
        STORE
        DISCARD_TOP
        """)
        c = bc.consts[0]
        assert isinstance(c, W_IntObject)
        assert c.intval == 3
        assert bc.stackdepth == 1

    def test_assign_nonconst(self):
        bc = self.check_compile("$x = $y;", """
        VAR_PTR 0
        LOAD_VAR 1
        STORE
        DISCARD_TOP
        """)
        assert bc.stackdepth == 1

    def test_addition(self):
        self.check_compile("3 + $x;", """
        LOAD_CONST 0
        LOAD_VAR 0
        BINARY_ADD
        DISCARD_TOP
        """)

    def test_substraction(self):
        self.check_compile("3 - $x;", """
        LOAD_CONST 0
        LOAD_VAR 0
        BINARY_SUB
        DISCARD_TOP
        """)

    def test_mul(self):
        self.check_compile("3 - $x * 3;", """
        LOAD_CONST 0
        LOAD_CONST 0
        LOAD_VAR_SWAP 0
        BINARY_MUL
        BINARY_SUB
        DISCARD_TOP
        """)

    def test_echo(self):
        bc = self.check_compile("echo 3;", """
        LOAD_CONST 0
        ECHO
        """)
        assert bc.stackdepth == 1

    def test_float_const(self):
        bc = self.check_compile("echo 3.5;", """
        LOAD_CONST 0
        ECHO
        """)
        assert bc.consts[0].floatval == 3.5

    def test_echo_2(self):
        bc = self.check_compile("echo $x, $y;", """
        LOAD_VAR 0
        ECHO
        LOAD_VAR 1
        ECHO
        """)
        assert bc.stackdepth == 1

    def test_unary_minus(self):
        self.check_compile("-$x;+$y;", """
        LOAD_VAR 0
        UNARY_MINUS
        DISCARD_TOP
        LOAD_VAR 1
        UNARY_PLUS
        DISCARD_TOP
        """)

    def test_bitwise_not(self):
        self.check_compile("~$x;", """
        LOAD_VAR 0
        BITWISE_NOT
        DISCARD_TOP
        """)

    def test_uplusplus(self):
        self.check_compile("echo ++$x;", """
        VAR_PTR 0
        PREFIX_PLUSPLUS
        ECHO
        """)

    def test_float_const_cache(self):
        bc = self.check_compile("echo 3.5 + 3.5;", """
        LOAD_CONST 0
        LOAD_CONST 0
        BINARY_ADD
        ECHO
        """)
        assert bc.consts[0].floatval == 3.5

    def test_if(self):
        bc = self.check_compile("""
        if (1) {
          $x = 1;
        }
        echo $x;
        """, """
        LOAD_CONST 0
        JUMP_IF_FALSE 12
        VAR_PTR 0
        LOAD_CONST 0
        STORE
        DISCARD_TOP
     12 LOAD_VAR 0
        ECHO
        """)
        assert bc.stackdepth == 1

    def test_ifelse(self):
        bc = self.check_compile("""
        if (1) {
          $x = 1;
        } else {
          $x = 1 + 3;
        }
        echo $x;
        """, """
        LOAD_CONST 0
        JUMP_IF_FALSE 16
        VAR_PTR 0
        LOAD_CONST 0
        STORE
        DISCARD_TOP
        JUMP_FORWARD 25
     16 VAR_PTR 0
        LOAD_CONST 0
        LOAD_CONST 1
        BINARY_ADD
        STORE
        DISCARD_TOP
     25 LOAD_VAR 0
        ECHO
        """)
        assert bc.stackdepth == 2

    def test_ifelseif(self):
        self.check_compile("""
        if (1) {
          $x = 1;
        } elseif (2) {
          $x = 2;
        }
        echo $x;
        """, """
        LOAD_CONST 0
        JUMP_IF_FALSE 16
        VAR_PTR 0
        LOAD_CONST 0
        STORE
        DISCARD_TOP
        JUMP_FORWARD 28
     16 LOAD_CONST 1
        JUMP_IF_FALSE 28
        VAR_PTR 0
        LOAD_CONST 1
        STORE
        DISCARD_TOP
     28 LOAD_VAR 0
        ECHO
        """)

    def test_ifelseif_else(self):
        self.check_compile("""
        if (1) {
          $x = 1;
        } elseif (2) {
          $x = 2;
        } else {
          $x = 3;
        }
        echo $x;
        """, """
        LOAD_CONST 0
        JUMP_IF_FALSE 16
        VAR_PTR 0
        LOAD_CONST 0
        STORE
        DISCARD_TOP
        JUMP_FORWARD 38
     16 LOAD_CONST 1
        JUMP_IF_FALSE 32
        VAR_PTR 0
        LOAD_CONST 1
        STORE
        DISCARD_TOP
        JUMP_FORWARD 38
     32 VAR_PTR 0
        LOAD_CONST 2
        STORE
        DISCARD_TOP
     38 LOAD_VAR 0
        ECHO
        """)

    def test_while(self):
        self.check_compile("""
        $i = 0;
        while ($i < 3)
          $i++;
        """, """
        VAR_PTR 0
        LOAD_CONST 0
        STORE
        DISCARD_TOP
      6 _CHECKSTACK 0
        LOAD_CONST 1
        LOAD_VAR_SWAP 0
        BINARY_LT
        JUMP_IF_FALSE 23
        VAR_PTR 0
        SUFFIX_PLUSPLUS
        DISCARD_TOP
        JUMP_BACKWARD 6
     23 _CHECKSTACK 0
        """)

    def test_function_call(self):
        bc = self.check_compile("""
        cos($i, $j, $k);
        """, """
        LOAD_NAME 0
        GETFUNC
        VAR_PTR 0
        ARG_BY_PTR 0
        VAR_PTR 1
        ARG_BY_PTR 1
        VAR_PTR 2
        ARG_BY_PTR 2
        CALL 3
        DISCARD_TOP
        """)
        assert bc.stackdepth == 4

    def test_function_call_nonref_arg(self):
        bc = self.check_compile("""
        f($i+2, $j);
        """, """
        LOAD_NAME 0
        GETFUNC
        LOAD_CONST 0
        LOAD_VAR_SWAP 0
        BINARY_ADD
        ARG_BY_VALUE 0
        VAR_PTR 1
        ARG_BY_PTR 1
        CALL 2
        DISCARD_TOP
        """)
        assert bc.stackdepth == 3

    def test_function_call_mayberef_arg(self):
        self.check_compile("""
        f($a[5]);
        """, """
        LOAD_NAME 0
        GETFUNC
        VAR_PTR 0
        LOAD_CONST 0
        ITEM_PTR
        ARG_BY_PTR 0
        CALL 1
        DISCARD_TOP
        """)

    def test_for(self):
        self.check_compile("""
        for ($i = 0; $i < 10; $i++) {$k++;}
        """, """
        VAR_PTR 0
        LOAD_CONST 0
        STORE
        DISCARD_TOP
      6 LOAD_CONST 1
        LOAD_VAR_SWAP 0
        BINARY_LT
        JUMP_IF_FALSE 27
        VAR_PTR 1
        SUFFIX_PLUSPLUS
        DISCARD_TOP
        _CHECKSTACK 0
        VAR_PTR 0
        SUFFIX_PLUSPLUS
        DISCARD_TOP
        JUMP_BACKWARD 6
     27 _CHECKSTACK 0
        """)

    def test_long_for(self):
        source = ["for ($i = 0; $i < 3; $i++) {"]
        for i in range(100):
            source.append("$j = 1;")
        source.append("}")
        source = "".join(source)
        space = getspace()
        ast = parse(space, source, i, '<input>')
        compile_ast('<input>', source, ast, None)
        # assert did not crash

    def test_constant_str(self):
        self.check_compile('$x = "abc"; echo $x . $x;', """
        VAR_PTR 0
        LOAD_NAME 0
        STORE
        DISCARD_TOP
        LOAD_VAR 0
        LOAD_VAR_SWAP 0
        BINARY_CONCAT
        ECHO
        """)

    def test_str_consts_preprocessed(self):
        bc = self.check_compile('$x = "\\n"; $y = "$x";', """
        VAR_PTR 0
        LOAD_NAME 0
        STORE
        DISCARD_TOP
        VAR_PTR 1
        LOAD_VAR 0
        LOAD_CONST 0
        INTERPOLATE 1
        STORE
        DISCARD_TOP
        """)
        assert bc.names[0] == '\n';

    def test_getitem_setitem(self):
        self.check_compile("$x[3]; $x[3] = 1;", """
        LOAD_CONST 0
        GETITEM_VAR 0
        DISCARD_TOP
        VAR_PTR 0
        LOAD_CONST 0
        ITEM_PTR
        LOAD_CONST 1
        STORE
        DISCARD_TOP
        """)

    def test_getitem_2(self):
        self.check_compile("$x[$y-1][$z+5];", """
        LOAD_CONST 0
        LOAD_VAR_SWAP 0
        BINARY_SUB     # $y-1
        GETITEM_VAR 1
        LOAD_CONST 1
        LOAD_VAR_SWAP 2
        BINARY_ADD     # $z+5
        GETITEM
        DISCARD_TOP
        """)

    def test_setitem_2(self):
        self.check_compile("$x[$y-1][$z+5] = 1;", """
        VAR_PTR 0
        LOAD_CONST 0
        LOAD_VAR_SWAP 1
        BINARY_SUB     # $y-1
        ITEM_PTR
        LOAD_CONST 1
        LOAD_VAR_SWAP 2
        BINARY_ADD     # $z+5
        ITEM_PTR
        LOAD_CONST 0
        STORE
        DISCARD_TOP
        """)

    def test_setitem_3(self):
        self.check_compile("$x[$i] = 1;", """
        VAR_PTR 0
        LOAD_VAR_ITEM_PTR 1
        LOAD_CONST 0
        STORE
        DISCARD_TOP
        """)

    def test_array_constructor(self):
        self.check_compile("$x = array(1, 2, $y);", """
        VAR_PTR 0
        LOAD_CONST 0
        DEREF
        LOAD_CONST 1
        DEREF
        LOAD_VAR 1
        DEREF
        MAKE_ARRAY 3
        STORE_UNIQUE
        DISCARD_TOP
        """)

    def test_getitem_2_reference(self):
        self.check_compile("$a = & $b[0][0];", """
        VAR_PTR 0
        LOAD_CONST 0
        ITEM_PTR
        LOAD_CONST 0
        ITEM_PTR
        RESOLVE_FOR_WRITING
        SET_FAST 1
        DISCARD_TOP
        """)

    def test_function_decl(self):
        bc = self.check_compile("""\
        // hi there
        function f($a, &$b, $c) { return $a + $b + $c; }""", "")
        assert bc.functions[0].types == [consts.ARG_ARGUMENT,
                                              consts.ARG_REFERENCE,
                                              consts.ARG_ARGUMENT]
        assert bc.functions[0].names == ['a', 'b', 'c']
        assert bc.startlineno == 1
        self.compare(bc.functions[0].bytecode, """
        LOAD_VAR 1
        LOAD_VAR_SWAP 0
        BINARY_ADD
        LOAD_VAR 2
        BINARY_ADD
        DEREF
        RETURN
        LOAD_NULL   # unreachable
        RETURN
        """)
        assert bc.functions[0].bytecode.startlineno == 2
        assert bc.functions[0].bytecode.name == 'f'

    def test_function_decl_2(self):
        bc = self.check_compile("""
        function f() { return; }""", "")
        assert bc.functions[0].types == []
        self.compare(bc.functions[0].bytecode, """
        LOAD_NULL
        RETURN
        LOAD_NULL   # unreachable
        RETURN
        """)

    def test_function_decl_warning(self):
        bc = self.check_compile("""
        function f($a, &$a) { }""", expected_warnings=[
            ("HIPPY WARNING", "Argument list contains twice '$a'")])

    def test_append(self):
        self.check_compile("""
        $a[] = $b;
        """, """
        VAR_PTR 0
        APPEND_PTR
        LOAD_VAR 1
        STORE
        DISCARD_TOP
        """)

    def test_append_reference(self):
        self.check_compile("""
        $a = &$b[];
        """, """
        VAR_PTR 0
        APPEND_PTR
        RESOLVE_FOR_WRITING
        SET_FAST 1
        DISCARD_TOP
        """)

    def test_reference_append(self):
        self.check_compile("""
        $a[] = &$b;
        """, """
        VAR_PTR 0
        RESOLVE_FOR_WRITING
        VAR_PTR 1
        APPEND_PTR
        STORE_REF
        DISCARD_TOP
        """)

    def test_append_invalid(self):
        with raises(CompilerError):
            self.check_compile("$x[];")
        with raises(CompilerError):
            self.check_compile("echo $x[];")
        with raises(CompilerError):
            self.check_compile("$a = $x[];")
        with raises(CompilerError):
            self.check_compile("isset($x[]);")
        with raises(CompilerError):
            self.check_compile("unset($x[]);")


    def test_and(self):
        self.check_compile("""
        $a && $b;
        """, """
        LOAD_VAR 0
        IS_TRUE
        JUMP_IF_FALSE_NO_POP 11
        DISCARD_TOP
        LOAD_VAR 1
        IS_TRUE
     11 DISCARD_TOP
        """)

    def test_and_or_forced_parenthesis(self):
        self.check_compile("""
        $a && ($b || $c);
        """, """
        LOAD_VAR 0
        IS_TRUE
        JUMP_IF_FALSE_NO_POP 20
        DISCARD_TOP
        LOAD_VAR 1
        IS_TRUE
        JUMP_IF_TRUE_NO_POP 19
        DISCARD_TOP
        LOAD_VAR 2
        IS_TRUE
     19 IS_TRUE
     20 DISCARD_TOP
        """)

    def test_and_or_default_precedence(self):
        self.check_compile("""
        $a && $b || $c;
        """, """
        LOAD_VAR 0
        IS_TRUE
        JUMP_IF_FALSE_NO_POP 11
        DISCARD_TOP
        LOAD_VAR 1
        IS_TRUE
     11 IS_TRUE
        JUMP_IF_TRUE_NO_POP 20
        DISCARD_TOP
        LOAD_VAR 2
        IS_TRUE
     20 DISCARD_TOP
        """)

    def test_xor(self):
        self.check_compile("$a xor $b; $a ^ $b;", """
        LOAD_VAR 0
        LOAD_VAR_SWAP 1
        LOGICAL_XOR
        DISCARD_TOP
        LOAD_VAR 0
        LOAD_VAR_SWAP 1
        BINARY_XOR
        DISCARD_TOP
        """)

    def test_inplace_add(self):
        self.check_compile("""
        $a += 2;
        """, """
        VAR_PTR 0
        PTR_DEREF
        LOAD_CONST 0
        BINARY_ADD
        STORE
        DISCARD_TOP
        """)

    def test_global(self):
        self.check_compile("""
        global $a, $b, $c;
        """, """
        DECLARE_GLOBAL 0
        DECLARE_GLOBAL 1
        DECLARE_GLOBAL 2
        """)

    def test_constant(self):
        self.check_compile("""
        $x = c;
        """, """
        VAR_PTR 0
        LOAD_NAMED_CONSTANT 0
        STORE
        DISCARD_TOP
        """)

    def test_dowhile(self):
        self.check_compile("""
        do { 1; } while (2);
        """, """
      0 _CHECKSTACK 0
        LOAD_CONST 0
        DISCARD_TOP
        LOAD_CONST 1
        JUMP_BACK_IF_TRUE 0
        _CHECKSTACK 0
        """)

    def test_reference_simple(self):
        self.check_compile("""
        $b; $a = &$b;
        """, """
        LOAD_VAR 0
        DISCARD_TOP
        VAR_PTR 0
        RESOLVE_FOR_WRITING
        SET_FAST 1
        DISCARD_TOP
        """)

    def test_reference_left_array(self):
        self.check_compile("""
        $b; $a[5][6][7] =& $b;
        """, """
        LOAD_VAR 0
        DISCARD_TOP
        VAR_PTR 0
        RESOLVE_FOR_WRITING
        VAR_PTR 1
        LOAD_CONST 0
        ITEM_PTR
        LOAD_CONST 1
        ITEM_PTR
        LOAD_CONST 2
        ITEM_PTR
        STORE_REF
        DISCARD_TOP
        """)

    def test_reference_right_array(self):
        self.check_compile("""
        $b; $a =& $b[7][8];
        """, """
        LOAD_VAR 0
        DISCARD_TOP
        VAR_PTR 0
        LOAD_CONST 0
        ITEM_PTR
        LOAD_CONST 1
        ITEM_PTR
        RESOLVE_FOR_WRITING
        SET_FAST 1
        DISCARD_TOP
        """)

    def test_reference_both_left_right_array(self):
        self.check_compile("""
        $b+0; $a[0] =& $b[1];
        """, """
        LOAD_CONST 0
        LOAD_VAR_SWAP 0
        BINARY_ADD
        DISCARD_TOP
        VAR_PTR 0
        LOAD_CONST 1
        ITEM_PTR
        RESOLVE_FOR_WRITING
        VAR_PTR 1
        LOAD_CONST 0
        ITEM_PTR
        STORE_REF
        DISCARD_TOP
        """)

    def test_reference_indirect(self):
        self.check_compile("$$a =& $$b;", """
        LOAD_VAR 0
        VAR_INDIRECT_PTR
        RESOLVE_FOR_WRITING
        LOAD_VAR 1
        SET_REF_INDIRECT
        DISCARD_TOP
        """)

    def test_break(self):
        self.check_compile("""
        while (1) {
           break;
        }
        """, """
      0 _CHECKSTACK 0
        LOAD_CONST 0
        JUMP_IF_FALSE 14
        JUMP_FORWARD 14
        JUMP_BACKWARD 0
     14 _CHECKSTACK 0
        """)

    def test_continue(self):
        self.check_compile("""
        while (1) {
           continue;
        }
        """, """
      0 _CHECKSTACK 0
        LOAD_CONST 0
        JUMP_IF_FALSE 12
        JUMP_BACKWARD 0
        JUMP_BACKWARD 0
     12 _CHECKSTACK 0
        """)

    def test_for_continue(self):
        self.check_compile("""
        for ($x = 0; $x < 10; $x++) {
           continue;
        }
        """, """
        VAR_PTR 0
        LOAD_CONST 0
        STORE
        DISCARD_TOP
      6 LOAD_CONST 1
        LOAD_VAR_SWAP 0
        BINARY_LT
        JUMP_IF_FALSE 27
        JUMP_FORWARD 19
     19 _CHECKSTACK 0
        VAR_PTR 0
        SUFFIX_PLUSPLUS
        DISCARD_TOP
        JUMP_BACKWARD 6
     27 _CHECKSTACK 0
        """)

    def test_break_for(self):
        self.check_compile("""
        for(1;1;1) {
           break;
        }
        """, """
        LOAD_CONST 0
        DISCARD_TOP
      3 LOAD_CONST 0
        JUMP_IF_FALSE 20
        JUMP_FORWARD 20
        _CHECKSTACK 0
        LOAD_CONST 0
        DISCARD_TOP
        JUMP_BACKWARD 3
     20 _CHECKSTACK 0
        """)

    def test_break_do_while(self):
        self.check_compile("""
        do {
           break;
        } while(1);
        """, """
      0 _CHECKSTACK 0
        JUMP_FORWARD 10
        LOAD_CONST 0
        JUMP_BACK_IF_TRUE 0
     10 _CHECKSTACK 0
        """)

    def test_break_do_while_continue(self):
        self.check_compile("""
        do {
           continue;
        } while(1);
        """, """
      0 _CHECKSTACK 0
        JUMP_BACKWARD 0
        LOAD_CONST 0
        JUMP_BACK_IF_TRUE 0
      8 _CHECKSTACK 0
        """)

    def test_if_expr(self):
        self.check_compile("""
        $a = 0 ? 5 : 10;
        """, """
        VAR_PTR 0
        LOAD_CONST 0
        JUMP_IF_FALSE 15
        LOAD_CONST 1
        JUMP_FORWARD 17
        DISCARD_TOP      # dead code, to fix the stack depth
     15 LOAD_CONST 2
     17 STORE
        DISCARD_TOP
        """)

    def test_iterator_1(self):
        bc = self.check_compile("""
        foreach ($a as $b) {$b+1;}
        """, """
        LOAD_VAR 0
        CREATE_ITER
      3 _CHECKSTACK 1
        NEXT_VALUE_ITER 21
        VAR_PTR 1
        STORE
        DISCARD_TOP
        LOAD_CONST 0       # start of the code within the { }
        LOAD_VAR_SWAP 1
        BINARY_ADD
        DISCARD_TOP
        JUMP_BACKWARD 3
     21 _CHECKSTACK 1
        DISCARD_TOP
        """)
        assert bc.stackdepth == 3

    def test_iterator_2(self):
        bc = self.check_compile("""
        foreach ($a as $b => $c) {$b;}
        """, """
        LOAD_VAR 0
        CREATE_ITER
      3 _CHECKSTACK 1
        NEXT_ITEM_ITER 22
        VAR_PTR 1           # store first $c
        STORE
        DISCARD_TOP
        VAR_PTR 2           # then store $b
        STORE
        DISCARD_TOP
        LOAD_VAR 2          # start of the code within the { }
        DISCARD_TOP
        JUMP_BACKWARD 3
     22 _CHECKSTACK 1
        DISCARD_TOP
        """)
        assert bc.stackdepth == 3

    def test_iterator_3(self):
        bc = self.check_compile("""
        foreach ($a as $b[0][1]) {$b+1;}
        """, """
        LOAD_VAR 0
        CREATE_ITER
      3 _CHECKSTACK 1
        NEXT_VALUE_ITER 27
        VAR_PTR 1
        LOAD_CONST 0
        ITEM_PTR
        LOAD_CONST 1
        ITEM_PTR
        STORE
        DISCARD_TOP
        LOAD_CONST 1       # start of the code within the { }
        LOAD_VAR_SWAP 1
        BINARY_ADD
        DISCARD_TOP
        JUMP_BACKWARD 3
     27 _CHECKSTACK 1
        DISCARD_TOP
        """)
        assert bc.stackdepth == 3

    def test_iterator_continue(self):
        bc = self.check_compile("""
        foreach ($a as $b) {continue;}
        """, """
        LOAD_VAR 0
        CREATE_ITER
      3 _CHECKSTACK 1
        NEXT_VALUE_ITER 17
        VAR_PTR 1
        STORE
        DISCARD_TOP
        JUMP_BACKWARD 3     # continue;
        JUMP_BACKWARD 3
     17 _CHECKSTACK 1
        DISCARD_TOP
        """)

    def test_iterator_ref_1(self):
        bc = self.check_compile("""
        foreach ($a as &$b) {$b+=1;}
        """, """
        VAR_PTR 0
        RESOLVE_FOR_WRITING
        CREATE_ITER_REF
      4 _CHECKSTACK 1
        NEXT_VALUE_ITER 23
        SET_FAST 1
        DISCARD_TOP
        VAR_PTR 1          # start of the code within the { }
        PTR_DEREF
        LOAD_CONST 0
        BINARY_ADD
        STORE
        DISCARD_TOP
        JUMP_BACKWARD 4
     23 _CHECKSTACK 1
        DISCARD_TOP
        """)
        assert bc.stackdepth == 3

    def test_iterator_ref_2(self):
        bc = self.check_compile("""
        foreach ($a as $k=>&$b[5][5]) {$b;}
        """, """
        VAR_PTR 0
        RESOLVE_FOR_WRITING
        CREATE_ITER_REF
      4 _CHECKSTACK 1
        NEXT_ITEM_ITER 29
        VAR_PTR 1           # store the value as reference into $b[5][5]
        LOAD_CONST 0
        ITEM_PTR
        LOAD_CONST 0
        ITEM_PTR
        STORE_REF
        DISCARD_TOP
        VAR_PTR 2           # then store the key into $k
        STORE
        DISCARD_TOP
        LOAD_VAR 1          # start of the code within the { }
        DISCARD_TOP
        JUMP_BACKWARD 4
     29 _CHECKSTACK 1
        DISCARD_TOP
        """)
        assert bc.stackdepth == 4

    def test_array_cast(self):
        self.check_compile("""
        (array)3;
        """, """
        LOAD_CONST 0
        CAST_ARRAY
        DISCARD_TOP
        """)

    def test_dynamic_call(self):
        self.check_compile("""
        $a = 'func';
        $a(3, 4);
        """, """
        VAR_PTR 0
        LOAD_NAME 0
        STORE
        DISCARD_TOP
        LOAD_VAR 0
        GETFUNC
        LOAD_CONST 0
        ARG_BY_VALUE 0
        LOAD_CONST 1
        ARG_BY_VALUE 1
        CALL 2
        DISCARD_TOP
        """)

    def test_lineno_mapping(self):
        bc = self.check_compile("""\
        1;
        2;
        3;
        """)
        assert bc.bc_mapping[0] == 1
        assert bc.bc_mapping[4] == 2
        assert bc.bc_mapping[8] == 3

    def test_make_hash(self):
        bc = self.check_compile("""
        array(1=>$a);
        """, """
        LOAD_CONST 0
        LOAD_VAR 0
        DEREF
        SWAP
        DEREF
        MAKE_HASH 1
        DISCARD_TOP
        """)
        assert bc.stackdepth == 2

    def test_make_hash_const(self):
        bc = self.check_compile("""
        array(1=>2, 5=>null, 6=>true, 4=>3.5, 'abc'=>'def',
              'h'=>false);
        """, """
        LOAD_CONST 0
        DISCARD_TOP
        """)
        assert bc.stackdepth == 1
        arr = bc.consts[0]
        assert isinstance(arr, DelayedHash)
        assert ((W_ConstStringObject('abc'), W_ConstStringObject('def')) in
                arr.pairs)

    def test_make_array_ref(self):
        self.check_compile("""
        array(&$a);
        """, """
        VAR_PTR 0
        RESOLVE_FOR_WRITING
        MAKE_ARRAY 1
        DISCARD_TOP
        """)

    def test_make_hash_ref(self):
        self.check_compile("""
        array(5=>&$a);
        """, """
        LOAD_CONST 0
        VAR_PTR 0
        RESOLVE_FOR_WRITING
        SWAP
        DEREF
        MAKE_HASH 1
        DISCARD_TOP
        """)

    def test_extra_offset(self):
        bc = self.check_compile("""\
        1;
        2;
        """, """
        LOAD_CONST 0
        DISCARD_TOP
        LOAD_CONST 1
        DISCARD_TOP
        """)
        assert bc.bc_mapping == [1, 1, 1, 2, 2, 2]

    def test_declare_static(self):
        self.check_compile("""
        static $a;
        """, """
        LOAD_STATIC 0      # loads a reference
        SET_FAST 0         # store it into $a
        DISCARD_TOP
        """)

    def test_initialized_static(self):
        from hippy.astcompiler import ConstantMarker
        bc = self.check_compile("""
        static $a = 17.5;
        """, """
        LOAD_STATIC 0      # loads a reference
        SET_FAST 0         # store it into $a
        DISCARD_TOP
        """)
        assert isinstance(bc.consts[0], ConstantMarker)
        assert bc.static_vars[bc.consts[0]].floatval == 17.5

    def test_static_warn(self):
        bc = self.check_compile(
            "static $a, $a;",
            expected_warnings=[('HIPPY WARNING',
                                "Static variable 'a' declared twice, "
                                "ignoring previous declaration")])

    def test_print_exprs(self):
        bc = self.check_compile("$x = 3;", """
        VAR_PTR 0
        LOAD_CONST 0
        STORE
        PRINT_EXPR
        """, print_exprs=True)
        c = bc.consts[0]
        assert isinstance(c, W_IntObject)
        assert c.intval == 3
        assert bc.stackdepth == 1

    def test_mixed_case(self):
        self.check_compile("array(nUll);", """
        LOAD_CONST 0
        DISCARD_TOP
        """)

    def test_unset(self):
        self.check_compile("unset($a, $b[5][6][7], $$c);", """
        UNSET_FAST 0
        VAR_PTR 1
        LOAD_CONST 0
        ITEM_PTR
        LOAD_CONST 1
        ITEM_PTR
        LOAD_CONST 2
        ITEM_PTR
        PTR_UNSET
        LOAD_VAR 2
        UNSET_VAR_INDIRECT
        """)

    def test_isset(self):
        self.check_compile("$c = isset($a, $b[5][6][7]);", """
        VAR_PTR 0
        VAR_PTR 1
        PTR_ISSET
        IS_TRUE
        JUMP_IF_FALSE_NO_POP 24
        DISCARD_TOP
        VAR_PTR 2
        LOAD_CONST 0
        ITEM_PTR
        LOAD_CONST 1
        ITEM_PTR
        LOAD_CONST 2
        ITEM_PTR
        PTR_ISSET
        IS_TRUE
     24 STORE
        DISCARD_TOP
        """)

    def test_empty(self):
        self.check_compile("$c = empty($b[5]);", """
        VAR_PTR 0
        VAR_PTR 1
        LOAD_CONST 0
        ITEM_PTR
        PTR_EMPTY
        STORE
        DISCARD_TOP
        """)

    def test_GLOBALS_1(self):
        self.check_compile("$GLOBALS['a'] = 42;", """
        VAR_PTR 0
        LOAD_NAME 0
        ITEM_PTR
        LOAD_CONST 0
        STORE
        DISCARD_TOP
        """)

    def test_GLOBALS_2(self):
        self.check_compile("$GLOBALS['a'] = &$x;", """
        VAR_PTR 0
        RESOLVE_FOR_WRITING
        VAR_PTR 1
        LOAD_NAME 0
        ITEM_PTR
        STORE_REF
        DISCARD_TOP
        """)

    def test_const_statement(self):
        self.check_compile("const x = 42;", """
        LOAD_NAME 0   # 'define'
        GETFUNC
        LOAD_NAME 1   # 'x'
        ARG_BY_VALUE 0
        LOAD_CONST 0  # 42
        ARG_BY_VALUE 1
        CALL 2
        DISCARD_TOP
        """)

    def test_class_decl(self):
        bc = self.check_compile("class Aa { }; class bB { }", "")
        assert isinstance(bc.classes[0], klass.ClassDeclaration)
        assert bc.classes[0].name == 'Aa'
        assert bc.classes[1].name == 'bB'

    def test_class_simple_new(self):
        self.check_compile("$x = new Aa;", """
        VAR_PTR 0
        LOAD_NAME 0
        GETCLASS 1
        CALL 0
        STORE
        DISCARD_TOP
        """)

    def test_class_simple_new_args(self):
        self.check_compile("$x = new Aa($y);", """
        VAR_PTR 0
        LOAD_NAME 0
        GETCLASS 1
        VAR_PTR 1
        ARG_BY_PTR 0
        CALL 1
        STORE
        DISCARD_TOP
        """)

    def test_class_simple_new_dynamic(self):
        self.check_compile("$x = new $y;", """
        VAR_PTR 0
        LOAD_VAR 1
        GETCLASS 1
        CALL 0
        STORE
        DISCARD_TOP
        """)

    def test_class_new_is_by_ref_when_passing_argument(self):
        self.check_compile("foo(new Aa);", """
        LOAD_NAME 0
        GETFUNC
        LOAD_NAME 1
        GETCLASS 1
        CALL 0
        MAKE_REF_PTR
        ARG_BY_PTR 0
        CALL 1
        DISCARD_TOP
        """)

    def _class_decl(self, source):
        bc = self.check_compile(source, "")
        assert isinstance(bc.classes[0], klass.ClassDeclaration)
        return bc.classes[0]

    def test_class_property(self):
        klass = self._class_decl('class A { public $foo; };')
        assert 'foo' in klass.property_decl
        pfoo = klass.property_decl['foo']
        assert pfoo.name == 'foo'
        assert pfoo.access_flags == consts.ACC_PUBLIC
        space = self.space
        assert space.is_w(pfoo.value, space.w_Null)

    def test_class_property_value(self):
        klass = self._class_decl('class A { public $foo = 42; };')
        assert 'foo' in klass.property_decl
        pfoo = klass.property_decl['foo']
        assert pfoo.name == 'foo'
        assert pfoo.access_flags == consts.ACC_PUBLIC
        space = self.space
        assert space.is_w(pfoo.value, space.newint(42))

    def test_class_property_several(self):
        klass = self._class_decl('class A { public $foo, $bar=2, $baz; };')
        assert 'foo' in klass.property_decl
        assert 'bar' in klass.property_decl
        assert 'baz' in klass.property_decl
        space = self.space
        assert space.is_w(klass.property_decl['foo'].value, space.w_Null)
        assert space.is_w(klass.property_decl['bar'].value, space.newint(2))
        assert space.is_w(klass.property_decl['baz'].value, space.w_Null)

    def test_class_extends(self):
        bc = self.check_compile("class A extends B { }", "DECLARE_CLASS 0")
        klass = bc.late_declarations[0]
        assert klass.extends_name == 'B'

    def test_class_method(self):
        klass = self._class_decl("""\
        class A {
            function foo($a)
            {
            }
        }""")
        assert len(klass.method_decl) == 1
        mfoo = klass.method_decl['foo']
        assert mfoo.access_flags == consts.ACC_PUBLIC
        func = mfoo.func
        assert isinstance(func, function.Function)
        assert func.name == 'foo'
        assert func.types == [consts.ARG_ARGUMENT]
        assert func.names == ['a']
        self.compare(func.bytecode, """
        LOAD_NULL
        RETURN
        """)
        assert func.bytecode.startlineno == 2
        assert func.bytecode.name == 'foo'

    def test_class_constant(self):
        klass = self._class_decl("""\
        class A {
            const foo = 42;
        }""")
        assert 'foo' in klass.constants_w
        assert self.space.int_w(klass.constants_w['foo']) == 42

    def test_class_constant_special(self):
        klass = self._class_decl("""\
        class A {
            const foo = 42;
            const bar = self::foo;
        }""")
        assert 'bar' in klass.constants_w
        assert self.space.int_w(klass.constants_w['bar']) == 42

        with py.test.raises(CompilerError):
            klass = self._class_decl("""\
            class A {
                const foo = 42;
                const bar = static::foo;
            }""")

    def test_class_in_namespace(self):
        klass = self._class_decl("namespace test; class A {}")
        assert klass.name == "test\\A"

    def test_extends_in_namespace(self):
        bc = self.check_compile("namespace test; class A {} "
                                 "class B extends a {}")
        klass = bc.classes[1]
        assert klass.name == "test\\B"
        assert klass.extends_name == "test\\a"

    def test_getattr_setattr(self):
        self.check_compile("$x->foo; $x->foo = 1;", """
        LOAD_NAME 0
        LOAD_VAR_SWAP 0
        GETATTR
        DISCARD_TOP
        VAR_PTR 0
        LOAD_NAME 0
        ATTR_PTR
        LOAD_CONST 0
        STORE
        DISCARD_TOP
        """)

    def test_getattr_ref(self):
        self.check_compile("$x; $a = &$x->foo;", """
        LOAD_VAR 0
        DISCARD_TOP
        VAR_PTR 0
        LOAD_NAME 0
        ATTR_PTR
        RESOLVE_FOR_WRITING
        SET_FAST 1
        DISCARD_TOP
        """)

    def test_getattr_getitem(self):
        self.check_compile("$x->foo[5][6];", """
        LOAD_NAME 0
        LOAD_VAR_SWAP 0
        GETATTR
        LOAD_CONST 0
        GETITEM
        LOAD_CONST 1
        GETITEM
        DISCARD_TOP
        """)

    def test_getattr_setitem(self):
        self.check_compile("$x->foo[5] = 6;", """
        VAR_PTR 0
        LOAD_NAME 0
        ATTR_PTR
        LOAD_CONST 0
        ITEM_PTR
        LOAD_CONST 1
        STORE
        DISCARD_TOP
        """)

    def test_getattr_getitem_ref(self):
        self.check_compile("$x; $a = &$x->foo[5];", """
        LOAD_VAR 0
        DISCARD_TOP
        VAR_PTR 0
        LOAD_NAME 0
        ATTR_PTR
        LOAD_CONST 0
        ITEM_PTR
        RESOLVE_FOR_WRITING
        SET_FAST 1
        DISCARD_TOP
        """)

    def test_getattr_uplusplus(self):
        self.check_compile("echo ++$x->foo;", """
        VAR_PTR 0
        LOAD_NAME 0
        ATTR_PTR
        PREFIX_PLUSPLUS
        ECHO
        """)

    def test_getattr_getitem_uplusplus(self):
        self.check_compile("echo ++$x->foo[2];", """
        VAR_PTR 0
        LOAD_NAME 0
        ATTR_PTR
        LOAD_CONST 0
        ITEM_PTR
        PREFIX_PLUSPLUS
        ECHO
        """)

    def test_cannot_assign_to_this(self):
        raises(CompilerError, self.check_compile, '$this = 5;')
        self.check_compile('$this->x = 42;')
        self.check_compile('$this[5] = 42;')

        raises(CompilerError, self.check_compile, '$this = &$x;')
        raises(CompilerError, self.check_compile, 'global $this;')
        raises(CompilerError, self.check_compile, 'static $this;')

        self.check_compile('$this += 5;')
        self.check_compile('$this /= 5;')
        self.check_compile('$this++;')
        self.check_compile('unset($this);')

        self.check_compile("function f($this) { }")
        self.check_compile("function f(&$this) { }")

        raises(CompilerError, self.check_compile, """
            class A {
                function f($this) { }
            };""")
        raises(CompilerError, self.check_compile, """
            class A {
                function f(&$this) { }
            };""")

    def test_call_method(self):
        self.check_compile("$x->foo(42);", """
        VAR_PTR 0
        LOAD_NAME 0
        GETMETH
        LOAD_CONST 0
        ARG_BY_VALUE 0
        CALL 1
        DISCARD_TOP
        """)

    def test_call_method_indirect(self):
        self.check_compile("$x->$bar(42);", """
        VAR_PTR 0
        LOAD_VAR 1
        GETMETH
        LOAD_CONST 0
        ARG_BY_VALUE 0
        CALL 1
        DISCARD_TOP
        """)

    def test_unset_property(self):
        self.check_compile("unset($x->foo);", """
        VAR_PTR 0
        LOAD_NAME 0
        ATTR_PTR
        PTR_UNSET
        """)

    def test_static_member(self):
        self.check_compile("A::$x; A::$x=5;", """
        LOAD_NAME 0
        LOAD_NAME 1
        STATICMEMBER
        DISCARD_TOP
        LOAD_NAME 0
        LOAD_NAME 1
        STATICMEMBER_PTR
        LOAD_CONST 0
        STORE
        DISCARD_TOP
        """)

    def test_no_static_constructor(self):
        raises(CompilerError, self.check_compile, '''
        class A { static function __construct() { } }
        ''')
        raises(CompilerError, self.check_compile, '''
        class A { static function A() { } }
        ''')
        raises(CompilerError, self.check_compile, '''
        class Aa { static function aA() { } }
        ''')

    def test_abstract_class(self):
        klass = self._class_decl('abstract class A { }')
        assert klass.access_flags == consts.ACC_ABSTRACT

    def test_abstract_method(self):
        klass = self._class_decl('abstract class A { abstract function f(); }')
        assert len(klass.method_decl) == 1
        decl = klass.method_decl['f']
        assert decl.func.name == 'f'
        assert decl.is_abstract()

    def test_abstract_errors(self):
        e = raises(CompilerError, self.check_compile, '''
        class A { abstract function f(); }
        ''')
        assert str(e.value) == ("Class A contains 1 abstract method and must "
                                "therefore be declared abstract or implement "
                                "the remaining methods (A::f)")
        #
        e = raises(CompilerError, self.check_compile, '''
        class A { abstract function f(); abstract function Gh(); }
        ''')
        assert str(e.value) == ("Class A contains 2 abstract methods and must "
                                "therefore be declared abstract or implement "
                                "the remaining methods (A::f, A::Gh)")
        #
        e = raises(CompilerError, self.check_compile, '''
        abstract class A { abstract function f() { } }
        ''')
        assert str(e.value) == "Abstract function A::f() cannot contain body"
        #
        e = raises(CompilerError, self.check_compile, '''
        class A { function f(); }
        ''')
        assert str(e.value) == "Non-abstract method A::f() must contain body"
        #
        e = raises(CompilerError, self.check_compile, '''
        abstract class A { function f(); }
        ''')
        assert str(e.value) == "Non-abstract method A::f() must contain body"
        #
        e = raises(CompilerError, self.check_compile, '''
        abstract class A { abstract private function f(); }
        ''')
        assert str(e.value) == ("Abstract function A::f() cannot be "
                                "declared private")

    def test_class_clone(self):
        self.check_compile("$x = clone $y;", """
        VAR_PTR 0
        LOAD_VAR 1
        CLONE
        STORE
        DISCARD_TOP
        """)

    def test_at_sign(self):
        self.check_compile("@$x=$y;", """
        SILENCE
        VAR_PTR 0
        LOAD_VAR 1
        STORE
        UNSILENCE
        DISCARD_TOP
        """)

    def test_at_sign_argument_by_ptr(self):
        self.check_compile("f(@$x);", """
        LOAD_NAME 0
        GETFUNC
        SILENCE
        LOAD_VAR 0
        UNSILENCE
        ARG_BY_VALUE 0
        CALL 1
        DISCARD_TOP
        """)

    def test_at_sign_argument_by_value(self):
        self.check_compile("f(@$x + 1);", """
        LOAD_NAME 0
        GETFUNC
        SILENCE
        LOAD_VAR 0
        UNSILENCE
        LOAD_CONST 0
        BINARY_ADD
        ARG_BY_VALUE 0
        CALL 1
        DISCARD_TOP
        """)

    def test_silence_setattr(self):
        self.check_compile("@$x->foo = 1;", """
        SILENCE
        VAR_PTR 0
        LOAD_NAME 0
        ATTR_PTR
        LOAD_CONST 0
        STORE
        UNSILENCE
        DISCARD_TOP
        """)


    def test_large_bytecode_block(self):
        count = 21
        block = "$y=$x;" * count
        block_disass = ("VAR_PTR 1\n"
                        "LOAD_VAR 0\n"
                        "STORE\n"
                        "DISCARD_TOP\n") * count
        #
        self.check_compile("if($x){%s}" % block, """
        LOAD_VAR 0
        JUMP_IF_FALSE 132
        %s
        """ % block_disass)

    def test_large_bytecode_encoding(self):
        count = 130
        block = ''.join(["$x%d=%d;" % (i, i) for i in range(count)])
        block_disass = ''.join([
            "VAR_PTR %d\n"
            "LOAD_CONST %d\n"
            "STORE\n"
            "DISCARD_TOP\n" % (i, i) for i in range(count)])
        #
        self.check_compile(block, """
        %s
        """ % block_disass)

    def test_huge_bytecode_block(self):
        count = 2730
        block = "$y=$x;" * count
        block_disass = ("VAR_PTR 1\n"
                        "LOAD_VAR 0\n"
                        "STORE\n"
                        "DISCARD_TOP\n") * count
        #
        self.check_compile("if($x){%s}" % block, """
        LOAD_VAR 0
        JUMP_IF_FALSE 16386
        %s
        """ % block_disass)

    def test_switch_simple(self):
        self.check_compile('switch ($x) { case $y: echo 5; case $z: echo 6; }',
        """
        LOAD_VAR 0
        LOAD_VAR 1
        CASE_IF_EQ 19
        LOAD_VAR 2
        CASE_IF_EQ 22
        DISCARD_TOP
        JUMP_FORWARD 27
     19 LOAD_CONST 0
        ECHO
     22 LOAD_CONST 1
        ECHO
        _CHECKSTACK 0
     27 _CHECKSTACK 0
        """)

    def test_switch_default(self):
        self.check_compile('switch ($x) { case $y: echo 5; default: echo 6; }',
        """
        LOAD_VAR 0
        LOAD_VAR 1
        CASE_IF_EQ 13
        DISCARD_TOP
        JUMP_FORWARD 16
     13 LOAD_CONST 0
        ECHO
     16 LOAD_CONST 1
        ECHO
        _CHECKSTACK 0
        _CHECKSTACK 0
        """)

    def test_switch_nonlast_and_multiple_defaults(self):
        self.check_compile("""
        switch ($x) {
            default: echo 1;
            case 9: echo 2;
            default: echo 3;
            case $a: echo 4;
        }""", """
        LOAD_VAR 0
        LOAD_CONST 0
        CASE_IF_EQ 22
        LOAD_VAR 1
        CASE_IF_EQ 28
        DISCARD_TOP
        JUMP_FORWARD 25
        LOAD_CONST 1     # dead code: echo 5
        ECHO
     22 LOAD_CONST 2
        ECHO
     25 LOAD_CONST 3
        ECHO
     28 LOAD_CONST 4
        ECHO
        _CHECKSTACK 0
        _CHECKSTACK 0
        """)

    def test_switch_break(self):
        self.check_compile("""
        switch ($x) {
            case $y: break;
            default: echo 6;
        }""", """
        LOAD_VAR 0
        LOAD_VAR 1
        CASE_IF_EQ 13
        DISCARD_TOP
        JUMP_FORWARD 17
     13 JUMP_FORWARD 22
     17 LOAD_CONST 0
        ECHO
        _CHECKSTACK 0
     22 _CHECKSTACK 0
        """)

    def test_switch_continue(self):
        self.check_compile("""
        switch ($x) {
            case $y: continue;
            default: echo 6;
        }""", """
        LOAD_VAR 0
        LOAD_VAR 1
        CASE_IF_EQ 13
        DISCARD_TOP
        JUMP_FORWARD 17
     13 JUMP_FORWARD 20
     17 LOAD_CONST 0
        ECHO
     20 _CHECKSTACK 0
        _CHECKSTACK 0
        """)

    def test_switch_stackdepth(self):
        bc = self.check_compile('switch ($x) { case $y: echo 2+(3*(4-5)); }',
        """
        LOAD_VAR 0
        LOAD_VAR 1
        CASE_IF_EQ 13
        DISCARD_TOP
        JUMP_FORWARD 27
     13 LOAD_CONST 0
        LOAD_CONST 1
        LOAD_CONST 2
        LOAD_CONST 3
        BINARY_SUB
        BINARY_MUL
        BINARY_ADD
        ECHO
        _CHECKSTACK 0
     27 _CHECKSTACK 0
        """)
        assert bc.stackdepth == 4

    def test_break_continue_pop(self):
        bc = self.check_compile("""
        while ($b) {
            foreach($b as $c) {
                while ($c) {
                    foreach($c as $d) {
                        break 1;
                        break 2;
                        break 3;
                        break 4;
                        continue 1;
                        continue 2;
                        continue 3;
                        continue 4;
                    }
                }
            }
        }
        """, """
      0 _CHECKSTACK 0          # while
        LOAD_VAR 0
        JUMP_IF_FALSE 94
        LOAD_VAR 0             # foreach
        CREATE_ITER
     11 _CHECKSTACK 1
        NEXT_VALUE_ITER 89
        VAR_PTR 1
        STORE
        DISCARD_TOP
     21 _CHECKSTACK 1
        LOAD_VAR 1             # while
        JUMP_IF_FALSE 85
        LOAD_VAR 1             # foreach
        CREATE_ITER
     32 _CHECKSTACK 2
        NEXT_VALUE_ITER 80
        VAR_PTR 2
        STORE
        DISCARD_TOP
     42 JUMP_FORWARD 80        # break 1
        BREAK_CONTINUE_POP 1   # break 2
        JUMP_FORWARD 85
        BREAK_CONTINUE_POP 1   # break 3
        JUMP_FORWARD 89
        BREAK_CONTINUE_POP 2   # break 4
        JUMP_FORWARD 94
        JUMP_BACKWARD 32       # continue 1
        BREAK_CONTINUE_POP 1   # continue 2
        JUMP_BACKWARD 21
        BREAK_CONTINUE_POP 1   # continue 3
        JUMP_BACKWARD 11
        BREAK_CONTINUE_POP 2   # continue 4
        JUMP_BACKWARD 0
        JUMP_BACKWARD 32       # endforeach
     80 _CHECKSTACK 2
        DISCARD_TOP
        JUMP_BACKWARD 21       # endwhile
     85 _CHECKSTACK 1
        JUMP_BACKWARD 11       # endforeach
     89 _CHECKSTACK 1
        DISCARD_TOP
        JUMP_BACKWARD 0        # endwhile
     94 _CHECKSTACK 0
        """)

    def test_typehint_cls(self):
        bc = self.check_compile("""
        function f($y, FooCls $x) { }""", "")
        self.compare(bc.functions[0].bytecode, """
        LOAD_NAME 0
        TYPEHINT_CLASS 2     # argument 1, null not allowed
        LOAD_NULL
        RETURN
        """)

    def test_typehint_cls_null(self):
        bc = self.check_compile("""
        function f($a, BarBaz $x=NULL) { }""", "")
        self.compare(bc.functions[0].bytecode, """
        LOAD_NAME 0
        TYPEHINT_CLASS 3     # argument 1, null allowed
        LOAD_NULL
        RETURN
        """)

    def test_typehint_array(self):
        bc = self.check_compile("""
        function f($n, array $x) { }""", "")
        self.compare(bc.functions[0].bytecode, """
        TYPEHINT_ARRAY 2
        LOAD_NULL
        RETURN
        """)

    def test_typehint_array_null(self):
        bc = self.check_compile("""
        function f($z, $y, array $x=NULL) { }""", "")
        self.compare(bc.functions[0].bytecode, """
        TYPEHINT_ARRAY 5
        LOAD_NULL
        RETURN
        """)

    def test_exit_or_die(self):
        self.check_compile("""
        exit; die($b);""", """
        LOAD_NAME 0   # 'exit'
        GETFUNC
        LOAD_CONST 0  # 0
        ARG_BY_VALUE 0
        CALL 1
        DISCARD_TOP
        LOAD_NAME 0   # 'exit' again
        GETFUNC
        VAR_PTR 0     # $b
        ARG_BY_PTR 0
        CALL 1
        DISCARD_TOP
        """)

    def test_declare_function_and_classes_early_1(self):
        bc = self.check_compile("""
        function g() { }
        class A { }
        return 5;
        function f() { }
        class B { }
        """, """
        LOAD_CONST 0
        DEREF
        RETURN
        """)
        assert len(bc.classes) == 2
        assert len(bc.functions) == 2

    def test_declare_function_and_classes_early_2(self):
        self.check_compile("""
        {
        function g() { }
        class A { }
        return 5;
        function f() { }
        class B { }
        }
        """, """
        DECLARE_FUNC 0
        DECLARE_CLASS 1
        LOAD_CONST 0
        DEREF
        RETURN
        DECLARE_FUNC 2
        DECLARE_CLASS 3
        """)

    def test_declare_function_and_classes_early_3(self):
        bc = self.check_compile("""
        function main() {
            function g() { }
            class A { }
            return 5;
            function f() { }
            class B { }
        }
        """, "")
        self.compare(bc.functions[0].bytecode, """
        DECLARE_FUNC 0
        DECLARE_CLASS 1
        LOAD_CONST 0
        DEREF
        RETURN
        DECLARE_FUNC 2
        DECLARE_CLASS 3
        LOAD_NULL
        RETURN
        """)

    def test_goto_1(self):
        self.check_compile("""
        echo 21;
        start:
        echo 42;
        goto start;
        """, """
        LOAD_CONST 0
        ECHO
      3 LOAD_CONST 1
        ECHO
        JUMP_BACKWARD 3
        """)

    def test_goto_2(self):
        self.check_compile("""
        echo 21;
        goto stop;
        echo 42;
        stop:
        """, """
        LOAD_CONST 0
        ECHO
        BREAK_CONTINUE_POP 0
        JUMP_FORWARD 14
        LOAD_CONST 1
        ECHO
        """)

    def test_goto_invalid(self):
        raises(CompilerError, self.check_compile, 'foo:foo:')
        raises(CompilerError, self.check_compile, 'goto unknownlbl;')
        raises(CompilerError, self.check_compile, '''
            goto a;
            while (1) { a: }
        ''')
        raises(CompilerError, self.check_compile, '''
            while (1) { a: }
            goto a;
        ''')

    def test_goto_3(self):
        self.check_compile("""
        foreach ($a as $b) { goto stop; }
        stop:
        """, """
        LOAD_VAR 0
        CREATE_ITER
      3 _CHECKSTACK 1
        NEXT_VALUE_ITER 23
        VAR_PTR 1
        STORE
        DISCARD_TOP
        BREAK_CONTINUE_POP 1    # goto stop;
        JUMP_FORWARD 26
        JUMP_BACKWARD 3
     23 _CHECKSTACK 1
        DISCARD_TOP
        """)

    def test_goto_4(self):
        self.check_compile("""
        stop:
        foreach ($a as $b) { goto stop; }
        """, """
      0 LOAD_VAR 0
        CREATE_ITER
      3 _CHECKSTACK 1
        NEXT_VALUE_ITER 19
        VAR_PTR 1
        STORE
        DISCARD_TOP
        BREAK_CONTINUE_POP 1    # goto stop;
        JUMP_BACKWARD 0
        JUMP_BACKWARD 3
     19 _CHECKSTACK 1
        DISCARD_TOP
        """)

    def test_compile_double_assign(self):
        self.check_compile("""
        $a->x()->$b = 3;
        """, """
        VAR_PTR 0
        LOAD_NAME 0
        GETMETH
        CALL 0
        REF_PTR
        LOAD_VAR 1
        ATTR_PTR
        LOAD_CONST 0
        STORE
        DISCARD_TOP
        """)

    def test_function_indexing(self):
        self.check_compile("""
        echo x()[0];
        """, """
        LOAD_NAME 0
        GETFUNC
        CALL 0
        LOAD_CONST 0
        GETITEM
        ECHO
        """)

    def test_method_indexing(self):
        self.check_compile("""
        echo $x->foo()[0];
        """, """
        VAR_PTR 0
        LOAD_NAME 0
        GETMETH
        CALL 0
        LOAD_CONST 0
        GETITEM
        ECHO
        """)

    def test_assign_to_function(self):
        with py.test.raises(CompilerError):
            print self.check_compile("f() = 2", "")
        with py.test.raises(CompilerError):
            self.check_compile("f() =& $x")

    @py.test.mark.xfail(reason="not getting the error at compile-time for now")
    def test_reference_error_to_argument(self):
        self.check_compile('''
        function f(&$x) { } if(0){f(42);}
        ''', expected_warnings=[
            'Fatal error: Only variables can be passed by reference'])
        #
        self.check_compile('''
        if(0){end(array());}
        ''', expected_warnings=[
            'Fatal error: Only variables can be passed by reference'])
        #
        self.check_compile('''
        if(0){echo next((object)array(11, 12, 13, 14));}
        ''', expected_warnings=[
            'Fatal error: Only variables can be passed by reference'])

    def test_closure(self):
        self.check_compile("function () use ($y, &$z) {};", """
        LOAD_CLOSURE 0
        LOAD_VAR 0
        DEREF
        VAR_PTR 1
        RESOLVE_FOR_WRITING
        PUT_CLOSURE_VARS 2
        DISCARD_TOP
        """)

    def test_try_catch(self):
        self.check_compile('''
        try {
            func();
        } catch (Foo $e) {
            handle_exception();
        }
        ''', '''
        LOAD_NAME 0
        PUSH_CATCH_BLOCK 16
        LOAD_NAME 1
        GETFUNC
        CALL 0
        DISCARD_TOP
        JUMP_FORWARD 27
        DUMMY_STACK_PUSH
        VAR_PTR 0
        STORE
        DISCARD_TOP
        LOAD_NAME 2
        GETFUNC
        CALL 0
        DISCARD_TOP
        ''')

    def test_multiple_catch(self):
        self.check_compile('''
        try {
            func();
        } catch (Foo $e) {
            handle_Foo();
        } catch (Bar $e) {
            handle_Bar();
        }
        ''', '''
        LOAD_NAME 0
        PUSH_CATCH_BLOCK 37
        LOAD_NAME 1
        PUSH_CATCH_BLOCK 22
        LOAD_NAME 2
        GETFUNC
        CALL 0
        DISCARD_TOP
        JUMP_FORWARD 48
        DUMMY_STACK_PUSH
        VAR_PTR 0
        STORE
        DISCARD_TOP
        LOAD_NAME 3
        GETFUNC
        CALL 0
        DISCARD_TOP
        JUMP_FORWARD 48
        DUMMY_STACK_PUSH
        VAR_PTR 0
        STORE
        DISCARD_TOP
        LOAD_NAME 4
        GETFUNC
        CALL 0
        DISCARD_TOP
        ''')

    def test_instanceof(self):
        self.check_compile("$x instanceof X", '''
        LOAD_NAME 0
        GETCLASS 0
        LOAD_VAR_SWAP 0
        BINARY_INSTANCEOF
        DISCARD_TOP
        ''')

    def test_instanceof_2(self):
        self.check_compile("$x instanceof $y", '''
        LOAD_VAR 0
        GETCLASS 0
        LOAD_VAR_SWAP 1
        BINARY_INSTANCEOF
        DISCARD_TOP
        ''')

    def test_instanceof_3(self):
        self.check_compile("$x instanceof $y->z", '''
        LOAD_NAME 0
        LOAD_VAR_SWAP 0
        GETATTR
        GETCLASS 0
        LOAD_VAR_SWAP 1
        BINARY_INSTANCEOF
        DISCARD_TOP
        ''')

    def test_instanceof_4(self):
        self.check_compile("$x instanceof $y->a->b", '''
        LOAD_NAME 0
        LOAD_VAR_SWAP 0
        GETATTR
        LOAD_NAME 1
        GETATTR
        GETCLASS 0
        LOAD_VAR_SWAP 1
        BINARY_INSTANCEOF
        DISCARD_TOP
        ''')
