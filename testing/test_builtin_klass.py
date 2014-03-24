from .test_interpreter import BaseTestInterpreter
from . import conftest


class TestBuiltinKlass(BaseTestInterpreter):

    def test_stdclass_constructor(self):
        self.run('''
        new stdClass(2, 3, "hi!");
        ''')      # no warning
        self.run('''
        $o = new stdClass(42);
        echo $o->scalar;
        ''', ["Notice: Undefined property: stdClass::$scalar"])

    def test_exception_protected_message(self):
        self.run('''
        function f() {
           return new Exception("xyz");
        }
        echo f()->message;
        ''', ["Fatal error: Cannot access protected property "
              "Exception::$message"])

    def test_exception(self):
        output = self.run('''
        function f() {
           return new Exception("xyz");
        }
        echo f()->getMessage();
        ''')
        assert self.space.str_w(output[0]) == "xyz"

    def test_exception_no_arg(self):
        output = self.run('''
        function f() {
           return new Exception();
        }
        echo gettype(f()->getMessage());
        echo f()->getMessage();
        ''')
        assert self.space.str_w(output[0]) == "string"
        assert self.space.str_w(output[1]) == ""

    def test_exception_code(self):
        output = self.run('''
        $e = new Exception();
        echo $e->getCode();
        $e = new Exception("xyz", 42);
        echo $e->getCode();
        ''')
        assert self.space.int_w(output[0]) == 0
        assert self.space.int_w(output[1]) == 42
        output = self.run('''
        $e = new Exception("xyz", "5yyyy");
        echo $e->getCode();
        ''', ['Notice: A non well formed numeric value encountered'])
        assert self.space.int_w(output[0]) == 5
        if conftest.option.runappdirect:
            expected = ('Fatal error: Wrong parameters for '
                        'Exception([string $exception [, long $code [, '
                        'Exception $previous = NULL]]])')
        else:
            expected = ('Warning: Exception::__construct() expects parameter '
                        '2 to be long, string given')
        self.run('''
        new Exception("xyz", "yyyy");
        ''', [expected])

    def test_exception_previous(self):
        output = self.run('''
        $e = new Exception("xyz", 42, NULL);
        echo $e->getPrevious();
        $f = new Exception("abcd", 11, $e);
        echo $f->getPrevious() === $e;
        ''')
        assert self.space.is_w(output[0], self.space.w_Null)
        assert self.space.int_w(output[1]) == 1

    def test_too_many_args(self):
        if conftest.option.runappdirect:
            expected = ('Fatal error: Wrong parameters for '
                        'Exception([string $exception [, long $code [, '
                        'Exception $previous = NULL]]])')
        else:
            expected = ('Warning: Exception::__construct() expects at most '
                        '3 parameters, 4 given')
        self.run('''
        new Exception("xyz", 42, NULL, NULL);
        ''', [expected])

    def test_bad_class_previous(self):
        self.run('''
        class A { };
        new Exception("xyz", 42, new A());
        ''', ["Fatal error: Wrong parameters for "
              "Exception([string $exception [, long $code [, "
              "Exception $previous = NULL]]])"])

    def test_not_an_object_arg(self):
        if conftest.option.runappdirect:
            expected = ('Fatal error: Wrong parameters for '
                        'Exception([string $exception [, long $code [, '
                        'Exception $previous = NULL]]])')
        else:
            expected = ('Warning: Exception::__construct() expects parameter '
                        '3 to be object, double given')
        self.run('''
        new Exception("xyz", 42, 4.56);
        ''', [expected])

    def test_subclass(self):
        output = self.run('''
        class A extends Exception {
            function __construct($a, $b) { $this->b = $b; }
        }
        function f() {
            return new A(42, "foo");
        }
        $a = f();
        echo $a->b;
        ''')
        assert self.space.str_w(output[0]) == "foo"

    def test_subclass_methods(self):
        output = self.run('''
        class A extends Exception { }
        $a = new A("xyz");
        echo $a->getMessage();
        ''')
        assert self.space.str_w(output[0]) == "xyz"

    def test_trace(self):
        output = self.run('''
        function f() {
            return new Exception();
        }
        $a = f();
        echo $a->getTrace();
        ''')
        it = output[0].as_rdict().items()
        assert len(it) >= 1
        assert it[0][0] == '0'
        d = it[0][1].as_rdict()
        assert d.keys() == ['file', 'line', 'function', 'args']
        assert self.space.str_w(d['function']) == 'f'

    def test_try_catch_custom_exception(self):
        output = self.run('''
        class MyException extends Exception { };
        class OtherException extends Exception { };
        function f() {
            try {
                throw new MyException("xyz");
            }
            catch (OtherException $e) {
                echo "oups";
            }
        }
        try {
            f();
        } catch (MyException $e) {
           echo $e->getMessage();
        }
        ''')
        assert self.space.str_w(output[0]) == 'xyz'

    def test_getfile(self):
        output = self.run('''
        $x = new Exception();
        echo $x->getFile(), __FILE__;
        ''')
        assert self.space.str_w(output[0]) == self.space.str_w(output[1])

    def test_exception_get_traceback_string(self):
        output = self.run("""
        function f() {
            return new Exception();
        }
        $a = f();
        echo $a->getTraceAsString();
        """)
        assert self.space.str_w(output[0]) == "#0 <input>(3): f()\n#1 <input>(5): <main>()"
