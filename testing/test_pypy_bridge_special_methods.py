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
