from testing.test_interpreter import BaseTestInterpreter
from hippy.error import FatalError
import pytest

class TestPyPyBridgeSpecialMethods(BaseTestInterpreter):
    def test_str(self, php_space):
        output = self.run('''
            class C {
                function __toString() {
                    return "C.__toString";
                }
            }

            $src = "def f(): return str(C())";
            $f = compile_py_func($src);

            echo($f());
        ''')
        assert php_space.str_w(output[0]) == "C.__toString"

    def test_str_of_py_mod_in_php(self, php_space):
        output = self.run('''
            $sys = import_py_mod("sys");
            echo $sys;
            echo (string) $sys;
        ''')
        expect = "<module 'sys' (built-in)>"
        assert php_space.str_w(output[0]) == expect
        assert php_space.str_w(output[1]) == expect

    def test_str_of_py_func_in_php(self, php_space):
        output = self.run('''
            $f = compile_py_func("def f(): pass");
            echo $f;
            echo (string) $f;
        ''')
        expect  = "<function f at "
        assert php_space.str_w(output[0]).startswith(expect)
        assert php_space.str_w(output[1]).startswith(expect)


    def test_str_of_py_meth_in_php001(self, php_space):
        output = self.run('''
            $pysrc = <<<EOD
            def f():
                class C(object):
                    def meth(self): pass
                return C.meth
            EOD;
            $f = compile_py_func($pysrc);
            $m = $f();
            echo $m;
            echo (string) $m;
        ''')
        expect  = "<unbound method C.meth>"
        assert php_space.str_w(output[0]) == expect
        assert php_space.str_w(output[1]) == expect

    def test_str_of_py_meth_in_php002(self, php_space):
        output = self.run('''
            $pysrc = <<<EOD
            def f():
                class C(object):
                    def meth(self): pass
                return C().meth
            EOD;
            $f = compile_py_func($pysrc);
            $m = $f();
            echo $m;
            echo (string) $m;
        ''')
        expect  = "<bound method C.meth of "
        assert php_space.str_w(output[0]).startswith(expect)
        assert php_space.str_w(output[1]).startswith(expect)


    def test_str_of_py_inst_in_php(self, php_space):
        output = self.run('''
            $pysrc = <<<EOD
            def f():
                class C(object): pass
                return C()
            EOD;
            $f = compile_py_func($pysrc);
            $c = $f();
            echo $c;
            echo (string) $c;
        ''')
        expect  = "<__builtin__.C object at "
        assert php_space.str_w(output[0]).startswith(expect)
        assert php_space.str_w(output[1]).startswith(expect)


    def test_str_of_py_list_in_php(self, php_space):
        # It's illegal to convert an array to a string in PHP
        errs = ["Notice: Array to string conversion"]
        output = self.run('''
            $pysrc = <<<EOD
            def f():
                return [1, 2, 3]
            EOD;
            $f = compile_py_func($pysrc);
            $a = $f();
            echo $a;
            echo (string) $a;
        ''', errs)
        expect = "Array"
        assert php_space.str_w(output[0]) == expect
        assert php_space.str_w(output[1]) == expect


    def test_str_of_py_dict_in_php(self, php_space):
        # It's illegal to convert an array to a string in PHP
        errs = ["Notice: Array to string conversion"]
        output = self.run('''
            $pysrc = <<<EOD
            def f():
                return {1: 'a', 2: 'b'}
            EOD;
            $f = compile_py_func($pysrc);
            $a = $f();
            echo $a;
            echo (string) $a;
        ''', errs)
        expect = "Array"
        assert php_space.str_w(output[0]) == expect
        assert php_space.str_w(output[1]) == expect


    def test_str_of_py_exn_in_php(self, php_space):
        output = self.run('''
            $pysrc = <<<EOD
            def f():
                return IndexError("questionable index")
            EOD;
            $f = compile_py_func($pysrc);
            $a = $f();
            echo $a;
            echo (string) $a;
        ''')
        expect = "questionable index"
        assert php_space.str_w(output[0]) == expect
        assert php_space.str_w(output[1]) == expect


    def test_str_of_py_class_in_php(self, php_space):
        output = self.run('''
            $pysrc = <<<EOD
            def f():
                class C(object): pass
                return C
            EOD;
            $f = compile_py_func($pysrc);
            $c = $f();
            echo $c;
            echo (string) $c;
        ''')
        expect = "<class 'C'>"
        assert php_space.str_w(output[0]) == expect
        assert php_space.str_w(output[1]) == expect

    def test_str_of_php_inst_in_py(self, php_space):
        output = self.run(r'''
        $pysrc = "def f(x): return str(x)";
        $f = compile_py_func($pysrc);

        class A {};
        try {
            $f(new A());
            echo "nope";
        } catch(PyException $e) {
            echo $e->getMessage();
        }
        ''')
        # You can't stringify a PHP instance in PHP, so we preserve this.
        err_s = "BridgeError: Wrapped PHP instance has no __toString method"
        assert php_space.str_w(output[0]) == err_s

    def test_str_of_php_class_in_py(self, php_space):
        output = self.run(r'''
        class A {};
        $pysrc = "def f(): return str(A)";
        $f = compile_py_func($pysrc);

        echo $f();
        ''')
        # Free to do whatever we want here really. In pure PHP you can't
        # get a handle on a class. They are instead passed around as strings.
        # This seems a reasonable behaviour.
        assert php_space.str_w(output[0]) == "A"

    def test_str_of_php_exn_in_py(self, php_space):
        output = self.run(r'''
        $pysrc = "def f(x): return str(x)";
        $f = compile_py_func($pysrc);

        echo $f(new LogicException("illogical"));
        ''')
        assert php_space.str_w(output[0]) == "illogical"

    def test_str_of_php_builtin_func_in_py(self, php_space):
        output = self.run(r'''
        $pysrc = "def f(): return str(array_shift)";
        $f = compile_py_func($pysrc);

        echo $f();
        ''')
        assert php_space.str_w(output[0]) == "array_shift"

    def test_str_of_php_user_func_in_py(self, php_space):
        output = self.run(r'''
        function ggg() {};
        $pysrc = "def f(): return str(ggg);";
        $f = compile_py_func($pysrc);

        echo $f();
        ''')
        assert php_space.str_w(output[0]) == "ggg"


    def test_str_of_php_unbound_meth_in_py(self, php_space):
        output = self.run(r'''
        class G { function w(){}};
        $pysrc = "def f(): return str(G.w)";
        $f = compile_py_func($pysrc);

        echo $f();
        ''')
        assert php_space.str_w(output[0]) == "w"


    def test_str_of_php_ref_in_py(self, php_space):
        output = self.run(r'''
        $pysrc = "def f(): return str(PHPRef(666))";
        $f = compile_py_func($pysrc);

        echo $f();
        ''')
        assert php_space.str_w(output[0]) == "<PHPRef>"
