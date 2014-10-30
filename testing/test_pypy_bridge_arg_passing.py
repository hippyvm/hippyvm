from testing.test_interpreter import BaseTestInterpreter
import pytest

class TestPyPyBridgeArgPassing(BaseTestInterpreter):

    def test_php2py_obj_by_ref(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(x):
                x.v = 1337
            EOD;

            $f = embed_py_func($src);

            class A {
                function __construct($v) {
                    $this->v = $v;
                }
            };

            $in = new A(666);
            $f($in);
            echo $in->v;
        ''')
        assert php_space.int_w(output[0]) == 1337

    def test_php2py_str_by_ref(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(s):
                s.replace("1", "x") # strs immutible, returns new str!
            EOD;

            $f = embed_py_func($src);

            $in = "123";
            $f($in);
            echo $in;
        ''')
        assert php_space.str_w(output[0]) == "123" # i.e. unchanged

    def test_php2py_str_literal_by_ref(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(s): pass
            EOD;

            $f = embed_py_func($src);

            // passing a string constant by reference should not crash
            $f("123");
        ''')
        # no assert, just no crash

    def test_php2py_str_literal_by_ref_global_embed(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(s): pass
            EOD;

            embed_py_func_global($src);

            // passing a string constant by reference should not crash
            f("123");
        ''')
        # no assert, just no crash

    def test_php2py_mixed_key_array_by_ref(self):
        php_space = self.space
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
        assert php_space.str_w(output[0]) == "y"

    def test_php2py_int_key_array_by_ref(self):
        php_space = self.space
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
        assert php_space.str_w(output[0]) == "a"

    # ---

    def test_py2php_list_by_val(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f():
                l = [1,2,3]
                g(l)
                return l[0]
            EOD;

            function g($l) { $l[0] = 666; }

            $f = embed_py_func($src);
            $r = $f();
            echo $r;
        ''')
        assert php_space.int_w(output[0]) == 1

    def test_py2php_list_by_ref(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f():
                l = PHPRef([1,2,3])
                g(l)
                return l.deref()[0]
            EOD;

            function g(&$l) { $l[0] = 666; }

            $f = embed_py_func($src);
            $r = $f();
            echo $r;
        ''')
        assert php_space.int_w(output[0]) == 666

    def test_py2php_dict_by_val(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f():
                d = { "a" : "b", "b": "c" }
                g(d)
                return d["a"]
            EOD;

            function g($d) { $d["a"] = "z"; }

            $f = embed_py_func($src);
            $r = $f();
            echo $r;
        ''')
        assert php_space.str_w(output[0]) == "b"

    def test_py2php_dict_by_ref2(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f():
                d = { "a" : "b", "b": "c" }
                d_ref = PHPRef(d)
                g(d_ref)
                return d_ref.deref()["a"]
            EOD;

            function g(&$d) { $d["a"] = "z"; }

            $f = embed_py_func($src);
            $r = $f();
            echo $r;
        ''')
        assert php_space.str_w(output[0]) == "z"


    def test_py2php_int_by_val(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f():
                i = 1
                g(i)
                return i
            EOD;

            function g($i) { $i = 666; }

            $f = embed_py_func($src);
            $r = $f();
            echo $r;
        ''')
        assert php_space.int_w(output[0]) == 1

    def test_py2php_int_by_ref(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f():
                i = PHPRef(1337)
                g(i)
                return i.deref()
            EOD;

            function g(&$i) { $i = 666; }

            $f = embed_py_func($src);
            $r = $f();
            echo $r;
        ''')
        assert php_space.int_w(output[0]) == 666

    def test_py2php_obj_by_val(self):
        """note that it is the object id that is by value.
        the object is not copied like an array"""
        php_space = self.space
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
        assert php_space.int_w(output[0]) == 1
        assert php_space.int_w(output[1]) == 2

    def test_py2php_obj_by_ref(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f(a1, a2):
                p1, p2 = PHPRef(a1), PHPRef(a2)
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
        assert php_space.int_w(output[0]) == 2
        assert php_space.int_w(output[1]) == 1

    def test_py2php_str_by_val(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f():
                i = "old"
                g(i)
                return i
            EOD;

            function g($s) { $s = "new"; }

            $f = embed_py_func($src);
            $r = $f();
            echo $r;
        ''')
        assert php_space.str_w(output[0]) == "old"

    def test_py2php_str_by_val2(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f():
                i = "old"
                g(i)
                return i
            EOD;

            function g($s) { $s[0] = "x"; }

            $f = embed_py_func($src);
            $r = $f();
            echo $r;
        ''')
        assert php_space.str_w(output[0]) == "old"

    def test_py2php_str_by_ref(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f():
                i = PHPRef("old")
                g(i)
                return i.deref()
            EOD;

            function g(&$s) { $s = "new"; }

            $f = embed_py_func($src);
            $r = $f();
            echo $r;
        ''')
        assert php_space.str_w(output[0]) == "new"

    def test_py2php_str_by_ref2(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f():
                i = PHPRef("old")
                g(i)
                return i.deref()
            EOD;

            function g(&$s) { $s[0] = "x"; }

            $f = embed_py_func($src);
            $r = $f();
            echo $r;
        ''')
        assert php_space.str_w(output[0]) == "xld"

    def test_py2php_pref_to_non_ref_is_error(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f():
                i = PHPRef("old")
                try:
                    g(i) # is an error since we passed a ref to a non-ref arg
                    return "No exception!"
                except BridgeError as e:
                    return e.message
            EOD;

            function g($s) {}

            $f = embed_py_func($src);
            $r = $f();
            echo($r);
        ''')
        assert(php_space.str_w(output[0]) ==
                "Arg 1 of PHP func 'g' is pass by value")

    def test_py2php_value_to_ref_is_error(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def f():
                i = "old"
                try:
                    g(i) # is an error since we passed a ref to a non-ref arg
                    return "No exception!"
                except BridgeError as e:
                    return e.message
            EOD;

            function g(&$s) {}

            $f = embed_py_func($src);
            $r = $f();
            echo($r);
        ''')
        assert(php_space.str_w(output[0]) ==
                "Arg 1 of PHP func 'g' is pass by reference")

    def test_php2py_meth_args_by_ref(self, php_space):
        php_space = self.space
        output = self.run('''
            class C {};

            $src = <<<EOD
            def myMeth(self, ary):
                ary[3] = 123
                return ary
            EOD;
            embed_py_meth("C", $src);
            $c = new C();
            $ary = $c->myMeth(array(1, 2, 3));
            for ($i = 0; $i < count($ary); $i++) {
                echo $ary[$i];
            }
        ''')
        assert php_space.int_w(output[0]) == 1
        assert php_space.int_w(output[1]) == 2
        assert php_space.int_w(output[2]) == 3
        assert php_space.int_w(output[3]) == 123

    def test_php2py_meth_args_by_ref2(self, php_space):
        php_space = self.space
        output = self.run('''
            class C {};

            $src = <<<EOD
            def myMeth(self, ary):
                ary[3] = 123
                return ary
            EOD;
            embed_py_meth("C", $src);

            function takes_ref(&$ary) {
                $c = new C();
                $c->myMeth($ary);
                // should be equiv to:
                //$ary[3] = 123;
            }

            $a = array(1, 2, 3);
            takes_ref($a);

            for ($i = 0; $i < count($a); $i++) {
                echo $a[$i];
            }
        ''')
        assert php_space.int_w(output[0]) == 1
        assert php_space.int_w(output[1]) == 2
        assert php_space.int_w(output[2]) == 3
        assert php_space.int_w(output[3]) == 123

    @pytest.mark.xfail
    def test_php2py_existing_ref_respected(self, php_space):
        output = self.run('''
        function takes_ref(&$x) {
            $src = "def mutate_ref(y): y = 666";
            $mutate_ref = embed_py_func($src);
            $mutate_ref($x);
            echo $x;
        }

        $a = 1;
        takes_ref($a);
        echo $a;
        ''')
        assert php_space.int_w(output[0]) == 666
        assert php_space.int_w(output[1]) == 666

    @pytest.mark.xfail
    def test_php2py_existing_ref_respected2(self, php_space):
        output = self.run('''
        function takes_ref(&$x) {
            $src = "def mutate_ref(y): y = y + 1";
            $mutate_ref = embed_py_func($src);
            $mutate_ref($x);
            echo $x;
        }

        $a = 1;
        takes_ref($a);
        echo $a;
        ''')
        assert php_space.int_w(output[0]) == 2
        assert php_space.int_w(output[1]) == 2
