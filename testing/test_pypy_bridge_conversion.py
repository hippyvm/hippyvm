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
        assert interp.pyspace.int_w(py_int) == 666

    def test_py_none_of_ph_null(self):
        interp = self.new_interp()
        wpy_none = interp.space.w_Null.to_py(interp)
        assert wpy_none is interp.pyspace.w_None

    def test_py_str_of_ph_string(self):
        interp = self.new_interp()
        wph_string = interp.space.wrap("smeg")
        wpy_str = wph_string.to_py(interp)
        assert interp.pyspace.str_w(wpy_str) == "smeg"

    def test_py_str_of_ph_string2(self):
        interp = self.new_interp()
        wph_string = interp.space.wrap("123") # can be interpreted as int
        wpy_str = wph_string.to_py(interp)
        assert interp.pyspace.str_w(wpy_str) == "123"

    def test_py_float_of_ph_float(self):
        interp = self.new_interp()
        wph_float = interp.space.wrap(1.337)
        wpy_float = wph_float.to_py(interp)
        assert interp.pyspace.float_w(wpy_float) == 1.337

    def test_py_bool_of_ph_boolean(self):
        interp = self.new_interp()
        for polarity in [True, False]:
            wph_boolean = interp.space.wrap(polarity)
            wpy_bool = wph_boolean.to_py(interp)
            assert interp.pyspace.bool_w(wpy_bool) == polarity

    def test_py_list_of_ph_array(self):
        pytest.skip("XXX disabled list conversions for now")
        interp = self.new_interp()
        phspace, pyspace = interp.space, interp.pyspace

        input = [1, 2, 3, "a", "b", "c" ]
        wph_elems = [ phspace.wrap(i) for i in input ]
        wph_arr = phspace.new_array_from_list(wph_elems)
        wpy_converted = wph_arr.to_py(interp)

        wpy_expect = pyspace.newlist([ pyspace.wrap(i) for i in input ])
        assert pyspace.is_true(pyspace.eq(wpy_converted, wpy_expect))

    def test_py_list_of_ph_array_nested(self):
        pytest.skip("XXX disabled list conversions for now")
        interp = self.new_interp()
        phspace, pyspace = interp.space, interp.pyspace

        # We will build a PHP list looking like this:
        # [ 666, False, [ 1, "a" ]]

        # inner list
        input_inner = [1, "a"]
        wph_elems_inner = [ phspace.wrap(i) for i in input_inner ]
        wph_arr_inner = phspace.new_array_from_list(wph_elems_inner)

        # outer list
        input_outer = [666, False]
        wph_elems_outer = [ phspace.wrap(i) for i in input_outer ]
        wph_arr_outer = phspace.new_array_from_list(wph_elems_outer)
        wph_arr_outer.appenditem_inplace(phspace, wph_arr_inner)

        wpy_l = wph_arr_outer.to_py(interp)

        consts = [ pyspace.wrap(i) for i in range(3) ]

        assert pyspace.int_w(pyspace.len(wpy_l)) == 3
        assert pyspace.int_w(pyspace.getitem(wpy_l, consts[0])) == 666
        assert pyspace.bool_w(pyspace.getitem(wpy_l, consts[1])) == False

        wpy_innr = pyspace.getitem(wpy_l, consts[2])
        assert pyspace.int_w(pyspace.getitem(wpy_innr, consts[0])) == 1
        assert pyspace.str_w(pyspace.getitem(wpy_innr, consts[1])) == "a"

    # XXX Test mutating the list

    def test_unwrap_php(self):
        phspace = self.space
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
        assert phspace.is_true(output[0])

    def test_ph_integer_of_py_int(self):
        interp = self.new_interp()
        py_int = interp.pyspace.newint(666)
        wph_integer = py_int.to_php(interp)
        assert interp.space.int_w(wph_integer) == 666
        assert wph_integer.tp == interp.space.tp_int

    def test_ph_float_of_py_float(self):
        interp = self.new_interp()
        py_float = interp.pyspace.newfloat(3.1415)
        wph_float = py_float.to_php(interp)
        assert interp.space.float_w(wph_float) == 3.1415
        assert wph_float.tp == interp.space.tp_float

    def test_ph_null_of_py_none(self):
        interp = self.new_interp()
        wph_null = interp.pyspace.w_None.to_php(interp)
        assert wph_null is interp.space.w_Null
        assert wph_null.tp == interp.space.tp_null

    def test_ph_string_of_py_str(self):
        interp = self.new_interp()
        wpy_str = interp.pyspace.wrap("transmogrification")
        wph_string = wpy_str.to_php(interp)
        assert interp.space.str_w(wph_string) == "transmogrification"
        assert wph_string.tp == interp.space.tp_str

    def test_ph_boolean_of_py_bool(self):
        interp = self.new_interp()
        for b in [True, False]:
            wpy_bool = interp.pyspace.wrap(b)
            wph_boolean = wpy_bool.to_php(interp)
            assert wph_boolean.boolval == b
            assert wph_boolean.tp == interp.space.tp_bool

    def test_ph_array_of_py_list(self):
        pytest.skip("XXX disabled list conversions for now")
        interp = self.new_interp()
        phspace, pyspace = interp.space, interp.pyspace

        input = [1, 2, "wibble", "chunks", True]
        wph_expect = phspace.new_array_from_list(
                [ phspace.wrap(x) for x in input ])

        wpy_list = pyspace.newlist([ pyspace.wrap(x) for x in input ])
        wph_actual = wpy_list.to_php(interp)

        assert phspace.is_true(phspace.eq(wph_actual, wph_expect))

    def test_ph_array_of_py_list_nested(self):
        pytest.skip("XXX disabled list conversions for now")
        interp = self.new_interp()
        phspace, pyspace = interp.space, interp.pyspace

        # Test the following list converts OK:
        # [1, 2, ["a", "b", "c"]]

        input_inner = ["a", "b", "c"]
        wph_input_inner = [ phspace.wrap(x) for x in input_inner ]
        wph_expect_inner = phspace.new_array_from_list(wph_input_inner)

        input_outer = [1, 2] # and we append the inner list also
        wph_input_outer = [ phspace.wrap(x) for x in input_outer ] + \
                [ wph_expect_inner ]
        wph_expect_outer = phspace.new_array_from_list(wph_input_outer)

        wpy_input_inner = [ pyspace.wrap(x) for x in input_inner ]
        wpy_list_inner = pyspace.newlist(wpy_input_inner)

        wpy_list_outer = [ pyspace.wrap(x) for x in input_outer ] + \
                [ wpy_list_inner ]
        wpy_list_outer = pyspace.newlist(wpy_list_outer)

        wph_got = wpy_list_outer.to_php(interp)
        assert phspace.is_true(phspace.eq(wph_expect_outer, wph_got))

    def test_ph_closure_of_py_function(self):
        interp = self.new_interp()
        pytest.skip("XXX")
        interp.space = self.space
        interp = MockInterpreter(interp.space)

        pysource = "def f(x): return x + 1"
        pycompiler = interp.pyspace.createcompiler()
        code = pycompiler.compile(pysource, 'XXX', 'exec', 0)

        from pypy.interpreter.module import Module
        wpy_mod_name = interp.pyspace.wrap("tests")
        wpy_module = Module(interp.pyspace, wpy_mod_name)
        code.exec_code(interp.pyspace, wpy_module.w_dict, wpy_module.w_dict)
        func = interp.pyspace.getattr(wpy_module, interp.pyspace.wrap("f"))
        wpy_func = interp.pyspace.wrap(func)

        wph_closure = wpy_func.to_php(interp)
        # XXX until interp.space.tp_closure
        assert type(wph_closure) is W_ClosureObject

    # XXX List slices
    # XXX Test mutating the list.

    def test_unwrap_py(self):
        phspace = self.space
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
        assert phspace.is_true(output[0])

    def test_php_null(self):
        phspace = self.space
        output = self.run('''
        $src = <<<EOD
        def n():
            return None
        EOD;
        $n = embed_py_func($src);

        echo(null === $n());
        ''')
        assert phspace.is_true(output[0])

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
