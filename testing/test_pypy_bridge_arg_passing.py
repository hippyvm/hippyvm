from testing.test_interpreter import BaseTestInterpreter
import pytest

class TestPyPyBridgeArgPassing(BaseTestInterpreter):

    def test_php2py_mixed_key_array_by_ref(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ary["x"] = "y"
            EOD;

            $f = embed_py_func($src);
            $in = array("x", "y", "z");
            $f($in);
            echo $in["x"];
        ''')
        assert phspace.str_w(output[0]) == "y"

    def test_php2py_int_key_array_by_ref(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ary_l = ary.as_list()
                ary_l.append("a")
            EOD;

            $f = embed_py_func($src);
            $in = array("x", "y", "z");
            $f($in);
            echo $in[3];
        ''')
        assert phspace.str_w(output[0]) == "a"

    @pytest.mark.xfail
    def test_py2php_list_default_by_val(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f():
                l = [1,2,3]
                g = embed_php_func("function g(\$l) { \$l[0] = 666; }")
                g(l)
                return l[0]
            EOD;

            $f = embed_py_func($src);
            $r = $f();
            echo $r;
        ''')
        assert phspace.int_w(output[0]) == 0

    def test_py2php_list_by_ref(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f():
                l = [1,2,3]
                g = embed_php_func("function g(&\$l) { \$l[0] = 666; }")
                g(l)
                return l[0]
            EOD;

            $f = embed_py_func($src);
            $r = $f();
            echo $r;
        ''')
        assert phspace.int_w(output[0]) == 666

    def test_py2php_int_default_by_val(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f():
                i = 1
                g = embed_php_func("function g(\$i) { \$i = 666; }")
                g(i)
                return i
            EOD;

            $f = embed_py_func($src);
            $r = $f();
            echo $r;
        ''')
        assert phspace.int_w(output[0]) == 1

    @pytest.mark.xfail
    def test_py2php_int_by_ref(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f():
                i = 1
                g = embed_php_func("function g(&\$i) { \$i = 666; }")
                g(i)
                return i
            EOD;

            $f = embed_py_func($src);
            $r = $f();
            echo $r;
        ''')
        assert phspace.int_w(output[0]) == 666
