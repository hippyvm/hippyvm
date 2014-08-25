import py
import os
import sys
import pytest
from collections import OrderedDict

# For tests we enable all optional extensions.
import hippy.hippyoption
hippy.hippyoption.enable_all_optional_extensions()

from hippy.objspace import ObjSpace, w_True, w_False
from hippy.objects.intobject import W_IntObject
from hippy.objects.floatobject import W_FloatObject
from hippy.objects.arrayobject import W_ListArrayObject, W_RDictArrayObject
from hippy.objects.reference import W_Reference
from hippy.objects.boolobject import W_BoolObject
from testing.runner import MockEngine, MockInterpreter, preparse
from testing.directrunner import DirectRunner
from testing.conftest import option


skip_on_travis = pytest.mark.skipif("os.environ.get('TRAVIS', False)")


def hippy_fail(*args, **kwargs):
    return py.test.mark.xfail("not config.option.runappdirect",
            *args, **kwargs)



class BaseTestInterpreter(object):
    Engine = MockEngine
    interpreter = MockInterpreter
    DirectRunner = DirectRunner

    def warnings(self, expected_warnings=None):
        return self.engine.warnings(expected_warnings)

    def init_space(self):
        self.space = ObjSpace()
        if option.runappdirect:
            self.engine = self.DirectRunner(self.space)
        else:
            self.engine = self.Engine(self.space)
            self.engine.Interpreter = self.interpreter


    @py.test.yield_fixture(autouse=True)
    def setup_interp(self):
        self.env_copy = os.environ.copy()
        self.init_space()
        yield
        os.environ = self.env_copy
        self.engine = None
        self.space = None

    def run(self, source, expected_warnings=[], extra_func=None,
            inp_stream=None, **kwds):
        __tracebackhide__ = True
        return self.engine.run(source, expected_warnings, extra_func,
                inp_stream, **kwds)

    @property
    def interp(self):
        return self.engine.interp

    def unwrap(self, w_item):
        space = self.space
        if isinstance(w_item, W_IntObject):
            return space.int_w(w_item)
        elif isinstance(w_item, W_FloatObject):
            return space.float_w(w_item)
        elif isinstance(w_item, W_ListArrayObject):
            return [self.unwrap(w_x) for w_x in w_item.lst_w]
        elif isinstance(w_item, W_RDictArrayObject):
            o = OrderedDict()
            for key, w_value in w_item.dct_w.iteritems():
                o[key] = self.unwrap(w_value)
            return o
        elif space.is_str(w_item):
            return space.str_w(w_item)
        elif isinstance(w_item, W_Reference):
            return self.unwrap(w_item.deref())
        elif isinstance(w_item, W_BoolObject):
            return w_item.boolval
        else:
            raise NotImplementedError

    def echo(self, source, expected_warnings=[]):
        assert isinstance(source, str)
        output = self.run("echo %s;" % (source,), expected_warnings)
        assert len(output) == 1
        return self.space.str_w(output[0])

    def is_array(self, w_obj, lst_w):
        assert w_obj.tp == self.space.tp_array
        assert self.space.arraylen(w_obj) == len(lst_w)
        for i in range(len(lst_w)):
            w_item = self.space.getitem(w_obj, self.space.newint(i))
            w_expected = lst_w[i]
            assert self.space.is_w(w_item, w_expected)
        return True

    def is_object(self, w_obj, expected_clsname, properties):
        clsname = w_obj.klass.name
        d = w_obj.get_instance_attrs()
        assert clsname == expected_clsname, "bad class name\n%s" % output
        for (key, w_value), (expected_name, w_expected_value) in \
                zip(d.iteritems(), properties):
            assert key == expected_name
            assert self.space.is_w(w_value, w_expected_value)
        assert len(d) == len(properties)
        return True


class LocalRunTestInterpreter(object):
    # a mixin class: overrides run() to preprocess the source code
    # and turn the snippet from global to local level.
    def run(self, source, *args, **kwds):
        source = ('function _local_() {\n' +
                  source +
                  '\n}\n_local_();')
        return super(LocalRunTestInterpreter, self).run(source, *args, **kwds)


class MockServerEngine(MockEngine):
    """Tests CGI server mode by running the same bytecode object twice."""
    def _run(self, source, extra_func=None, inp_stream=None,
            expected_warnings=None, **kwds):
        source = preparse(source)
        interp = self.new_interp(inp_stream=inp_stream,
            extra_func=extra_func, **kwds)
        bc = interp.compile(source)
        if bc is None:
            return interp.output
        compilation_warnings = self.err_stream[:]
        bc.show()
        interp.run_bytecode(bc, self.warn_ctx.expected_warnings)
        interp.shutdown()
        self.err_stream[:] = compilation_warnings
        self.interp = self.new_interp(inp_stream=inp_stream,
            extra_func=extra_func, **kwds)
        res = self.interp.run_bytecode(bc, self.warn_ctx.expected_warnings)
        return res


class _TestInterpreter(BaseTestInterpreter):

    def test_simple(self):
        output = self.run("$x = 3;\necho $x;")
        assert self.space.int_w(output[0]) == 3

    def test_add(self):
        output = self.run("$x = 3;\necho $x + 10;")
        assert self.space.int_w(output[0]) == 13

    def test_sub(self):
        output = self.run("$x = 3;\necho $x - 10;")
        assert self.space.int_w(output[0]) == -7

    def test_mul(self):
        output = self.run("$x = 3;\necho $x * 10;")
        assert self.space.int_w(output[0]) == 30

    def test_float(self):
        output = self.run("echo 3.5;")
        assert self.space.float_w(output[0]) == 3.5

    def test_float_add(self):
        output = self.run("$x = .2;\necho 3.5 + $x;")
        assert self.space.float_w(output[0]) == 3.7

    def test_floats_ints(self):
        output = self.run("$x = 2;\necho 2.3 + $x;")
        assert self.space.float_w(output[0]) == 4.3
        output = self.run("$x = 2;\necho $x + 2.3;")
        assert self.space.float_w(output[0]) == 4.3
        output = self.run("$x = 2;\necho $x/4;")
        assert self.space.float_w(output[0]) == 0.5
        if option.runappdirect:
            py.test.skip("inexact float")
        output = self.run("$x = 2;\necho $x/3;")
        assert self.space.float_w(output[0]) == float(2) / 3

    def test_plusplus(self):
        output = self.run("$x = 1;\necho $x++;\necho ++$x;")
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 3

    def test_minusminus(self):
        output = self.run("$x = 1;\necho $x--;\necho --$x;")
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == -1

    def test_plusplus_2(self):
        output = self.run("$x = 9;\necho $x * (++$x);")
        assert self.space.int_w(output[0]) == 100
        output = self.run("$x = 9;\necho ($x + 0) * (++$x);")
        assert self.space.int_w(output[0]) == 90
        output = self.run("$x = 9;\necho (++$x) * $x;")
        assert self.space.int_w(output[0]) == 100
        output = self.run("$x = 9;\necho (++$x) * ($x + 0);")
        assert self.space.int_w(output[0]) == 100
        output = self.run("$x = 9;\necho $x * ($x++);")
        assert self.space.int_w(output[0]) == 90
        output = self.run("$x = 9;\necho ($x + 0) * ($x++);")
        assert self.space.int_w(output[0]) == 81
        output = self.run("$x = 9;\necho ($x++) * $x;")
        assert self.space.int_w(output[0]) == 90
        output = self.run("$x = 9;\necho ($x++) * ($x + 0);")
        assert self.space.int_w(output[0]) == 90
        output = self.run("$x = 9;\necho (++$x) * (++$x);")
        assert self.space.int_w(output[0]) == 110
        output = self.run("$x = 9;\necho (++$x) * ($x++);")
        assert self.space.int_w(output[0]) == 100
        output = self.run("$x = 9;\necho ($x++) * (++$x);")
        assert self.space.int_w(output[0]) == 99
        output = self.run("$x = 9;\necho ($x++) * ($x++);")
        assert self.space.int_w(output[0]) == 90

    def test_comparison(self):
        output = self.run("""$x = 3;\necho $x > 1;\necho $x < 1;\necho $x == 3;
        echo $x >= 3;\necho $x <= 3;\necho $x != 8;\necho $x == 8;
        echo $x != 3;
        """)
        assert [i.boolval for i in output] == [True, False, True, True, True,
                                               True, False, False]

    def test_unary(self):
        output = self.run("$x = 3;\necho +$x;\necho -$x;")
        assert [i.intval for i in output] == [3, -3]
        output = self.run("$x = 3.5;\necho +$x;\necho -$x;")
        assert [i.floatval for i in output] == [3.5, -3.5]

    def test_bitwise_not(self):
        output = self.run('''
        echo ~3;
        echo ~ 3.5;
        echo ~"34";
        ''')
        expected = [-4, -4, "\xcc\xcb"]
        assert all(self.space.is_w(out, self.space.wrap(exp))
                for out, exp in zip(output, expected))

    @py.test.mark.parametrize(["input"],
            [["true"], ["false"], ["null"], ["array(0, 1)"]])
    def test_bitwise_not_error(self, input):
        with self.warnings(['Fatal error: Unsupported operand types']):
            self.run('~ %s;' % input)

    def test_bitwise_and(self):
        with self.warnings():
            output = self.run("""
            echo %(maxint)s & 0;
            echo %(maxint)s & -1;
            echo %(ovf)s & -1;
            """ % {'maxint': sys.maxint, 'ovf': sys.maxint + 1})
        assert self.space.int_w(output[0]) == 0
        assert self.space.int_w(output[1]) == sys.maxint
        assert self.space.int_w(output[2]) == -sys.maxint - 1

    def test_if(self):
        output = self.run("""
        $x = 3;
        if ($x)
           $x = 18;
        else
           $x = 13;
        echo $x;
        """)
        assert self.space.int_w(output[0]) == int(18)

    def test_while(self):
        output = self.run("""
        $i = 0;
        while ($i < 3)
          $i++;
        echo $i;
        """)
        assert self.space.int_w(output[0]) == 3

    def test_shifts(self):
        output = self.run("""
        echo 1 << 30, 15 >> 1;
        """)
        assert [self.space.int_w(i) for i in output] == [1 << 30, 15 >> 1]

    def test_assign_inplace(self):
        output = self.run("""
        $x = 15;
        echo $x += 3;
        echo $x -= 17;
        echo $x *= 2;
        echo $x /= 4;
        echo $x;
        """)
        assert [self.space.int_w(i) for i in output[:-2]] == [18, 1, 2]
        assert [self.space.float_w(i) for i in output[-2:]] == [0.5, 0.5]
        output = self.run("""
        $x = 25;
        echo $x %= 10;
        $x = 3;
        echo $x &= 5;
        $x = 3;
        echo $x |= 5;
        $x = 3;
        echo $x ^= 5;
        """)
        assert [self.space.int_w(i) for i in output] == [5, 1, 7, 6]

    def test_assign_inplace_array(self):
        output = self.run("""
        $x = array(15);
        echo $x[0] += 3;
        echo $x[0] -= 17;
        echo $x[0] *= 2;
        echo $x[0] /= 4;
        echo $x[0];
        """)
        assert [self.space.int_w(i) for i in output[:-2]] == [18, 1, 2]

    def test_simple_assignment(self):
        output = self.run("""
        $y = 3;
        $x = 0;
        echo $x;\necho $y;
        """)
        assert [self.space.int_w(i) for i in output] == [0, 3]

    def test_for(self):
        output = self.run("""
        $y = 3;
        for ($x = 0; $x < 10; $x++) { $y++; }
        echo $x;\necho $y;
        """)
        assert [self.space.int_w(i) for i in output] == [10, 13]

    def test_for_empty(self):
        output = self.run("""
        for ($x = 0; $x < 10; ) { $x++; }
        echo $x;
        """)
        assert self.space.int_w(output[0]) == 10

    def test_aliasing(self):
        output = self.run("""
        $x = 3;
        $y = $x;
        $y++;
        echo $x;\necho $y;
        """)
        assert [self.space.int_w(i) for i in output] == [3, 4]

    def test_echo_multielement(self):
        output = self.run("""
        echo 1, 2, 3;
        """)
        assert [self.space.int_w(i) for i in output] == [1, 2, 3]

    @py.test.mark.skipif("config.option.runappdirect",
            reason="confused by print")
    def test_bare_print(self):
        output = self.run('''
        print("xyz");
        ''')
        assert self.space.str_w(output[0]) == 'xyz'
        #
        output = self.run('''
        echo print("xyz");
        ''')
        assert self.space.str_w(output[0]) == 'xyz'
        assert self.space.int_w(output[1]) == 1

    @py.test.mark.skipif("config.option.runappdirect",
            reason="confused by print")
    def test_print_evaluation_order(self):
        output = self.run('''
        print("foo")&&print("bar");
        ''')
        assert [self.space.str_w(out) for out in output] == ['bar', '1']

        # Here's what the above nonsense actually means
        output2 = self.run('''
        print ("foo" && (print "bar"));
        ''')
        assert all(self.space.str_w(out2) == self.space.str_w(out)
                for out, out2 in zip(output, output2))

    def test_string_ops_basic(self):
        output = self.run('''
        $a = "abc";
        echo $a;
        ''')
        assert self.space.str_w(output[0]) == 'abc'

    def test_string_ops(self):
        output = self.run('''
        $a = "abc";
        echo $a[0];
        $b = $a;
        $c = "abc";
        $a[1] = "d";
        echo $a, $b, $c;
        ''')
        assert [self.space.str_w(i) for i in output] == [
            'a', 'adc', 'abc', 'abc']

    def test_string_setitem_result(self):
        output = self.run('''
        $a = "abc";
        $b = $a[1] = "X";
        echo $a, $b;
        ''')
        assert [self.space.str_w(i) for i in output] == [
            'aXc', 'X']

    def test_string_coerce(self):
        output = self.run('''
        $a = "10 abc";
        echo $a + 1, $a + 1.5, "1.5" + 1, "1.5" + 1.2;
        ''')
        assert self.space.int_w(output[0]) == 11
        assert self.space.float_w(output[1]) == 11.5
        assert self.space.float_w(output[2]) == 2.5
        assert self.space.float_w(output[3]) == 2.7

    def test_mixed_string_ops(self):
        output = self.run('''
        $a = "abc";
        $a[0] = 12;
        echo $a;
        $a++;
        echo $a;
        ''')
        assert [self.space.str_w(i) for i in output] == ["1bc", "1bd"]

    def test_string_copies(self):
        output = self.run('''
        $a = "abc";
        $b = $a;
        $c = $b;
        $c[0] = 1;
        $a[0] = 5;
        echo $b[0], $a, $b, $c;
        ''')
        assert [self.space.str_w(i) for i in output] == [
            'a', '5bc', 'abc', '1bc']

    def test_string_copies2(self):
        output = self.run('''
        $a = "abc";
        $a[0] = "3";
        $b = $a;
        echo $b[0];
        ''')
        assert [self.space.str_w(i) for i in output] == [
            '3']

    def test_string_copies3(self):
        output = self.run('''
        $a = "abc";
        $a[0] = "3";
        $b = $a;
        $a[0] = "4";
        echo $a, $b;
        ''')
        assert [self.space.str_w(i) for i in output] == [
            '4bc', '3bc']

    def test_string_empty(self):
        output = self.run('''
        $b = "";
        $a = "abc";
        $a[0] = $b;
        echo $a;
        ''')
        assert self.space.str_w(output[0]) == '\x00bc'

    def test_string_concat(self):
        output = self.run('''
        $a = "abc";
        echo $a . "def";
        $a[0] = "1";
        $b = $a;
        echo $a . "def", $a . $b . $a;
        ''')
        assert [self.space.str_w(i) for i in output] == [
            "abcdef", "1bcdef", "1bc1bc1bc"]

    def test_plusplus_comp(self):
        output = self.run('''
        $n = 3;
        while ($n-- > 0) {
           echo $n;
        }
        ''')
        assert [self.space.int_w(i) for i in output] == [2, 1, 0]

    def test_declare_function_call(self):
        output = self.run('''
        function f($a, $b) {
           echo $a;
           echo $b;
           return $a + $b;
        }
        echo f(10, 20);
        ''')
        assert self.space.int_w(output[0]) == 10
        assert self.space.int_w(output[1]) == 20
        assert self.space.int_w(output[2]) == 30

    def test_declare_function_call_2(self):
        output = self.run('''
        function f($a) {
           return $a + 1;
        }
        echo f(1);
        ''')
        assert self.space.int_w(output[0]) == 2

    def test_declare_function_call_3(self):
        output = self.run('''
        function f($a) {
           $b = 2;
           return $a + $b;
        }
        $b = 5;
        echo f(10);
        echo $b;
        ''')
        assert [self.space.int_w(i) for i in output] == [12, 5]

    def test_declare_function_call_4(self):
        output = self.run('''
        function f($a, $a, $b) {    // ugh! supported
           echo $a, $b;
        }
        f(10, 20, 30);
        ''', ["Hippy warning: Argument list contains twice '$a'"])
        assert [self.space.int_w(i) for i in output] == [20, 30]

    def test_declare_inside(self):
        output = self.run('''
        function f() {
           function g() {
              return 1;
           }
        }
        echo g();
        ''', ['Fatal error: Call to undefined function g()'])
        output = self.run('''
                function f() {
           function g() {
              return 1;
           }
        }
        f();
        echo g();
        ''')
        assert self.space.int_w(output[0]) == 1

    def test_undeclared_traceback(self):
        self.run('''
        function f() {
           g();
        }
        f();
        ''', ['Fatal error: Call to undefined function g()'])
        if not option.runappdirect:
            if not isinstance(self, LocalRunTestInterpreter):
                tb = self.interp.tb
                assert tb == [('<input>', '<main>', 5, 'f();'),
                              ('<input>', 'f', 3, '   g();')]

    def test_recursion(self):
        output = self.run('''
        function f($n) {
           if ($n == 0)
              return 0;
           return $n + f($n - 1);
        }
        echo f(5);
        ''')
        assert self.space.int_w(output[0]) == 5 + 4 + 3 + 2 + 1

    def test_and_or(self):
        output = self.run('''
        echo 1 && 0 || 3;
        echo 1 && 2;
        echo 0 && 1;
        echo 1 && 0;
        echo 1 && 0 || "";
        ''')
        for i, expected in enumerate([True, True, False, False, False]):
            if expected:
                assert self.space.is_true(output[i])
            else:
                assert not self.space.is_true(output[i])

    def test_negation(self):
        output = self.run('''
        echo !15,!!15;
        ''')
        assert [i.boolval for i in output] == [False, True]

    def test_double_dollar_1(self):
        output = self.run('''
        $x = 5;
        $y = "x";
        echo $$y;
        ''')
        assert self.space.int_w(output[0]) == 5

    def test_double_dollar_2(self):
        output = self.run('''
        $x = 5;
        $y = "x";
        $z = "y";
        echo $$$z;
        ''')
        assert self.space.int_w(output[0]) == 5

    def test_double_dollar_3(self):
        output = self.run('''
        $x = 5;
        $y = "x";
        $$y = 6;
        echo $x;
        ''')
        assert self.space.int_w(output[0]) == 6

    def test_double_dollar_4(self):
        output = self.run('''
        $x = 5;
        $y = "x";
        $$y++;
        echo $x;
        ''')
        assert self.space.int_w(output[0]) == 6

    def test_double_dollar_5(self):
        output = self.run('''
        $x = 5;
        $y = "xyz";
        echo $$y[0];
        ''')   # bah, it means ${$y[0]}
        assert self.space.int_w(output[0]) == 5

    def test_double_dollar_6(self):
        output = self.run('''
        $x = 5;
        $y = "x";
        $z = &$$y;
        $x = array(42);
        echo $z[0];
        ''')
        assert self.space.int_w(output[0]) == 42

    def test_double_dollar_7(self):
        output = self.run('''
        $xyz = 41;
        echo ${"x" . "y" . "z"};
        ''')
        assert self.space.int_w(output[0]) == 41

    def test_double_dollar_8(self):
        output = self.run('''
        ${"x" . "y" . "z"} = 40;
        echo $xyz;
        ''')
        assert self.space.int_w(output[0]) == 40

    def test_double_dollar_9(self):
        output = self.run('''
        ${"x" . "yz"} = 39;
        echo ${"xy" . "z"};
        ''')
        assert self.space.int_w(output[0]) == 39

    @py.test.mark.xfail("not config.option.runappdirect",
            reason="obscure, compare with test_double_dollar_10bis")
    def test_double_dollar_10(self):
        output = self.run('''
        $a = 41;
        $b = 42;
        $name = "a";
        $$name = ($name = "b");
        echo $a, $b;
        ''')
        assert self.space.str_w(output[0]) == "41"
        assert self.space.str_w(output[1]) == "b"

    def test_double_dollar_10bis(self):
        output = self.run('''
        $a = 41;
        $b = 42;
        $name = "a";
        ${$name[0]} = ($name = "b");
        echo $a, $b;
        ''')
        assert self.space.str_w(output[0]) == "b"
        assert self.space.str_w(output[1]) == "42"

    def test_double_dollar_11(self):
        output = self.run('''
        $a = 40;
        $c = 50;
        $name = "a";
        $$name = ($a =& $c);
        echo $a, $c;
        ''')
        assert self.space.int_w(output[0]) == 50
        assert self.space.int_w(output[1]) == 50

    def test_double_dollar_12(self):
        output = self.run('''
        $b = array(10);
        $name = "a";
        $$name = &$b;
        $b[0] = 15;
        $a0 = $$name;
        echo $a0[0];
        ''')
        assert self.space.int_w(output[0]) == 15

    def test_references(self):
        output = self.run('''
        $a = 3;      // [Int(3), None]
        $b = &$a;    // [r, r]  with r == Ref(Int(3),c=2)
        $b = 5;      //                       Int(5)
        echo $b, $a;
        ''')
        assert [self.space.int_w(i) for i in output] == [5, 5]

    def test_references_left_array_1(self):
        output = self.run('''
        $a = 3;
        $b = array(0);
        $b[0] = & $a;
        $a = 5;
        echo $b[0];
        $b[0] = 7;
        echo $a;
        ''')
        assert [self.space.int_w(i) for i in output] == [5, 7]

    def test_references_left_array_2(self):
        output = self.run('''
        $a = 3;
        $b = array(array(0));
        $b[0][0] = & $a;
        $a = 5;
        echo $b[0][0];
        $b[0][0] = 7;
        echo $a;
        ''')
        assert [self.space.int_w(i) for i in output] == [5, 7]

    def test_references_right_array_1(self):
        output = self.run('''
        $b = array(0);
        $a = & $b[0];
        $a = 15;
        echo $b[0];
        $b[0] = 17;
        echo $a;
        ''')
        assert [self.space.int_w(i) for i in output] == [15, 17]

    def test_references_right_array_2(self):
        output = self.run('''
        $b = array(array(0));
        $a = & $b[0][0];
        $a = 12;
        echo $b[0][0];
        $b[0][0] = 13;
        echo $a;
        ''')
        assert [self.space.int_w(i) for i in output] == [12, 13]

    def test_array_copy_reference(self):
        output = self.run('''
        $x = 5;
        $a = array(&$x);
        $b = $a;
        $b[0] = 6;
        echo $a[0];
        ''')
        assert self.space.int_w(output[0]) == 6

    @hippy_fail(reason="PHP is too crazy")
    def test_array_copy_reference_2(self):
        output = self.run('''
        $x = 5;
        $a = array(&$x);
        $b = $a;
        unset($x);
        $b[0] = 6;
        echo $a[0];
        ''')
        assert self.space.int_w(output[0]) == 5

    def test_references_plusplus_1(self):
        output = self.run("""
        $x = 1;
        $y =& $x;
        echo ++$x, ++$x, $y;
        """)
        assert self.space.int_w(output[0]) == 2
        assert self.space.int_w(output[1]) == 3
        assert self.space.int_w(output[2]) == 3

    def test_references_plusplus_2(self):
        output = self.run("""
        $x = 1;
        $y =& $x;
        echo $x++, $x++, $y;
        """)
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 2
        assert self.space.int_w(output[2]) == 3

    def test_references_assign(self):
        output = self.run("""
        $x = 15;
        $y =& $x;
        echo $x = $x + 3;
        echo $y;
        """)
        assert self.space.int_w(output[0]) == 18
        assert self.space.int_w(output[1]) == 18

    def test_references_assign_inplace(self):
        output = self.run("""
        $x = 15;
        $y =& $x;
        echo $x += 3;
        echo $y;
        """)
        assert self.space.int_w(output[0]) == 18
        assert self.space.int_w(output[1]) == 18

    def test_references_2(self):
        output = self.run('''
        function f() {
        $a = 3;
        $b = &$a;
        $b = 5;
        echo $b, $a;
        }
        f();
        ''')
        assert [self.space.int_w(i) for i in output] == [5, 5]

    def test_references_3(self):
        output = self.run('''
        $a = 5;         // [Int(5), None]
        $x = array();   // [Int(5), Array([],c=1)]
        $x[] = &$a;     // [r, Array([r],c=1)],  r == Ref(Int(5),c=2)
        $x[0] = 3;
        echo $a;
        ''')
        assert [self.space.int_w(i) for i in output] == [3]

    def test_references_4(self):
        output = self.run('''
        $a = 5;
        $x = array(0);
        $x[0] = &$a;
        $x[0] = 3;
        echo $a;
        ''')
        assert [self.space.int_w(i) for i in output] == [3]

    def test_references_6(self):
        output = self.run('''
        function f() {
           global $x;
           $x = 3;
        }
        $a = 5;
        $x = &$a;
        f();
        echo $a;
        ''')
        expected = 3 if not isinstance(self, LocalRunTestInterpreter) else 5
        assert [self.space.int_w(i) for i in output] == [expected]

    def test_references_7(self):
        output = self.run('''
        function foo1(&$a) {
            $a[1] = & $a[0];
            return 5;
        }
        $a = array(-5, 0);
        $a[0] = foo1($a);
        echo $a[1];
        ''')
        assert [self.space.int_w(i) for i in output] == [5]

    def test_references_function(self):
        output = self.run('''
        function f(&$a) {
           $a = 3;
        }
        $a = 5;
        f($a);
        echo $a;
        ''')
        assert [self.space.int_w(i) for i in output] == [3]

    def test_references_function_2(self):
        output = self.run('''
        function f(&$a, $b) {
           $a[0] = 3;
           $b[0] = 4;
        }
        $a = array(15);
        $b = array(20);
        f($a, $b);
        echo $a[0], $b[0];
        ''')
        assert [self.space.int_w(i) for i in output] == [3, 20]

    def test_reference_indirect(self):
        output = self.run('''
        $name = 'a';
        $$name =& $b;
        $b = 42;
        echo $$name;
        ''')
        assert self.space.int_w(output[0]) == 42

    def test_reference_indirect_2(self):
        output = self.run('''
        $name = 'a';
        $$name =& $b;
        $b = 42;
        echo $a;
        ''')
        assert self.space.int_w(output[0]) == 42

    def test_store_order_1(self):
        output = self.run('''
        $a = 5;
        $v = 6;
        $a = ($a =& $v);
        // we must not read the reference to the leftmost $a
        // before we evaluate the expression ($a =& $v)
        echo $a;
        $a = 7;
        echo $v;
        ''')
        assert self.space.int_w(output[0]) == 6
        assert self.space.int_w(output[1]) == 7

    @py.test.mark.parametrize('value', [('true', 'boolean'),
                                        ('false', 'boolean'),
                                        ('null', 'null'),
                                        ('1', 'integer'),
                                        ('1.', 'double')])
    def test_getitem_scalar(self, value):
        if value[1] == 'null':
            expected_warnings = []
        else:
            expected_warnings = [
                'Hippy warning: Cannot use %s as an array' % value[1]]
        output = self.run('''
        $x = %s;
        echo $x[0];''' % value[0], expected_warnings)
        assert self.space.is_w(output[0], self.space.w_Null)

    def test_getitem_string(self):
        with self.warnings(["Warning: Illegal string offset 'fgh'"]):
            output = self.run('''
            $x = "abc";
            echo $x[0];
            echo $x['fgh'];
            ''')
        assert self.space.str_w(output[0]) == "a"
        assert self.space.str_w(output[1]) == "a"

    def test_getitem_stringoffset(self):
        output = self.run('''
        $x = "abc";
        echo $x[0][0];
        ''')
        assert self.space.str_w(output[0]) == "a"

    @py.test.mark.parametrize('value',
            ['true', '1', '1.'])
    def test_setitem_scalar(self, value):
        with self.warnings(["Warning: Cannot use a scalar value as an array"]):
            output = self.run('''
            $x = %s;
            echo $x[0] = 5;
            echo $x;''' % value)
        assert self.space.is_w(output[0], self.space.w_Null)
        assert self.space.int_w(output[1]) == 1

    @py.test.mark.parametrize('value',
            ['null', 'false', '""'])
    def test_setitem_implicit_cast(self, value):
        with self.warnings(['Hippy warning: Creating array from empty value']):
            output = self.run('''
            $x = %s;
            echo $x[0] = 5;
            echo $x;''' % value)
        assert self.space.int_w(output[0]) == 5
        assert self.is_array(output[1], [self.space.newint(5)])

    def test_setitem_string(self):
        with self.warnings(["Warning: Illegal string offset 'fgh'"]):
            output = self.run('''
            $x = "abc";
            echo $x[1] = 'xyz';
            echo $x['fgh'] = 'xyz';
            echo $x;
            ''')
        assert self.space.str_w(output[0]) == "x"
        assert self.space.str_w(output[1]) == "x"
        assert self.space.str_w(output[2]) == "xxc"

    def test_setitem_stringoffset(self):
        with self.warnings(
                ["Fatal error: Cannot use string offset as an array"]):
            self.run('''
            $x = "abc";
            $x[0][0] = "x";
            ''')

    @py.test.mark.parametrize('value',
            ['true', '1', '1.'])
    def test_setitemref_scalar(self, value):
        with self.warnings(["Warning: Cannot use a scalar value as an array"]):
            output = self.run('''
            $x = %s;
            $a = 5;
            echo $x[0] =& $a;
            echo $x;''' % value)
        assert self.space.is_w(output[0], self.space.w_Null)
        assert self.space.int_w(output[1]) == 1

    @py.test.mark.parametrize('value',
            ['null', 'false', '""'])
    def test_setitemref_implicit_cast(self, value):
        with self.warnings(['Hippy warning: Creating array from empty value']):
            output = self.run('''
            $x = %s;
            $a = 5;
            echo $x[0] =& $a;
            echo $x;''' % value)
        assert self.space.int_w(output[0]) == 5
        assert self.is_array(output[1], [self.space.newint(5)])

    def test_setitemref_string(self):
        with self.warnings(['Fatal error: Cannot create references to/from '
                            'string offsets...']):
            self.run('''
            $x = "abc";
            $a = "a";
            $x[0] =& $a;
            ''')

    @py.test.mark.parametrize('value',
            ['true', '1', '1.'])
    def test_itemref_scalar(self, value):
        with self.warnings(["Warning: Cannot use a scalar value as an array"]):
            output = self.run('''
            $x = %s;
            echo $a =& $x[0];
            $a = 5;
            echo $x;''' % value)
        assert self.space.is_w(output[0], self.space.w_Null)
        assert self.space.int_w(output[1]) == 1

    @py.test.mark.parametrize('value',
            ['null', 'false', '""'])
    def test_itemref_implicit_cast(self, value):
        with self.warnings(['Hippy warning: Creating array from empty value']):
            output = self.run('''
            $x = %s;
            echo $a =& $x[0];
            $a = 5;
            echo $x;''' % value)
        assert self.space.is_w(output[0], self.space.w_Null)
        assert self.is_array(output[1], [self.space.newint(5)])

    def test_itemref_string(self):
        with self.warnings(['Fatal error: '
                'Cannot create references to/from string offsets...']):
            self.run('''
            $x = "abc";
            $a =& $x[0];
            ''')

    def test_undefined_var_1(self):
        with self.warnings(["Notice: Undefined variable: x"]):
            output = self.run('''
            echo $x;
            ''')
        assert self.space.is_w(output[0], self.space.w_Null)

    def test_undefined_var(self):
        with self.warnings(["Notice: Undefined variable: x",
                "Hippy warning: Creating array from empty value"]):
            output = self.run('''
            echo $x[5];
            $x[5] = 42;
            echo $x[5];
            ''')
        assert self.space.is_w(output[0], self.space.w_Null)
        assert self.space.int_w(output[1]) == 42

    def test_loading_undefined_var_does_not_define_it(self):
        with self.warnings(["Notice: Undefined variable: x"] * 2):
            self.run('''
            echo $x;
            echo $x;
            ''')

    def test_indexing_with_undefined_var(self):
        # uses GETITEM
        with self.warnings(["Notice: Undefined variable: a",
                "Notice: Undefined index: "]):
            output = self.run("""
            $x = array(1, 2, 3);
            echo $x[$a];
            """)
        assert self.space.is_w(output[0], self.space.w_Null)

    def test_indexing_with_undefined_var_2(self):
        # uses LOAD_VAR_ITEM_PTR
        with self.warnings(["Notice: Undefined variable: a",
                "Notice: Undefined index: "]):
            output = self.run("""
            function f($x) {return $x;}
            $x = array(1, 2, 3);
            echo f($x[$a]);
            """)
        assert self.space.is_w(output[0], self.space.w_Null)

    def test_getitem_object(self):
        with self.warnings(["Fatal error: "
                "Cannot use object of type stdClass as array"]):
            self.run('''
            $x = new stdClass;
            $x[0];
            ''')

    def test_array_store_simple_1(self):
        output = self.run('''
        $v = 5;
        $a = array(&$v);
        $a[0] = 40 + 2;
        echo $v;
        ''')
        assert self.space.int_w(output[0]) == 42

    def test_array_store_simple_2(self):
        output = self.run('''
        $v = 5;
        $a = array(array(&$v));
        $a[0][0] = 40 + 2;
        echo $v;
        ''')
        assert self.space.int_w(output[0]) == 42

    def test_array_store_simple_3(self):
        output = self.run('''
        $c = array(5);
        $a = array(&$c);
        $a[0][0] = 40 + 2;
        echo $c[0];
        ''')
        assert self.space.int_w(output[0]) == 42

    def test_array_store_order_0(self):
        output = self.run('''
        $a = array(10, 11, 12, 13, array(20, 21, 22, 23));
        $n = 2;
        $a[$n *= 2][$n -= 1] = $n += 100;
        echo $a[4][3], $n;
        ''')
        assert self.space.int_w(output[0]) == 103
        assert self.space.int_w(output[1]) == 103

    def test_array_store_order_1(self):
        output = self.run('''
        $a = array(5);
        $a[0] = 3+!($a=array(6, 7));
        echo $a[0], $a[1];
        ''')
        assert self.space.int_w(output[0]) == 3
        assert self.space.int_w(output[1]) == 7

    def test_array_store_order_2(self):
        output = self.run('''
        $a = array(5);
        $v = 5;
        $a[0] = 3+!($a=array(&$v, 7));
        echo $a[0], $a[1], $v;
        ''')
        assert self.space.int_w(output[0]) == 3
        assert self.space.int_w(output[1]) == 7
        assert self.space.int_w(output[2]) == 3

    def test_array_store_order_3(self):
        output = self.run('''
        $v = 5;
        $a = array(&$v);
        $b = $a[0] = count($a=array(6, 7, 8));
        echo $a[0], $b;
        echo $v;
        ''')
        assert self.space.int_w(output[0]) == 3
        assert self.space.int_w(output[1]) == 3
        assert self.space.int_w(output[2]) == 5

    def test_array_store_order_4(self):
        output = self.run('''
        $a = array(5, 0);
        $b = array(6, 1);
        $a[0] = count($a=&$b);
        echo $a[0], $a[1];
        ''')
        assert self.space.int_w(output[0]) == 2
        assert self.space.int_w(output[1]) == 1

    def test_array_store_order_5(self):
        output = self.run('''
        $a = array(10);
        $b = array(20);
        $c =& $a;
        $a[0] = !($a =& $b);
        echo $c[0], $b[0];
        ''')
        assert self.space.int_w(output[0]) == 10
        assert self.space.int_w(output[1]) == 0

    @hippy_fail(reason="obscure refcounting trick needed")
    def test_array_store_order_prelim(self):
        output = self.run('''
        $f = array(50);
        $f[0] = $f;
        echo $f[0] === $f;
        ''')
        assert self.space.int_w(output[0]) == 0
        output = self.run('''
        $f = array(50);
        $g =& $f;   // extra line
        $f[0] = $f;
        echo $f[0] === $f;
        ''')
        assert self.space.int_w(output[0]) == 1

    @hippy_fail(reason="obscure refcounting trick needed")
    def test_array_store_order_9(self):
        output = self.run('''
        $a = array(40);
        $c = array(50);
        $a0 =& $a;
        $a[0] = ($a =& $c);
        echo $a === $c;
        echo $a0[0] === 40;
        echo $c[0] === $a0;
        echo $c[0] === 50;
        echo gettype($c[0]);
        echo gettype($c[0][0]);
        echo gettype($c[0][0][0]);
        echo $c[0] === $c;
        ''')
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 1
        assert self.space.int_w(output[2]) == 0
        assert self.space.int_w(output[3]) == 0
        assert self.space.str_w(output[4]) == "array"
        assert self.space.str_w(output[5]) == "array"
        assert self.space.str_w(output[6]) == "array"
        assert self.space.int_w(output[7]) == 1

    def test_array_store_order_10(self):
        output = self.run('''
        $a = array(10);
        $b = array(20);
        $x = $a[(int)!($a=&$b)];
        echo $x;
        ''')
        assert self.space.int_w(output[0]) == 20

    def test_array_store_order_11(self):
        output = self.run('''
        $a = array(2=>array(4=>42));
        $n = 1;
        $x = $a[$n+=1][$n*=2];
        echo $x;
        ''')
        assert self.space.int_w(output[0]) == 42

    @py.test.mark.skipif("True", "recursion error both in hippy and in php")
    def test_recursive_array_identity(self):
        output = self.run('''
        $a = array(0); $a[0] =& $a;
        $b = array(0); $b[0] =& $b;
        echo $a === $a;
        echo $a === $b;
        ''')
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 1

    @py.test.mark.skipif("True", "recursion error both in hippy and in php")
    def test_recursive_array_difference(self):
        output = self.run('''
        $a = array(0, 42); $a[0] =& $a;
        $b = array(0, 43); $b[0] =& $b;
        echo $a === $a;
        echo $a === $b;
        ''')
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 0

    def test_dense_array_not_from_0(self):
        output = self.run('''
        $a = array();
        $a[10] = 5;
        echo $a[10];
        ''')
        assert self.space.int_w(output[0]) == 5

    def test_plusplus_on_array(self):
        output = self.run('''
        $a = array(10, 20, 30);
        echo $a[1]++;
        echo ++$a[2];
        echo $a[0];
        echo $a[1];
        echo $a[2];
        ''')
        assert [self.space.int_w(o) for o in output] == [20, 31, 10, 21, 31]

    def test_array_append_1(self):
        output = self.run('''
        $a = array();
        $b = $a[] = 42;
        echo $a, $b;
        ''')
        assert self.is_array(output[0], [self.space.newint(42)])
        assert self.space.is_w(output[1], self.space.newint(42))

    def test_array_append_2(self):
        output = self.run('''
        $a = array();
        $a[] = ($a[] = 42);
        echo $a;
        ''')
        assert self.is_array(output[0], [self.space.newint(42)] * 2)

    def test_array_append_unset(self):
        with self.warnings(['Fatal error: Cannot use [] for unsetting']):
            self.run('unset($a[]);')

    def test_array_append_isset(self):
        with self.warnings(['Fatal error: Cannot use [] for reading']):
            self.run('isset($a[]);')

    def test_array_append_empty(self):
        with self.warnings(['Fatal error: Cannot use [] for reading']):
            self.run('empty($a[]);')

    def test_array_append_ref(self):
        output = self.run('''
        $a = array();
        $a[] =& $b;
        echo $a[0];
        $b = 5;
        echo $a[0];
        ''')
        assert self.space.is_w(output[0], self.space.w_Null)
        assert self.space.int_w(output[1]) == 5

    def test_set_ref_array_append(self):
        output = self.run('''
        $a = array();
        $b =& $a[];
        echo $a[0];
        $b = 5;
        echo $a[0];
        ''')
        assert self.space.is_w(output[0], self.space.w_Null)
        assert self.space.int_w(output[1]) == 5

    def test_string_append(self):
        with self.warnings(['Fatal error: '
                '[] operator not supported for strings']):
            self.run('''
            $a = 'abc';
            $a[] = 'x';
            ''')

    def test_scalar_append(self):
        with self.warnings(['Warning: '
                'Cannot use a scalar value as an array'] * 2):
            output = self.run('''
            $a = 1;
            echo $a[] = 5;
            echo $a;
            $b = 1.;
            echo $b[] = 5;
            echo $b;
            ''')
        space = self.space
        for out, expected in zip(output, [space.w_Null, space.newint(1),
                space.w_Null, space.newfloat(1.)]):
            assert space.is_w(out, expected)

    def test_bool_append(self):
        with self.warnings(['Warning: Cannot use a scalar value as an array',
                'Hippy warning: Creating array from empty value']):
            output = self.run('''
            $a = true;
            echo $a[] = 5;
            echo $a;
            $b = false;
            echo $b[] = 5;
            echo $b;
            ''')
        space = self.space
        for out, expected in zip(output[:-1], [space.w_Null, space.w_True,
                space.newint(5)]):
            assert space.is_w(out, expected)
        assert self.is_array(output[-1], [space.newint(5)])

    def test_null_append(self):
        with self.warnings(['Hippy warning: Creating array from empty value']):
            output = self.run('''
            $a[] = 5;
            echo $a;
            ''')
        assert self.is_array(output[0], [self.space.newint(5)])

    def test_append_setitem(self):
        with self.warnings(['Hippy warning: '
                'Creating array from empty value'] * 2):
            output = self.run('''
            $x[][1] = 42;
            echo $x[0][1];
            ''')
        assert self.space.int_w(output[0]) == 42

    def test_append_setattr(self):
        with self.warnings(['Hippy warning: Creating array from empty value',
                'Warning: Creating default object from empty value']):
            output = self.run('''
            $x[]->foo = 42;
            echo $x[0]->foo;
            ''')
        assert self.space.int_w(output[0]) == 42

    @py.test.mark.parametrize('value',
            ['true', '1', '1.'])
    def test_appendref_scalar(self, value):
        with self.warnings(["Warning: Cannot use a scalar value as an array"]):
            output = self.run('''
            $x = %s;
            $a = 5;
            echo $x[] =& $a;
            echo $x;''' % value)
        assert self.space.is_w(output[0], self.space.w_Null)
        assert self.space.int_w(output[1]) == 1

    @py.test.mark.parametrize('value',
            ['null', 'false', '""'])
    def test_appendref_implicit_cast(self, value):
        with self.warnings(['Hippy warning: Creating array from empty value']):
            output = self.run('''
            $x = %s;
            $a = 5;
            echo $x[] =& $a;
            echo $x;''' % value)
        assert self.space.int_w(output[0]) == 5
        assert self.is_array(output[1], [self.space.newint(5)])

    def test_appendref_undefined(self):
        with self.warnings([
                "Hippy warning: Creating array from empty value"]):
            output = self.run('''
            $a = 42;
            $x[] =& $a;
            echo $x[0];
            ''')
        assert self.space.int_w(output[0]) == 42

    def test_array_obscure1(self):
        output = self.run('''
        $a = array(10);
        echo $a[0] * ($a[0]=5);
        ''')
        assert self.space.is_w(output[0], self.space.newint(50))

    def test_array_obscure1_2(self):
        output = self.run('''
        $a = array(10);
        $b = 5;
        echo $a[0] * ($a[0]=&$b);
        ''')
        assert self.space.is_w(output[0], self.space.newint(50))

    def test_evaluation_order_int(self):
        # same test as above, but using $v instead of $a[0], gives
        # different results
        output = self.run('''
        $v = 10;
        echo $v * ($v=5);
        ''')
        assert self.space.is_w(output[0], self.space.newint(25))

    def test_reference_array_obscure0(self):
        output = self.run('''
        $a = array(10);
        $b = 10;
        $a[0] = &$b;
        echo $a[0] * ($a[0]=5);
        ''')
        assert self.space.is_w(output[0], self.space.newint(25))

    def test_reference_array_obscure1(self):
        # just like test_array_obscure1, but because $a[0] is a reference,
        # the assignment $a[0]=5 really changes it in-place and then the
        # load of the value of the left-hand side of the '*' returns the
        # new value
        output = self.run('''
        $a = array(10);
        $a[0] = &$a[0];
        echo $a[0] * ($a[0]=5);
        ''')
        assert self.space.is_w(output[0], self.space.newint(25))

    @hippy_fail(reason="REFCOUNTING NEEDED")
    def test_reference_array_obscure2(self):
        output = self.run('''
        $v = 10;
        $a = array(&$v);
        echo $a[0] * ($a[0] = 5);
        ''')
        assert self.space.is_w(output[0], self.space.newint(25))
        output = self.run('''
        $v = 10;
        $a = array(&$v);
        $v = &$a;        // reference goes away
        echo $a[0] * ($a[0] = 5);
        ''')
        assert self.space.is_w(output[0], self.space.newint(50))

    @hippy_fail(reason="REFCOUNTING NEEDED")
    def test_reference_array_obscure3(self):
        # no no, this test really makes "sense" in the PHP world,
        # with enough levels of quotes around "sense"
        output = self.run('''
        $v = 10;
        $a = array(&$v);
        $v = &$a;
        echo $a[0] * ($a[0] = 5);   // 50
        $v = 10;
        $a = array(&$v);
        $v = &$a;
        echo $a[0] * ($a[0] = 5);   // 25
        echo $a;                    // 5
        ''')
        assert self.space.is_w(output[0], self.space.newint(50))
        assert self.space.is_w(output[1], self.space.newint(25))
        assert self.space.is_w(output[2], self.space.newint(5))

    def test_array_of_array(self):
        output = self.run('''
        $a = array();
        $b = array($a);
        $b[0][] = 3;
        echo !$a, $b[0][0];
        ''')
        assert self.space.is_w(output[0], self.space.newbool(True))
        assert self.space.is_w(output[1], self.space.newint(3))

    def test_array_of_array_2(self):
        output = self.run('''
        $a = array(array(42));
        $b = $a;
        $a[0][0] = 50;
        echo $b[0][0];
        ''')
        assert self.space.is_w(output[0], self.space.newint(42))

    def test_inplace_concat(self):
        output = self.run('''
        $a = "x";
        $a .= "y";
        echo $a;
        ''')
        assert self.space.str_w(output[0]) == "xy"

    def test_function_var_unused(self):
        self.run('''
        function f($a) {}
        f(3);
        ''')
        # this used to explode

    def test_inplace_str_concat(self):
        output = self.run('''
        $a = "abc";
        $b = $a;
        $b[0] = "x";
        $c = $a . $a;
        $d = $a;
        $e = $c;
        $e .= "0";
        $d .= "0";
        $c .= "0";
        $b .= "0";
        $a .= "0";
        echo $a, $b, $c, $d, $e;
        ''')
        assert [self.space.str_w(i) for i in output] == ["abc0", "xbc0",
                                                         "abcabc0", "abc0",
                                                         "abcabc0"]

    def test_if_expr(self):
        output = self.run('''
        $a = 1 ? 3 : 0;
        $b = 0 ? 5 : 7;
        echo $a, $b;
        ''')
        assert [self.space.int_w(i) for i in output] == [3, 7]

    def test_globals_locals(self):
        output = self.run('''
        function f() {
            $x = 3;
            echo $x;
            global $x;
            echo $x;
            $x = 5;
        }
        $x = 4;
        echo $x;
        f();
        echo $x;
        ''')
        exp1 = 4 if not isinstance(self, LocalRunTestInterpreter) else 0
        exp2 = 5 if not isinstance(self, LocalRunTestInterpreter) else 4
        assert [self.space.int_w(i) for i in output] == [4, 3, exp1, exp2]

    def test_const(self):
        output = self.run("""
        define('x', 13);
        echo x;
        """)
        assert self.space.int_w(output[0]) == 13

    def test_const_2(self):
        output = self.run("""
        function f() {
            define('x', 13);
        }
        f();
        echo x;
        """)
        assert self.space.int_w(output[0]) == 13

    def test_mod(self):
        output = self.run('''
        echo 15 % 2, 14 % 2;
        ''')  # XXX negative values
        assert [self.space.int_w(i) for i in output] == [1, 0]

    def test_mod_by_zero(self):
        with self.warnings(["Warning: Division by zero"]):
            output = self.run("echo 42 % 0;")
        assert output == [self.space.w_False]

    def test_string_interpolation(self):
        output = self.run("""
        $x = 'abc';
        $y = 1;
        echo "$x$y";
        echo "$x[$y]";
        echo "\${x$x[$y]$x}";
        """)
        assert map(self.space.str_w, output) == ['abc1', 'b', '${xbabc}']

    @py.test.mark.skipif("config.option.runappdirect")
    def test_string_interpolation_newline_var(self):
        output = self.run('''
        $s = "\\n";
        echo $s;
        echo "$s :-) \$s";
        echo "\\t";
        ''')
        assert self.space.str_w(output[0]) == '\n'
        assert self.space.str_w(output[1]) == '\n :-) $s'
        assert self.space.str_w(output[2]) == '\t'

    def test_single_quoted_string(self):
        output = self.run(r"""
        echo 'foo\'bar\nbaz';
        """)
        assert self.space.str_w(output[0]) == "foo'bar\\nbaz"

    def test_prebuilt_consts(self):
        output = self.run('''
        echo TRUE, FALSE, NULL;
        echo TrUe, FaLsE, NuLl;
        echo tRuE, fAlSe, nUlL;
        ''')
        assert [self.space.is_true(i) for i in output] == (
            [True, False, False] * 3)

    def test_do_while(self):
        output = self.run('''
        $x = 0;
        do { $x++; } while ($x < 10);
        echo $x;
        ''')
        assert self.space.int_w(output[0]) == 10

    def test_inplace_shift(self):
        output = self.run('''
        $x = 1;
        $x <<= 2;
        echo $x;
        $x >>= 1;
        echo $x;
        ''')
        assert [self.space.int_w(i) for i in output] == [1 << 2, 1 << 1]

    @hippy_fail(reason='precision issues in str to float conversions')
    def test_mixed_eq(self):
        output = self.run('''
        echo "abc" == "abc", "abc" != "abc";
        echo "abc" == "abcc", "abc" != "abcc";
        echo 1 == "1bc", "1bc" == 1;
        echo 1.2 == 1, 1 == 1.2, 1 == 1.0, 1.0 == 1;
        echo NULL == NULL, NULL == 0, 1 == NULL;
        echo 55123.456 == '55123.456', 55123.456 <> '55123.456';
        ''')
        assert [self.space.is_true(i) for i in output] == [
            True, False, False, True, True, True, False, False, True, True,
            True, True, False, True, False]

    def test_mixed_str_eq(self):
        output = self.run('''
        $a = "abc";
        $b = $a;
        $b[0] = "a";
        $c = $a + "";
        $d = $a;
        echo $a == $a, $b == $b, $c == $c, $d == $d;
        ''')
        assert [self.space.is_true(i) for i in output] == [
            True, True, True, True]

    def test_global_in_global(self):
        self.run('''
        global $x;
        ''')
        # assert did not crash

    def test_invariant_global_namespace(self):
        output = self.run('''
        echo TruE;
        ''')
        assert self.space.is_true(output[0])

    def test_triple_eq(self):
        output = self.run('''
        echo 1.0 === 1;
        echo 1 === 1;
        echo 1 === true;
        ''')
        assert not self.space.is_true(output[0])
        assert self.space.is_true(output[1])
        assert not self.space.is_true(output[2])

    def test_triple_ne(self):
        output = self.run('''
        echo 1.0 !== 1;
        echo 1 !== 1;
        echo 1 !== true;
        ''')
        assert self.space.is_true(output[0])
        assert not self.space.is_true(output[1])
        assert self.space.is_true(output[2])

    def test_dynamic_call(self):
        output = self.run('''
        function f($a, $b) {
           return $a + $b;
        }
        $c = "f";
        echo $c(1, 2);
        ''')
        assert self.space.int_w(output[0]) == 3

    @hippy_fail(reason="parsing error")
    def test_complex_dynamic_call(self):
        output = self.run('''
        function foo() {return 42;}
        $x->foo[5] = "foo";
        echo $x->foo[5]();
        ''')
        assert self.space.int_w(output[0]) == 42

    def test_call_array_1(self):
        output = self.run('''
        class foo {
            static function bar() {return 42;}
        }
        $a = array('foo', 'bar');
        echo $a();
        ''')
        assert self.space.int_w(output[0]) == 42

    def test_call_array_2(self):
        output = self.run('''
        class foo {
            function bar() {return 42;}
        }
        $a = array(new Foo, 'bar');
        echo $a();
        ''')
        assert self.space.int_w(output[0]) == 42

    def test_call_array_error_1(self):
        with self.warnings(["Fatal error: Function name must be a string"]):
            self.run('''
            class foo {
                static function bar() {return 42;}
            }
            $a = array('foo', 'bar', 'baz');
            echo $a();
            ''')

    def test_call_array_error_2(self):
        with self.warnings(["Fatal error: "
                "Array callback has to contain indices 0 and 1"]):
            self.run('''
            class foo {
                static function bar() {return 42;}
            }
            $a = array('foo', 2 => 'bar');
            echo $a();
            ''')

    def test_call_array_error_3(self):
        with self.warnings(["Fatal error: "
                "First array member is not a valid class name or object"]):
            self.run('''
            class foo {
                static function bar() {return 42;}
            }
            $a = array(0, 'bar');
            echo $a();
            ''')

    def test_call_array_error_4(self):
        with self.warnings(["Fatal error: "
                "Second array member is not a valid method"]):
            self.run('''
            class foo {
                static function bar() {return 42;}
            }
            $a = array('foo', 0);
            echo $a();
            ''')

    def test_call_array_error_5(self):
        with self.warnings(["Fatal error: "
                "Class 'bar' not found"]):
            self.run('''
            class foo {
                static function bar() {return 42;}
            }
            $a = array('bar', 'bar');
            echo $a();
            ''')

    def test_call_array_error_6(self):
        with self.warnings(["Fatal error: "
                "Call to undefined method foo::FOO()"]):
            self.run('''
            class foo {
                static function bar() {return 42;}
            }
            $a = array('FOO', 'FOO');
            echo $a();
            ''')

    def test_call_array_error_7(self):
        with self.warnings(["Fatal error: "
                "Call to undefined method foo::__construct()"]):
            self.run('''
            class foo {}
            $a = array('FOO', '__construct');
            echo $a();
            ''')

    def test_assignment_in_and(self):
        output = self.run('''
        $a = 3;
        $a && $b = "x";
        echo $b;
        ''')
        assert self.space.str_w(output[0]) == 'x'

    def test_global_no_local(self):
        output = self.run('''
        function f() {
           global $aa;
           $aa = 3;
           return $aa;
        }
        echo f();
        ''')
        assert self.space.int_w(output[0]) == 3

    def test_global_store(self):
        output = self.run('''
        function f() {
           global $a;
           $b = $a;
           echo $b;
        }
        $a = 3;
        f();
        ''')
        expected = 3 if not isinstance(self, LocalRunTestInterpreter) else 0
        assert self.space.int_w(output[0]) == expected

    def test_superglobals(self):
        expected_warnings = (['Notice: Undefined index: a']
                             if isinstance(self, LocalRunTestInterpreter)
                             else [])
        output = self.run('''
        function f() {
           return $GLOBALS["a"];
        }
        $a = 3;
        echo f();
        ''', expected_warnings)
        expected = 3 if not isinstance(self, LocalRunTestInterpreter) else 0
        assert self.space.int_w(output[0]) == expected

    def test_superglobals_assign(self):
        expected_warnings = (['Notice: Undefined variable: b']
                             if isinstance(self, LocalRunTestInterpreter)
                             else [])
        output = self.run('''
        function f() {
            global $b;
            $GLOBALS['b'] = 43;
            echo $b;
        }
        function g() {
            global $b;
            echo $b;
        }
        f();
        echo $b;
        g();
        ''', expected_warnings)
        expected = 43 if not isinstance(self, LocalRunTestInterpreter) else 0
        assert [self.space.int_w(i) for i in output] == [43, expected, 43]

    def test_superglobals_write(self):
        expected_warnings = (['Notice: Undefined variable: c']
                             if isinstance(self, LocalRunTestInterpreter)
                             else [])
        output = self.run('''
        $GLOBALS["c"] = 42;
        echo $c;
        ''', expected_warnings)
        expected = 42 if not isinstance(self, LocalRunTestInterpreter) else 0
        assert self.space.int_w(output[0]) == expected

    def test_null_eq(self):
        output = self.run('''
        $a = "x";
        echo $a == null, null == $a, null == null;
        echo $a != null, null != $a, null != null;
        ''')
        assert [i.boolval for i in output] == [False, False, True,
                                               True, True, False]

    def test_hash_of_a_copy_of_concat(self):
        output = self.run('''
        $a = "x";
        $b = $a . $a;
        $c = $b;
        $x = array();
        $x[$c] = 3;
        echo $x["xx"];
        ''')
        assert self.space.int_w(output[0]) == 3

    def test_hash_order_1(self):
        output = self.run('''
        $a = 5;
        $x = array($a, $a+=1);
        echo $x[0], $x[1];
        ''')
        assert self.space.int_w(output[0]) == 5
        assert self.space.int_w(output[1]) == 6

    def test_hash_order_2(self):
        output = self.run('''
        $a = 5;
        $x = array($a=>($a+=1));
        echo $x[6];
        ''')
        assert self.space.int_w(output[0]) == 6

    def test_hash_order_3(self):
        output = self.run('''
        $a = 5;
        $x = array(($a+=1)=>$a);
        echo $x[6];
        ''')
        assert self.space.int_w(output[0]) == 6

    def test_hash_order_4(self):
        output = self.run('''
        $a = 5;
        $x = array($a=>42, 11=>($a+=1));
        echo $x[5], $x[11];
        ''')
        assert self.space.int_w(output[0]) == 42
        assert self.space.int_w(output[1]) == 6

    def test_hash_order_5(self):
        output = self.run('''
        $a = 5;
        $x = array(11=>($a+=1), $a=>42);
        echo $x[11], $x[6];
        ''')
        assert self.space.int_w(output[0]) == 6
        assert self.space.int_w(output[1]) == 42

    def test_hash_order_6(self):
        output = self.run('''
        $a = 5;
        $x = array(($a+=1)=>($a*=2));
        echo $x[6];
        ''')
        assert self.space.int_w(output[0]) == 12

    def test_reference_error_to_argument(self):
        self.run('''
        { function f(&$x) { } f(42); }
        ''', ['Fatal error: Cannot pass parameter 1 by reference'])

    def test_reference_to_a_reference(self):
        output = self.run('''
        function f(&$x) {
            $x = 3;
        }
        function g() {
            $x = 2;
            f($x);
            return $x;
        }
        echo g();
        ''')
        assert self.space.int_w(output[0]) == 3

    def test_function_returns_reference_0(self):
        output = self.run('''
        function &f(&$x) { return $x; }
        $a = array(5);
        $b = &f($a);
        $b[0] = 6;
        echo $a[0];
        ''')
        assert self.space.int_w(output[0]) == 6

    def test_function_returns_reference_1(self):
        output = self.run('''
        function &f(&$x) {
            $y = &$x[0];
            return $y;
        }
        $a = array(array(5));
        $b = &f($a);
        $b[0] = 6;
        echo $a[0][0];
        ''')
        assert self.space.int_w(output[0]) == 6

    def test_function_returns_reference_2(self):
        output = self.run('''
        function &f(&$x) {
            $y = &$x[0];
            return $y;
        }
        $a = array(array(5));
        $b = f($a);
        $b[0] = 6;
        echo $a[0][0];
        ''')               # missing '&' in front of the call to f()
        assert self.space.int_w(output[0]) == 5

    def test_function_returns_reference_3(self):
        with self.warnings(['Strict Standards: '
                'Only variables should be assigned by reference']):
            output = self.run('''
            function f(&$x) {
                $y = &$x[0];
                return $y;
            }
            $a = array(array(5));
            $b = &f($a);
            $b[0] = 6;
            echo $a[0][0];
            ''')    # missing '&' in front of the function declaration
        assert self.space.int_w(output[0]) == 5

    def test_function_returns_reference_4(self):
        output = self.run('''
        function &f(&$x) {
            $y = &$x[0];
            return $y;
        }
        function g(&$x) {
            $x[0] = 6;
        }
        $a = array(array(5));
        g(f($a));
        echo $a[0][0];
        ''')               # passing a reference directly to another call
        assert self.space.int_w(output[0]) == 6

    def test_function_returns_reference_5(self):
        output = self.run('''
        function &f(&$x) {
            $y = &$x[0];
            return $y;
        }
        function g($x) {
            $x[0] = 6;
        }
        $a = array(array(5));
        g(f($a));
        echo $a[0][0];
        ''')               # missing '&' in the argument in g()
        assert self.space.int_w(output[0]) == 5

    def test_function_returns_reference_5bis(self):
        with self.warnings(['Strict Standards: '
                'Only variables should be passed by reference']):
            output = self.run('''
            function f(&$x) {
                $y = &$x[0];
                return $y;
            }
            function g(&$x) {
                $x[0] = 6;
            }
            $a = array(array(5));
            g(f($a));
            echo $a[0][0];
            ''')               # missing '&' in the return from f()
        assert self.space.int_w(output[0]) == 5

    def test_function_returns_reference_6(self):
        output = self.run('''
        function &f(&$x) {
            $y = &$x[0];
            return $y;
        }
        $a = array(array(5));
        $b = array(f($a));
        $b[0] = "foo";
        echo $a[0][0];
        ''')
        assert self.space.int_w(output[0]) == 5

    def test_function_returns_reference_7(self):
        output = self.run('''
        function &f(&$x) {
            $y = &$x[0];
            return $y;
        }
        function makearray(&$a) {
            return array(&$a);
        }
        $a = array(array(5));
        $b = makearray(f($a));
        $b[0][0] = 6;
        echo $a[0][0];
        ''')
        assert self.space.int_w(output[0]) == 6

    def test_function_returns_reference_8(self):
        output = self.run('''
        function &f(&$x) {
            return $x[];
        }
        $a = array(4, 5, 6);
        $b = &f($a);
        echo gettype($a[3]);
        echo gettype($b);
        $b = 42;
        echo $a[3];
        ''')
        assert self.space.str_w(output[0]) == 'NULL'
        assert self.space.str_w(output[1]) == 'NULL'
        assert self.space.str_w(output[2]) == '42'

    def test_assign_to_function_result(self):
        with self.warnings(["Fatal error: "
                "Can't use function return value in write context"]):
            self.run('''
            function f(){}
            f() = 2;
            ''')

    def test_assign_to_function_result_2(self):
        with self.warnings(["Fatal error: "
                "Can't use function return value in write context"]):
            self.run('''
            function &f(){}
            f() = 2;
            ''')

    def test_assign_to_function_result_3(self):
        with self.warnings(["Fatal error: "
                "Can't use function return value in write context"]):
            self.run('''
            function &f($x){return $x;}
            f($x) = 2;
            ''')

    def test_function_mixed_case(self):
        output = self.run('''
        function F(){
            return 3;
        }
        echo f();
        ''')
        assert self.space.int_w(output[0]) == 3

    def test_global_2(self):
        output = self.run('''
        function f() {
          global $x;
          $x = 3;
        }
        function g() {
          global $x;
          echo $x;
        }
        g(); f(); g();
        ''')
        assert self.space.w_Null is output[0]
        assert self.space.int_w(output[1]) == 3

    def test_static_var(self):
        output = self.run('''
        function f() {
           $a = 15;
           static $a = 0;
           $a++;
           echo $a;
        }
        f(); f(); f(); f();
        ''')
        assert [self.space.int_w(i) for i in output] == [1, 2, 3, 4]

    def test_double_static_declarations(self):
        output = self.run('''
        function f() {
           static $a = 10;
           echo $a;
           static $a = 20;
           echo $a;
        }
        f();
        ''', ["Hippy warning: Static variable 'a' declared twice, "
              "ignoring previous declaration"])
        assert [self.space.int_w(i) for i in output] == [20, 20]

    def test_double_static_declarations_uninit(self):
        output = self.run('''
        function f() {
           static $a = 10;
           echo $a;
           static $a;    // equivalent to: static $a = NULL;
           echo $a;
        }
        f();
        ''', ["Hippy warning: Static variable 'a' declared twice, "
              "ignoring previous declaration"])
        assert [self.space.str_w(i) for i in output] == ['', '']  # NULL, NULL

    def test_default_args(self):
        output = self.run('''
        function f($n = 10) {
           echo $n;
        }
        f();
        f(5);
        ''')
        assert [self.space.int_w(i) for i in output] == [10, 5]

    def test_constant_default(self):
        output = self.run('''
        function f($n = PHP_MAJOR_VERSION) {
        echo $n;
        }
        f();
        ''')
        assert [self.space.int_w(i) for i in output] == [5]

    def test_unknown_constant_default(self):
        with self.warnings([
                "Notice: Use of undefined constant DOES_NOT_COMPUTE "
                "- assumed 'DOES_NOT_COMPUTE'"]):
            output = self.run('''
            function f($n = DOES_NOT_COMPUTE) {
            echo $n;
            }
            f();
            ''')
        assert [self.space.str_w(i) for i in output] == ["DOES_NOT_COMPUTE"]

    def test_bit_or(self):
        output = self.run('''
        echo 1 | 2;
        ''')
        assert self.space.int_w(output[0]) == 3

    def test_evaluation_order_str(self):
        output = self.run('''
        $A = "xx"; $a = 0;
        $A[$a] = ++$a;        // changes $A[1]
        echo $A;
        ''')
        assert self.space.str_w(output[0]) == "x1"

        output = self.run('''
        $B = "xx"; $b = 0;
        $B[++$b] = ++$b;      // changes $B[1]
        echo $B;
        ''')
        assert self.space.str_w(output[0]) == "x2"

        output = self.run('''
        $C = "xx"; $c = 0;
        $C[$c+=0] = ++$c;     // changes $C[0]
        echo $C;
        ''')
        assert self.space.str_w(output[0]) == "1x"

        output = self.run('''
        $D = "xxx"; $d = 0;
        $D[$d+=1] = ++$d;     // changes $D[1]
        echo $D;
        ''')
        assert self.space.str_w(output[0]) == "x2x"

        output = self.run('''
        $E = "xxx"; $e = 0;
        $E[$e=1] = ++$e;      // changes $E[1]
        echo $E;
        ''')
        assert self.space.str_w(output[0]) == "x2x"

        output = self.run('''
        $F = "xxx"; $f = 0; $s = "x";
        $F[$s[0]=$f] = ++$f;      // changes $F[0]
        echo $F . $s;
        ''')
        assert self.space.str_w(output[0]) == "1xx0"

    def test_evaluation_order_array(self):
        output = self.run('''
        $A = array(9, 9); $a = 0;
        $A[$a] = ++$a;        // changes $A[1]
        echo $A[0], $A[1];
        ''')
        assert self.space.int_w(output[0]) == 9
        assert self.space.int_w(output[1]) == 1

        output = self.run('''
        $B = array(9, 9); $b = 0;
        $B[++$b] = ++$b;      // changes $B[1]
        echo $B[0], $B[1];
        ''')
        assert self.space.int_w(output[0]) == 9
        assert self.space.int_w(output[1]) == 2

        output = self.run('''
        $C = array(9, 9); $c = 0;
        $C[$c+=0] = ++$c;     // changes $C[0]
        echo $C[0], $C[1];
        ''')
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 9

    def test_store_character(self):
        output = self.run('$a="x";\necho gettype($a[0]=5);')
        assert self.space.str_w(output[0]) == "string"

    def test_array_collisions(self):
        output = self.run('$a = array(0=>5, 0=>6);\necho $a[0];')
        assert self.space.int_w(output[0]) == 6
        output = self.run('''
        $b = 5;
        $a = array(0=>&$a, 0=>6);
        echo $b;
        ''')
        assert self.space.int_w(output[0]) == 5
        output = self.run('''
        $b = 5;
        $a = array($b, $b=7);
        echo $a[0];
        ''')
        assert self.space.int_w(output[0]) == 5
        output = self.run('''
        $key = "key";
        $a = array($key=>5, $key="bar");
        echo $a["key"];
        ''')
        assert self.space.int_w(output[0]) == 5
        output = self.run('''
        $key = "key";
        $a = array($key="bar", $key=>5);
        echo $a["bar"];
        ''')
        assert self.space.int_w(output[0]) == 5

    def test_getitem_does_not_create(self):
        output = self.run('''
        $a = array();
        $b = $a[0];   // NULL, but not stored in $a
        echo count($a);
        $a[] = 5;
        echo $a[0];
        $a["foo"];
        echo count($a);
        ''', ['Notice: Undefined offset: 0',
              'Notice: Undefined index: foo'])
        assert [self.space.int_w(i) for i in output] == [0, 5, 1]

    def test_function_call_difference_based_on_actual_parameter(self):
        with self.warnings(['Notice: Undefined offset: 0',
                'Notice: Undefined index: foo']):
            output = self.run('''
            function f1($a, $i) { g1($a[$i]); return $a; } //does not create $a[$i]
            function f2($a, $i) { g2($a[$i]); return $a; } //creates $a[$i]
            function g1($x) { }
            function g2(&$x) { }
            echo count(f1(array(), 0));
            echo count(f2(array(), 0));
            echo count(f1(array(), "foo"));
            echo count(f2(array(), "foo"));
            ''')

        assert [self.space.int_w(i) for i in output] == [0, 1, 0, 1]

    def test_function_call_difference_based_on_actual_parameter_lazy(self):
        source = '''
        function f1($a, $j) { h1($j); g1($a[0]); return $a; }
        function h1($j) {
            if ($j == 5) {
                function g1($x) { }
            } else {
                function g1(&$x) { }
            }
        }
        '''
        with self.warnings(['Notice: Undefined offset: 0']):
            output1 = self.run(source + 'echo count(f1(array(), 5));')
        assert self.space.int_w(output1[0]) == 0
        #
        output2 = self.run(source + 'echo count(f1(array(), 3));')
        assert self.space.int_w(output2[0]) == 1

    def test_function_call_must_be_a_string(self):
        self.run('''
        $x = 42;
        $x();
        ''', ["Fatal error: Function name must be a string"])

    def test_function_call_difference_based_on_actual_parameter_dyn(self):
        with self.warnings(['Notice: Undefined offset: 0']):
            output = self.run('''
            function f1($name, $a) { $x = $name(count($a), $a[0], count($a));
                                    return $x + 100 * count($a); }
            function g1($m, $x, $n) { return 10+$n+1000*$m; }
            function g2($m, &$x, $n) { return 20+$n+1000*$m; }
            echo f1("g1", array());
            echo f1("g2", array());
            ''')
        assert [self.space.int_w(i) for i in output] == [10, 121]

    def test_function_call_argument_eval_order_1(self):
        output = self.run('''
        function f($a, $b) {
           echo $a, $b;
        }
        $x = 10;
        f($x, $x=12);
        ''')
        assert [self.space.int_w(i) for i in output] == [10, 12]

    def test_function_call_argument_eval_order_2(self):
        output = self.run('''
        function f(&$a, $b) {    // <-- difference with the previous test
           echo $a, $b;
        }
        $x = 10;
        f($x, $x=12);
        ''')
        assert [self.space.int_w(i) for i in output] == [12, 12]

    def test_builtin_function_call_argument_eval_order(self):
        output = self.run('''
        $x = 2;
        echo pow($x, $x=3);
        $y = 3;
        echo max($y, $y=1, $y);
        ''')
        assert self.space.float_w(output[0]) == 8.0
        assert self.space.int_w(output[1]) == 3

    def test_function_call_undeclared_var_1(self):
        with self.warnings(['Notice: Undefined variable: dummy']):
            self.run('''
            function f($x) { }
            f($dummy);
            ''')

    def test_function_call_undeclared_var_2(self):
        self.run('''
        function f(&$x) { }
        f($dummy);
        ''')

    def test_foreach_1(self):
        output = self.run('''
        $a = array(10, 20, 30, 40);
        foreach($a as $n) {
            echo $n;
        }
        ''')
        assert [self.space.int_w(i) for i in output] == [10, 20, 30, 40]

    def test_foreach_2(self):
        output = self.run('''
        $a = array(10, 20, 30, 40);
        foreach($a as $k => $n) {
            echo gettype($k);
            echo $k;
            echo $n;
        }
        ''')
        assert [self.space.str_w(i) for i in output] == [
            'integer', '0', '10',
            'integer', '1', '20',
            'integer', '2', '30',
            'integer', '3', '40']

    def test_foreach_3(self):
        output = self.run('''
        $a = array("0"=>10, "1"=>20, "2"=>30, "3"=>40);
        foreach($a as $k => $n) {
            echo gettype($k);
            echo $k;
            echo $n;
        }
        ''')
        assert [self.space.str_w(i) for i in output] == [
            'integer', '0', '10',
            'integer', '1', '20',
            'integer', '2', '30',
            'integer', '3', '40']

    def test_foreach_4(self):
        output = self.run('''
        $a = array(10, 20, 30, 40);
        $c = 0;
        $b = array(1=>&$c);
        foreach($a as $k => $b[1]) {
            echo $c;
        }
        ''')
        assert [self.space.int_w(i) for i in output] == [10, 20, 30, 40]

    def test_foreach_ref_1(self):
        output = self.run('''
        $a = array(10, 20, 30, 40);
        foreach($a as &$n) {
            $n *= 10;
        }
        echo $a[0];
        echo $a[3];
        ''')
        assert [self.space.int_w(i) for i in output] == [100, 400]

    def test_foreach_ref_2(self):
        output = self.run('''
        $a = array(10, 20, 30, 40);
        foreach($a as $k => &$n) {
            echo gettype($k);
            echo $k;
            echo $n++;
        }
        echo $a[0];
        echo $a[3];
        ''')
        assert [self.space.str_w(i) for i in output] == [
            'integer', '0', '10',
            'integer', '1', '20',
            'integer', '2', '30',
            'integer', '3', '40',
            '11', '41']

    def test_foreach_ref_3(self):
        output = self.run('''
        $a = array(10, 20, 30, 40);
        $c = 0;
        $b = array(1=>&$c);
        foreach($a as $k => &$b[1]) {
            echo $b[1];
            echo $c;
        }
        ''')
        assert [self.space.int_w(i) for i in output] == [
            10, 0, 20, 0, 30, 0, 40, 0]

    def test_foreach_ref_cornercase_1(self):
        output = self.run('''
        $a = array(10);
        foreach($a as &$v) {
            echo $v;
            $a[] = 42;
        }
        ''')
        assert [self.space.int_w(i) for i in output] == [10]

    def test_foreach_ref_cornercase_2(self):
        output = self.run('''
        $a = array(10, 20);
        $n = 8;
        foreach($a as &$v) {
            if (!--$n) break;
            echo $v;
            $a[] = 42;
        }
        ''')
        assert [self.space.int_w(i) for i in output] == [
            10, 20, 42, 42, 42, 42, 42]

    def test_foreach_unset(self):
        output = self.run('''
        $a = array(10, 20);
        foreach($a as $k=>$v) {
            unset($a[$k]);
        }
        echo count($a);
        ''')
        assert self.space.int_w(output[0]) == 0


    def test_foreach_unset_2(self):
        output = self.run('''
        $a = array(10, 20);
        foreach($a as $v) {
            echo $v;
            unset($a[1]);
        }
        echo count($a);
        ''')
        assert [self.space.int_w(i) for i in output] == [10, 20, 1]

    def test_foreach_unset_3(self):
        output = self.run('''
        $a = array(10, 20);
        foreach($a as &$v) {
            echo $v;
            unset($a[1]);
        }
        echo count($a);
        ''')
        assert [self.space.int_w(i) for i in output] == [10, 1]


    def test_foreach_unset_4(self):
        output = self.run('''
        $a = array('a' => 10, 'b' => 20);
        foreach($a as &$v) {
            echo $v;
            unset($a['b']);
        }
        echo count($a);
        ''')
        assert [self.space.int_w(i) for i in output] == [10, 1]

    def test_foreach_ref_unset(self):
        output = self.run('''
        $a = array(10, 20);
        foreach($a as $k=>&$v) {
            unset($a[$k]);
        }
        echo count($a);
        ''')
        assert self.space.int_w(output[0]) == 0

    def test_unset_2(self):
        output = self.run('''
        function destroy_bar() {
            global $bar;
            unset($bar);
        }
        $bar = "baz";
        destroy_bar();
        echo $bar;
        ''')
        assert self.space.str_w(output[0]) == 'baz'

    def test_unset_3(self):
        expected_warnings = (['Notice: Undefined variable: bar']
                             if not isinstance(self, LocalRunTestInterpreter)
                             else [])
        with self.warnings(expected_warnings):
            output = self.run('''
            function destroy_bar() {
                unset($GLOBALS['bar']);
            }
            $bar = "baz";
            $baz = &$bar;
            destroy_bar();
            echo gettype($bar);
            echo gettype($baz);
            ''')
        expected = ('NULL' if not isinstance(self, LocalRunTestInterpreter)
                    else 'string')
        assert self.space.str_w(output[0]) == expected
        assert self.space.str_w(output[1]) == 'string'

    def test_unset_4(self):
        output = self.run('''
        function foo(&$bar) {
            unset($bar);
            echo empty($bar);
            $bar = "othervalue";
            echo $bar;
        }
        $bar = "baz";
        foo($bar);
        echo $bar;
        ''')
        assert self.space.int_w(output[0]) == 1
        assert self.space.str_w(output[1]) == 'othervalue'
        assert self.space.str_w(output[2]) == 'baz'

    def test_unset_5(self):
        output = self.run('''
        function foo() {
            static $bar;
            $bar++;
            echo $bar;
            unset($bar);
            $bar = 23;
            echo $bar;
        }
        foo();
        foo();
        foo();
        ''')
        assert [self.space.int_w(i) for i in output] == [
            1, 23, 2, 23, 3, 23]

    def test_unset_6(self):
        output = self.run('''
        $v = 42;
        $a = array(&$v);
        unset($a[0]);
        echo $v;
        ''')
        assert self.space.int_w(output[0]) == 42
        output = self.run('''
        $v = 42;
        $a = array(&$v);
        $a[0] = NULL;
        echo gettype($v);
        ''')
        assert self.space.str_w(output[0]) == 'NULL'

    def test_unset_double_dollar(self):
        output = self.run('''
        $name = 'a';
        unset($$name);
        $a = 42;
        unset($$name);
        echo isset($a);
        $name = 'b';
        $$name = 43;
        echo $$name;
        unset($$name);
        echo isset($$name);
        ''')
        assert map(self.space.int_w, output) == [0, 43, 0]

    @py.test.mark.parametrize('value', [('true', 'boolean'),
                                        ('1', 'integer'),
                                        ('1.', 'double')])
    def test_unsetitem_scalar(self, value):
        with self.warnings(['Hippy warning: Cannot use %s as an array' %
                            value[1]]):
            output = self.run('''
            $x = %s;
            unset($x[0]);
            echo $x;''' % value[0])
        assert self.space.int_w(output[0]) == 1

    @py.test.mark.parametrize('value', [('null', 'null'),
                                        ('false', 'boolean')])
    def test_unsetitem_nulls(self, value):
        with self.warnings(['Hippy warning: Cannot use %s as an array' %
                            value[1]]):
            output = self.run('''
            $x = %s;
            unset($x[0]);
            echo $x;''' % value[0])
        assert self.space.int_w(output[0]) == 0

    def test_unset_nested_item(self):
        output = self.run('''
        $a = array('foo' => array('bar' => 42));
        unset($a['foo']['bar']);
        echo isset($a['foo']['bar']);
        echo isset($a['foo']);
        ''')
        assert output == [w_False, w_True]

    def test_unsetitem_of_item_of_scalar(self):
        with self.warnings(['Warning: '
                'Cannot unset offset in a non-array variable']):
            self.run('''
            $x = 0;
            unset($x[0][0]);
            ''')

    def test_unset_call_result(self):
        with self.warnings(["Fatal error: "
                "Can't use function return value in write context"]):
            self.run('''
            function foo(&$x) {return $x;}
            $x = 42;
            unset(foo($x));
            ''')

    def test_isset_effects(self):
        output = self.run('''
        isset($x[1][2][3]);
        echo isset($x);
        isset($x->a->b->c);
        echo isset($x);
        ''')
        assert map(self.space.int_w, output) == [0, 0]

    def test_unset_effects_ignoring_warnings(self):
        with self.warnings():
            output = self.run('''
            unset($x[1][2][3]);
            echo isset($x);
            unset($x->a->b->c);
            echo isset($x);
            ''')
        assert map(self.space.int_w, output) == [0, 0]

    @hippy_fail(reason='missing notices')
    def test_unset_effects(self):
        zend_warnings = ["Notice: Undefined variable: x",
                "Notice: Undefined variable: x",
                "Warning: Attempt to modify property of non-object"]
        with self.warnings(zend_warnings):
            output = self.run('''
            unset($x[1][2][3]);
            echo isset($x);
            unset($x->a->b->c);
            echo isset($x);
            ''')
        assert map(self.space.int_w, output) == [0, 0]

    @py.test.mark.skipif("config.option.runappdirect")
    def test_float_constants(self):
        output = self.run('''
        echo INF;
        echo -INF;
        echo NAN;
        echo INF-INF;
        ''')
        assert [self.space.str_w(i) for i in output] == ['INF', '-INF',
                                                         'NAN', 'NAN']
        output = self.run('''
        echo %d;
        ''' % (-sys.maxint - 1,))
        assert self.space.float_w(output[0]) == -float(sys.maxint + 1)

    def test_class_gettype(self):
        output = self.run('''
        class A { };
        echo gettype(new A);
        ''')
        assert self.space.str_w(output[0]) == "object"

    def test_slow_eq_lt_le_gt_ge(self):
        from itertools import product
        _input = ['TRUE', 'FALSE', 1, 0, -1, '"1"', '"0"', '"-1"',
                  'NULL', 'array()', '"php"', '""', '1.30', '1.3',
                  '"1.30"', '"1.3"', 'array(0, 1, 2)',
                  'array(0=>1, 1=>1, 2=>2)',
                  'array("0", "1", "2")',
                  'array("0"=>"1", "1"=>"1", "2"=>"2")',
                  'array("0", "1", "2", "php")',
                  'array("0"=>"1", "1"=>"1", "2"=>"2", 4=>"php")',
                  'INF', '-INF'
                  ]

        eq_result = "101011010010111111111111010100101101000000000000"
        eq_result += "10100100000000000000000001010010101100000000000"
        eq_result += "01000100100000000000000001010010000000000000000"
        eq_result += "00010100100000000000000000100010010000000000000"
        eq_result += "00001010000110100000000000001000000110000000000"
        eq_result += "00001001000000100000000000000101000010010000000"
        eq_result += "00000100000000000111100000000100000000000111100"
        eq_result += "00000010000000000011110000000010000000000011110"
        eq_result += "00000001000000000000000101000001000000000000000"
        eq_result += "01010000100000000000000010100000100000000000000"
        eq_result += "00101000010000000000000000000100010000000000000"
        eq_result += "00000001001000000000000000000000101000000000000"
        eq_result += "00000000001"

        ne_result = "010100101101000000000000101011010010111111111111"
        ne_result += "01011011111111111111111110101101010011111111111"
        ne_result += "10111011011111111111111110101101111111111111111"
        ne_result += "11101011011111111111111111011101101111111111111"
        ne_result += "11110101111001011111111111110111111001111111111"
        ne_result += "11110110111111011111111111111010111101101111111"
        ne_result += "11111011111111111000011111111011111111111000011"
        ne_result += "11111101111111111100001111111101111111111100001"
        ne_result += "11111110111111111111111010111110111111111111111"
        ne_result += "10101111011111111111111101011111011111111111111"
        ne_result += "11010111101111111111111111111011101111111111111"
        ne_result += "11111110110111111111111111111111010111111111111"
        ne_result += "11111111110"

        gt_result = "010100101101000000000000000000000000000000000000"
        gt_result += "01011011101100000000000100001001000000000000000"
        gt_result += "10100000010000000000000010101101110010000000000"
        gt_result += "01000010011001000000000001010000001001000000000"
        gt_result += "00100000000000000000000000000111111001111110000"
        gt_result += "00110100111110010011000000010000100000000000000"
        gt_result += "00001011111111011000000000001011111111011000000"
        gt_result += "00000101111111100100000000000101111111100100000"
        gt_result += "00000010111111111111111000000110111111111111111"
        gt_result += "10100011011111111111111100000011011111111111111"
        gt_result += "11010001101111111111111111111001101111111111111"
        gt_result += "11111110110111111110111111000000010100000010000"
        gt_result += "00000000000"

        lt_result = "000000000000000000000000101011010010111111111111"
        lt_result += "00000000010011111111111010100100010011111111111"
        lt_result += "00011011001111111111111100000000001101111111111"
        lt_result += "10101001000110111111111110001101100110111111111"
        lt_result += "11010101111001011111111111110000000000000001111"
        lt_result += "11000010000001001100111111101010011101101111111"
        lt_result += "11110000000000100000011111110000000000100000011"
        lt_result += "11111000000000011000001111111000000000011000001"
        lt_result += "11111100000000000000000010111000000000000000000"
        lt_result += "00001100000000000000000001011100000000000000000"
        lt_result += "00000110000000000000000000000010000000000000000"
        lt_result += "00000000000000000001000000111111000011111101111"
        lt_result += "11111111110"

        le_result = "101011010010111111111111111111111111111111111111"
        le_result += "10100100010011111111111011110110111111111111111"
        le_result += "01011111101111111111111101010010001101111111111"
        le_result += "10111101100110111111111110101111110110111111111"
        le_result += "11011111111111111111111111111000000110000001111"
        le_result += "11001011000001101100111111101111011111111111111"
        le_result += "11110100000000100111111111110100000000100111111"
        le_result += "11111010000000011011111111111010000000011011111"
        le_result += "11111101000000000000000111111001000000000000000"
        le_result += "01011100100000000000000011111100100000000000000"
        le_result += "00101110010000000000000000000110010000000000000"
        le_result += "00000001001000000001000000111111101011111101111"
        le_result += "11111111111"

        ge_result = "1111111111111111111111110101001011010000000000001"
        ge_result += "111111110110000000000010101101110110000000000011"
        ge_result += "100100110000000000000011111111110010000000000010"
        ge_result += "101101110010000000000011100100110010000000000010"
        ge_result += "101000011010000000000000111111111111111000000111"
        ge_result += "101111110110011000000010101100010010000000000011"
        ge_result += "111111110111111000000011111111110111111000000011"
        ge_result += "111111110011111000000011111111110011111000000011"
        ge_result += "111111111111111101000111111111111111111111100111"
        ge_result += "111111111111111101000111111111111111111111100111"
        ge_result += "111111111111111111110111111111111111111111111111"
        ge_result += "11111111011111100000011110000001000000000000001"

        seq_result = "100000000000000000000000010000000000000000000000"
        seq_result += "00100000000000000000000000010000000000000000000"
        seq_result += "00000100000000000000000000000010000000000000000"
        seq_result += "00000000100000000000000000000000010000000000000"
        seq_result += "00000000000100000000000000000000000010000000000"
        seq_result += "00000000000000100000000000000000000000010000000"
        seq_result += "00000000000000000110000000000000000000000110000"
        seq_result += "00000000000000000000100000000000000000000000010"
        seq_result += "00000000000000000000000100000000000000000000000"
        seq_result += "01000000000000000000000000100000000000000000000"
        seq_result += "00001000000000000000000000000100000000000000000"
        seq_result += "00000001000000000000000000000000100000000000000"
        seq_result += "00000000001"

        results = {
            "!=":   ne_result,
            "==":   eq_result,
            "===":  seq_result,
            ">":    gt_result,
            "<":    lt_result,
            ">=":   ge_result,
            "<=":   le_result,
        }

        prefix = '\n'.join("$a%d = %s;" % (i, expr)
                           for i, expr in enumerate(_input))
        for oper in ["===", "!=", "==", ">", "<", ">=", "<="]:
            code = [prefix]
            for l, r in product(range(len(_input)), repeat=2):
                code.append("echo (int)($a%d %s $a%d);" % (l, oper, r))
            output = self.run("\n".join(code))
            i = 0
            for l, r in product(range(len(_input)), repeat=2):
                if self.space.int_w(output[i]) != int(results[oper][i]):
                    if option.runappdirect and 'INF' in _input[l]:
                        continue  #bah on 5.3: INF != INF, INF < INF, INF > INF
                    raise AssertionError('%s %s %s: got %d' % (
                        _input[l], oper, _input[r],
                        self.space.int_w(output[i])))
                i += 1

    def test_array_compare(self):
        output = self.run('''
        $x = array(0, 1, 2, 3);
        $x["php"] = "php";
        unset($x["php"]);

        echo (int)(array(0, 1, 2, 3) == $x);
        echo (int)(array(0, 1, 2, 3) === $x);

        $x = array(0=>0, 1=>1, 2=>2, 3=>3);
        echo (int)(array(0, 1, 2, 3) == $x);
        echo (int)(array(0, 1, 2, 3) === $x);

        $x = array("0"=>0, "1"=>1, "2"=>2, "3"=>3);
        echo (int)(array(0, 1, 2, 3) == $x);
        echo (int)(array(0, 1, 2, 3) === $x);

        $x = array(0=>"0", 1=>"1", 2=>"2", 3=>"3");
        echo (int)(array(0, 1, 2, 3) == $x);
        echo (int)(array(0, 1, 2, 3) === $x);

        $x = array("0"=>"0", "1"=>"1", "2"=>"2", "3"=>"3");
        echo (int)(array(0, 1, 2, 3) == $x);
        echo (int)(array(0, 1, 2, 3) === $x);

        ''')
        assert [self.space.int_w(i) for i in output] == [1, 1, 1, 1, 1, 1,
                                                         1, 0, 1, 0]

    def test_function_redeclaration(self):
        self.run('''
        function f() { }
        function F($x) { }
        ''', ['Fatal error: Cannot redeclare F() (previously declared in ...'])

    def test_undefined_variable(self):
        output = self.run('echo $a + 42;',
                          ['Notice: Undefined variable: a'])
        assert self.space.int_w(output[0]) == 42

    def test_at_sign(self):
        output = self.run('echo @$a + @($b + 42) + @(@$c + @$d);',
                          [])    # expects no warning at all
        assert self.space.int_w(output[0]) == 42

    def test_and_or_xor(self):
        output = self.run('''
        echo 3 | 5, 3 & 5, 3 ^ 5;
        echo 3 or nothing(), 3 and 5, 3 xor 5;
        echo 0 or 5, 0 and nothing(), 0 xor 5;
        echo 0 or 0, 3 and 0, 3 xor 0, 0 xor 0;
        ''')
        assert [self.space.int_w(i) for i in output] == [
            7, 1, 6,
            1, 1, 0,
            1, 0, 1,
            0, 0, 1, 0]

    def test_switch_1(self):
        output = self.run('''
        switch (4+5) {
        case 8: echo 8;
        case 9: echo 9;
        case 10: echo 10;
        }
        ''')
        assert [self.space.int_w(i) for i in output] == [9, 10]

    def test_switch_2(self):
        output = self.run('''
        switch (6*7) {
        case 8: echo 8;
        default:
        case 9: echo 9;
        case 10: echo 10;
        }
        ''')
        assert [self.space.int_w(i) for i in output] == [9, 10]

    def test_switch_3(self):
        output = self.run('''
        switch (2*4) {
        case 8: echo 8;
        case 9: echo 9; continue;
        case 10: echo 10;
        }
        ''')
        assert [self.space.int_w(i) for i in output] == [8, 9]

    def test_switch_4(self):
        output = self.run('''
        switch (6*7) {
        case 8: echo 8;
        case 9: echo 9;
        case 10: echo 10;
        }
        ''')
        assert [self.space.int_w(i) for i in output] == []

    def test_for_continue(self):
        output = self.run('''
        for ($x = 0; $x < 10; $x++) {
            for ($y = 0; $y < 10; $y++) {
                continue 2;
            }
            echo "never here";
        }
        ''')
        assert len(output) == 0

    def test_foreach_return(self):
        output = self.run('''
        function f($b) {
            foreach($b as $m) {
                return $m;
            }
        }
        echo f(array(10,20,30,40));
        ''')
        assert [self.space.int_w(i) for i in output] == [10]

    def test_break_continue_stack_bug(self):
        output = self.run('''
        $b = array(10,20,30,40);
        foreach($b as $m) {
            $a = array(10,20,30,40);
            foreach ($a as $n) {
                continue 2;
            }
            echo "never here";
        }
        ''')
        assert len(output) == 0

    def test_default_value_on_ref_argument(self):
        output = self.run('''
        function f(&$x=5) {
            $x++;
            echo $x;
        }
        f(); f(); f();
        $y = 42;
        f($y); f($y); f($y);
        ''')
        assert [self.space.int_w(i) for i in output] == [6, 6, 6, 43, 44, 45]

    @py.test.mark.skipif("config.option.runappdirect")
    def test_exit(self):
        from hippy.error import ExplicitExitException
        with py.test.raises(ExplicitExitException) as excinfo:
            self.run("exit; some_invalid_function();")
        assert excinfo.value.message == ""
        assert excinfo.value.code == 0

        with py.test.raises(ExplicitExitException) as excinfo:
            self.run("exit(42);")
        assert excinfo.value.message == ""
        assert excinfo.value.code == 42

        with py.test.raises(ExplicitExitException) as excinfo:
            self.run("exit(42.5);")
        assert excinfo.value.message == "42.5"
        assert excinfo.value.code == 0

    def test_undefined_constant(self):
        with self.warnings(["Notice: Use of undefined constant "
                "UNDEFINED_CONSTANT - assumed 'UNDEFINED_CONSTANT'"]):
            output = self.run('''
            echo UNDEFINED_CONSTANT;
            ''')
        assert self.space.str_w(output[0]) == 'UNDEFINED_CONSTANT'

    def test_new_by_reference(self):
        output = self.run('''
        function f(&$x) { return 42; }
        echo f(new stdClass);
        ''')
        assert self.space.int_w(output[0]) == 42


class TestInterpreter(_TestInterpreter):
    def test_references_function_3(self):
        output = self.run('''
        function foo(&$x) { global $a; $c=42; $a[10]=&$c; $y=$x; return $y; }
        $a = array(1,2,3,4,5,6,7,8,9,10,11);
        echo foo($a[10]);
        echo $a[10];
        ''')
        assert self.space.int_w(output[0]) == 11
        assert self.space.int_w(output[1]) == 42

    def test_globals_unset(self):
        output = self.run('''
        function f() {
            global $b;
            echo $b;
            unset($GLOBALS['b']);
        }
        $b = 42;
        f();
        echo isset($b);
        ''')
        assert [self.space.int_w(i) for i in output] == [42, 0]

    def test_superglobals_ref(self):
        output = self.run('''
        $a = 43;
        $b = &$a;
        echo $GLOBALS["a"], $GLOBALS["b"];
        $GLOBALS["c"] = &$a;
        echo $c;
        $GLOBALS["d"] = $a;
        echo $d;
        $a = 44;
        echo $a, $b, $c, $d;
        echo $GLOBALS["a"], $GLOBALS["b"], $GLOBALS["c"], $GLOBALS["d"];
        ''')
        assert [self.space.int_w(i) for i in output] == [
            43,   43,   43,   43,
            44,   44,   44,   43,
            44,   44,   44,   43]

    def test_superglobals_ref_2(self):
        output = self.run('''
        $c = 1;
        $d = 2;
        $GLOBALS["c"] =& $d;
        echo $c;
        ''')
        assert self.space.int_w(output[0]) == 2

    def test_superglobals_ref_3(self):
        output = self.run('''
        $a =& $b;
        $a = 1;
        $GLOBALS["b"] = 2;
        echo $a;
        ''')
        assert self.space.int_w(output[0]) == 2

    def test_globals_indirect_ref_1(self):
        output = self.run('''
        $name = 'a';
        $GLOBALS['a'] =& $b;
        $b = 42;
        echo $$name;
        unset($$name);
        echo isset($GLOBALS['a']);
        ''')
        assert self.space.int_w(output[0]) == 42
        assert self.space.int_w(output[1]) == 0

    def test_globals_indirect_ref_2(self):
        output = self.run('''
        $name = 'a';
        $$name =& $b;
        $b = 42;
        echo $GLOBALS['a'];
        unset($GLOBALS['a']);
        echo isset($$name);
        ''')
        assert self.space.int_w(output[0]) == 42
        assert self.space.int_w(output[1]) == 0

    def test_const_statement(self):
        output = self.run('''
        const x = 3, Y = 4, y = 5;
        echo x + Y * y;
        ''')
        assert self.space.int_w(output[0]) == 3 + 4 * 5

    def test_unset_1(self):
        with self.warnings(['Notice: Undefined variable: x1']):
            output = self.run('''
            $x1 = 42;
            $x2 = &$x1;
            unset($x1);
            foreach($GLOBALS as $key=>$value) {
                echo $key;
            }
            echo gettype($x1);
            echo gettype($x2);
            ''')
        assert self.space.str_w(output[-2]) == 'NULL'
        assert self.space.str_w(output[-1]) == 'integer'
        assert 'x1' not in [self.space.str_w(i) for i in output]
        assert 'x2' in [self.space.str_w(i) for i in output]

    def test_list_assignment(self):
        output = self.run("""
        list($a, $b) = array(2, 3);
        echo $a, $b;
        """)
        assert [self.space.int_w(w_v) for w_v in output] == [2, 3]
        with self.warnings(['Notice: Undefined offset: 1']):
            output = self.run("""
            list($a, $b) = array(2);
            echo $a, $b;
            """)
        assert self.space.int_w(output[0]) == 2
        assert output[1] is self.space.w_Null
        with self.warnings(['Hippy warning: Cannot use integer as an array',
                            'Hippy warning: Cannot use integer as an array']):
            output = self.run("""
            list($a, $b) = 3;
            echo $a, $b;
            """)
        assert output[0] is self.space.w_Null
        assert output[1] is self.space.w_Null
        output = self.run('''
        $c = list($a, $b) = array(2, 3);
        echo $c[0], $c[1];
        ''')
        assert [self.space.int_w(w_v) for w_v in output] == [2, 3]

    def test_list_assignment_empty(self):
        output = self.run('''
        list($a,,$b) = array(1, 2, 3);
        list(,$c) = array(4, 5);
        list($d,) = array(6, 7);
        echo $a, $b, $c, $d;
        ''')
        assert [self.space.int_w(w_v) for w_v in output] == [1, 3, 5, 6]

    def test_list_assignment_nested(self):
        output = self.run('''
        list($a, list($c, $d)) = array(1, array(2, 3));
        echo $a, $c, $d;
        ''')
        assert [self.space.int_w(w_v) for w_v in output] == [1, 2, 3]

    def test_basic_try_catch(self):
        output = self.run('''
        $a = 15;
        try {
           throw new Exception("message");
        } catch (Exception $e) {
           $a = 3;
        }
        echo $a;
        ''')
        assert self.space.int_w(output[0]) == 3

    def test_try_catch_no_match(self):
        output = self.run('''
        $a = 15;

        class X extends Exception {}

        try {
            try {
               throw new Exception("message");
            } catch (X $e) {
               $a = 3;
            }
        } catch (Exception $e) {
            $a = 5;
        }
        echo $a;
        ''')
        assert self.space.int_w(output[0]) == 5

    def test_try_catch_function(self):
        output = self.run('''
        function f() {
           throw new Exception();
        }
        try {
           f();
        } catch (Exception $e) {
           echo "13";
        }
        ''')
        assert self.space.int_w(output[0]) == 13

    def test_try_catch_variable(self):
        output = self.run('''
        try {
           throw new Exception("message");
        } catch (Exception $e) {
           echo $e->getMessage();
        }
        ''')
        assert self.space.str_w(output[0]) == 'message'

    def test_try_catch_multiple_exc_blocks(self):
        output = self.run('''
        class X extends Exception { }

        try {
           throw new Exception();
           echo "not executed";
        } catch (X $e) {
           echo "not executed";
        } catch (Exception $e) {
           echo "executed";
        }
        echo "also executed";
        ''')
        assert [self.space.str_w(w_v) for w_v in output] == [
            'executed', 'also executed']

    def test_try_catch_multiple_2(self):
        output = self.run('''
        class X extends Exception { }

        try {
           throw new X();
           echo "not executed";
        } catch (X $e) {
           echo "executed";
        } catch (Exception $e) {
           echo "not executed";
        }
        echo "also executed";
        ''')
        assert [self.space.str_w(w_v) for w_v in output] == [
            'executed', 'also executed']

    def test_try_catch_multiple_3(self):
        output = self.run('''
        class X extends Exception { }

        try {
           throw new X();
           echo "not executed";
        } catch (X $e) {
           echo "executed";
        } catch (Exception $e) {
           echo "not executed";
        } catch (X $e) {
           echo "not executed";
        }
        echo "also executed";
        ''')
        assert [self.space.str_w(w_v) for w_v in output] == [
            'executed', 'also executed']

    def test_throw_in_toString(self):
        with self.warnings(["Fatal error: "
                "Method X::__toString() must not throw an exception"]):
            self.run('''
            class X {
                function __toString(){ throw new Exception("message"); }
            }
            try {
                $x = new X;
                (string)$x;
            } catch (Exception $e) {
            echo $e->getMessage();
            }
            ''')

    def test_throw_in_magic(self):
        output = self.run('''
        class X {
            function __get($name){ throw new Exception("message"); }
        }
        try {
            $x = new X;
            $x->a;
        } catch (Exception $e) {
        echo $e->getMessage();
        }
        ''')
        assert self.space.str_w(output[0]) == 'message'

    def test_array_foreach_expression(self):
        output = self.run('''
        foreach ( array(1, 2, 3, 4) as $a ) {
           echo $a;
        }
        ''')
        assert [self.space.int_w(w_v) for w_v in output] == [1, 2, 3, 4]

    def test_static_function_callback(self):
        output = self.run('''
        class A {
           static public function x() {
              return "a";
           }
        }
        echo call_user_func("A::x");
        ''')
        assert self.space.str_w(output[0]) == "a"

    @py.test.mark.parametrize(['call_syntax', 'expected'],
        [["A::foo()", ['B->foo']],
         ["call_user_func(array('A', 'foo'))", ['B->foo']],
         ["$a = array('A', 'foo'); $a()", ['B->foo']],
         ["call_user_func('A::foo')", ['B->foo']],
         ["parent::foo()", ['B->foo']],
         ["self::foo()", ['B->foo']],
         ["B::foo()", ['B->foo']],
         ["call_user_func(array('B', 'foo'))", ['B->foo']],
         ["call_user_func('B::foo')", ['B->foo']],
         ["call_user_func(array($this, 'foo'))", ['B->foo']],
         ["C::foo()", ['C::foo']],
         ["call_user_func(array('C', 'foo'))", ['C::foo']],
         ["Other::foo()", ['Other::foo']],
         ["call_user_func(array('Other', 'foo'))", ['Other::foo']]])
    def test_static_calls(self, call_syntax, expected):
        output = self.run('''
        class A {
            function __call($name, $args) { echo 'A->'.$name; }
            static function __callStatic($name, $args) { echo 'A::'.$name; }
        }
        class B extends A {
            function __call($name, $args) { echo 'B->'.$name; }
            static function __callStatic($name, $args) { echo 'B::'.$name; }
            function test() {
                %s;
            }
        }
        class C extends B {
            function __call($name, $args) { echo 'C->'.$name; }
            static function __callStatic($name, $args) { echo 'C::'.$name; }
        }
        class Other {
            function __call($name, $args) { echo 'Other->'.$name; }
            static function __callStatic($name, $args) {echo 'Other::'.$name;}
        }
        $b = new B;
        $b->test();
        ''' % (call_syntax,))
        assert map(self.space.str_w, output) == expected

    def test_array_callback(self):
        output = self.run('''
        class A {
          static public function x() {
            return "a";
          }
        }
        echo call_user_func(array('A', 'x'));
        ''')
        assert self.space.str_w(output[0]) == "a"

    def test_array_cast_from_reference(self):
        output = self.run('''
        $v = 3;
        $a = Array(&$v);
        $a[0] = 15;
        echo $v;
        ''')
        assert self.space.int_w(output[0]) == 15

    def test_default_parameter_from_constant(self):
        output = self.run('''
        function f($default=CONSTANT)
        {
           return $default;
        }
        define("CONSTANT", 3);
        echo f();
        ''')
        assert self.space.int_w(output[0]) == 3

    def test_for_with_comma(self):
        output = self.run('''
        for ($i = 0, $j = 0; $z = 8, $j < 13; $i++, $j++) {}
        echo $i, $j, $z;
        ''')
        assert [self.space.int_w(w_v) for w_v in output] == [13, 13, 8]

    def test_call_function_by_name(self):
        # may I say that this feature is entirely obscure?
        output = self.run('''
        function f() { return 3; }
        $x = "f";
        echo $x();
        ''')
        assert self.space.int_w(output[0]) == 3

    def test_lambda_expr(self):
        output = self.run('''
        $x = function() { echo "dupa"; };
        $x();
        ''')
        assert self.space.str_w(output[0]) == "dupa"

    def test_lambda_expr_invoke(self):
        output = self.run('''
        $x = function() { echo "dupa"; };
        $x->__invoke();
        ''')
        assert self.space.str_w(output[0]) == "dupa"

    def test_class_constant_as_default(self):
        output = self.run('''
        class X {
           const X = 3;
        }

        function x($a=X::X) {
           return $a;
        }
        echo x();
        ''')
        assert self.space.int_w(output[0]) == 3

    def test_class_constant_self(self):
        output = self.run('''
        class X {
            const Y = 3;
            const Z = self::Y;
        }
        function x($a=X::Z) {
            return $a;
        }
        echo x();
        ''')
        assert self.space.int_w(output[0]) == 3

    def test_callback_error(self):
        with self.warnings(["Warning: set_exception_handler() expects "
                            "parameter 1 to be a valid callback, no array or "
                            "string given"]):
            self.run('set_exception_handler(3);')

    def test_reference_update_does_not_change_array(self):
        output = self.run('''
        $a = array();
        $a[0] =& $a;
        $a[0] = "foo";
        echo $a;
        ''')
        assert self.space.str_w(output[0]) == "foo"

    def test_lambda_scoping_simple(self):
        output = self.run('''
        function f() {
            $a = 3;
            $x = function() use ($a) {
                return $a;
            };
            $a = 15;
            return $x;
        }

        $a = f();
        echo $a();
        ''')
        assert output[0].intval == 3

    def test_lambda_scoping_ref(self):
        output = self.run('''
        function f() {
            $a = 3;
            $x = function() use (&$a) {
                return $a;
            };
            $a = 15;
            return $x;
        }

        $a = f();
        echo $a();
        ''')
        assert output[0].intval == 15

    def test_empty_for(self):
        output = self.run('''
        $x = 0;
        for (; $x < 3; $x++) {
        }
        echo $x;
        ''')
        assert self.space.int_w(output[0]) == 3

    def test_callback_array_instance(self):
        output = self.run("""
        class A {
          function __construct ($x) {
             $this->x = $x;
          }

          public function x() {
            return $this->x;
          }
        }
        $x = new A("13");
        echo call_user_func(array($x, 'x'));
        """)
        assert self.space.str_w(output[0]) == "13"

    def test_callback_context_0(self):
        with self.warnings(["Warning: call_user_func() expects parameter 1 "
                            "to be a valid callback, class 'A' does not "
                            "have a method 'f'"]):
            output = self.run("""
            class A { }
            $a = new A;
            echo call_user_func(array($a, 'f'));
            """)
        assert self.space.is_w(output[0], self.space.w_Null)

    def test_callback_context_1(self):
        with self.warnings(["Warning: call_user_func() expects parameter 1 "
                            "to be a valid callback, cannot access private "
                            "method A::f()"]):
            output = self.run("""
            class A {
                private function f() { return 42; }
            }
            $a = new A;
            echo call_user_func(array($a, 'f'));
            """)
        assert self.space.is_w(output[0], self.space.w_Null)

    def test_callback_context_2(self):
        output = self.run("""
        class A {
            private function f() { return 42; }
            public function g() { return call_user_func(array($this, 'f')); }
        }
        $a = new A;
        echo $a->g();
        """)
        assert self.space.int_w(output[0]) == 42

    def test_callback_context_3(self):
        with self.warnings(["Warning: call_user_func() expects parameter 1 "
                            "to be a valid callback, cannot access private "
                            "method B::f()"]):
            output = self.run("""
            class A {
                private function f() { return 42; }
            }
            class B extends A {
                public function g() {return call_user_func(array($this, 'f'));}
            }
            $b = new B;
            echo $b->g();
            """)
        assert self.space.is_w(output[0], self.space.w_Null)

    def test_callback_context_4(self):
        with self.warnings(["Warning: call_user_func() expects parameter 1 "
                            "to be a valid callback, cannot access protected "
                            "method A::f()"]):
            output = self.run("""
            class A {
                protected function f() { return 42; }
            }
            $a = new A;
            echo call_user_func(array($a, 'f'));
            """)
        assert self.space.is_w(output[0], self.space.w_Null)

    def test_callback_context_5(self):
        output = self.run("""
        class A {
            protected function f() { return 42; }
        }
        class B extends A {
            public function g() { return call_user_func(array($this, 'f')); }
        }
        $b = new B;
        echo $b->g();
        """)
        assert self.space.int_w(output[0]) == 42

    def test_callback_context_6(self):
        output = self.run("""
        class A {
            private function f() { return 42; }
            public function g() { return call_user_func(array($this, 'f')); }
        }
        class B extends A {
        }
        $b = new B;
        echo $b->g();
        """)
        assert self.space.int_w(output[0]) == 42

    def test_callback_context_7(self):
        output = self.run("""
        class A {
            private function f() { return 42; }
            public function __call($func, $args) { return $func . '<-'; }
        }
        $a = new A;
        echo call_user_func(array($a, 'f'));
        """)
        assert self.space.str_w(output[0]) == 'f<-'

    def test_callback_context_static_0(self):
        with self.warnings(["Warning: call_user_func() expects parameter 1 "
                            "to be a valid callback, class 'A' does not have "
                            "a method 'f'"]):
            output = self.run("""
            class A { }
            echo call_user_func(array('A', 'f'));
            """)
        assert self.space.is_w(output[0], self.space.w_Null)

    def test_callback_context_static_1(self):
        with self.warnings(["Warning: call_user_func() expects parameter 1 "
                            "to be a valid callback, cannot access private "
                            "method A::f()"]):
            output = self.run("""
            class A {
                private static function f() { return 42; }
            }
            echo call_user_func(array('A', 'f'));
            """)
        assert self.space.is_w(output[0], self.space.w_Null)

    def test_callback_context_static_2(self):
        output = self.run("""
        class A {
            private static function f() { return 42; }
            public static function g() { return call_user_func('A::f'); }
        }
        echo A::g();
        """)
        assert self.space.int_w(output[0]) == 42

    def test_callback_context_static_3(self):
        with self.warnings(["Warning: call_user_func() expects parameter 1 "
                            "to be a valid callback, cannot access private "
                            "method A::f()"]):
            output = self.run("""
            class A {
                private static function f() { return 42; }
            }
            class B extends A {
                public static function g() { return call_user_func('A::f'); }
            }
            echo B::g();
            """)
        assert self.space.is_w(output[0], self.space.w_Null)

    def test_callback_context_static_4(self):
        with self.warnings(["Warning: call_user_func() expects parameter 1 "
                            "to be a valid callback, cannot access protected "
                            "method A::f()"]):
            output = self.run("""
            class A {
                protected static function f() { return 42; }
            }
            echo call_user_func('A::f');
            """)
        assert self.space.is_w(output[0], self.space.w_Null)

    def test_callback_context_static_5(self):
        output = self.run("""
        class A {
            protected static function f() { return 42; }
        }
        class B extends A {
            public static function g() { return call_user_func('A::f'); }
        }
        echo B::g();
        """)
        assert self.space.int_w(output[0]) == 42

    def test_function_server_and_globals(self):
        output = self.run("""
        function f() {
           return $_SERVER === $GLOBALS;
        }
        echo f();
        """)
        assert self.space.int_w(output[0]) == 0

    def test_if_combination(self):
        output = self.run('''
        $x = true;
        $y = false;
        if (!$x && $y) {
           echo 1;
        } else {
           echo 0;
        }
        ''')
        assert self.space.int_w(output[0]) == 0

    def test_superglobals_indirect_set(self):
        with self.warnings(['Hippy warning: Creating array from empty value']):
            output = self.run('''
            function f() {
                $_SESSION['a']['b'] = 3;
                echo $_SESSION;
            }
            f();
            ''')
            assert self.unwrap(output[0])['a']['b'] == 3

    def test_exception_inside_complex_structure(self):
        self.run('''

        class Cls {
            public static function stuff() {
                throw new Exception();
            }
        }

        function f() {
            try {
                $x = Cls::stuff();
            } catch (Exception $e) {
                return;
            }
        }

        f();

        ''')
        # assert did not crash

    def test_empty_for2(self):
        output = self.run("""
        $i = 0;
        for(;;) {
           $i++;
           if ($i == 10) break;
        }
        echo $i;
        """)
        assert self.space.int_w(output[0]) == 10

    def test_reference_as_foreach(self):
        output = self.run("""
        $a = array(array(1, 2, 3));
        foreach ($a[0] as &$x) {
            $x = 13;
        }
        echo $a[0][2];
        """)
        assert self.space.int_w(output[0]) == 13

    def test_ordering_case_1(self):
        output = self.run("""
        $i = 5;
        $j = 6;
        echo $i * ($i=&$j);
        """)
        assert self.space.int_w(output[0]) == 36

    def test_ordering_case_2(self):
        output = self.run('''
        $a = array(3=>"oops");
        $b = array(6, 7, 3=>"ok");
        echo $a[count($a=&$b)];
        ''')
        assert self.space.str_w(output[0]) == "ok"

    def test_ordering_case_3(self):
        output = self.run("""
        $a = array(4, 5, 6, 10=>0);
        $i = 1; $j = 2;
        $a[$i] = ($i=&$j);
        echo $a;
        """)
        assert self.unwrap(output[0]) == {'0': 4, '1': 5, '2': 2, '10': 0}

    def test_object_cast_to_array_empty(self):
        output = self.run("""
        $a = new stdClass();
        foreach ( (array)$a as $k => $v ) {
           echo $k;
           echo $v;
        }
        """)
        assert output == []

    def test_object_cast_to_array_non_empty(self):
        output = self.run("""
        $a = (object) array('foo' => 'bar', 'property' => 'value');
        foreach ( (array)$a as $k => $v ) {
           echo $k;
           echo $v;
        }
        """)
        assert [self.space.str_w(w_v) for w_v in output] == ['foo', 'bar',
                                                             'property',
                                                             'value']

    def test_object_cast_to_array_non_empty_2(self):
        output = self.run("""
        class DB {
            private $type='mysql';
            private $conn=null;
            private $user='';
            private $pass='';

        public function setUser($user=null) {
            if($user===null) return false;
            $this->user = $user;
        }
        public function setPass($pass=null) {
            if($pass === null) return false;
            $this->pass = $pass;
        }

        }

        $a = new DB();
        foreach ( (array)$a as $k => $v ) {
           echo $k.'-'.$v;
        }

        """)
        assert [self.space.str_w(w_v) for w_v in output] == [
            '\x00DB\x00type-mysql', '\x00DB\x00conn-', '\x00DB\x00user-',
            '\x00DB\x00pass-']

    def test_constant_in_namespace(self):
        output = self.run("""
        namespace foo\\bar;
        $x = falsE;
        echo $x;
        """)
        assert output == [self.space.w_False]

    def test_constant_in_classdef_in_namespace(self):
        output = self.run("""
        namespace foo\\bar;
        class A {
            static $x = falsE;
        }
        echo A::$x;
        """)
        assert output == [self.space.w_False]

    @skip_on_travis
    def test_backtick_expr(self):
        output = self.run("""
        $x = `echo "5*5" | bc`;
        echo $x;
        """)
        assert [self.space.str_w(w_v) for w_v in output] == [
            '25\n']

    @skip_on_travis
    def test_backtick_expr_variable(self):
        output = self.run("""
        $op = "5*5";
        $x = `echo $op | bc`;
        echo $x;
        """)
        assert [self.space.str_w(w_v) for w_v in output] == [
            '25\n']

    @skip_on_travis
    def test_backtick_expr_variable_2(self):
        output = self.run("""
        $op = "5*5";
        $x = `echo ${op} | bc`;
        echo $x;
        """)
        assert [self.space.str_w(w_v) for w_v in output] == [
            '25\n']

    @skip_on_travis
    def test_backtick_expr_variable_3(self):
        output = self.run("""
        $cmd = "echo";
        $op = "5*5";
        $x = `$cmd ${op} | bc`;
        echo $x;
        """)
        assert [self.space.str_w(w_v) for w_v in output] == [
            '25\n']

    @skip_on_travis
    def test_backtick_expr_singlequote(self):
        output = self.run("""
        $x = `echo '5*5' | bc`;
        echo $x;
        """)
        assert [self.space.str_w(w_v) for w_v in output] == [
            '25\n']


class TestLocalInterpreter(LocalRunTestInterpreter, _TestInterpreter):
    @py.test.mark.xfail(reason="confused by Stack trace:")
    def test_uncaught_exception_1(self):
        with self.warnings(["Fatal error: Uncaught exception "
                            "'Exception' with message 'message' in ...:4"]):
            self.run("""
                throw new Exception('message');
            """)

class TestMultipleInterpreters(TestInterpreter):
    Engine = MockServerEngine
