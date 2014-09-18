from testing.test_interpreter import MockInterpreter, BaseTestInterpreter

import pytest

class TestPyPyBridgeArrayConversions(BaseTestInterpreter):

    def test_return_py_list_len_in_php(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return [1,2,3]
            EOD;

            $f = embed_py_func($src);
            $ar = $f();
            echo(count($ar));
        ''')
        assert phspace.int_w(output[0]) == 3

    def test_return_py_list_vals_in_php(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return [3, 2, 1]
            EOD;

            $f = embed_py_func($src);
            $ar = $f();

            for ($i = 0; $i < 3; $i++) {
                echo($ar[$i]);
            }
        ''')
        for i in range(3):
            assert phspace.int_w(output[i]) == 3 - i

    def test_iter_vals_py_list_in_php(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return [3, 2, 1]
            EOD;

            $f = embed_py_func($src);
            $ar = $f();

            foreach ($ar as $i) {
                echo($i);
            }
        ''')
        for i in range(3):
            assert phspace.int_w(output[i]) == 3 - i

    def test_iter_keys_vals_py_list_in_php(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return ["zero", "one", "two"]
            EOD;

            $f = embed_py_func($src);
            $ar = $f();

            foreach ($ar as $k => $v) {
                echo("$k:$v");
            }
        ''')
        assert phspace.str_w(output[0]) == "0:zero"
        assert phspace.str_w(output[1]) == "1:one"
        assert phspace.str_w(output[2]) == "2:two"


    def test_py_list_setitem_in_php(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return ["zero", "one", "two"]
            EOD;

            $f = embed_py_func($src);
            $ar = $f();

            $ar[1] = "three";
            for ($i = 0; $i < 3; $i++) {
                echo($ar[$i]);
            }
        ''')
        assert phspace.str_w(output[0]) == "zero"
        assert phspace.str_w(output[1]) == "three"
        assert phspace.str_w(output[2]) == "two"

    def test_py_list_append_in_php(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return ["zero", "one", "two"]
            EOD;

            $f = embed_py_func($src);
            $ar = $f();

            $ar[] = "three";
            for ($i = 0; $i < 4; $i++) {
                echo($ar[$i]);
            }
        ''')
        assert phspace.str_w(output[0]) == "zero"
        assert phspace.str_w(output[1]) == "one"
        assert phspace.str_w(output[2]) == "two"
        assert phspace.str_w(output[3]) == "three"

    def test_return_py_dict_len_in_php(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return {"a" : "b", "c" : "d", "e" : "f"}
            EOD;

            $f = embed_py_func($src);
            $ar = $f();
            echo(count($ar));
        ''')
        assert phspace.int_w(output[0]) == 3

    def test_return_py_dict_vals_str_key_in_php(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return {"a" : "b", "c" : "d", "e" : "f"}
            EOD;

            $f = embed_py_func($src);
            $ar = $f();
            echo($ar["a"]);
            echo($ar["c"]);
            echo($ar["e"]);
        ''')
        assert phspace.str_w(output[0]) == "b"
        assert phspace.str_w(output[1]) == "d"
        assert phspace.str_w(output[2]) == "f"

    def test_return_py_dict_vals_int_key_in_php(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return {6 : "a", 7 : "b", 8 : "c"}
            EOD;

            $f = embed_py_func($src);
            $ar = $f();
            echo($ar[8]);
            echo($ar[7]);
            echo($ar[6]);
        ''')
        assert phspace.str_w(output[0]) == "c"
        assert phspace.str_w(output[1]) == "b"
        assert phspace.str_w(output[2]) == "a"

    def test_iter_vals_py_dict_in_php(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return {"x" : 10, 999 : 14, "z" : -1}
            EOD;

            $f = embed_py_func($src);
            $ar = $f();

            foreach ($ar as $i) {
                echo($i);
            }
        ''')
        # ordering is that of python dict
        assert phspace.int_w(output[0]) == 10
        assert phspace.int_w(output[1]) == -1
        assert phspace.int_w(output[2]) == 14

    def test_iter_keys_vals_py_dict_in_php(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return {"x" : 10, 999 : 14, "z" : -1}
            EOD;

            $f = embed_py_func($src);
            $ar = $f();

            foreach ($ar as $k => $v) {
                echo("$k:$v");
            }
        ''')
        # ordering is that of python dict
        assert phspace.str_w(output[0]) == "x:10"
        assert phspace.str_w(output[1]) == "z:-1"
        assert phspace.str_w(output[2]) == "999:14"

    def test_py_dict_setitem_int_in_php(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return { 0 : "one", 1 : "two", 2 : "three" }
            EOD;

            $f = embed_py_func($src);
            $ar = $f();

            $ar[1] = "bumble";
            for ($i = 0; $i < 3; $i++) {
                echo($ar[$i]);
            }
        ''')
        assert phspace.str_w(output[0]) == "one"
        assert phspace.str_w(output[1]) == "bumble"
        assert phspace.str_w(output[2]) == "three"

    def test_py_dict_setitem_str_in_php(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return { 0 : "one", 1 : "two", 2 : "three" }
            EOD;

            $f = embed_py_func($src);
            $ar = $f();

            $ar["x"] = "bumble";
            echo($ar[0]);
            echo($ar[1]);
            echo($ar[2]);
            echo($ar["x"]);
        ''')
        assert phspace.str_w(output[0]) == "one"
        assert phspace.str_w(output[1]) == "two"
        assert phspace.str_w(output[2]) == "three"
        assert phspace.str_w(output[3]) == "bumble"

    def test_py_dict_setitem_str_in_php2(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return { "one" : "one", "two" : "two", "three" : "three" }
            EOD;

            $f = embed_py_func($src);
            $ar = $f();

            $ar["two"] = "bumble";
            echo($ar["one"]);
            echo($ar["two"]);
            echo($ar["three"]);
        ''')
        assert phspace.str_w(output[0]) == "one"
        assert phspace.str_w(output[1]) == "bumble"
        assert phspace.str_w(output[2]) == "three"

    # We need to decide a semantics for [] on a wrapped Python dict/list
    @pytest.mark.xfail
    def test_py_dict_append_in_php(self):

        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(): return { "x" : "one", "y" : "two", "z" : "three" }
            EOD;

            $f = embed_py_func($src);
            $ar = $f();

            $ar[] = "bumble"; # ?!?!
                    ''')
        # XXX assert

    def test_array_type_over_php_py_boundary(self):
        phspace = self.space
        output = self.run('''
            $src = "def f(a): return type(a) == dict";
            $f = embed_py_func($src);

            $in = array("my", "array", 2, 3);

            echo($f($in));
        ''')
        assert phspace.is_true(output[0])

    def test_array_type_over_php_py_boundary2(self):
        phspace = self.space
        output = self.run('''
            $src = "def f(a): return type(a.as_list()) == list";
            $f = embed_py_func($src);

            $in = array(1, 2, 4, 8, 16);

            echo($f($in));
        ''')
        assert phspace.is_true(output[0])

    def test_cannot_apply_as_list_to_wrapped_mixed_key_php_array(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(a):
                try:
                    a.as_list() # boom
                except BridgeError: # XXX read message
                    return True
                else:
                    return False
            EOD;

            $f = embed_py_func($src);
            $in = array("a" => 1); // mixed keys
            echo($f($in));
        ''')

        assert self.space.is_true(output[0])

    def test_as_list_invalidates(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(arry_d):
                arry_l = arry_d.as_list()
                arry_d["x"] = 890 #non-integer keyed
                try:
                    arry_l[0] # stale!
                except BridgeError as e:
                    return e.args[0]
            EOD;

            $f = embed_py_func($src);
            $in = array(1, 2, 3); // int keys
            echo($f($in));
        ''')
        assert phspace.str_w(output[0]) == \
                "Stale wrapped PHP array. No longer integer keyed!"

    # XXX We need a load more invalidation tests.
    # One for every operation that could cause a WListArrayObject to become
    # a WRDictArrayObject.

    def test_php_empty_array_len_in_python(self):
        phspace = self.space
        output = self.run('''
            $src = "def f(a): return len(a)";
            $f = embed_py_func($src);
            $in = array();
            echo($f($in));
        ''')
        assert phspace.int_w(output[0]) == 0

    def test_php_int_key_array_len_in_python(self):
        phspace = self.space
        output = self.run('''
            $src = "def f(a): return len(a.as_list())";
            $f = embed_py_func($src);
            $in = array("an", "intkeyed", "array");
            echo($f($in));
        ''')
        assert phspace.int_w(output[0]) == 3

    def test_php_mixed_key_array_len_in_python(self):
        phspace = self.space
        output = self.run('''
            $src = "def f(ary): return len(ary)";
            $f = embed_py_func($src);
            $in = array("a" => 1, "b" => "mixed-key", "c" => "array");
            echo($f($in));
        ''')
        assert phspace.int_w(output[0]) == 3

    def test_php_int_key_array_vals_in_python(self):
        phspace = self.space
        output = self.run('''
            $src = "def f(ary, idx): return ary[idx]";
            $f = embed_py_func($src);
            $in = array("an", "intkeyed", "array");

            echo($f($in, 0));
            echo($f($in, 1));
            echo($f($in, 2));
        ''')
        assert phspace.str_w(output[0]) == "an"
        assert phspace.str_w(output[1]) == "intkeyed"
        assert phspace.str_w(output[2]) == "array"

    def test_php_int_key_array_vals_in_python_as_list(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(ary, idx):
                ls = ary.as_list()
                return ls[idx]
            EOD;

            $f = embed_py_func($src);
            $in = array("an", "intkeyed", "array");

            echo($f($in, 0));
            echo($f($in, 1));
            echo($f($in, 2));
        ''')
        assert phspace.str_w(output[0]) == "an"
        assert phspace.str_w(output[1]) == "intkeyed"
        assert phspace.str_w(output[2]) == "array"

    def test_php_int_key_array_len_in_python_as_list(self):
        phspace = self.space
        output = self.run('''
            $src = "def f(ary): return len(ary.as_list())";
            $f = embed_py_func($src);
            $in = array("an", "intkeyed", "array");
            echo($f($in));
        ''')
        assert phspace.int_w(output[0]) == 3

    def test_php_mixed_key_array_vals_in_python(self):
        phspace = self.space
        output = self.run('''
            $src = "def f(ary, idx): return ary[idx]";
            $f = embed_py_func($src);
            $in = array("a" => 1, "b" => 22, "c" => 333);

            echo($f($in, "a"));
            echo($f($in, "b"));
            echo($f($in, "c"));
        ''')
        assert phspace.int_w(output[0]) == 1
        assert phspace.int_w(output[1]) == 22
        assert phspace.int_w(output[2]) == 333

    def test_php_mixed_key_array_iteritems_in_python(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ret = []
                for x, y in ary.iteritems():
                    ret += ["%s,%s" % (x, y)]
                return "|".join(ret)
            EOD;

            $f = embed_py_func($src);
            $in = array("a" => 1, "b" => 22, "c" => 333);
            echo($f($in));
        ''')
        assert phspace.str_w(output[0]) == "a,1|b,22|c,333"

    def test_php_mixed_key_array_iterkeys_in_python(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ret = [ x for x in ary.iterkeys() ]
                return "|".join(ret)
            EOD;

            $f = embed_py_func($src);
            $in = array("a" => 1, "b" => 22, "c" => 333);
            echo($f($in));
        ''')
        assert phspace.str_w(output[0]) == "a|b|c"

    def test_php_mixed_key_array_itervalues_in_python(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ret = [ str(x) for x in ary.itervalues() ]
                return "|".join(ret)
            EOD;

            $f = embed_py_func($src);
            $in = array("a" => 1, "b" => 22, "c" => 333);
            echo($f($in));
        ''')
        assert phspace.str_w(output[0]) == "1|22|333"

    def test_php_int_key_array_iteritems_in_python(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ret = []
                for x, y in ary.iteritems():
                    ret += ["%s,%s" % (x, y)]
                return "|".join(ret)
            EOD;

            $f = embed_py_func($src);
            $in = array(2, 1, 0);
            echo($f($in));
        ''')
        assert phspace.str_w(output[0]) == "0,2|1,1|2,0"

    def test_php_int_key_array_iterkeys_in_python(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ret = [ str(x) for x in ary.iterkeys() ]
                return "|".join(ret)
            EOD;

            $f = embed_py_func($src);
            $in = array("a", "b", "c");
            echo($f($in));
        ''')
        assert phspace.str_w(output[0]) == "0|1|2"

    def test_php_int_key_array_itervalues_in_python(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ret = [ x for x in ary.itervalues() ]
                return "|".join(ret)
            EOD;

            $f = embed_py_func($src);
            $in = array("x", "y", "z");
            echo($f($in));
        ''')
        assert phspace.str_w(output[0]) == "x|y|z"

    def test_php_mixed_key_array_setitem_in_python_ret(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ary["x"] = "y"
                print(72 * "*")
                print(ary)
                return ary
            EOD;

            $f= embed_py_func($src);
            $in = array("x", "y", "z");
            $out = $f($in);
            echo $out["x"];
        ''')
        assert phspace.str_w(output[0]) == "y"

    def test_php_mixed_key_array_setitem_in_python_no_ret(self):
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

    def test_php_int_key_array_setitem_in_python_ret(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ary_l = ary.as_list()
                ary_l[3] = "a"
                return ary
            EOD;

            $f = embed_py_func($src);
            $in = array("x", "y", "z");
            $out = $f($in);
            echo $out[3];
        ''')
        assert phspace.str_w(output[0]) == "a"

    def test_php_int_key_array_append_in_python(self):
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

class TestPyPyBridgeArrayConversionsInstances(BaseTestInterpreter):

    def test_python_array_in_php_instance(self):
        phspace = self.space
        output = self.run('''
            $src = <<<EOD
            def A_construct(self, v):
                self.v = v + 1
            EOD;
            $A_construct = embed_py_func($src);

            class A {
                function __construct($v) {
                    global $A_construct;
                    $A_construct($this, $v);
                }
            }

            $a = new A(665);
            echo($a->v);
        ''')
        assert phspace.int_w(output[0]) == 666
