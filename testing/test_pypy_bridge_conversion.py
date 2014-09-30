from testing.test_interpreter import MockInterpreter, BaseTestInterpreter

import pytest

class TestPyPyBridgeConversions(BaseTestInterpreter):
    """ Interpreter level conversion code tests """

    def new_interp(self):
        return self.engine.new_interp(None, None)

    def test_py_int_of_ph_integer(self):
        interp = self.new_interp()
        wph_integer = interp.space.newint(666)
        py_int = wph_integer.to_py(interp)
        assert interp.py_space.int_w(py_int) == 666

    def test_py_none_of_ph_null(self):
        interp = self.new_interp()
        w_py_none = interp.space.w_Null.to_py(interp)
        assert w_py_none is interp.py_space.w_None

    def test_py_str_of_ph_string(self):
        interp = self.new_interp()
        wph_string = interp.space.wrap("smeg")
        w_py_str = wph_string.to_py(interp)
        assert interp.py_space.str_w(w_py_str) == "smeg"

    def test_py_str_of_ph_string2(self):
        interp = self.new_interp()
        wph_string = interp.space.wrap("123") # can be interpreted as int
        w_py_str = wph_string.to_py(interp)
        assert interp.py_space.str_w(w_py_str) == "123"

    def test_py_float_of_ph_float(self):
        interp = self.new_interp()
        wph_float = interp.space.wrap(1.337)
        w_py_float = wph_float.to_py(interp)
        assert interp.py_space.float_w(w_py_float) == 1.337

    def test_py_bool_of_ph_boolean(self):
        interp = self.new_interp()
        for polarity in [True, False]:
            wph_boolean = interp.space.wrap(polarity)
            w_py_bool = wph_boolean.to_py(interp)
            assert interp.py_space.bool_w(w_py_bool) == polarity

    def test_py_list_of_ph_array(self):
        pytest.skip("XXX disabled list conversions for now")
        interp = self.new_interp()
        php_space, py_space = interp.space, interp.py_space

        input = [1, 2, 3, "a", "b", "c" ]
        wph_elems = [ php_space.wrap(i) for i in input ]
        wph_arr = php_space.new_array_from_list(wph_elems)
        w_py_converted = wph_arr.to_py(interp)

        w_py_expect = py_space.newlist([ py_space.wrap(i) for i in input ])
        assert py_space.is_true(py_space.eq(w_py_converted, w_py_expect))

    def test_py_list_of_ph_array_nested(self):
        pytest.skip("XXX disabled list conversions for now")
        interp = self.new_interp()
        php_space, py_space = interp.space, interp.py_space

        # We will build a PHP list looking like this:
        # [ 666, False, [ 1, "a" ]]

        # inner list
        input_inner = [1, "a"]
        wph_elems_inner = [ php_space.wrap(i) for i in input_inner ]
        wph_arr_inner = php_space.new_array_from_list(wph_elems_inner)

        # outer list
        input_outer = [666, False]
        wph_elems_outer = [ php_space.wrap(i) for i in input_outer ]
        wph_arr_outer = php_space.new_array_from_list(wph_elems_outer)
        wph_arr_outer.appenditem_inplace(php_space, wph_arr_inner)

        w_py_l = wph_arr_outer.to_py(interp)

        consts = [ py_space.wrap(i) for i in range(3) ]

        assert py_space.int_w(py_space.len(w_py_l)) == 3
        assert py_space.int_w(py_space.getitem(w_py_l, consts[0])) == 666
        assert py_space.bool_w(py_space.getitem(w_py_l, consts[1])) == False

        w_py_innr = py_space.getitem(w_py_l, consts[2])
        assert py_space.int_w(py_space.getitem(w_py_innr, consts[0])) == 1
        assert py_space.str_w(py_space.getitem(w_py_innr, consts[1])) == "a"

    # XXX Test mutating the list

    def test_unwrap_php(self):
        php_space = self.space
        output = self.run('''
        $src = <<<EOD
        def dummy(x):
            return x
        EOD;
        $dummy = embed_py_func($src);

        class C { }
        $x = new C();
        echo($dummy($x) === $x);
        ''')
        assert php_space.is_true(output[0])

    def test_ph_integer_of_py_int(self):
        interp = self.new_interp()
        py_int = interp.py_space.newint(666)
        wph_integer = py_int.to_php(interp)
        assert interp.space.int_w(wph_integer) == 666
        assert wph_integer.tp == interp.space.tp_int

    def test_ph_float_of_py_float(self):
        interp = self.new_interp()
        py_float = interp.py_space.newfloat(3.1415)
        wph_float = py_float.to_php(interp)
        assert interp.space.float_w(wph_float) == 3.1415
        assert wph_float.tp == interp.space.tp_float

    def test_ph_null_of_py_none(self):
        interp = self.new_interp()
        wph_null = interp.py_space.w_None.to_php(interp)
        assert wph_null is interp.space.w_Null
        assert wph_null.tp == interp.space.tp_null

    def test_ph_string_of_py_str(self):
        interp = self.new_interp()
        w_py_str = interp.py_space.wrap("transmogrification")
        wph_string = w_py_str.to_php(interp)
        assert interp.space.str_w(wph_string) == "transmogrification"
        assert wph_string.tp == interp.space.tp_str

    def test_ph_boolean_of_py_bool(self):
        interp = self.new_interp()
        for b in [True, False]:
            w_py_bool = interp.py_space.wrap(b)
            wph_boolean = w_py_bool.to_php(interp)
            assert wph_boolean.boolval == b
            assert wph_boolean.tp == interp.space.tp_bool

    def test_ph_array_of_py_list(self):
        pytest.skip("XXX disabled list conversions for now")
        interp = self.new_interp()
        php_space, py_space = interp.space, interp.py_space

        input = [1, 2, "wibble", "chunks", True]
        wph_expect = php_space.new_array_from_list(
                [ php_space.wrap(x) for x in input ])

        w_py_list = py_space.newlist([ py_space.wrap(x) for x in input ])
        wph_actual = w_py_list.to_php(interp)

        assert php_space.is_true(php_space.eq(wph_actual, wph_expect))

    def test_ph_array_of_py_list_nested(self):
        pytest.skip("XXX disabled list conversions for now")
        interp = self.new_interp()
        php_space, py_space = interp.space, interp.py_space

        # Test the following list converts OK:
        # [1, 2, ["a", "b", "c"]]

        input_inner = ["a", "b", "c"]
        wph_input_inner = [ php_space.wrap(x) for x in input_inner ]
        wph_expect_inner = php_space.new_array_from_list(wph_input_inner)

        input_outer = [1, 2] # and we append the inner list also
        wph_input_outer = [ php_space.wrap(x) for x in input_outer ] + \
                [ wph_expect_inner ]
        wph_expect_outer = php_space.new_array_from_list(wph_input_outer)

        w_py_input_inner = [ py_space.wrap(x) for x in input_inner ]
        w_py_list_inner = py_space.newlist(w_py_input_inner)

        w_py_list_outer = [ py_space.wrap(x) for x in input_outer ] + \
                [ w_py_list_inner ]
        w_py_list_outer = py_space.newlist(w_py_list_outer)

        wph_got = w_py_list_outer.to_php(interp)
        assert php_space.is_true(php_space.eq(wph_expect_outer, wph_got))

    def test_ph_closure_of_py_function(self):
        interp = self.new_interp()
        pytest.skip("XXX")
        interp.space = self.space
        interp = MockInterpreter(interp.space)

        pysource = "def f(x): return x + 1"
        pycompiler = interp.py_space.createcompiler()
        code = pycompiler.compile(pysource, 'XXX', 'exec', 0)

        from pypy.interpreter.module import Module
        w_py_mod_name = interp.py_space.wrap("tests")
        w_py_module = Module(interp.py_space, w_py_mod_name)
        code.exec_code(interp.py_space, w_py_module.w_dict, w_py_module.w_dict)
        func = interp.py_space.getattr(w_py_module, interp.py_space.wrap("f"))
        w_py_func = interp.py_space.wrap(func)

        wph_closure = w_py_func.to_php(interp)
        # XXX until interp.space.tp_closure
        assert type(wph_closure) is W_ClosureObject

    # XXX List slices
    # XXX Test mutating the list.

    def test_unwrap_py(self):
        php_space = self.space
        output = self.run('''
        function dummy($x) {
            return $x;
        }

        $src = <<<EOD
        def tst():
            class C: pass
            x = C()
            print x, dummy(x)
            return x is dummy(x)
        EOD;
        $tst = embed_py_func($src);

        echo($tst());
        ''')
        assert php_space.is_true(output[0])

    def test_php_null(self):
        php_space = self.space
        output = self.run('''
        $src = <<<EOD
        def n():
            return None
        EOD;
        $n = embed_py_func($src);

        echo(null === $n());
        ''')
        assert php_space.is_true(output[0])

    def test_wrapped_php_instance_attributeerror(self):
        php_space = self.space
        output = self.run('''
        class A {};

        $src = <<<EOD
        def f(a):
            try:
                x = a.no_exist
            except BridgeError as e:
                return e.message
            return "test failed"
        EOD;
        $f = embed_py_func($src);

        $inst = new A();
        echo $f($inst);
        ''')
        err_s = "Wrapped PHP instance has no attribute 'no_exist'"
        assert php_space.str_w(output[0]) == err_s

    def test_using_kwargs_to_a_php_func_raises(self):
        php_space = self.space
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

    def test_calling_callable_php_inst_in_py(self):
        php_space = self.space
        output = self.run('''
        class A {
                function __invoke() {
                    return "invoked";
                }
        };

        $src = <<<EOD
        def py_func(inst):
            return inst()
        EOD;
        $py_func = embed_py_func($src);

        $inst = new A();
        echo($py_func($inst));
        ''')
        assert php_space.str_w(output[0]) == "invoked"

    def test_calling_callable_php_inst_with_args_in_py(self):
        php_space = self.space
        output = self.run('''
        class A {
                function __invoke($x, $y) {
                    return $x . $y;
                }
        };

        $src = <<<EOD
        def py_func(inst):
            return inst("abc", "123")
        EOD;
        $py_func = embed_py_func($src);

        $inst = new A();
        echo($py_func($inst));
        ''')
        assert php_space.str_w(output[0]) == "abc123"

    def test_calling_a_non_callable_php_instance_in_py_raises(self):
        php_space = self.space
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


    def test_calling_a_callable_php_instance_with_kwargs_in_py_raises(self):
        php_space = self.space
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
