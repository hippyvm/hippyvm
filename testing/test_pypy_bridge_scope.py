from testing.test_interpreter import BaseTestInterpreter
from hippy.error import FatalError
import pytest

class TestPyPyBridgeScope(BaseTestInterpreter):

    def test_embed_py_func(self):
        phspace = self.space
        output = self.run('''

$src = <<<EOD
def f(a, b):
    return sum([a, b])
EOD;

$f = embed_py_func($src);

echo $f(4, 7);

        ''')
        assert phspace.int_w(output[0]) == 11


    def test_embed_py_func_inside_php_func(self):
        phspace = self.space
        output = self.run('''

function make() {

    $src = <<<EOD
def f(a, b):
    return sum([a, b])
EOD;

    $f = embed_py_func($src);
    return $f;
}

$g = make();
echo $g(5, 7);

        ''')
        assert phspace.int_w(output[0]) == 12


    def test_embed_py_func_resolve_var_outer(self):
        phspace = self.space
        output = self.run('''

function make() {

    $a = 2;

    $src = <<<EOD
def f(b):
    return sum([a, b])
EOD;

    $f = embed_py_func($src);
    return $f;
}

$g = make();
echo $g(3);

        ''')
        assert phspace.int_w(output[0]) == 5


    # embed_php_func

    # XXX move
    # --
    def test_embed_php_func(self):
        phspace = self.space
        output = self.run('''

$pysrc = <<<EOD
def f():
    php_src = "function g(\$a, \$b) { return \$a + \$b; }"
    g = embed_php_func(php_src)
    return g(5, 4)
EOD;

$f = embed_py_func($pysrc);
echo $f();

        ''')
        assert phspace.int_w(output[0]) == 9

    # --

    def test_php_looks_into_lexical_scope(self):
        phspace = self.space
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
        assert phspace.int_w(output[0]) == 8

    def test_lookup_php_constant(self):
        phspace = self.space
        output = self.run('''
            define("x", 3);
            $pysrc = <<<EOD
            def f():
                return x
            EOD;
            $f = embed_py_func($pysrc);
            echo($f());
        ''')
        assert phspace.int_w(output[0]) == 3

    # XXX test for looking up PHP function from python code
    # XXX test lookup up Python outer-outer scopes from PHP

    def test_transitive_scope_lookup(self):
        phspace = self.space
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
        assert phspace.int_w(output[0]) == 668

    def test_increment_outer_php_scope_from_python(self):
        pytest.skip("BROKEN")
        phspace = self.space
        output = self.run('''
$x = 44;
$src = <<<EOD
def f():
    php_src = "function g() { return \$x; }"
    g = embed_php_func(php_src)
    x += 1
    return g()
EOD;
$f = embed_py_func($src);

echo($f());
        ''')
        assert phspace.int_w(output[0]) == 45

    def test_php_sees_outer_py_functions(self):
        phspace = self.space
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
        assert phspace.int_w(output[0]) == 42

    # Broken, will need to be addressed when we overhaul scoping.
    # FatalError: Call to undefined function len()
    # FAO: ltratt
    @pytest.mark.xfail()
    def test_php_can_call_python_builtin(self):
        phspace = self.space

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
        assert phspace.int_w(output[0]) == 4

    def test_python_can_call_php_global_builtin(self):
        phspace = self.space

        output = self.run('''
            $src = <<<EOD
            def c(ary):
                return count(ary) # count is a PHP builtin func
            EOD;
            $c = embed_py_func($src);
            $n = $c(array(1, 2, 3, 4, 5, 6));
            echo($n);
        ''')
        assert phspace.int_w(output[0]) == 6

    def test_php_cant_call_normal_python_objects(self):
        phspace = self.space
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

    def test_python_calling_php_func(self):
        phspace = self.space
        output = self.run('''
        function f() {
            return "f";
        }

        $src = <<<EOD
        def test():
            return f()
        EOD;
        $test = embed_py_func($src);

        echo($test()); ''')
        assert phspace.str_w(output[0]) == "f"

    def test_python_calling_php_func_case_insensitive(self):
        phspace = self.space
        output = self.run('''
        function F() {
            return "F";
        }

        $src = <<<EOD
        def test():
            return "%s %s" % (f(), F())
        EOD;
        $test = embed_py_func($src);

        echo($test()); ''')
        assert phspace.str_w(output[0]) == "F F"

    def test_python_ref_php_class(self):
        phspace = self.space
        output = self.run('''
        $src = <<<EOD
        def ref():
            return C()
        EOD;

        $ref = embed_py_func($src);

        class C {
            function m() { return "c.m"; }
        }
        echo($ref()->m()); ''')
        assert phspace.str_w(output[0]) == "c.m"

    def test_python_lookup_php_attr(self):
        phspace = self.space
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
        assert phspace.int_w(output[0]) == 2

    def test_python_lookup_missing_php_attr(self):
        pytest.skip("BROKEN")
        phspace = self.space
        output = self.run("""
            $src = <<<EOD
            def ref():
                return C().x
            EOD;
            $ref = embed_py_func($src);

            class C {}
            $ref();
        """)
        assert phspace.int_w(output[0]) == 2

    def test_python_set_php_attr(self):
        phspace = self.space
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
        assert phspace.int_w(output[0]) == 3

    def test_python_call_php_method(self):
        phspace = self.space
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
        assert phspace.str_w(output[0]) == "c.m"

    def test_python_call_php_method_case_insensitive(self):
        phspace = self.space
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
        assert phspace.str_w(output[0]) == "c.m"

    def test_python_referencing_dollardollar_var(self):
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

    #
    # PHP importing Python
    #

    def test_import_py_mod_attr(self):
        import math
        phspace = self.space
        output = self.run('''
        $math = import_py_mod("math");
        echo($math->pi);
        ''')
        assert phspace.float_w(output[0]) == math.pi

    def test_import_py_nested1_mod_func(self):
        phspace = self.space
        output = self.run('''
        $os_path = import_py_mod("os.path");
        echo($os_path->join("a", "b"));
        ''')
        assert phspace.str_w(output[0]) == "a/b"

    def test_import_py_nested2_mod_func(self):
        phspace = self.space
        output = self.run('''
        $os = import_py_mod("os");
        echo($os->path->join("a", "b"));
        ''')
        assert phspace.str_w(output[0]) == "a/b"



    #
    # Python importing PHP
    #

    def test_import_global_php_ns(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def test():
                php = php_global_ns()
                return php.strlen("test")
            EOD;
            $test = embed_py_func($src);
            echo($test());
        ''')
        assert phspace.int_w(output[0]) == 4
