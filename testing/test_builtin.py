import py
import math, os
from hippy.objspace import ObjSpace
from hippy.phpcompiler import compile_php
from hippy.objects.reference import W_Reference
from hippy.builtin import (
    BuiltinFunctionBuilder, BuiltinSignature, Optional, FilenameArg,
    StreamContextArg, Nullable)

from testing.test_interpreter import BaseTestInterpreter, MockInterpreter
from testing.conftest import option


def test_signature():
    sig = BuiltinSignature(['space', int, int])
    assert sig.php_indices == [0, 0, 1]

    sig = BuiltinSignature(['space', 'reference', Optional(int)])
    assert sig.php_indices == [0, 0, 1]
    assert sig.min_args == 1
    assert sig.max_args == 2

    with py.test.raises(ValueError) as excinfo:
        sig = BuiltinSignature([Optional(int), 'args_w'])
    assert excinfo.value.args[0].startswith("Cannot combine")


def test_builder():
    def add(space, m, n):
        return space.newint(m + n)
    signature = ['space', int, int]
    builder = BuiltinFunctionBuilder(signature, add)
    assert builder.make_source() == """\
@unroll_safe
def php_add(interp, args_w, w_this, thisclass):
    nb_args = len(args_w)
    space = interp.space
    if nb_args != 2:
        arguments_exactly(interp, fname, 2, nb_args, error_handler)
    nb_args = 2  # constant below
    arg0 = space
    w_arg = args_w[0].deref_unique()
    try:
        arg1 = w_arg.as_int_arg(space)
    except ConvertError:
        raise argument_not(interp, "long", fname, 1, w_arg.tp, error_handler)
    w_arg = args_w[1].deref_unique()
    try:
        arg2 = w_arg.as_int_arg(space)
    except ConvertError:
        raise argument_not(interp, "long", fname, 2, w_arg.tp, error_handler)
    return (arg0, arg1, arg2)
"""

    def incr(space, a, increment=1):
        return space.newint(a + increment)
    signature = ['space', 'reference', Optional(int)]
    builder = BuiltinFunctionBuilder(signature, incr)
    expected = """\
@unroll_safe
def php_incr(interp, args_w, w_this, thisclass):
    nb_args = len(args_w)
    space = interp.space
    if nb_args < 1:
        warn_at_least(space, fname, 1, nb_args)
    if nb_args > 2:
        warn_at_most(space, fname, 2, nb_args)
    arg2 = default2
    arg0 = space
    w_arg = args_w[0]
    arg1 = check_reference(space, w_arg, fname)
    if nb_args > 1:
        w_arg = args_w[1].deref_unique()
        try:
            arg2 = w_arg.as_int_arg(space)
        except ConvertError:
            raise argument_not(interp, "long", fname, 2, w_arg.tp, error_handler)
    return (arg0, arg1, arg2)
"""
    assert builder.make_source() == expected

    def foo(space, fname, ctx=None):
        pass
    signature = ['space', FilenameArg(False), Optional(Nullable(StreamContextArg(False)))]
    builder = BuiltinFunctionBuilder(signature, foo)
    assert builder.make_source() == """\
@unroll_safe
def php_foo(interp, args_w, w_this, thisclass):
    nb_args = len(args_w)
    space = interp.space
    if nb_args < 1:
        warn_at_least(space, fname, 1, nb_args)
    if nb_args > 2:
        warn_at_most(space, fname, 2, nb_args)
    arg2 = default2
    arg0 = space
    w_arg = args_w[0].deref_unique()
    if w_arg.tp == space.tp_dir_res or w_arg.tp == space.tp_file_res or w_arg.tp == space.tp_array:
        raise argument_not(interp, "a valid path", fname, 1, w_arg.tp, error_handler)
    arg = w_arg.maybe_str(space)
    if arg is None:
        raise argument_not(interp, "a valid path", fname, 1, w_arg.tp, error_handler)
    arg1 = arg
    if nb_args > 1:
        w_arg = args_w[1].deref_temp()
        if w_arg.tp == space.tp_null:
            arg2 = None
        else:
            w_arg = args_w[1].deref_unique()
            if space.is_resource(w_arg):
                if w_arg.tp != space.tp_stream_context:
                    interp.warn("%s(): supplied resource is not a valid Stream-Context resource" % fname)
                    arg2 = None
                else:
                    arg2 = w_arg
            else:
                raise warn_not_stream_context(space, fname, 2, space.int_w(w_arg), w_arg.tp)
    return (arg0, arg1, arg2)
"""


class TestBuiltinDirect(object):
    def test_call_args(self):
        space = ObjSpace()
        interp = MockInterpreter(space)
        sin = interp.locate_function("sin")
        w_res = space.call_args(sin, [space.wrap(1.2)])
        assert space.float_w(w_res) == math.sin(1.2)
        max = interp.locate_function("max")
        w_res = space.call_args(max, [space.wrap(2), space.wrap(15),
                                      space.wrap(3)])
        assert space.int_w(w_res) == 15
        w_res = space.call_args(max, [W_Reference(space.wrap(2)),
                                      space.wrap(15),
                                      space.wrap(3)])
        assert space.int_w(w_res) == 15
        str_repeat = interp.locate_function("str_repeat")
        w_res = space.call_args(str_repeat, [space.newstr("a"), space.wrap(3)])
        assert space.str_w(w_res) == "aaa"
        source = """<?php
        function f($a, $b) {
            return $a + 10 * $b;
        }
        """
        bc = compile_php('<input>', source, space, interp)
        interp.run_main(space, bc)
        f = interp.locate_function("f")
        w_res = space.call_args(f, [space.wrap(1), space.wrap(2)])
        assert space.int_w(w_res) == 21


class TestFile(BaseTestInterpreter):
    def setup_class(cls):
        tmpdir = py.path.local.make_numbered_dir('hippy')
        cls.tmpdir = tmpdir

    def test_get_file_contents(self):
        fname = self.tmpdir.join('get_file_contents')
        fname.write('xyyz')
        output = self.run('''
        echo file_get_contents("%s");
        ''' % fname)
        assert self.space.str_w(output[0]) == 'xyyz'


class TestBuiltin(BaseTestInterpreter):
    def test_StringArg_bad_object_1(self):
        with self.warnings(['Warning: stripslashes() '
                'expects parameter 1 to be string, object given']):
            self.run('''
            class Test {}
            stripslashes(new Test);
            ''')

    def test_StringArg_bad_object_2(self):
        with self.warnings(['Fatal error: Method '
                'Test::__toString() must not throw an exception']):
            self.run('''
            class Test {
                function __toString() {throw new Exception;}
            }
            stripslashes(new Test);
            ''')

    def test_StringArg_bad_object_3(self):
        with self.warnings(['Catchable fatal error: '
                'Method Test::__toString() must return a string value']):
            self.run('''
            class Test {
                function __toString() { return null;}
            }
            stripslashes(new Test);
            ''')

    def test_builtin_sin_cos(self):
        output = self.run("""
        $i = 1.5707963267948966;
        echo cos($i) + 2 * sin($i);
        """)
        assert self.space.float_w(output[0]) == 2.0

    def test_builtin_pow(self):
        output = self.run("""
        echo pow(2.0, 3.0);
        $i = pow(1.2, 2.4);
        echo $i;
        """)
        assert self.space.float_w(output[0]) == 8.0
        if option.runappdirect:
            py.test.skip("float precision")
        assert self.space.float_w(output[1]) == 1.2 ** 2.4

    def test_builtin_max(self):
        output = self.run("""
        echo max(1, 1.2), max(5, 4), max(1.1, 0.0), max(NULL, 3);
        """)
        assert self.space.float_w(output[0]) == 1.2
        assert self.space.int_w(output[1]) == 5
        assert self.space.float_w(output[2]) == 1.1
        assert self.space.int_w(output[3]) == 3

    def test_unset(self):
        output = self.run("""
        $a = 3;
        echo $a;
        $b = $a;
        $c = $a;
        unset($a, $c);
        echo $a, $b, $c;
        """, [
            'Notice: Undefined variable: a',
            'Notice: Undefined variable: c'])
        assert self.space.int_w(output[0]) == 3
        assert self.space.int_w(output[2]) == 3
        assert output[1] is self.space.w_Null
        assert output[3] is self.space.w_Null

    def test_unset_array_elems(self):
        output = self.run("""
        $a = array(1);
        unset($a[0], $a['xyz']);
        echo $a, $a[0];
        """, [
            'Notice: Undefined offset: 0'])
        assert output[1] is self.space.w_Null
        if not option.runappdirect:
            assert not output[0]._has_string_keys

    def test_count(self):
        output = self.run('''
        $a = array(1, 2, 3);
        echo count($a), sizeof($a);
        echo count(5), count(0), count(""), count(NULL);
        ''')
        assert [self.space.int_w(i) for i in output] == [3, 3, 1, 1, 1, 0]

    def test_count_not_full(self):
        output = self.run('''
        $a = array(1, 2, 3);
        $a[15] = 3;
        echo count($a), $a[15];
        ''')
        assert self.space.int_w(output[0]) == 4
        assert self.space.int_w(output[1]) == 3

    def test_count_not_full_2(self):
        output = self.run('''
        $a = array();
        $a[15] = 3;
        echo count($a), $a[15];
        ''')
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 3

    def test_count_not_full_3(self):
        output = self.run('''
        $a = array("xyz");
        $a[15] = 3;
        echo count($a), $a[15];
        ''')
        assert self.space.int_w(output[0]) == 2
        assert self.space.int_w(output[1]) == 3

    def test_empty(self):
        output = self.run('''
        $a = 1; $b = array(1, 2); $c = 0; $d = array();
        echo empty($a), empty($b), empty($c), empty($d), empty($eee);
        ''')
        assert [i.boolval for i in output] == [False, False, True, True, True]

    def test_isset(self):
        output = self.run('''
        $a = array(1, null);
        $b = null;
        echo isset($a[3]), isset($a[1]), isset($a), isset($a[0]);
        echo isset($b), isset($c);
        echo isset($a, $a[0]), isset($a, $b);
        echo isset($b, $a[no_such_function()]);
        ''')
        assert [i.boolval for i in output] == [False, False, True, True,
                                               False, False,
                                               True, False,
                                               False]

    def test_is_array(self):
        output = self.run('''
        echo is_array(0), is_array(0.0), is_array(NULL), is_array(array());
        echo is_array(FALSE), is_array(TRUE), is_array("foo");
        ''')
        assert [i.boolval for i in output] == [False, False, False, True,
                                               False, False, False]

    def test_is_bool(self):
        output = self.run('''
        echo is_bool(0), is_bool(0.0), is_bool(NULL), is_bool(array());
        echo is_bool(FALSE), is_bool(TRUE), is_bool("foo");
        ''')
        assert [i.boolval for i in output] == [False, False, False, False,
                                               True, True, False]

    def test_is_int(self):
        output = self.run('''
        echo is_int(0), is_int(0.0), is_int(NULL), is_int(array());
        echo is_int(FALSE), is_int(TRUE), is_int("foo");
        ''')
        assert [i.boolval for i in output] == [True, False, False, False,
                                               False, False, False]

    def test_is_integer(self):
        output = self.run('''
        echo is_integer(0), is_integer(0.0), is_integer(NULL),
        is_integer(array());
        echo is_integer(FALSE), is_integer(TRUE), is_integer("foo");
        ''')
        assert [i.boolval for i in output] == [True, False, False, False,
                                               False, False, False]

    def test_is_long(self):
        output = self.run('''
        echo is_long(0), is_long(0.0), is_long(NULL), is_long(array());
        echo is_long(FALSE), is_long(TRUE), is_long("foo");
        ''')
        assert [i.boolval for i in output] == [True, False, False, False,
                                               False, False, False]

    def test_is_float(self):
        output = self.run('''
        echo is_float(0), is_float(0.0), is_float(NULL), is_float(array());
        echo is_float(FALSE), is_float(TRUE), is_float("foo");
        ''')
        assert [i.boolval for i in output] == [False, True, False, False,
                                               False, False, False]

    def test_is_double(self):
        output = self.run('''
        echo is_double(0), is_double(0.0), is_double(NULL), is_double(array());
        echo is_double(FALSE), is_double(TRUE), is_double("foo");
        ''')
        assert [i.boolval for i in output] == [False, True, False, False,
                                               False, False, False]

    def test_is_real(self):
        output = self.run('''
        echo is_real(0), is_real(0.0), is_real(NULL), is_real(array());
        echo is_real(FALSE), is_real(TRUE), is_real("foo");
        ''')
        assert [i.boolval for i in output] == [False, True, False, False,
                                               False, False, False]

    def test_is_null(self):
        output = self.run('''
        echo is_null(0), is_null(0.0), is_null(NULL), is_null(array());
        echo is_null(FALSE), is_null(TRUE), is_null("foo");
        ''')
        assert [i.boolval for i in output] == [False, False, True, False,
                                               False, False, False]

    def test_is_scalar(self):
        output = self.run('''
        echo is_scalar(0), is_scalar(0.0), is_scalar(NULL), is_scalar(array());
        echo is_scalar(FALSE), is_scalar(TRUE), is_scalar("foo");
        ''')
        assert [i.boolval for i in output] == [True, True, False, False,
                                               True, True, True]

    def test_is_string(self):
        output = self.run('''
        echo is_string(0), is_string(0.0), is_string(NULL), is_string(array());
        echo is_string(FALSE), is_string(TRUE), is_string("foo");
        ''')
        assert [i.boolval for i in output] == [False, False, False, False,
                                               False, False, True]

    def test_defined(self):
        output = self.run('''
        echo define("abc", 3);
        echo defined("abc"), defined("def");
        define("abcd", NULL);
        echo defined("abcd");
        ''')
        assert [i.boolval for i in output] == [True, True, False, True]
        output = self.run('''
        define("abc", 3);
        define("aBc", 511);
        echo define("abc", 31);
        echo abc, aBc;
        ''', [
            'Notice: Constant abc already defined'])
        assert not output[0].boolval
        assert self.space.int_w(output[1]) == 3
        assert self.space.int_w(output[2]) == 511

    def test_gettype(self):
        output = self.run('''
        echo gettype(5 > 2);
        echo gettype(5);
        echo gettype(5.5);
        echo gettype("5");
        echo gettype(array());
        echo gettype(NULL);
        ''')
        assert self.space.str_w(output[0]) == 'boolean'
        assert self.space.str_w(output[1]) == 'integer'
        assert self.space.str_w(output[2]) == 'double'
        assert self.space.str_w(output[3]) == 'string'
        assert self.space.str_w(output[4]) == 'array'
        assert self.space.str_w(output[5]) == 'NULL'

    def test_function_exists(self):
        output = self.run('''
        function f42() { }
        echo function_exists("f42");
        echo function_exists("function_exists");
        echo function_exists("f43");
        ''')
        assert self.space.str_w(output[0]) == '1'
        assert self.space.str_w(output[1]) == '1'
        assert self.space.str_w(output[2]) == ''

    def test_class_exists(self):
        output = self.run("""
        class MyClass {}
        echo class_exists('myclass');
        echo class_exists('stdClass');
        echo class_exists('anotherclass');
        """)
        assert [x.boolval for x in output] == [True, True, False]

    def test_property_exists(self):
        output = self.run('''
        $x = new stdClass;
        $x->foo = 0;
        $x->bar = null;
        echo property_exists($x, 'foo');
        echo property_exists($x, 'bar');
        echo property_exists($x, 'baz');
        ''')
        assert [x.boolval for x in output] == [True, True, False]


    def test_var_dump(self):
        if option.runappdirect:
            py.test.skip("outputs to stdout, confuses the runner")
        output = self.run('''
        var_dump(5);
        $a = 5.5; var_dump($a);
        var_dump(5.0);
        var_dump(TRUE);
        var_dump(FALSE);
        var_dump(NULL);
        var_dump(5, 6, 7);
        var_dump("foobar");
        $a = array(4, 5); var_dump($a);
        $a[2] =& $a; var_dump($a);
        class A { }
        var_dump(new A);
        ''')
        assert ''.join(output) == '''\
int(5)
float(5.5)
float(5)
bool(true)
bool(false)
NULL
int(5)
int(6)
int(7)
string(6) "foobar"
array(2) {
  [0]=>
  int(4)
  [1]=>
  int(5)
}
array(3) {
  [0]=>
  int(4)
  [1]=>
  int(5)
  [2]=>
  &array(3) {
    [0]=>
    int(4)
    [1]=>
    int(5)
    [2]=>
    &*RECURSION*
  }
}
object(A)#1 (0) {
}
'''

    def test_var_dump_2(self):
        py.test.skip("FIXME")
        output = self.run('''
        var_dump(array(TRUE, 5), array("xx"=>array(0), 7));
        ''')
        assert ''.join(output) == '''\
array(2) {
  [0]=>
  bool(true)
  [1]=>
  int(5)
}
array(2) {
  ["xx"]=>
  array(1) {
    [0]=>
    int(0)
  }
  [0]=>
  int(7)
}
'''

    def test_var_dump_recursion(self):
        if option.runappdirect:
            py.test.skip("outputs to stdout, confuses the runner")
        output = self.run('var_dump($GLOBALS);')
        assert '*RECURSION*' in ''.join(output)

    def test_print_r_0(self):
        if option.runappdirect:
            py.test.skip("outputs to stdout, confuses the runner")
        output = self.run('''
        print_r(25);
        $a = 25.5; print_r($a);
        print_r(25.0);
        print_r(TRUE);
        print_r(FALSE);
        print_r(NULL);
        print_r("foobar");
        $a = array(4, 5); print_r($a);
        ''')
        assert output == [
            '25',
            '25.5',
            '25',
            '1',
            '',
            '',
            'foobar',
            'Array\n(\n    [0] => 4\n    [1] => 5\n)\n']

    def test_print_r_recursion(self):
        if option.runappdirect:
            py.test.skip("outputs to stdout, confuses the runner")
        output = self.run('''
        print_r($GLOBALS);
        ''')
        assert '*RECURSION*' in output[0]

    def test_print_r_1(self):
        if option.runappdirect:
            py.test.skip("outputs to stdout, confuses the runner")
        output = self.run('''
        $a = print_r(array(25.5), 1);
        echo "the result is: ", $a;
        ''')
        assert self.space.str_w(output[0]) == 'the result is: '
        assert self.space.str_w(output[1]) == 'Array\n(\n    [0] => 25.5\n)\n'

    def test_intval(self):
        assert self.echo("intval(42)") == "42"
        assert self.echo("intval(4.2)") == "4"
        assert self.echo("intval('42')") == "42"
        assert self.echo("intval('+42')") == "42"
        assert self.echo("intval('-42')") == "-42"
        assert self.echo("intval(042)") == "34"
        assert self.echo("intval('042')") == "42"
        #assert self.echo("intval(1e10)") == "1410065408"
        assert self.echo('intval("1980-1")') == "1980"
        assert self.echo("intval('1e10')") == "1"
        assert self.echo("intval(0x1A)") == "26"
        assert self.echo("intval(42000000)") == "42000000"
        assert self.echo("intval(420000000000000000000)") == "0"
        #assert self.echo("intval('420000000000000000000')") == "2147483647"
        assert self.echo("intval(42, 8)") == "42"
        assert self.echo("intval('42', 8)") == "34"
        assert self.echo("intval(array())") == "0"
        assert self.echo("intval(array('foo', 'bar'))") == "1"

    def test_warn_not_by_reference(self):
        self.run('array_filter(array(4), "next");', [
            "Hippy warning: The built-in function next() takes an "
            "argument by reference, but didn't get a reference in "
            "the indirect call",
            "Warning: next() expects parameter 1 to be array, integer given"])

    def test_constant(self):
        output = self.run("""
        echo constant('fAlSe');
        echo constant('tRuE');
        echo constant('foobarbaz') === NULL;
        """, ["Warning: constant(): Couldn't find constant foobarbaz"])
        assert self.space.int_w(output[0]) == 0
        assert self.space.int_w(output[1]) == 1
        assert self.space.int_w(output[2]) == 1

    def test_sys_getloadavg(self):
        output = self.run("""
        $x = sys_getloadavg();
        echo $x[0], $x[1], $x[2];
        """)
        reference = os.getloadavg()
        for n in range(3):
            assert abs(self.space.float_w(output[n]) - reference[n]) < 0.021

    def test_phpversion(self):
        output = self.run("""
        echo phpversion();
        echo phpversion('xyz');
        """)
        assert self.space.str_w(output[0]) == '5.4.17'

    def test_is_callable(self):
        output = self.run("""
        echo is_callable("xyz");
        echo is_callable("htmlspecialchars");

        function f() {}

        echo is_callable("f");
        """)
        assert [self.space.is_true(w_v) for w_v in output] == [False, True,
                                                               True]
        output = self.run("""
        echo is_callable("xyz", true);
        """)
        assert self.space.is_true(output[0])
        output = self.run("""
        echo is_callable(array(3, 4), true);

        class X {
           function method () {
           }
        }

        echo is_callable(array(new X(), "xyz"), true);
        echo is_callable(array(new X(), "xyz"));
        echo is_callable(array(new X(), "method"));
        """)
        assert [self.space.is_true(w_v) for w_v in output] == [
            False, True, False, True]

    def test_func_get_args(self):
        output = self.run('''
        function f($a) {
           echo(func_get_args());
           echo(func_num_args());
        }
        f(3, 4, 5);
        ''')
        space = self.space
        assert space.is_array(output[0])
        assert space.arraylen(output[0]) == 3
        assert space.int_w(space.getitem(output[0], space.wrap(0))) == 3
        assert self.unwrap(output[1]) == 3

    def test_get_obj_vars(self):
        output = self.run('''
        class X {
            private $c;

            function __construct() {
               $this->a = 3;
               $this->b = 4;
               $this->c = 5;
            }

            function x() {
               return get_object_vars($this);
            }
        }

        $x = new X();
        echo get_object_vars($x);
        echo $x->x();

        ''')
        assert self.unwrap(output[0]) == {'a': 3, 'b': 4}
        assert self.unwrap(output[1]) == {'a': 3, 'b': 4, 'c': 5}

    def test_call_user_func_array(self):
        output = self.run('''
        function f($a, $b) {
           echo $a, $b;
        }
        call_user_func_array("f", array(1, 2));
        ''')
        assert [self.space.int_w(w_v) for w_v in output] == [1, 2]
        with self.warnings(["Warning: call_user_func_array() expects parameter 1 to be a valid callback, function 'xyz' not found or invalid function name"]):
            self.run('''
            call_user_func_array("xyz", array());
            ''')

    def test_call_user_func(self):
        output = self.run('''
        function f($a, $b) {
           echo $a, $b;
        }
        call_user_func("f", 1, 2);
        ''')
        assert [self.space.int_w(w_v) for w_v in output] == [1, 2]

    def test_call_user_func_instance_method(self):
        output = self.run('''
        class MyClass {
            function seeme($a) {
                echo $this->x, $a;
            }
        }
        $myinst = new MyClass;
        $myinst->x = 42;
        call_user_func(array($myinst, 'seeme'), -5);
        ''')
        assert [self.space.int_w(w_v) for w_v in output] == [42, -5]

    def test_call_user_func_static_method(self):
        output = self.run('''
        class MyClass {
            static function seeme($a) {
                echo $a;
            }
        }
        $myinst = new MyClass;
        call_user_func(array($myinst, 'seeme'), 42);
        call_user_func(array('MyClass', 'seeme'), -5);
        call_user_func('MyClass::seeme', 654);
        ''')
        assert [self.space.int_w(w_v) for w_v in output] == [42, -5, 654]

    def test_call_user_func_anonymous(self):
        output = self.run('''
        $f = function ($a) { echo $a * 7; };
        call_user_func($f, 6);
        ''')
        assert [self.space.int_w(w_v) for w_v in output] == [42]

    def test_debug_backtrace(self):
        output = self.run('''
        function g($a) {
            return f($a, $a+1);
        }
        function f($c, $d) {
            return debug_backtrace();
        }
        echo g(42);
        ''')
        it = output[0].as_rdict().items()
        assert len(it) >= 2
        assert it[0][0] == '0'
        d = it[0][1].as_rdict()
        assert d.keys() == ['file', 'line', 'function', 'args']
        assert self.space.str_w(d['function']) == 'f'
        assert it[1][0] == '1'
        d = it[1][1].as_rdict()
        assert d.keys() == ['file', 'line', 'function', 'args']
        assert self.space.str_w(d['function']) == 'g'

    def test_warn_argument_method(self):
        self.run('''
        class My extends Exception { }
        $e = new My();
        $e->getMessage(5);
        ''', ['Warning: Exception::getMessage() expects exactly 0 parameters, '
              '1 given'])

    def test_settype(self):
        output = self.run('''
        $a = "5a";
        settype($a, "int");
        echo $a;
        settype($a, "string");
        echo $a;
        settype($a, "bool");
        echo $a;
        $a = "5.3";
        settype($a, "float");
        echo $a;
        ''')
        assert self.unwrap(output[0]) == 5
        assert self.unwrap(output[1]) == "5"
        assert self.unwrap(output[2]) == True
        assert self.unwrap(output[3]) == 5.3

    def test_number_format(self):
        output = self.run("""
        echo number_format(123456.12);
        echo number_format(123456.12, 1);
        echo number_format(123, 1);
        echo number_format(123.12, 3);
        echo number_format(123.9, 0);
        echo number_format(123.99, 1);
        echo number_format(123.89, 1);
        echo number_format(0.045, 2);
        """)
        assert [self.unwrap(w_x) for w_x in output] == [
            "123,456", "123,456.1", "123.0", "123.120", "124", "124.0", "123.9",
            "0.05",
            ]

    def test_get_defined_constants(self):
        output = self.run("""
        define("foobar", 42);
        echo get_defined_constants();
        """)
        d = output[0].as_rdict()
        assert d['NuLl'] == d['NULL'] == d['null']
        assert self.unwrap(d['foobar']) == 42

    def test_get_defined_constants_categories(self):
        output = self.run("""
        define("foobar", 42);
        echo get_defined_constants(1);
        """)
        d = output[0].as_rdict()
        std = d['standard'].as_rdict()
        assert self.unwrap(std['INI_SYSTEM']) == 4
        user = d['user'].as_rdict()
        assert self.unwrap(user['foobar']) == 42

    def test_assert_global(self):
        output = self.run("""
        $x = 4;
        echo assert('$x == 4');
        """)
        assert self.unwrap(output[0]) == True

    def test_assert_class(self):
        output = self.run("""
        class Peoples
        {
            public $x = 5;

            function check() {
                echo assert('$this->x == 5');
            }
        }

        $people = new Peoples;
        $people->check();

        """)
        assert self.unwrap(output[0]) == True

    def test_eval(self):
        output = self.run("""
        echo eval('echo 4;');
        """)
        assert self.unwrap(output[0]) == 4

    def test_extract(self):
        output = self.run("""
        $a = array("b"=>2);
        extract($a);
        echo $b;
        """)
        assert self.unwrap(output[0]) == 2

    def test_class_alias_instanceof(self):
        output = self.run('''
        class foo {}
        class_alias('foo', 'bar');
        $foo1 = new foo;
        $bar1 = new bar;
        echo $foo1 instanceof $bar1;
        echo $bar1 instanceof $foo1;
        echo $bar1 instanceof foo;
        echo $bar1 instanceof bar;
        $name = 'bar';
        echo $bar1 instanceof $name;
        echo $foo1 instanceof $name;
        ''')
        assert output == map(self.space.newbool, [True] * 6)

    def test_class_alias_exceptions(self):
        output = self.run('''
        class Error1 extends Exception {}
        class_alias('Error1', 'Error2');
        try {
            throw new Error2;
        } catch (Error1 $e) {
            echo 'OK';
        }
        try {
            throw new Error1;
        } catch (Error2 $e) {
            echo 'OK';
        }
        ''')
        assert output == [self.space.newstr('OK')] * 2

    def test_class_alias_typehint(self):
        output = self.run('''
        class foo {}
        class_alias('foo', 'bar');
        $foo1 = new foo;
        $bar1 = new bar;

        function takes_foo(foo $x) { echo 'OK'; }
        function takes_bar(bar $x) { echo 'OK'; }
        takes_foo($bar1);
        takes_bar($foo1);
        ''')
        assert output == [self.space.newstr('OK')] * 2
