from testing.test_interpreter import BaseTestInterpreter
import pytest

class TestPyPyBridgeExceptions(BaseTestInterpreter):

    @pytest.fixture
    def php_space(self):
        return self.space

    def test_py_exn_is_passed_up_to_phpc(self, php_space):
        output = self.run('''
            $src = "def raise_ex(): raise ValueError('my error')";
            $raise_ex = compile_py_func($src);
            try {
                $raise_ex();
                echo "no";
            } catch (ValueError $e) {
                echo "yes";
            }
        ''')
        assert php_space.str_w(output[0]) == "yes"

    def test_py_exn_is_passed_up_to_phpc_catch_superclass(self, php_space):
        output = self.run('''
            $src = "def raise_ex(): raise ValueError('my error')";
            $raise_ex = compile_py_func($src);
            try {
                $raise_ex();
                echo "no";
            } catch (BaseException $e) {
                echo "yes";
            }
        ''')
        assert php_space.str_w(output[0]) == "yes"

    def test_wrapped_py_exn_message(self, php_space):
        output = self.run('''
            $src = "def raise_ex(): raise ValueError('my error')";
            $raise_ex = compile_py_func($src);
            try {
                $raise_ex();
                echo "no";
            } catch (ValueError $e) {
                echo $e->getMessage();
            }
        ''')
        assert php_space.str_w(output[0]) == "ValueError: my error"

    def test_php_exn_is_passed_up_to_py(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def catch_php_exn():
                try:
                    raise_php_exn();
                    return "bad"
                except PHPException:
                    return "ok"
            EOD;

            $catch_php_exn = compile_py_func($src);

            function raise_php_exn() {
                throw new RuntimeException("oh no!");
            }

            $r = $catch_php_exn();
            echo $r;

        ''')
        assert php_space.str_w(output[0]) == "ok"

    def test_php_exn_str_in_py(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def catch_php_exn():
                try:
                    raise_php_exn();
                    return "bad"
                except PHPException as e:
                    return str(e)
            EOD;

            $catch_php_exn = compile_py_func($src);

            function raise_php_exn() {
                throw new RuntimeException("oh no!");
            }

            $r = $catch_php_exn();
            echo $r;

        ''')
        assert php_space.str_w(output[0]) == "oh no!"

    def test_php_exn_message_in_py(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def catch_php_exn():
                #x = PHPException # forces PHPException to exist
                try:
                    raise_php_exn();
                    return "bad"
                except PHPException as e:
                    return e.message
            EOD;

            $catch_php_exn = compile_py_func($src);

            function raise_php_exn() {
                throw new RuntimeException("oh no!");
            }

            $r = $catch_php_exn();
            echo $r;

        ''')
        assert php_space.str_w(output[0]) == "oh no!"

        # XXX more tests that check line number, trace, filename etc.

    @pytest.mark.xfail
    def test_custom_py_exn_is_passed_up_to_phpc(self, php_space):
        # could this ever work
        output = self.run('''
            $src = <<<EOD
            def make_exception():
                class MyException(BaseException): pass
                return MyException
            EOD;
            $my_exception_maker = compile_py_func($src);
            $my_exception = $my_exception_maker();

            $src = <<<EOD
            def custom_exception(x):
                raise x
            EOD;

            $raise_ex = compile_py_func($src);
            try {
                $raise_ex($my_exception);
                echo "no";
            } catch (my_exception $e) {
                echo "yes";
            }
        ''')
        assert php_space.str_w(output[0]) == "yes"

    def test_local_py_exn_can_be_used_in_php(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def make_nested():
                class MyException(BaseException): pass
                php_src = """function g() {
                    try { throw new MyException(); }
                    catch (MyException \$e) { echo "yes"; }
                }"""

                compile_php_func(php_src)()
            EOD;

            $make_nested = compile_py_func($src);
            $make_nested();
        ''')
        assert php_space.str_w(output[0]) == "yes"

    def test_local_py_exn_inherited_catch_in_php(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def make_nested():
                class MyException(BaseException): pass
                php_src = """function g() {
                    try { throw new MyException(); }
                    catch (BaseException \$e) { echo "yes"; }
                }"""

                compile_php_func(php_src)()
            EOD;

            $make_nested = compile_py_func($src);
            $make_nested();
        ''')
        assert php_space.str_w(output[0]) == "yes"

    def test_exns_can_pass_pass_thru_multiple_langs(self, php_space):
        output = self.run('''
            $src = "def py_f1(): php_f()";
            $py_f1 = compile_py_func($src);

            $src2 = "def py_f2(): raise ValueError('explosion')";
            $py_f2 = compile_py_func($src2);

            function php_f() {
                global $py_f2;
                $py_f2();
            }

            try {
                $py_f1();
                echo "fail";
            } catch (ValueError $e) {
                echo $e->getMessage();
            }
        ''')
        assert php_space.str_w(output[0]) == "ValueError: explosion"

    def test_python_lookup_missing_php_attr(self, php_space):
        output = self.run("""
            $src = <<<EOD
            def ref():
                c = C()
                try:
                    c.x # boom
                    return "fails"
                except BridgeError as e:
                    return e.message
            EOD;
            $ref = compile_py_func($src);

            class C {}
            echo($ref());
        """)
        e_str = "Wrapped PHP instance has no attribute 'x'"
        assert php_space.str_w(output[0]) == e_str

    def test_bridgeerror_subclasses_exception(self, php_space):
        output = self.run("""
            $src = <<<EOD
            def do():
                e = BridgeError("test")
                try:
                    raise e
                    return "failed"
                except Exception as e:
                    return e.message
            EOD;
            $do = compile_py_func($src);
            echo($do());
        """)
        e_str = "test"
        assert php_space.str_w(output[0]) == e_str

    @pytest.mark.xfail
    def test_call_nonexist(self, php_space):

        output = self.run('''
        $m = import_py_mod("os");
        try {
            echo($m->wibble); // nonexistent
        } catch(BridgeException $e) {
            echo($e->getMessage());
        }
        ''')
        err_s = "XXX"
        assert php_space.str_w(output[0]) == err_s

    def test_using_kwargs_to_a_php_func_raises(self, php_space):
        output = self.run('''
        function php_func($a) {
        }

        $src = <<<EOD
        def py_func():
            try:
                php_func(a=1)
                return "test fail"
            except BridgeError as e:
                return e.message
        EOD;
        $py_func = compile_py_func($src);
        echo($py_func());
        ''')
        err_s = "Cannot use kwargs when calling PHP functions"
        assert php_space.str_w(output[0]) == err_s

    def test_calling_a_non_callable_php_instance_in_py_raises(self, php_space):
        output = self.run('''
        class A {
                // has no __invoke
        };

        $src = <<<EOD
        def py_func(inst):
            try:
                return inst()
                return "fail"
            except BridgeError as e:
                return e.message
        EOD;
        $py_func = compile_py_func($src);

        $inst = new A();
        echo($py_func($inst));
        ''')
        err_s = "Wrapped PHP instance is not callable"
        assert php_space.str_w(output[0]) == err_s

    def test_calling_a_callable_php_instance_with_kwargs_in_py_raises(self, php_space):
        output = self.run('''
        class A {
                function __invoke($x) { }
        };

        $src = <<<EOD
        def py_func(inst):
            try:
                return inst(x=1)
                return "fail"
            except BridgeError as e:
                return e.message
        EOD;
        $py_func = compile_py_func($src);

        $inst = new A();
        echo($py_func($inst));
        ''')
        err_s = "Cannot use kwargs with callable PHP instances"
        assert php_space.str_w(output[0]) == err_s

    def test_dict_like_py_list_setitem_out_of_range(self, php_space):
        output = self.run('''
            function f_id($x) { return $x; }

            $src = <<<EOD
            def f():
                r = f_id([1, 2, 3])
                try:
                    r[999] = "lala"
                    return "failed"
                except IndexError as e:
                    return e.message
            EOD;

            $f = compile_py_func($src);
            echo($f());
        ''')
        err_s = "list index out of range"
        assert php_space.str_w(output[0]) == err_s

    def test_dict_like_py_list_getitem_out_of_range(self, php_space):
        output = self.run('''
            function f_id($x) { return $x; }

            $src = <<<EOD
            def f():
                r = f_id([1, 2, 3])
                try:
                    x = r[999]
                    return "failed"
                except IndexError as e:
                    return e.message
            EOD;

            $f = compile_py_func($src);
            echo($f());
        ''')
        err_s = "list index out of range"
        assert php_space.str_w(output[0]) == err_s

    def test_dict_like_py_list_setitem_index_not_int(self, php_space):
        output = self.run('''
            function f_id($x) { return $x; }

            $src = <<<EOD
            def f():
                r = f_id([1, 2, 3])
                try:
                    r["a"] = 0
                    return "fail"
                except BridgeError as e:
                    return e.message
            EOD;

            $f = compile_py_func($src);
            echo($f());
        ''')
        err_s = "Non-integer key used on a Python dict with internal list storage"
        assert php_space.str_w(output[0]) == err_s

    def test_dict_like_py_list_getitem_index_not_int(self, php_space):
        output = self.run('''
            function f_id($x) { return $x; }

            $src = <<<EOD
            def f():
                r = f_id([1, 2, 3])
                try:
                    x = r["a"]
                    return "fail"
                except BridgeError as e:
                    return e.message
            EOD;

            $f = compile_py_func($src);
            echo($f());
        ''')
        err_s = "Non-integer key used on a Python dict with internal list storage"
        assert php_space.str_w(output[0]) == err_s

    def test_py_dict_cant_as_list(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f():
                dct = {1 :  2}
                try:
                    dct.as_list()
                    return "failed"
                except BridgeError as e:
                    return e.message
            EOD;

            $f = compile_py_func($src);
            echo($f());
        ''')
        err_s = "as_list does not apply"
        assert php_space.str_w(output[0]) == err_s

    def test_kwargs_raise(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f():
                try:
                    count(myarg=123)
                    return "fail"
                except BridgeError as e:
                    return e.message
            EOD;

            $f = compile_py_func($src);
            echo($f());
        ''')
        err_s = "Cannot use kwargs when calling PHP functions"
        assert php_space.str_w(output[0]) == err_s

    def test_py_compile_error(self, php_space):
        output = self.run('''
            $src = "    def bad_indent(): pass";
            try {
                $f = compile_py_func($src);
                echo "fail";
            } catch (BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        err_start = "Failed to compile Python code: IndentationError: unexpected indent"
        assert php_space.str_w(output[0]).startswith(err_start)

    def test_call_py_meth_wrong_num_args(self, php_space):
        output = self.run('''
            class A {};
            $src = "def f(): pass";
            compile_py_meth("A", $src);
            $a = new A();

            try {
                $a->f(1, 2, 3);
                echo "fail";
            } catch (TypeError $e) {
                echo $e->getMessage();
            }
        ''')
        err_s = "TypeError: f() takes no arguments (4 given)"
        assert php_space.str_w(output[0]) == err_s

    def test_class_cannot_be_passed_to_php(self, php_space):
        output = self.run('''
        class A {};

        $src = <<<EOD
        def f():
            return A
        EOD;

        compile_py_func_global($src);
        try {
            f();
            $s = "failed";
        } catch (BridgeException $e) {
            $s = $e->getMessage();
        }
        echo $s;
        ''')
        estr = "Cannot convert wrapped PHP class to PHP. Classes are not first class"
        assert php_space.str_w(output[0]) == estr

    def test_except_kwarg_from_php(self, php_space):
        output = self.run('''
            function f() {}
            try {
                call_py_func("f", [], ["a" => "z"]);
                echo "fail";
            } catch (BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        assert php_space.str_w(output[0]) == "Failed to find Python function or method"

    def test_except_kwarg_from_php2(self, php_space):
        output = self.run('''
            class A {
                static function f() {}
            }
            try {
                call_py_func("A::f", [], ["a" => "z"]);
                echo "fail";
            } catch (BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        err_s = "Method 'f' is not a static Python method"
        assert php_space.str_w(output[0]) == err_s

    def test_except_kwarg_from_php3(self, php_space):
        output = self.run('''
            $f = function() {};
            try {
                call_py_func($f, [], ["a" => "z"]);
                echo "fail";
            } catch (BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        assert php_space.str_w(output[0]) == "Not a Python callable"

    def test_except_kwarg_from_php4(self, php_space):
        output = self.run('''
            try {
                call_py_func([], [], ["a" => "z"]);
                echo "fail";
            } catch (BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        err_s = "When passing an array to call_py_func, len must be 2"
        assert php_space.str_w(output[0]) == err_s

    def test_except_kwarg_from_php5(self, php_space):
        output = self.run('''
            try {
                call_py_func([1, 2], [], ["a" => "z"]);
                echo "fail";
            } catch (BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        err_s = "method name should be a string"
        assert php_space.str_w(output[0]) == err_s

    def test_except_kwarg_from_php6(self, php_space):
        expected_warnings = ["Fatal error: Call to a member function f() on a non-object"]
        output = self.run('''
            call_py_func([1, "f"], [], ["a" => "z"]);
        ''', expected_warnings)

    def test_except_kwarg_from_php7(self, php_space):
        output = self.run('''
            class A{};
            $a = new A();
            try {
                call_py_func([$a, "f"], [], ["a" => "z"]);
                echo "fail";
            } catch (BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        assert php_space.str_w(output[0]) == "Failed to find Python function or method"

    def test_except_kwarg_from_php8(self, php_space):
        output = self.run('''
            class A{
                  private function f() {}
            };
            $a = new A();
            try {
                call_py_func([$a, "f"], [], ["a" => "z"]);
                echo "fail";
            } catch (BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        assert php_space.str_w(output[0]) == "Failed to find Python function or method"

    def test_except_kwarg_from_php9(self, php_space):
        output = self.run('''
            class A {}
            $src = <<<EOD
            @php_decor(access="private")
            def f(self, a="a", b="b", c="c"):
                  return a + b + c
            EOD;
            compile_py_meth("A", $src);

            $a = new A();
            try {
                call_py_func([$a, "f"], [], ["a" => "z"]);
                echo "fail";
            } catch (BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        assert php_space.str_w(output[0]) == "Failed to find Python function or method"

    def test_except_kwarg_from_php10(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(a="a", b="b", c="c"):
                  return a + b + c
            EOD;

            compile_py_func_global($src);
            try {
                // 1 indistinguishable from "1" in array key in PHP
                call_py_func("f", [], [1 => "z"]);
                echo "fail";
            } catch (BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        assert php_space.str_w(output[0]) == "TypeError: f() got an unexpected keyword argument '1'"

    def test_except_kwarg_from_php11(self, php_space):
        output = self.run('''
            // any old python function
            $sys = import_py_mod("sys");
            $rl = $sys->getrecursionlimit;

            try {
                call_py_func($rl, 1, []); // type is wrong
                echo "fail";
            } catch (BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        err_s = "Bad call_py_func argument specification"
        assert php_space.str_w(output[0]) == err_s

    def test_except_kwarg_from_php12(self, php_space):
        output = self.run('''
            // any old python function
            $sys = import_py_mod("sys");
            $rl = $sys->getrecursionlimit;

            try {
                call_py_func($rl, [], 1); // type is wrong
                echo "fail";
            } catch (BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        err_s = "Bad call_py_func argument specification"
        assert php_space.str_w(output[0]) == err_s

    def test_except_kwarg_from_php13(self, php_space):
        output = self.run('''
            class A {
                function a() {} // not in Python
            };

            try {
                call_py_func('A::a', [], []);
                echo "fail";
            } catch (BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        err_s = "Method 'a' is not a static Python method"
        assert php_space.str_w(output[0]) == err_s

    def test_except_kwarg_from_php14(self, php_space):
        output = self.run('''
            class A {
            };

            $src = 'def a(): pass'; // not static
            compile_py_meth("A", $src);

            try {
                call_py_func('A::a', [], []);
                echo "fail";
            } catch (BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        err_s = "Method 'a' is not a static Python method"
        assert php_space.str_w(output[0]) == err_s

    def test_kwarg_from_php15(self, php_space):
        output = self.run('''
            $A = 1;
            try {
                call_py_func(["A", "f"], [], []);
                echo "fail";
            } catch(BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        err_s = "Name 'A' is not a class"
        assert php_space.str_w(output[0]) == err_s

    def test_kwarg_from_php16(self, php_space):
        output = self.run('''
            $pysrc = <<<EOD
            def f():
                A = 1 # not a class
                php_src = "function g() { call_py_func('A::k', [], []); }"
                g = compile_php_func(php_src)
                return g
            EOD;
            $f = compile_py_func($pysrc);
            $g = $f();

            try {
                $g();
                echo "fail";
            } catch(BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        err_s = "Name 'A' is not a class"
        assert php_space.str_w(output[0]) == err_s

    def test_kwarg_from_php17(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(a="a", b="b", c="c"):
                  return a + b + c
            EOD;

            $f = compile_py_func_global($src);

            try {
                // positional arguments with string keys -- bogus
                call_py_func("f", ["b" => "b"], ["a" => "z"]);
                echo "fail";
            } catch(BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        err_s = "Bad call_py_func argument specification"
        assert php_space.str_w(output[0]) == err_s

    def test_unbound_meth_too_no_self(self, php_space):
        output = self.run('''
        {
            class Base {
                public $a = 0;
                function __construct($a) {
                    $this->a = $a;
                }
            }

            class Sub extends Base {
            }

            // too few args, needs at the very least 1 to bind to
            // when called will raise BridgeError which is passed up
            $src = "def __construct(self, a): Base.__construct()";
            compile_py_meth("Sub", $src);

            try {
                $inst = new Sub(6);
                echo "fail";
            } catch (BridgeError $e) {
                echo $e->getMessage();
            }
        }
        ''')
        err_s = "BridgeError: Call to unbound PHP method requires at-least one argument (for $this)"
        assert php_space.str_w(output[0]) == err_s

    def test_php_unbound_meth_bad_ref_arg(self, php_space):
        output = self.run('''
        {
            class Base {
                public $a = 0;
                function __construct(&$a) {
                    $this->a = $a;
                }
            }

            class Sub extends Base {
            }

            // will raise BridgeError
            $src = "def __construct(self, a): Base.__construct(self, a)";
            compile_py_meth("Sub", $src);

            try {
                $inst = new Sub(6);
                echo "fail";
            } catch (BridgeError $e) {
                echo $e->getMessage();
            }
        }
        ''')
        err_s = "BridgeError: Arg 1 of PHP func '__construct' is pass by reference"
        assert php_space.str_w(output[0]) == err_s

    def test_php_unbound_meth_bad_val_arg(self, php_space):
        output = self.run('''
        {
            class Base {
                public $a = 0;
                function __construct($a) {
                    $this->a = $a;
                }
            }

            class Sub extends Base {
            }

            // will raise BridgeError
            $src = "def __construct(self, a): Base.__construct(self, PHPRef(a))";
            compile_py_meth("Sub", $src);

            try {
                $inst = new Sub(6);
                echo "fail";
            } catch (BridgeError $e) {
                echo $e->getMessage();
            }
        }
        ''')
        err_s = "BridgeError: Arg 1 of PHP func '__construct' is pass by value"
        assert php_space.str_w(output[0]) == err_s

    def test_php_unbound_meth_unwrap_raises(self, php_space):
        output = self.run('''
        {
            class Base {
                public $a = 0;
                function __construct($a) {
                    $this->a = $a;
                }
            }

            // will raise BridgeError
            $src = "def f(): return Base.__construct";
            compile_py_func_global($src);

            try {
                f();
                echo "fail";
            } catch (BridgeError $e) {
                echo $e->getMessage();
            }
        }
        ''')
        err_s = "BridgeError: Cannot unwrap unbound PHP method."
        assert php_space.str_w(output[0]) == err_s

    def test_pop_empty_on_php_array_strategy(self, php_space):
        output = self.run('''
        $src = "def f(a): return a.as_list().pop()";
        compile_py_func_global($src);

        try {
            f(array());
            echo "fail";
        } catch(IndexError $e) {
            echo $e->getMessage();
        }
        ''')
        err_s = "IndexError: pop from empty list"
        assert php_space.str_w(output[0]) == err_s

    def test_pop_empty_on_php_array_strategy2(self, php_space):
        expected_warnings = ["Notice: Undefined index: a"]
        output = self.run('''
        $src = "def f(a): return a.pop('a')";
        compile_py_func_global($src);
        f(array());
        ''', expected_warnings)

    @pytest.mark.xfail
    def test_incorrect_access_on_php_decor(self, php_space):
        output = self.run('''
        $src = <<<EOD
        @php_decor(access="bacon")
        def f(self):
            pass
        EOD;

        class A{};

        compile_py_meth("A", $src);
        /*
        try {
            compile_py_meth("A", $src);
            echo "fail";
        } catch (PyException $e) {
            echo "ok";
        }
        */
        ''')
        # XXX suitable error message
        assert php_space.str_w(output[0]) == "ok"

    def test_compile_py_in_py(self, php_space):
        output = self.run('''

        $src = <<<EOD
        def f():
            src2 = 'def g(): return 123'
            g = compile_py_func(src2)
            return g()
        EOD;
        $f = compile_py_func($src);
        try {
            $f();
            echo 'fail';
        } catch (BridgeError $e) {
            echo $e->getMessage();
        }
        ''')
        err_s = 'BridgeError: Adapting forbidden PHP function'
        assert php_space.str_w(output[0]) == err_s

    def test_compile_py_in_py2(self, php_space):
        output = self.run('''
        $src = <<<EOD
        def f():
            src2 = 'def g(): 123'
            compile_py_func_global(src2)
        EOD;
        $f = compile_py_func($src);
        try {
            $f();
            echo 'fail';
        } catch (BridgeError $e) {
            echo $e->getMessage();
        }
        ''')
        err_s = 'BridgeError: Adapting forbidden PHP function'
        assert php_space.str_w(output[0]) == err_s

    def test_compile_py_in_py3(self, php_space):
        output = self.run('''
        {
            class A {};

            $src = <<<EOD
def f():
    src2 = 'def g(): return 123'
    compile_py_meth('A', src2)
EOD;
            $f = compile_py_func($src);

            $a = new A();
            try {
                $f();
                echo 'fail';
            } catch (BridgeError $e) {
                echo $e->getMessage();
            }
        }
        ''')
        err_s = 'BridgeError: Adapting forbidden PHP function'
        assert php_space.str_w(output[0]) == err_s

    def test_compile_php_in_php(self, php_space):
        output = self.run('''

        $src = <<<EOD
        def f():
            src2 = "function g() { compile_php_func('function h(){}'); }"
            return compile_php_func(src2)
        EOD;
        $f = compile_py_func($src);
        try {
            $ff = $f();
            $ff();
            echo 'fail';
        } catch (BridgeException $e) {
            echo $e->getMessage();
        }
        ''')
        err_s = "Adapting forbidden Python function"
        assert php_space.str_w(output[0]) == err_s

    def test_compile_php_func_two_funcs(self, php_space):
        output = self.run('''
            $pysrc = <<<EOD
            def comp():
                php_src = "function f(){}; function g(){};"
                g = compile_php_func(php_src)
            EOD;

            $comp = compile_py_func($pysrc);
            try {
                $comp();
                echo "fail";
            } catch (BridgeError $e) {
                echo $e->getMessage();
            }
        ''')
        err_s = "BridgeError: compile_php_func expects source code for a single PHP function"
        assert php_space.str_w(output[0]) == err_s

    def test_call_pyclass_attr(self, php_space):
        expected_warnings = ["Fatal error: Call to undefined method A::x()"]
        output = self.run('''
        $src = <<<EOD
        def f():
            class A:
                x = 1
            return A
        EOD;
        compile_py_func_global($src);
        $a = f();
        $a::x(); // bogus
        ''', expected_warnings)

    def test_call_py_func_on_pyclass_attr(self, php_space):
        output = self.run('''
        $src = <<<EOD
        def f():
            class A:
                x = 1
            return A
        EOD;
        compile_py_func_global($src);
        $a = f();

        try {
            call_py_func([$a, "x"], [], []); // bogus
            echo "fail";
        } catch(BridgeException $e) {
            echo $e->getMessage();
        }
        ''')
        err_s = "Failed to find Python function or method"
        assert php_space.str_w(output[0]) == err_s

    def test_call_private_method_from_subclass_in_py(self, php_space):
        output = self.run('''
        {
        class A {
            private function secret() { return 31415; }
        }

        class B extends A {}

        $pysrc = <<<EOD
        def get_secret(self):
            return self.secret()
        EOD;
        compile_py_meth("B", $pysrc);

        $b = new B();
        try {
            $b->get_secret();
            echo "failed";
        } catch (BridgeError $e) {
            echo $e->getMessage();
        }
        }
        ''')
        err_s = "BridgeError: Wrapped PHP instance has no attribute 'secret'"
        assert php_space.str_w(output[0]) == err_s

    def test_call_private_method_from_py_func(self, php_space):
        output = self.run('''
        {
        class A {
            private function secret() { return 31415; }
        }

        $pysrc = <<<EOD
        def get_secret():
            a = A()
            return a.secret()
        EOD;
        compile_py_func_global($pysrc);

        try {
            $s = get_secret();
            echo $s;
        } catch (BridgeError $e) {
            echo $e->getMessage();
        }
        }
        ''')
        err_s = "BridgeError: Wrapped PHP instance has no attribute 'secret'"
        assert php_space.str_w(output[0]) == err_s

    def test_get_private_attr_from_subclass_in_py(self, php_space):
        output = self.run('''
        {
        class A {
            private $secret = 454;
        }

        class B extends A{};

        $pysrc = <<<EOD
        def get_secret(self):
            return self.secret
        EOD;
        compile_py_meth("B", $pysrc);

        $b = new B();
        try {
            echo $b->get_secret();
        } catch(BridgeError $e) {
            echo $e->getMessage();
        }
        }
        ''')
        err_s = "BridgeError: Wrapped PHP instance has no attribute 'secret'"
        assert php_space.str_w(output[0]) == err_s

    def test_get_private_attr_from_py_func(self, php_space):
        errs = ["Fatal error: Cannot access private property A::$secret"]
        output = self.run('''
        {
        class A {
            private $secret = 454;
        }

        $pysrc = <<<EOD
        def get_secret():
            a = A();
            return a.secret
        EOD;
        compile_py_func_global($pysrc);

        get_secret();
        }
        ''', expected_warnings=errs)

    def test_set_private_attr_from_py_func(self, php_space):
        errs = ["Fatal error: Cannot access private property A::$secret"]
        output = self.run('''
        {
        class A {
            private $secret = 454;
        }

        $pysrc = <<<EOD
        def set_secret():
            a = A();
            a.secret = 555;
            return a.secret
        EOD;
        compile_py_func_global($pysrc);

        try {
            echo set_secret();
        } catch(PyException $e) {
            echo $e->getMessage();
        }
        }
        ''', errs)

    def test_throw_from_php_box(self, php_space):
        output = self.run('''
        $src = <<<EOD
        def f():
            psrc = "function g() { throw new LogicException('oops'); }"
            g = compile_php_func(psrc)
            g();
        EOD;
        compile_py_func_global($src);

        try {
            f();
        } catch(LogicException $e) {
            echo $e->getMessage();
        }
        ''')
        assert php_space.str_w(output[0]) == "oops"

    def test_bad_access_php_decor(self, php_space):
        output = self.run(r'''
        class A {};

        $pysrc = <<<EOD
        @php_decor(access="kangaroo")
        def f(self):
            pass
        EOD;
        try {
            compile_py_meth("A", $pysrc);
            echo "failed";
        } catch (BridgeError $e) {
                echo $e->getMessage();
        }
        ''')
        err_s = "BridgeError: 'kangaroo' is not a valid access modifier"
        assert php_space.str_w(output[0]) == err_s
