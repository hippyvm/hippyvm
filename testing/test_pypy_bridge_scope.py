from testing.test_interpreter import BaseTestInterpreter
from hippy.error import FatalError
import pytest

class TestPyPyBridgeScope(BaseTestInterpreter):

    def test_embed_py_func_inside_php_func(self, php_space):
        output = self.run('''
            function make() {
                $src = "def f(a, b): return sum([a, b])";
                $f = embed_py_func($src);
                return $f;
            }

            $g = make();
            echo $g(5, 7);
        ''')
        assert php_space.int_w(output[0]) == 12

    def test_embed_py_func_resolve_var_outer(self, php_space):
        output = self.run('''
            function make() {
                $a = 2;
                $src = "def f(b): return sum([a, b])";
                $f = embed_py_func($src);
                return $f;
            }

            $g = make();
            echo $g(3);
        ''')
        assert php_space.int_w(output[0]) == 5

    def test_php_looks_into_lexical_scope(self, php_space):
        output = self.run('''
            $pysrc = <<<EOD
            def f():
                x = 1
                php_src = "function g(\$a) { return \$a + \$x; }"
                g = embed_php_func(php_src)
                return g
            EOD;

            $f = embed_py_func($pysrc);
            $g = $f();
            echo $g(7);
        ''')
        assert php_space.int_w(output[0]) == 8

    def test_lookup_php_constant(self, php_space):
        output = self.run('''
            define("x", 3);
            $pysrc = <<<EOD
            def f():
                return x
            EOD;
            $f = embed_py_func($pysrc);
            echo($f());
        ''')
        assert php_space.int_w(output[0]) == 3

    # XXX test for looking up PHP function from python code
    # XXX test lookup up Python outer-outer scopes from PHP

    def test_transitive_scope_lookup(self, php_space):
        output = self.run('''
            $x = 668;

            $src1 = <<<EOD
            def f1():
                src2 = """
                function f2() {
                    \$src3 = "def f3(): return x";
                    \$f3 = embed_py_func(\$src3);
                    return \$f3();
                }
                """
                f2 = embed_php_func(src2)
                return f2();
            EOD;

            $f1 = embed_py_func($src1);
            echo $f1();
        ''')
        assert php_space.int_w(output[0]) == 668

    def test_increment_outer_php_scope_from_python(self, php_space):
        output = self.run('''
            $x = 44;
            $src = <<<EOD
            def f():
                global x
                php_src = "function g() { return \$x; }"
                g = embed_php_func(php_src)
                x += 1
                return g()
            EOD;
            $f = embed_py_func($src);

            echo($f());
        ''')
        assert php_space.int_w(output[0]) == 45

    def test_php_sees_outer_py_functions(self, php_space):
        output = self.run('''
            $pysrc = <<<EOD
            def f():
                def g(): return 42

                phsrc = "function h() { return g(); }"
                h = embed_php_func(phsrc)

                return h()
            EOD;
            $f = embed_py_func($pysrc);
            echo($f());
        ''')
        assert php_space.int_w(output[0]) == 42

    # Broken, will need to be addressed when we overhaul scoping.
    # FatalError: Call to undefined function len()
    # FAO: ltratt
    @pytest.mark.xfail()
    def test_php_can_call_python_builtin(self, php_space):

        output = self.run('''
            $src = <<<EOD
            def c():
                src2 = "function c2(\$ls) { return len(\$ls); }"
                c2 = embed_php_func(src2)
                return(c2([1,2,3,4]))
            EOD;
            $c = embed_py_func($src);
            $n = $c();
            echo($n);
        ''')
        assert php_space.int_w(output[0]) == 4

    def test_python_can_call_php_global_builtin(self, php_space):

        output = self.run('''
            $src = <<<EOD
            def c(ary):
                return count(ary) # count is a PHP builtin func
            EOD;
            $c = embed_py_func($src);
            $n = $c(array(1, 2, 3, 4, 5, 6));
            echo($n);
        ''')
        assert php_space.int_w(output[0]) == 6

    def test_php_cant_call_normal_python_objects(self, php_space):
        with pytest.raises(FatalError):
            output = self.run('''
                $pysrc = <<<EOD
                def f():
                    g = 42

                    phsrc = "function h() { return g(); }"
                    h = embed_php_func(phsrc)

                    return h()
                EOD;
                $f = embed_py_func($pysrc);
                echo($f());
            ''')

    def test_python_calling_php_func(self, php_space):
        output = self.run('''
            function f() {
                return "f";
            }

            $src = <<<EOD
            def test():
                return f()
            EOD;
            $test = embed_py_func($src);

            echo($test());
        ''')
        assert php_space.str_w(output[0]) == "f"

    def test_python_calling_php_func_case_insensitive(self, php_space):
        output = self.run('''
            function F() {
                return "F";
            }

            $src = <<<EOD
            def test():
                return "%s %s" % (f(), F())
            EOD;
            $test = embed_py_func($src);

            echo($test());
        ''')
        assert php_space.str_w(output[0]) == "F F"

    def test_python_ref_php_class(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def ref():
                return C()
            EOD;

            $ref = embed_py_func($src);

            class C {
                function m() { return "c.m"; }
            }

            $inst = $ref();
            echo $inst->m();
        ''')
        assert php_space.str_w(output[0]) == "c.m"

    def test_python_lookup_php_attr(self, php_space):
        output = self.run("""
            $src = <<<EOD
            def ref():
                return C(2).x
            EOD;
            $ref = embed_py_func($src);

            class C {
                public $x;
                function __construct($x) {
                    $this->x = $x;
                }
            }
            echo($ref());
        """)
        assert php_space.int_w(output[0]) == 2

    def test_python_set_php_attr(self, php_space):
        output = self.run("""
            $src = <<<EOD
            def ref(c):
                c.x = 3
            EOD;
            $ref = embed_py_func($src);

            class C {
                public $x;
                function __construct($x) {
                    $this->x = $x;
                }
            }
            $c = new C(2);
            $ref($c);
            echo($c->x);
        """)
        assert php_space.int_w(output[0]) == 3

    def test_python_call_php_method(self, php_space):
        output = self.run("""
            $src = <<<EOD
            def ref():
                return C().m()
            EOD;
            $ref = embed_py_func($src);

            class C {
                function m() { return "c.m"; }
            }
            echo($ref());
        """)
        assert php_space.str_w(output[0]) == "c.m"

    def test_python_call_php_method_case_insensitive(self, php_space):
        output = self.run("""
            $src = <<<EOD
            def ref():
                return C().M()
            EOD;
            $ref = embed_py_func($src);

            class C {
                function M() { return "c.m"; }
            }
            echo($ref());
        """)
        assert php_space.str_w(output[0]) == "c.m"

    def test_python_referencing_dollardollar_var(self, php_space):
        output = self.run("""
            $a = "b";
            $$a = "c";

            $src = <<<EOD
            def ref():
                return b
            EOD;
            $ref = embed_py_func($src);
            echo($ref());
        """)
        assert self.space.str_w(output[0]) == "c"

    def test_import_py_mod_attr(self, php_space):
        import math
        output = self.run('''
            $math = import_py_mod("math");
            echo($math->pi);
        ''')
        assert php_space.float_w(output[0]) == math.pi

    def test_import_py_nested1_mod_func(self, php_space):
        output = self.run('''
            $os_path = import_py_mod("os.path");
            echo($os_path->join("a", "b"));
        ''')
        assert php_space.str_w(output[0]) == "a/b"

    def test_import_py_nested2_mod_func(self, php_space):
        output = self.run('''
            $os = import_py_mod("os");
            echo($os->path->join("a", "b"));
        ''')
        assert php_space.str_w(output[0]) == "a/b"

    def test_php2py_cross_lang_closure_is_late_binding(self, php_space):
        output = self.run('''
            $x = 42;
            $src = <<<EOD
            def f():
                return x;
            EOD;
            $f = embed_py_func($src);
            $x = 43;

            echo($f());
        ''')
        assert php_space.int_w(output[0]) == 43

    def test_php2py_cross_lang_closure_is_late_binding2(self, php_space):
        output = self.run('''
            $x = 64;
            $src = <<<EOD
            def f():
                def g():
                    return x;
                return g
            EOD;
            $f = embed_py_func($src);
            $x = 11;

            $g = $f();
            echo($g());
        ''')
        assert php_space.int_w(output[0]) == 11

    def test_py2php_cross_lang_closure_is_late_binding(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f():
                x = 44
                php_src = "function g() { return \$x; }"
                g = embed_php_func(php_src)
                x += 1
                return g()
            EOD;
            $f = embed_py_func($src);

            echo($f());
        ''')
        assert php_space.int_w(output[0]) == 45

    def test_py2php_cross_lang_closure_is_late_binding2(self, php_space):
        output = self.run('''
            $x = 44;
            $src = <<<EOD
            def f():
                php_src = "function g() { return \$x; }"
                g = embed_php_func(php_src)
                x = 45
                return g()
            EOD;
            $f = embed_py_func($src);

            echo($f());
        ''')
        assert php_space.int_w(output[0]) == 45

    def test_py2php_cross_lang_closure_is_late_binding3(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f():
                x = 44
                php_src = "function g() { return \$x; }"
                g = embed_php_func(php_src)
                x += 1
                return g
            EOD;
            $f = embed_py_func($src);
            $g = $f();

            echo($g());
        ''')
        assert php_space.int_w(output[0]) == 45

    def test_get_php_range(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f():
                php_src = "function g() { return range(0, 2); }"
                g = embed_php_func(php_src)
                return g()
            EOD;
            $f = embed_py_func($src);

            foreach ($f() as $i) {
                echo($i);
            }
        ''')
        assert len(output) == 3 \
           and php_space.str_w(output[0]) == "0" \
           and php_space.str_w(output[1]) == "1" \
           and php_space.str_w(output[2]) == "2"

    def test_get_py_range(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f():
                return range(0, 2)
            EOD;
            $f = embed_py_func($src);

            foreach ($f() as $i) {
                echo($i);
            }
        ''')
        assert len(output) == 2 \
           and php_space.str_w(output[0]) == "0" \
           and php_space.str_w(output[1]) == "1"

    def test_get_php_count(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f():
                def count(x): return -1
                php_src = "function g() { return count(array(0, 1)); }"
                g = embed_php_func(php_src)
                return g()
            EOD;
            $f = embed_py_func($src);

            echo($f());
        ''')
        assert self.space.int_w(output[0]) == 2

    def test_scopes_are_deterministic1(self, php_space):
        output = self.run('''
            function b() { return "b"; }
            $src = <<<EOD
            def f():
                print "f", b
                return b()
            EOD;
            $f = embed_py_func($src);
            echo $f();
            $a = "b";
            $$a = 2;
            echo $f();
        ''')
        assert self.space.str_w(output[0]) == "b" \
          and self.space.str_w(output[1]) == "b"

    def test_scopes_are_deterministic2(self, php_space):
        output = self.run('''
            class b { }
            function b() { return "b"; }
            $src = <<<EOD
            def f():
                return b()
            EOD;
            $f = embed_py_func($src);
            echo $f();
            echo $f();
        ''')
        assert self.space.str_w(output[0]) == "b" \
          and self.space.str_w(output[1]) == "b"

    def test_scopes_are_deterministic3(self, php_space):
        output = self.run('''
            $b = 2;
            function b() { return "b"; }
            $src = <<<EOD
            def f():
                return b
            EOD;
            $f = embed_py_func($src);
            echo $f();
            unset($b);
            try {
                echo $f();
            }
            catch (BridgeException $e) {
                echo "caught";
            }
        ''')
        assert self.space.int_w(output[0]) == 2 \
               and self.space.str_w(output[1]) == "caught"

    def test_php_global_scope_does_exist(self, php_space):
        output = self.run('''
            function f() { return "f"; }

            $pysrc = <<<EOD
            def g():
                return php_global_ns().f()
            EOD;
            $f = embed_py_func($pysrc);
            echo($f());
        ''')
        assert self.space.str_w(output[0]) == "f"

    def test_php_global_scope_doesnt_exist(self, php_space):
        output = self.run('''
            function f() { return "f"; }

            $pysrc = <<<EOD
            def g():
                return php_global_ns().e()
            EOD;
            $f = embed_py_func($pysrc);
            try {
                $f();
            } catch (BridgeException $e) {
                echo "caught";
            }
        ''')
        assert self.space.str_w(output[0]) == "caught"

    def test_mutate_php_array_in_py_scope_as_dict(self, php_space):
        output = self.run('''
        $arry = array(1, 2, 3);
        $f = embed_py_func("def f(): arry[3] = 4");

        $f();
        echo count($arry);
        echo $arry[3];
        ''')
        assert php_space.int_w(output[0]) == 4
        assert php_space.int_w(output[1]) == 4

    def test_mutate_php_array_in_py_scope_as_list(self, php_space):
        output = self.run('''
        $arry = array(1, 2, 3);
        $f = embed_py_func("def f(): arry.as_list()[3] = 4");

        $f();
        echo count($arry);
        echo $arry[3];
        ''')
        assert php_space.int_w(output[0]) == 4
        assert php_space.int_w(output[1]) == 4
