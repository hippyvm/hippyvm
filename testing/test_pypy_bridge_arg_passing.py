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

    def test_py2php_list_by_val(self):
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
        assert phspace.int_w(output[0]) == 1

    def test_py2php_list_by_ref(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f():
                l = PRef([1,2,3])
                g = embed_php_func("function g(&\$l) { \$l[0] = 666; }")
                g(l)
                return l.deref()[0]
            EOD;

            $f = embed_py_func($src);
            $r = $f();
            echo $r;
        ''')
        assert phspace.int_w(output[0]) == 666

    def test_py2php_int_by_val(self):
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

    def test_py2php_int_by_ref(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f():
                i = PRef(1337)
                g = embed_php_func("function g(&\$i) { \$i = 666; }")
                g(i)
                return i.deref()
            EOD;

            $f = embed_py_func($src);
            $r = $f();
            echo $r;
        ''')
        assert phspace.int_w(output[0]) == 666

    def test_py2php_obj_by_val(self):
        """note that it is the object id that is by value.
        the object is not copied like an array"""
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(a1, a2):
                swap_local(a1, a2)
                return [a1, a2]
            EOD;

            $f = embed_py_func($src);

            class C {
                function __construct($v) {
                    $this->v = $v;
                }
            };

            function swap_local($o1, $o2) {
                $tmp = $o1;
                $o1 = $o2;
                $o2 = $tmp;
            }

            $c1 = new C(1);
            $c2 = new C(2);

            $arr = $f($c1, $c2);
            echo $arr[0]->v;
            echo $arr[1]->v;
        ''')
        # they should not swap
        assert phspace.int_w(output[0]) == 1
        assert phspace.int_w(output[1]) == 2

    def test_py2php_obj_by_ref(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(a1, a2):
                p1, p2 = PRef(a1), PRef(a2)
                swap(p1, p2)
                return [p1.deref(), p2.deref()]
            EOD;

            $f = embed_py_func($src);

            class C {
                function __construct($v) {
                    $this->v = $v;
                }
            };

            function swap(&$o1, &$o2) {
                $tmp = $o1;
                $o1 = $o2;
                $o2 = $tmp;
            }

            $c1 = new C(1);
            $c2 = new C(2);

            $arr = $f($c1, $c2);
            echo $arr[0]->v;
            echo $arr[1]->v;
        ''')
        assert phspace.int_w(output[0]) == 2
        assert phspace.int_w(output[1]) == 1
