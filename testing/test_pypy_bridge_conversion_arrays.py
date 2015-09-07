from testing.test_interpreter import BaseTestInterpreter, SeqAssert

import pytest

class TestPyPyBridgeArrayConversions(BaseTestInterpreter):

    def test_nested_py_list_in_php(self, php_space):
        output = self.run('''
        $src = <<<EOD
        def make():
            return [1, 2, ["a", "b", "c"]]
        EOD;

        $make = compile_py_func($src);
        $arr = $make();

        echo count($arr);
        echo $arr[0];
        echo $arr[1];

        echo count($arr[2]);
        echo $arr[2][0];
        echo $arr[2][1];
        echo $arr[2][2];
        ''')
        assert php_space.int_w(output[0]) == 3
        assert php_space.int_w(output[1]) == 1
        assert php_space.int_w(output[2]) == 2

        assert php_space.int_w(output[3]) == 3
        assert php_space.str_w(output[4]) == "a"
        assert php_space.str_w(output[5]) == "b"
        assert php_space.str_w(output[6]) == "c"

    def test_nested_py_list_compare_in_php(self, php_space):
        output = self.run('''
        $src = <<<EOD
        def make():
            return [1, 2, ["a", "b", "c"]]
        EOD;

        $make = compile_py_func($src);
        $arr1 = $make();
        $arr2 = array(1, 2, array("a", "b", "c"));

        echo $arr1 == $arr2;
        ''')
        assert php_space.is_true(output[0])

    def test_return_py_list_len_in_php(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(): return [1,2,3]
            EOD;

            $f = compile_py_func($src);
            $ar = $f();
            echo(count($ar));
        ''')
        assert php_space.int_w(output[0]) == 3

    def test_return_py_list_vals_in_php(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(): return [3, 2, 1]
            EOD;

            $f = compile_py_func($src);
            $ar = $f();

            for ($i = 0; $i < 3; $i++) {
                echo($ar[$i]);
            }
        ''')
        for i in range(3):
            assert php_space.int_w(output[i]) == 3 - i

    def test_cannot_getitem_str_on_py_list_in_php(self, php_space):
        output = self.run('''
            $src = "def f(): return [3, 2, 1]";
            $f = compile_py_func($src);

            $ar = $f();
            try {
                $ar["k"];
            } catch(BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        err_s = "Cannot access string keys of wrapped Python list"
        assert php_space.str_w(output[0]) == err_s

    def test_cannot_setitem_str_on_py_list_in_php(self, php_space):
        output = self.run('''
            $src = "def f(): return [3, 2, 1]";
            $f = compile_py_func($src);

            $ar = $f();
            try {
                $ar["k"] = "oops";
            } catch(BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        err_s = "Cannot set string keys of wrapped Python list"
        assert php_space.str_w(output[0]) == err_s

    def test_iter_vals_py_list_in_php(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(): return [3, 2, 1]
            EOD;

            $f = compile_py_func($src);
            $ar = $f();

            foreach ($ar as $i) {
                echo($i);
            }
        ''')
        for i in range(3):
            assert php_space.int_w(output[i]) == 3 - i

    def test_iter_keys_vals_py_list_in_php(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(): return ["zero", "one", "two"]
            EOD;

            $f = compile_py_func($src);
            $ar = $f();

            foreach ($ar as $k => $v) {
                echo("$k:$v");
            }
        ''')
        assert php_space.str_w(output[0]) == "0:zero"
        assert php_space.str_w(output[1]) == "1:one"
        assert php_space.str_w(output[2]) == "2:two"


    def test_py_list_setitem_in_php(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(): return ["zero", "one", "two"]
            EOD;

            $f = compile_py_func($src);
            $ar = $f();

            $ar[1] = "three";
            for ($i = 0; $i < 3; $i++) {
                echo($ar[$i]);
            }
        ''')
        assert php_space.str_w(output[0]) == "zero"
        assert php_space.str_w(output[1]) == "three"
        assert php_space.str_w(output[2]) == "two"

    def test_py_list_is_copy_on_write_in_php(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(): return ["zero", "one", "two"]
            EOD;

            $f = compile_py_func($src);
            $ar1 = $f();
            $ar2 = $ar1;

            $ar1[0] = "apples";
            echo($ar1[0]);
            echo($ar2[0]);

        ''')
        assert php_space.str_w(output[0]) == "apples"
        assert php_space.str_w(output[1]) == "zero"

    def test_py_list_is_copy_on_write_in_php2(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(): return ["zero", "one", "two"]
            EOD;

            $f = compile_py_func($src);
            $ar1 = $f();
            $ar2 = $ar1;

            $ar2[0] = "apples";
            echo($ar1[0]);
            echo($ar2[0]);

        ''')
        assert php_space.str_w(output[0]) == "zero"
        assert php_space.str_w(output[1]) == "apples"

    def test_py_dict_is_copy_on_write_in_php(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(): return { "aa" : "a", "bb" : "b", "cc" : "c" }
            EOD;

            $f = compile_py_func($src);
            $ar1 = $f();
            $ar2 = $ar1;

            $ar1["aa"] = "apples";
            echo($ar1["aa"]);
            echo($ar2["aa"]);

        ''')
        assert php_space.str_w(output[0]) == "apples"
        assert php_space.str_w(output[1]) == "a"

    def test_py_dict_is_copy_on_write_in_php2(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(): return { "aa" : "a", "bb" : "b", "cc" : "c" }
            EOD;

            $f = compile_py_func($src);
            $ar1 = $f();
            $ar2 = $ar1;

            $ar2["aa"] = "apples";
            echo($ar1["aa"]);
            echo($ar2["aa"]);

        ''')
        assert php_space.str_w(output[0]) == "a"
        assert php_space.str_w(output[1]) == "apples"

    def test_py_list_append_in_php(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(): return ["zero", "one", "two"]
            EOD;

            $f = compile_py_func($src);
            $ar = $f();

            $ar[] = "three";
            for ($i = 0; $i < 4; $i++) {
                echo($ar[$i]);
            }
        ''')
        assert php_space.str_w(output[0]) == "zero"
        assert php_space.str_w(output[1]) == "one"
        assert php_space.str_w(output[2]) == "two"
        assert php_space.str_w(output[3]) == "three"

    def test_return_py_dict_len_in_php(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(): return {"a" : "b", "c" : "d", "e" : "f"}
            EOD;

            $f = compile_py_func($src);
            $ar = $f();
            echo(count($ar));
        ''')
        assert php_space.int_w(output[0]) == 3

    def test_return_py_dict_vals_str_key_in_php(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(): return {"a" : "b", "c" : "d", "e" : "f"}
            EOD;

            $f = compile_py_func($src);
            $ar = $f();
            echo($ar["a"]);
            echo($ar["c"]);
            echo($ar["e"]);
        ''')
        assert php_space.str_w(output[0]) == "b"
        assert php_space.str_w(output[1]) == "d"
        assert php_space.str_w(output[2]) == "f"

    def test_return_py_dict_vals_int_key_in_php(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(): return {6 : "a", 7 : "b", 8 : "c"}
            EOD;

            $f = compile_py_func($src);
            $ar = $f();
            echo($ar[8]);
            echo($ar[7]);
            echo($ar[6]);
        ''')
        assert php_space.str_w(output[0]) == "c"
        assert php_space.str_w(output[1]) == "b"
        assert php_space.str_w(output[2]) == "a"

    def test_iter_vals_py_dict_in_php(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(): return {"x" : 10, 999 : 14, "z" : -1}
            EOD;

            $f = compile_py_func($src);
            $ar = $f();

            foreach ($ar as $i) {
                echo($i);
            }
        ''')
        # ordering is that of python dict
        assert php_space.int_w(output[0]) == 10
        assert php_space.int_w(output[1]) == -1
        assert php_space.int_w(output[2]) == 14

    def test_iter_keys_vals_py_dict_in_php(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(): return {"x" : 10, 999 : 14, "z" : -1}
            EOD;

            $f = compile_py_func($src);
            $ar = $f();

            foreach ($ar as $k => $v) {
                echo("$k:$v");
            }
        ''')
        # ordering is that of python dict
        assert php_space.str_w(output[0]) == "x:10"
        assert php_space.str_w(output[1]) == "z:-1"
        assert php_space.str_w(output[2]) == "999:14"

    def test_py_dict_setitem_int_in_php(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(): return { 0 : "one", 1 : "two", 2 : "three" }
            EOD;

            $f = compile_py_func($src);
            $ar = $f();

            $ar[1] = "bumble";
            for ($i = 0; $i < 3; $i++) {
                echo($ar[$i]);
            }
        ''')
        assert php_space.str_w(output[0]) == "one"
        assert php_space.str_w(output[1]) == "bumble"
        assert php_space.str_w(output[2]) == "three"

    def test_py_dict_setitem_str_in_php(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(): return { 0 : "one", 1 : "two", 2 : "three" }
            EOD;

            $f = compile_py_func($src);
            $ar = $f();

            $ar["x"] = "bumble";
            echo($ar[0]);
            echo($ar[1]);
            echo($ar[2]);
            echo($ar["x"]);
        ''')
        assert php_space.str_w(output[0]) == "one"
        assert php_space.str_w(output[1]) == "two"
        assert php_space.str_w(output[2]) == "three"
        assert php_space.str_w(output[3]) == "bumble"

    def test_py_dict_setitem_str_in_php2(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(): return { "one" : "one", "two" : "two", "three" : "three" }
            EOD;

            $f = compile_py_func($src);
            $ar = $f();

            $ar["two"] = "bumble";
            echo($ar["one"]);
            echo($ar["two"]);
            echo($ar["three"]);
        ''')
        assert php_space.str_w(output[0]) == "one"
        assert php_space.str_w(output[1]) == "bumble"
        assert php_space.str_w(output[2]) == "three"

    def test_py_dict_append_in_php(self, php_space):

        output = self.run('''
            $src = <<<EOD
            def f(): return { "x" : "one", "y" : "two", "z" : "three" }
            EOD;

            $f = compile_py_func($src);
            $ar = $f();

            $ar[] = "bumble"; # ?!?!
                    ''')
        # XXX assert

    def test_array_type_over_php_py_boundary(self, php_space):
        output = self.run('''
            $src = "def f(a): return type(a) == dict";
            $f = compile_py_func($src);

            $in = array("my", "array", 2, 3);

            echo($f($in));
        ''')
        assert php_space.is_true(output[0])

    def test_array_type_over_php_py_boundary2(self, php_space):
        output = self.run('''
            $src = "def f(a): return type(a.as_list()) == list";
            $f = compile_py_func($src);

            $in = array(1, 2, 4, 8, 16);

            echo($f($in));
        ''')
        assert php_space.is_true(output[0])

    def test_cannot_apply_as_list_to_wrapped_mixed_key_php_array(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(a):
                try:
                    a.as_list() # boom
                except BridgeError as e:
                    return e.message
                else:
                    return "fail"
            EOD;

            $f = compile_py_func($src);
            $in = array("a" => 1); // mixed keys
            echo($f($in));
        ''')

        e_str = "can only apply as_list() to a wrapped PHP array in dict form"
        assert php_space.str_w(output[0]) == e_str

    def test_as_list_invalidates(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(arry_d):
                arry_l = arry_d.as_list()
                arry_d["x"] = 890 #non-integer keyed
                try:
                    arry_l[0] # stale!
                except BridgeError as e:
                    return e.message
                return "fail"
            EOD;

            $f = compile_py_func($src);
            $in = array(1, 2, 3); // int keys
            echo($f($in));
        ''')
        assert php_space.str_w(output[0]) == \
                "Stale wrapped PHP array. No longer integer keyed!"

    # XXX We need a load more invalidation tests.
    # One for every operation that could cause a WListArrayObject to become
    # a WRDictArrayObject.

    def test_php_empty_array_len_in_python(self, php_space):
        output = self.run('''
            $src = "def f(a): return len(a)";
            $f = compile_py_func($src);
            $in = array();
            echo($f($in));
        ''')
        assert php_space.int_w(output[0]) == 0

    def test_php_int_key_array_len_in_python(self, php_space):
        output = self.run('''
            $src = "def f(a): return len(a.as_list())";
            $f = compile_py_func($src);
            $in = array("an", "intkeyed", "array");
            echo($f($in));
        ''')
        assert php_space.int_w(output[0]) == 3

    def test_php_mixed_key_array_len_in_python(self, php_space):
        output = self.run('''
            $src = "def f(ary): return len(ary)";
            $f = compile_py_func($src);
            $in = array("a" => 1, "b" => "mixed-key", "c" => "array");
            echo($f($in));
        ''')
        assert php_space.int_w(output[0]) == 3

    def test_php_int_key_array_vals_in_python(self, php_space):
        output = self.run('''
            $src = "def f(ary, idx): return ary[idx]";
            $f = compile_py_func($src);
            $in = array("an", "intkeyed", "array");

            echo($f($in, 0));
            echo($f($in, 1));
            echo($f($in, 2));
        ''')
        assert php_space.str_w(output[0]) == "an"
        assert php_space.str_w(output[1]) == "intkeyed"
        assert php_space.str_w(output[2]) == "array"

    def test_php_int_key_array_vals_in_python_as_list(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(ary, idx):
                ls = ary.as_list()
                return ls[idx]
            EOD;

            $f = compile_py_func($src);
            $in = array("an", "intkeyed", "array");

            echo($f($in, 0));
            echo($f($in, 1));
            echo($f($in, 2));
        ''')
        assert php_space.str_w(output[0]) == "an"
        assert php_space.str_w(output[1]) == "intkeyed"
        assert php_space.str_w(output[2]) == "array"

    def test_php_int_key_array_len_in_python_as_list(self, php_space):
        output = self.run('''
            $src = "def f(ary): return len(ary.as_list())";
            $f = compile_py_func($src);
            $in = array("an", "intkeyed", "array");
            echo($f($in));
        ''')
        assert php_space.int_w(output[0]) == 3

    def test_php_mixed_key_array_vals_in_python(self, php_space):
        output = self.run('''
            $src = "def f(ary, idx): return ary[idx]";
            $f = compile_py_func($src);
            $in = array("a" => 1, "b" => 22, "c" => 333);

            echo($f($in, "a"));
            echo($f($in, "b"));
            echo($f($in, "c"));
        ''')
        assert php_space.int_w(output[0]) == 1
        assert php_space.int_w(output[1]) == 22
        assert php_space.int_w(output[2]) == 333

    def test_php_mixed_key_array_iteritems_in_python(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ret = []
                for x, y in ary.iteritems():
                    ret += ["%s,%s" % (x, y)]
                return "|".join(ret)
            EOD;

            $f = compile_py_func($src);
            $in = array("a" => 1, "b" => 22, "c" => 333);
            echo($f($in));
        ''')
        assert php_space.str_w(output[0]) == "a,1|b,22|c,333"

    def test_php_mixed_key_array_iterkeys_in_python(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ret = [ x for x in ary.iterkeys() ]
                return "|".join(ret)
            EOD;

            $f = compile_py_func($src);
            $in = array("a" => 1, "b" => 22, "c" => 333);
            echo($f($in));
        ''')
        assert php_space.str_w(output[0]) == "a|b|c"

    def test_php_mixed_key_array_itervalues_in_python(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ret = [ str(x) for x in ary.itervalues() ]
                return "|".join(ret)
            EOD;

            $f = compile_py_func($src);
            $in = array("a" => 1, "b" => 22, "c" => 333);
            echo($f($in));
        ''')
        assert php_space.str_w(output[0]) == "1|22|333"

    def test_php_int_key_array_iteritems_in_python(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ret = []
                for x, y in ary.iteritems():
                    ret += ["%s,%s" % (x, y)]
                return "|".join(ret)
            EOD;

            $f = compile_py_func($src);
            $in = array(2, 1, 0);
            echo($f($in));
        ''')
        assert php_space.str_w(output[0]) == "0,2|1,1|2,0"

    def test_php_int_key_array_iterkeys_in_python(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ret = [ str(x) for x in ary.iterkeys() ]
                return "|".join(ret)
            EOD;

            $f = compile_py_func($src);
            $in = array("a", "b", "c");
            echo($f($in));
        ''')
        assert php_space.str_w(output[0]) == "0|1|2"

    def test_php_int_key_array_itervalues_in_python(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ret = [ x for x in ary.itervalues() ]
                return "|".join(ret)
            EOD;

            $f = compile_py_func($src);
            $in = array("x", "y", "z");
            echo($f($in));
        ''')
        assert php_space.str_w(output[0]) == "x|y|z"

    def test_php_mixed_key_array_setitem_in_python_ret(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ary["x"] = "y"
                return ary
            EOD;

            $f= compile_py_func($src);
            $in = array("x", "y", "z");
            $out = $f($in);
            echo $out["x"];
        ''')
        assert php_space.str_w(output[0]) == "y"

    def test_php_int_key_array_setitem_in_python_ret(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ary_l = ary.as_list()
                ary_l[3] = "a"
                return ary_l
            EOD;

            $f = compile_py_func($src);
            $in = array("x", "y", "z");
            $out = $f($in);
            echo $out[3];
        ''')
        assert php_space.str_w(output[0]) == "a"

    def test_dict_like_py_list_works(self, php_space):
        output = self.run('''
            function f_id($x) { return $x; }

            $src = <<<EOD
            def f():
                r = f_id([1, 2, 3])
                if type(r) == dict:
                    return True
                else:
                    return False
            EOD;

            $f = compile_py_func($src);
            echo($f());
        ''')
        assert php_space.is_true(output[0])

    def test_dict_like_py_list_getitem(self, php_space):
        output = self.run('''
            function f_id($x) { return $x; }

            $src = <<<EOD
            def f():
                r = f_id([1, 2, 3])
                for i in range(3):
                    assert r[i] == i + 1
            EOD;

            $f = compile_py_func($src);
            $f();
        ''')
        # will fail if py assert raises

    def test_dict_like_py_list_setitem(self, php_space):
        output = self.run('''
            function f_id($x) { return $x; }

            $src = <<<EOD
            def f():
                r = f_id([1, 2, 3])
                r[0] = 666
                assert r[0] == 666
            EOD;

            $f = compile_py_func($src);
            $f();
        ''')
        # will fail if py assert raises

    def test_dict_like_py_list_length(self, php_space):
        output = self.run('''
            function f_id($x) { return $x; }

            $src = <<<EOD
            def f():
                r = f_id([1, 2, 3])
                return len(r)
            EOD;

            $f = compile_py_func($src);
            echo($f());
        ''')
        assert php_space.int_w(output[0]) == 3

    def test_dict_like_py_list_iterkeys(self, php_space):
        output = self.run('''
            function f_id($x) { return $x; }

            $src = <<<EOD
            def f():
                r = f_id([1, 2, 3])
                return list(r.iterkeys())
            EOD;

            $f = compile_py_func($src);
            $a = $f();
            echo $a[0];
            echo $a[1];
            echo $a[2];
        ''')
        assert php_space.int_w(output[0]) == 0
        assert php_space.int_w(output[1]) == 1
        assert php_space.int_w(output[2]) == 2

    def test_dict_like_py_list_itervalues(self, php_space):
        output = self.run('''
            function f_id($x) { return $x; }

            $src = <<<EOD
            def f():
                r = f_id([6, 77, 888])
                return list(r.itervalues())
            EOD;

            $f = compile_py_func($src);
            $a = $f();
            echo $a[0];
            echo $a[1];
            echo $a[2];
        ''')
        assert php_space.int_w(output[0]) == 6
        assert php_space.int_w(output[1]) == 77
        assert php_space.int_w(output[2]) == 888

    def test_dict_like_py_list_iteritems(self, php_space):
        output = self.run('''
            function f_id($x) { return $x; }

            $src = <<<EOD
            def f():
                r = f_id(["a", "b", "c"])
                return [ "%s%s" % (k, v) for k, v in r.iteritems() ]
            EOD;

            $f = compile_py_func($src);
            $a = $f();
            echo $a[0];
            echo $a[1];
            echo $a[2];
        ''')
        assert php_space.str_w(output[0]) == "0a"
        assert php_space.str_w(output[1]) == "1b"
        assert php_space.str_w(output[2]) == "2c"

    def test_dict_like_py_list_as_list(self, php_space):
        output = self.run('''
            function f_id($x) { return $x; }

            $src = <<<EOD
            def f():
                r = f_id([1, 2, 3])
                r_l = r.as_list()
                assert type(r_l) == list
                return r_l
            EOD;

            $f = compile_py_func($src);
            $lst = $f();
            for ($i = 0; $i < 3; $i++) {
                echo $lst[$i];
            }
        ''')
        for i in range(3):
            assert php_space.int_w(output[i]) == i + 1

    def test_php_array_as_list_val_iterator_in_py(self, php_space):
        output = self.run('''
            $a = array("a", "b", "c");

            $src = <<<EOD
            def f():
                it = iter(a.as_list())
                consume = [it.next() for x in range(3)]
                print(72 * "-")
                print(consume)
                assert consume == ["a", "b", "c"]

                try:
                    x = it.next()
                    print(x)
                    return "fail"
                except StopIteration:
                    return "ok"
            EOD;
            $f = compile_py_func($src);
            echo($f());
        ''')
        assert php_space.str_w(output[0]) == "ok"

    def test_php_array_as_list_val_iterator_in_py2(self, php_space):
        output = self.run('''
            $a = array("a", "b", "c");

            $src = <<<EOD
            def f():
                s = []
                for i in a.as_list():
                    s.append(i)
                return "".join(s)
            EOD;
            $f = compile_py_func($src);
            echo($f());
        ''')
        assert php_space.str_w(output[0]) == "abc"

    def test_str_of_py_list_passed_to_php_and_back(self, php_space):
        output = self.run('''
            $mk = compile_py_func("def mk(): return [1,2,3]");
            $str_ary = compile_py_func("def str_ary(a): return str(a)");

            $x = $mk();
            $s = $str_ary($x);
            echo($s);
        ''')
        assert php_space.str_w(output[0]) == "{0: 1, 1: 2, 2: 3}"

    def test_setdefault_on_wrapped_php_array(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def sd(ary, key, default):
                return ary.setdefault(key, default)
            EOD;
            $sd = compile_py_func($src);

            $ary = array("x" => "y");
            echo $sd($ary, "x", "k");
            echo $sd($ary, "y", "k");
        ''')
        assert php_space.str_w(output[0]) == "y"
        assert php_space.str_w(output[1]) == "k"

    def test_appenditem_on_wrapped_py_dict(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def createarray():
                return {0: "a", 1: "b", 32: "c", 3: "d"}
            EOD;
            $ca = compile_py_func($src);

            $ary = $ca();
            $ary[] = "item";
            echo $ary[33];
            $ary[] = "item2";
            echo $ary[34];
            $ary[40] = "item3";
            echo $ary[40];
            $ary[] = "item4";
            echo $ary[41];
        ''')
        assert php_space.str_w(output[0]) == "item"
        assert php_space.str_w(output[1]) == "item2"
        assert php_space.str_w(output[2]) == "item3"
        assert php_space.str_w(output[3]) == "item4"

    def test_arraypop_on_py_dict(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def createarray():
                return {1: "a", 2: "b"}
            EOD;
            $ca = compile_py_func($src);

            $ary = $ca();
            try {
                array_pop($ary);
            }
            catch (BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        assert php_space.str_w(output[0]) == "array_pop is invalid for wrapped Python dict"

    def test_arraypop_on_py_list(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def createlist():
                return [1,2,3]
            EOD;
            $ca = compile_py_func($src);

            $ary = $ca();
            $ary[] = "c";
            $ary[] = "d";
            $result = array_pop($ary);
            echo $result;
            $result = array_pop($ary);
            echo $result;
            $result = array_pop($ary);
            echo $result;
        ''')
        assert php_space.str_w(output[0]) == "d"
        assert php_space.str_w(output[1]) == "c"
        assert php_space.str_w(output[2]) == "3"

    def test_end_on_py_dict(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def createdict():
                return {1: "a", 2: "b"}
            EOD;
            $ca = compile_py_func($src);
            $ary = $ca();

            try {
                end($ary);
            }
            catch (BridgeException $e) {
                echo $e->getMessage();
            }
        ''')
        assert php_space.str_w(output[0]) == "PHP iteration is invalid for wrapped Python dict"

    def test_end_on_py_list(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def createlist():
                return [1,2,3]
            EOD;
            $ca = compile_py_func($src);
            $ary = $ca();

            echo end($ary);
            $ary[] = "c";
            echo end($ary);
            $ary[] = "d";
            echo end($ary);
        ''')
        assert php_space.str_w(output[0]) == "3"
        assert php_space.str_w(output[1]) == "c"
        assert php_space.str_w(output[2]) == "d"

    def test_end_on_empty_py_list(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def createlist():
                return []
            EOD;
            $ca = compile_py_func($src);
            $ary = $ca();

            echo end($ary);
        ''')
        assert output[0] is php_space.w_False

    def test_compare_two_python_lists(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def createlist():
                return []
            EOD;
            $ca = compile_py_func($src);
            $a1 = $ca();
            $a1[] = 100;
            $a2 = $ca();
            $a2[] = 2;

            if($a1 == $a2){
                echo "equal";
            }
            else{
                echo "unequal";
            }

        ''')
        assert php_space.str_w(output[0]) == "unequal"

    def test_compare_two_python_lists_str(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def createlist():
                return []
            EOD;
            $ca = compile_py_func($src);
            $a1 = $ca();
            $a1[] = 100;
            $a2 = $ca();
            $a2[] = 100;

            if(isset($a["hello"])){
                echo "foo";
            }
            else{
                echo "bar";
            }
        ''')
        assert php_space.str_w(output[0]) == "bar"

    def test_compare_two_python_dicts(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def createlist():
                return {}
            EOD;
            $ca = compile_py_func($src);
            $a1 = $ca();
            $a1["foo"] = 100;
            $a2 = $ca();
            $a2["bar"] = 100;

            if($a1 == $a2){
                echo "equal";
            }
            else{
                echo "unequal";
            }
        ''')
        assert php_space.str_w(output[0]) == "unequal"

    def test_compare_two_python_dicts_ints(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def createlist():
                return {}
            EOD;
            $ca = compile_py_func($src);
            $a1 = $ca();
            $a1[1] = 100;
            $a2 = $ca();
            $a2[2] = 100;

            if($a1 == $a2){
                echo "equal";
            }
            else{
                echo "unequal";
            }
        ''')
        assert php_space.str_w(output[0]) == "unequal"

    @pytest.mark.xfail
    def test_mutible_plus_eq_on_wrapped_php_array_in_python(self, php_space):
        self.run('''
        $src = <<<EOD
        def ext(x, y):
            xl, yl = x.as_list(), y.as_list()
            xl += yl
            return xl
        EOD;
        $ext = compile_py_func($src);

        $a = array("1");
        $b = array("2");
        $new = $ext($a, $b);

        foreach ($new as $x) {
                echo $x;
        }
        ''')
        assert php_space.int_w(output[0]) == 1
        assert php_space.int_w(output[1]) == 2

class TestPyPyBridgeArrayConversionsInstances(BaseTestInterpreter):

    def test_python_array_in_php_instance(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def A_construct(self, v):
                self.v = v + 1
            EOD;
            $A_construct = compile_py_func($src);

            class A {
                function __construct($v) {
                    global $A_construct;
                    $A_construct($this, $v);
                }
            }

            $a = new A(665);
            echo($a->v);
        ''')
        assert php_space.int_w(output[0]) == 666

    def test_as_list_and_mutate(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ary_l = ary.as_list()
                ary_l[3] = "a"
                return ary == ary_l
            EOD;

            $f = compile_py_func($src);
            $in = array("x", "y", "z");
            $rv = $f($in);
            echo $rv;
        ''')
        assert not php_space.is_true(output[0])

    def test_php_array_consts_are_not_mutated_by_python(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f(ary):
                ary[3] = 666;
            EOD;

            $f = compile_py_func($src);
            $in = array(0, 1, 2);
            $f($in);
            echo $in[3];
            $in = array(0, 1, 2); # should not contain new element
            echo count($in);
        ''')
        assert php_space.int_w(output[0]) == 666
        assert php_space.int_w(output[1]) == 3

    def test_list_in_php_attr_field_append(self, php_space):
        output = self.run('''
        class A {
            public $elms;

            function __construct() {
                $this->elms = array();
            }
        }

        $src = <<<EOD
def add(self, elm):
    elms_l = self.elms.as_list()
    elms_l.append(elm)
EOD;
        compile_py_meth("A", $src);

        $a = new A();
        echo count($a->elms);

        $a->add("one");
        echo count($a->elms);
        echo $a->elms[0];

        $a->add("two");
        echo count($a->elms);
        echo $a->elms[1];
        ''')
        assert php_space.int_w(output[0]) == 0

        assert php_space.int_w(output[1]) == 1
        assert php_space.str_w(output[2]) == "one"

        assert php_space.int_w(output[3]) == 2
        assert php_space.str_w(output[4]) == "two"

    def test_list_in_php_attr_field_setattr(self, php_space):
        output = self.run('''
        class A {
            public $elms;

            function __construct() {
                $this->elms = array();
            }

        }

        $src = <<<EOD
def add(self, idx, elm):
    elms_l = self.elms.as_list()
    elms_l[idx] = elm
EOD;
        compile_py_meth("A", $src);

        $a = new A();
        echo count($a->elms);

        $a->add(0, "one");
        echo count($a->elms);
        echo $a->elms[0];

        $a->add(1, "two");
        echo count($a->elms);
        echo $a->elms[1];
        ''')
        assert php_space.int_w(output[0]) == 0

        assert php_space.int_w(output[1]) == 1
        assert php_space.str_w(output[2]) == "one"

        assert php_space.int_w(output[3]) == 2
        assert php_space.str_w(output[4]) == "two"

    def test_array_attr_set_from_py(self, php_space):
        output = self.run('''
        class A {
            public $elms;

            function __construct() {
                $this->elms = array(1, 2, 3);
            }

        }

        $src = "def addidx(inst, idx, elm): inst.elms[idx] = elm";
        compile_py_func_global($src);

        $a = new A();
        addidx($a, "here", "value");
        echo $a->elms["here"];
        ''')
        assert php_space.str_w(output[0]) == "value"

# XXX no need for most of these to be interp-level
class TestPyPyBridgeArrayConversionsInterp(BaseTestInterpreter):

    @pytest.fixture
    def interp(self):
        return self.engine.new_interp(None, None)

    def test_py_list_of_ph_array(self, interp):
        php_space, py_space = interp.space, interp.py_space

        input = [1, 2, 3, "a", "b", "c" ]
        w_php_elems = [ php_space.wrap(i) for i in input ]
        w_php_arr = php_space.new_array_from_list(w_php_elems)
        w_py_converted = w_php_arr.to_py(interp).descr_as_list(interp)

        w_py_expect = py_space.newlist([ py_space.wrap(i) for i in input ])
        assert py_space.is_true(py_space.eq(w_py_converted, w_py_expect))

    def test_py_list_of_ph_array_nested(self, interp):
        php_space, py_space = interp.space, interp.py_space

        # We will build a PHP list looking like this:
        # [ 666, False, [ 1, "a" ]]

        # inner list
        input_inner = [1, "a"]
        w_php_elems_inner = [ php_space.wrap(i) for i in input_inner ]
        w_php_arr_inner = php_space.new_array_from_list(w_php_elems_inner)

        # outer list
        input_outer = [666, False]
        w_php_elems_outer = [ php_space.wrap(i) for i in input_outer ]
        w_php_arr_outer = php_space.new_array_from_list(w_php_elems_outer)
        w_php_arr_outer.appenditem_inplace(php_space, w_php_arr_inner)

        w_py_l = w_php_arr_outer.to_py(interp)

        consts = [ py_space.wrap(i) for i in range(3) ]

        assert py_space.int_w(py_space.len(w_py_l)) == 3
        assert py_space.int_w(py_space.getitem(w_py_l, consts[0])) == 666
        assert py_space.bool_w(py_space.getitem(w_py_l, consts[1])) == False

        w_py_innr = py_space.getitem(w_py_l, consts[2])
        assert py_space.int_w(py_space.getitem(w_py_innr, consts[0])) == 1
        assert py_space.str_w(py_space.getitem(w_py_innr, consts[1])) == "a"

    def test_ph_array_of_py_list(self, interp):
        php_space, py_space = interp.space, interp.py_space

        input = [1, 2, "wibble", "chunks", True]
        w_php_expect = php_space.new_array_from_list(
                [ php_space.wrap(x) for x in input ])

        w_py_list = py_space.newlist([ py_space.wrap(x) for x in input ])
        w_php_actual = w_py_list.to_php(interp)

        assert php_space.is_true(php_space.eq(w_php_actual, w_php_expect))

    def test_pop_on_php_array_strategy(self, php_space):
        output = self.run('''
        $src = "def f(a): return a.as_list().pop()";
        compile_py_func_global($src);

        echo f(array(8, 3, 2));
        ''')
        assert php_space.int_w(output[0]) == 2

    def test_pop_on_php_array_strategy2(self, php_space):
        output = self.run('''
        $src = "def f(a): return a.pop('a')";
        compile_py_func_global($src);

        echo f(array("a" => "zzz", 0 => 666));
        ''')
        assert php_space.str_w(output[0]) == "zzz"

    def test_binary_add_on_php_array_in_python001(self, php_space):
        output = self.run('''
        $src = "def f(a): return a.as_list() + ['hi']";
        compile_py_func_global($src);

        $a = [56, 57];
        $b = f($a);

        echo count($a);
        echo count($b);
        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 2)
        sa.asrt(int, 3)
        sa.asrt(int, 56)
        sa.asrt(int, 57)
        sa.asrt(str, "hi")

    def test_binary_add_on_php_array_in_python002(self, php_space):
        output = self.run('''
        $src = "def f(a, b): return a.as_list() + b.as_list()";
        compile_py_func_global($src);

        $a1 = [56, 57];
        $a2 = ["g", "l"];
        $b = f($a1, $a2);

        echo count($a1);
        echo count($a2);
        echo count($b);
        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 2)
        sa.asrt(int, 2)
        sa.asrt(int, 4)
        sa.asrt(int, 56)
        sa.asrt(int, 57)
        sa.asrt(str, "g")
        sa.asrt(str, "l")

    def test_binary_add_on_php_array_in_python003(self, php_space):
        output = self.run('''
        $src = "def f(a): return ['hi'] + a.as_list()";
        compile_py_func_global($src);

        $a = [56, 57];
        $b = f($a);

        echo count($a);
        echo count($b);
        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 2)
        sa.asrt(int, 3)
        sa.asrt(str, "hi")
        sa.asrt(int, 56)
        sa.asrt(int, 57)

    def test_binary_sub_on_php_array_in_python001(self, php_space):
        output = self.run('''
        $src = "def f(a): return a.as_list() - ['hi']";
        compile_py_func_global($src);

        $a = [56, 57];

        try {
            $b = f($a);
            echo "fail";
        } catch (PyException $e) {
            echo $e->getMessage();
        }
        ''')
        err_s = "TypeError: unsupported operand type(s) for -: 'list' and 'list'"
        assert php_space.str_w(output[0]) == err_s

    def test_binary_sub_on_php_array_in_python002(self, php_space):
        output = self.run('''
        $src = "def f(a, b): return a.as_list() - b.as_list()";
        compile_py_func_global($src);

        $a1 = [56, 57];
        $a2 = ["g", "l"];
        try {
            $b = f($a1, $a2);
            echo "fail";
        } catch (PyException $e) {
            echo $e->getMessage();
        }
        ''')
        err_s = "TypeError: unsupported operand type(s) for -: 'list' and 'list'"
        assert php_space.str_w(output[0]) == err_s

    def test_binary_div_on_php_array_in_python001(self, php_space):
        output = self.run('''
        $src = "def f(a): return a.as_list() / ['hi']";
        compile_py_func_global($src);

        $a = [56, 57];

        try {
            $b = f($a);
            echo "fail";
        } catch (PyException $e) {
            echo $e->getMessage();
        }
        ''')
        err_s = "TypeError: unsupported operand type(s) for div: 'list' and 'list'"
        assert php_space.str_w(output[0]) == err_s

    def test_binary_div_on_php_array_in_python002(self, php_space):
        output = self.run('''
        $src = "def f(a, b): return a.as_list() / b.as_list()";
        compile_py_func_global($src);

        $a1 = [56, 57];
        $a2 = ["g", "l"];
        try {
            $b = f($a1, $a2);
            echo "fail";
        } catch (PyException $e) {
            echo $e->getMessage();
        }
        ''')
        err_s = "TypeError: unsupported operand type(s) for div: 'list' and 'list'"
        assert php_space.str_w(output[0]) == err_s

    def test_binary_mul_on_php_array_in_python001(self, php_space):
        output = self.run('''
        $src = "def f(a): return a.as_list() * ['hi']";
        compile_py_func_global($src);

        $a = [56, 57];

        try {
            $b = f($a);
            echo "fail";
        } catch (PyException $e) {
            echo $e->getMessage();
        }
        ''')
        err_s = "TypeError: unsupported operand type(s) for *: 'list' and 'list'"
        assert php_space.str_w(output[0]) == err_s

    def test_binary_mul_on_php_array_in_python002(self, php_space):
        output = self.run('''
        $src = "def f(a, b): return a.as_list() * b.as_list()";
        compile_py_func_global($src);

        $a1 = [56, 57];
        $a2 = ["g", "l"];
        try {
            $b = f($a1, $a2);
            echo "fail";
        } catch (PyException $e) {
            echo $e->getMessage();
        }
        ''')
        err_s = "TypeError: unsupported operand type(s) for *: 'list' and 'list'"
        assert php_space.str_w(output[0]) == err_s

    def test_binary_mul_on_php_array_in_python003(self, php_space):
        output = self.run('''
        $src = "def f(a): return a.as_list() * 3";
        compile_py_func_global($src);

        $a = [1, 2];
        $b = f($a);

        echo count($a);
        echo count($b);
        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 2)
        sa.asrt(int, 6)

        for i in xrange(3):
            sa.asrt(int, 1)
            sa.asrt(int, 2)

    def test_binary_mul_on_php_array_in_python004(self, php_space):
        output = self.run('''
        $src = "def f(a): return 3 * a.as_list()";
        compile_py_func_global($src);

        $a = [1, 2];
        $b = f($a);

        echo count($a);
        echo count($b);
        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 2)
        sa.asrt(int, 6)

        for i in xrange(3):
            sa.asrt(int, 1)
            sa.asrt(int, 2)

    def test_py_extend_on_php_array_in_python001(self, php_space):
        output = self.run('''
        $src = <<<EOD
        def f(a):
            a.as_list().extend(['x', 'y', 'z'])
            return a
        EOD;
        compile_py_func_global($src);

        $a = [1, 2];
        $b = f($a);

        echo count($a);
        echo count($b);

        // both lists should mutate
        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }

        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 5)
        sa.asrt(int, 5)

        for i in xrange(2):
            sa.asrt(int, 1)
            sa.asrt(int, 2)
            sa.asrt(str, "x")
            sa.asrt(str, "y")
            sa.asrt(str, "z")

    def test_inplace_add_on_php_array_in_python001(self, php_space):
        output = self.run('''
        $src = <<<EOD
        def f(a):
            l = a.as_list()
            l += ['x', 'y', 'z']
            return l
        EOD;
        compile_py_func_global($src);

        $a = [1, 2];
        $b = f($a);

        echo count($a);
        echo count($b);

        // both lists should mutate
        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }

        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 5)
        sa.asrt(int, 5)

        for i in xrange(2):
            sa.asrt(int, 1)
            sa.asrt(int, 2)
            sa.asrt(str, "x")
            sa.asrt(str, "y")
            sa.asrt(str, "z")

    def test_inplace_mul_on_php_array_in_python001(self, php_space):
        output = self.run('''
        $src = <<<EOD
        def f(a):
            l = a.as_list()
            l *= 3
            return l
        EOD;
        compile_py_func_global($src);

        $a = [1, 2];
        $b = f($a);

        echo count($a);
        echo count($b);

        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }

        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 6)
        sa.asrt(int, 6)

        for i in xrange(2):
            for j in xrange(3):
                sa.asrt(int, 1)
                sa.asrt(int, 2)

    def test_inplace_mul_on_php_array_in_python002(self, php_space):
        output = self.run('''
        $src = <<<EOD
        def f(a):
            l = a.as_list()
            l *= 1
            return l
        EOD;
        compile_py_func_global($src);

        $a = [1, 2];
        $b = f($a);

        echo count($a);
        echo count($b);

        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }

        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 2)
        sa.asrt(int, 2)

        for i in xrange(2):
            sa.asrt(int, 1)
            sa.asrt(int, 2)

    def test_inplace_mul_on_php_array_in_python003(self, php_space):
        output = self.run('''
        $src = <<<EOD
        def f(a):
            l = a.as_list()
            l *= 0
            return l
        EOD;
        compile_py_func_global($src);

        $a = [1, 2];
        $b = f($a);

        echo count($a);
        echo count($b);
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 0)
        sa.asrt(int, 0)

    def test_inplace_mul_on_php_array_in_python004(self, php_space):
        output = self.run('''
        $src = <<<EOD
        def f(a):
            l = a.as_list()
            l *= - 666
            return l
        EOD;
        compile_py_func_global($src);

        $a = [1, 2];
        $b = f($a);

        echo count($a);
        echo count($b);
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 0)
        sa.asrt(int, 0)

    def test_mutate_elsewhere_refd_php_array_in_python001(self, php_space):
        output = self.run('''

        class A {
                public $v;
                function __construct($v) {
                    // $v has been passed by value, so $this->v should
                    // be immune from any mutations outside.
                    $this->v = $v;
                }
        }

        $src = <<<EOD
        def f(a):
            a.as_list()[0] = 777
        EOD;
        compile_py_func_global($src);

        $ar = [666];
        $a = new A($ar);

        f($ar);

        echo $a->v[0];
        echo $ar[0];
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 666)
        sa.asrt(int, 777)

    def test_mutate_elsewhere_refd_php_array_in_python002(self, php_space):
        output = self.run('''

        class A {
                public $v;
                function __construct($v) {
                    // $v has been passed by value, so $this->v should
                    // be immune from any mutations outside.
                    $this->v = $v;
                }
        }

        $src = <<<EOD
        def f(a):
            a.as_list().extend([777])
        EOD;
        compile_py_func_global($src);

        $ar = [666];
        $a = new A($ar);

        f($ar);

        echo count($a->v);
        echo count($ar);
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 1)
        sa.asrt(int, 2)

    def test_mutate_elsewhere_refd_php_array_in_python003(self, php_space):
        output = self.run('''

        class A {
                public $v;
                function __construct($v) {
                    // $v has been passed by value, so $this->v should
                    // be immune from any mutations outside.
                    $this->v = $v;
                }
        }

        $src = <<<EOD
        def f(a):
            l = a.as_list()
            l *= 3
        EOD;
        compile_py_func_global($src);

        $ar = ["ping", "pong"];
        $a = new A($ar);

        f($ar);

        echo count($a->v);
        echo count($ar);
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 2)
        sa.asrt(int, 6)

    def test_mutate_elsewhere_refd_php_array_in_python004(self, php_space):
        output = self.run('''

        class A {
                public $v;
                function __construct($v) {
                    // $v has been passed by value, so $this->v should
                    // be immune from any mutations outside.
                    $this->v = $v;
                }
        }

        $src = <<<EOD
        def f(a):
            l = a.as_list()
            l *= 3
        EOD;
        compile_py_func_global($src);

        $ar = ["ping", "pong"];
        $a = new A($ar);

        f($ar);

        echo count($a->v);
        echo count($ar);
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 2)
        sa.asrt(int, 6)

    def test_mutate_elsewhere_refd_php_array_in_python005(self, php_space):
        output = self.run('''

        class A {
                public $v;
                function __construct($v) {
                    // $v has been passed by value, so $this->v should
                    // be immune from any mutations outside.
                    $this->v = $v;
                }
        }

        $src = <<<EOD
        def f(a):
            l = a.as_list()
            l += [3]
        EOD;
        compile_py_func_global($src);

        $ar = ["ping", "pong"];
        $a = new A($ar);

        f($ar);

        echo count($a->v);
        echo count($ar);
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 2)
        sa.asrt(int, 3)

    def test_mutate_elsewhere_refd_php_array_in_python006(self, php_space):
        output = self.run('''

        class A {
                public $v;
                function __construct(&$v) {
                    $this->v = &$v; // passed and assigned by ref, should mutate
                }
        }

        $src = <<<EOD
        def f(a):
            l = a.as_list()
            l += [3]
        EOD;
        compile_py_func_global($src);

        $ar = ["ping", "pong"];
        $a = new A($ar);

        f($ar);

        echo count($a->v);
        echo count($ar);
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 3)
        sa.asrt(int, 3)

    def test_pop_on_php_array_strategy2(self, php_space):
        output = self.run('''
        $src = "def f(a): return a.pop('a')";
        compile_py_func_global($src);

        echo f(array("a" => "zzz", 0 => 666));
        ''')
        assert php_space.str_w(output[0]) == "zzz"

    def test_py_update_on_adapted_php_array001(self, php_space):
        output = self.run('''
        $src = "def f(a): a.update({2:3})";
        compile_py_func_global($src);

        $a = [1 => 2];
        f($a);
        echo count($a);
        echo $a[1];
        echo $a[2];
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 2);

        sa.asrt(int, 2);
        sa.asrt(int, 3);

    def test_py_update_on_adapted_php_array002(self, php_space):
        output = self.run('''
        $src = "def f(a): a.update({'a': 'wibble'})";
        compile_py_func_global($src);

        $a = [1 => 2];
        f($a);
        echo count($a);
        echo $a[1];
        echo $a["a"];
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 2)

        sa.asrt(int, 2)
        sa.asrt(str, "wibble")

    def test_py_update_on_adapted_php_array003(self, php_space):
        output = self.run('''
        $src = "def f(a): a.update({'b': 'wibble'})";
        compile_py_func_global($src);

        $a = ["a" => "b", "b" => "c"];
        f($a);
        echo count($a);
        echo $a["a"];
        echo $a["b"];
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 2)

        sa.asrt(str, "b")
        sa.asrt(str, "wibble")

    def test_py_in_php_array001(self, php_space):
        output = self.run('''
        $src = "def f(a): return 'a' in a";
        compile_py_func_global($src);

        $a = ["a" => "b", "b" => "c"];
        echo f($a);
        ''')
        assert php_space.is_true(output[0])

    def test_py_keys_php_array001(self, php_space):
        output = self.run('''
        $src = "def f(a): return a.keys()";
        compile_py_func_global($src);

        $a = ["a" => "b", "b" => "c"];
        $ks =  f($a);

        echo count($ks);
        echo $ks[0];
        echo $ks[1];
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 2)

        sa.asrt(str, "a")
        sa.asrt(str, "b")

    def test_py_vals_php_array001(self, php_space):
        output = self.run('''
        $src = "def f(a): return a.values()";
        compile_py_func_global($src);

        $a = ["a" => "b", "b" => "c"];
        $vs =  f($a);

        echo count($vs);
        echo $vs[0];
        echo $vs[1];
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 2)

        sa.asrt(str, "b")
        sa.asrt(str, "c")

    def test_py_binary_add_php_mixed_array001(self, php_space):
        output = self.run('''
        $src = "def f(a): a + {}";
        compile_py_func_global($src);

        $a = ["a" => "b", "b" => "c"];
        try {
            f($a);
            echo "fail";
        } catch (PyException $e) {
            echo $e-> getMessage();
        }

        ''')
        err_s = "TypeError: unsupported operand type(s) for +: 'dict' and 'dict'"
        assert php_space.str_w(output[0]) == err_s

    def test_py_binary_add_php_mixed_array002(self, php_space):
        output = self.run('''
        $src = "def f(a, b): a + {}";
        compile_py_func_global($src);

        $a = ["a" => "b", "b" => "c"];
        $b = ["a" => "b", "x" => "R"];
        try {
            f($a, $b);
            echo "fail";
        } catch (PyException $e) {
            echo $e-> getMessage();
        }

        ''')
        err_s = "TypeError: unsupported operand type(s) for +: 'dict' and 'dict'"
        assert php_space.str_w(output[0]) == err_s

    def test_py_inplace_add_php_mixed_array001(self, php_space):
        output = self.run('''
        $src = "def f(a): a += {}";
        compile_py_func_global($src);

        $a = ["a" => "b", "b" => "c"];
        try {
            f($a);
            echo "fail";
        } catch (PyException $e) {
            echo $e-> getMessage();
        }

        ''')
        err_s = "TypeError: unsupported operand type(s) for +: 'dict' and 'dict'"
        assert php_space.str_w(output[0]) == err_s

    def test_py_del_php_mixed_array001(self, php_space):
        output = self.run('''
        $src = "def f(a): del(a['a'])";
        compile_py_func_global($src);

        $a = ["a" => "d", "k" => "l"];
        f($a);
        echo count($a);
        echo $a["k"];
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 1)
        sa.asrt(str, "l")

    @pytest.mark.xfail
    def test_py_del_php_mixed_array002(self, php_space):
        output = self.run('''
        $src = "def f(a): del(a['a'])";
        compile_py_func_global($src);

        $a = [];
        try {
            f($a);
            echo "fail";
        } catch (PyException $e) {
            echo $e->getMessage();
        }
        ''')
        err_s = "KeyError: 'a'"
        assert php_space.str_w(output[0]) == err_s

    @pytest.mark.xfail
    def test_py_del_php_intkey_array001(self, php_space):
        output = self.run('''
        $src = "def f(a): del(a[1])";
        compile_py_func_global($src);

        $a = [1, 2, 3];
        f($a);
        echo count($a);
        echo $a[0];
        echo $a[2];
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 2)
        sa.asrt(int, 1)
        sa.asrt(int, 3)

    @pytest.mark.xfail
    def test_py_del_php_intkey_array002(self, php_space):
        output = self.run('''
        $src = "def f(a): del(a[1])";
        compile_py_func_global($src);

        $a = [];
        try {
            f($a);
            echo "fail";
        } catch (PyException $e) {
            echo $e->getMessage();
        }
        ''')
        err_s = "KeyError: 1"
        assert php_space.str_w(output[0]) == err_s
