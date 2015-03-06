from testing.test_interpreter import BaseTestInterpreter
import pytest

class TestPyPyBridgeExceptions(BaseTestInterpreter):

    @pytest.fixture
    def php_space(self):
        return self.space

    def test_py_exn_is_passed_up_to_phpc(self, php_space):
        output = self.run('''
            $src = "def raise_ex(): raise ValueError('my error')";
            $raise_ex = embed_py_func($src);
            try {
                $raise_ex();
                echo "no";
            } catch (PyException $e) {
                echo "yes";
            }
        ''')
        assert php_space.str_w(output[0]) == "yes"

    def test_wrapped_py_exn_message(self, php_space):
        output = self.run('''
            $src = "def raise_ex(): raise ValueError('my error')";
            $raise_ex = embed_py_func($src);
            try {
                $raise_ex();
                echo "no";
            } catch (PyException $e) {
                echo $e->getMessage();
            }
        ''')
        assert php_space.str_w(output[0]) == "my error"

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

            $catch_php_exn = embed_py_func($src);

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

            $catch_php_exn = embed_py_func($src);

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

            $catch_php_exn = embed_py_func($src);

            function raise_php_exn() {
                throw new RuntimeException("oh no!");
            }

            $r = $catch_php_exn();
            echo $r;

        ''')
        assert php_space.str_w(output[0]) == "oh no!"

        # XXX more tests that check line number, trace, filename etc.

    def test_exns_can_pass_pass_thru_multiple_langs(self, php_space):
        output = self.run('''
            $src = "def py_f1(): php_f()";
            $py_f1 = embed_py_func($src);

            $src2 = "def py_f2(): raise ValueError('explosion')";
            $py_f2 = embed_py_func($src2);

            function php_f() {
                global $py_f2;
                $py_f2();
            }

            try {
                $py_f1();
                echo "fail";
            } catch (PyException $e) {
                echo $e->getMessage();
            }
        ''')
        assert php_space.str_w(output[0]) == "explosion"

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
            $ref = embed_py_func($src);

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
            $do = embed_py_func($src);
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
        $py_func = embed_py_func($src);
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
        $py_func = embed_py_func($src);

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
        $py_func = embed_py_func($src);

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

            $f = embed_py_func($src);
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

            $f = embed_py_func($src);
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

            $f = embed_py_func($src);
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

            $f = embed_py_func($src);
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

            $f = embed_py_func($src);
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

            $f = embed_py_func($src);
            echo($f());
        ''')
        err_s = "Cannot use kwargs when calling PHP functions"
        assert php_space.str_w(output[0]) == err_s

    def test_py_compile_error(self, php_space):
        output = self.run('''
            $src = "    def bad_indent(): pass";
            try {
                $f = embed_py_func($src);
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
            embed_py_meth("A", $src);
            $a = new A();

            try {
                $a->f(1, 2, 3);
                echo "fail";
            } catch (PyException $e) {
                echo $e->getMessage();
            }
        ''')
        err_s = "f() takes no arguments (4 given)"
        assert php_space.str_w(output[0]) == err_s

    def test_class_cannot_be_passed_to_php(self, php_space):
        output = self.run('''
        class A {};

        $src = <<<EOD
        def f():
            return A
        EOD;

        embed_py_func_global($src);
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
        assert php_space.str_w(output[0]) == "Failed to find Python function or method"

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
        assert php_space.str_w(output[0]) == "Invalid argument to call_py_func"

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
            embed_py_meth("A", $src);

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

            embed_py_func_global($src);
            try {
                call_py_func("f", [], [1 => "z"]);
                echo "fail";
            } catch (BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        assert php_space.str_w(output[0]) == "Python kwargs must have string keys"
