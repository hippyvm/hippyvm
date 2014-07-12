import pytest
from testing.test_interpreter import BaseTestInterpreter, hippy_fail


class TestReflectionClass(BaseTestInterpreter):

    def test_constants(self):
        output = self.run("""

            echo ReflectionClass::IS_IMPLICIT_ABSTRACT;
            echo ReflectionClass::IS_EXPLICIT_ABSTRACT;
            echo ReflectionClass::IS_FINAL;

        """)

        assert self.space.int_w(output[0]) == 16
        assert self.space.int_w(output[1]) == 32
        assert self.space.int_w(output[2]) == 64

    def test_construct(self):
        output = self.run("""
        class X {
            function __construct ($x) {
                $this->x = $x;
            }
        }
        $x = new ReflectionClass("X");
        echo $x->name;

        $x = new ReflectionClass(new X('a'));
        echo $x->name;

        """)

        assert self.space.str_w(output[0]) == "X"
        assert self.space.str_w(output[1]) == "X"

    def test_reflection_class(self):
        output = self.run("""
        class X {
            function __construct ($x) {
                $this->x = $x;
            }
        }
        $x = new ReflectionClass("X");
        echo $x->name;
        $a = $x->newInstance(13);
        echo $a->x;
        $a = $x->newInstanceArgs(array(14));
        echo $a->x;
        """)
        assert self.space.str_w(output[0]) == "X"
        assert self.space.int_w(output[1]) == 13
        assert self.space.int_w(output[2]) == 14

    def test_get_constant(self):

        output = self.run("""
        class Test {
            const VALUE = "1";
        }

        $test_reflection = new ReflectionClass("Test");

        echo $test_reflection->getConstant("VALUE");
        echo $test_reflection->getConstant("NOTHING");
        """)

        assert self.space.str_w(output[0]) == "1"
        assert self.space.str_w(output[1]) == ""

    def test_get_constants(self):

        output = self.run("""
        class Test {
            const VALUE_1 = "1";
            const VALUE_2 = "2";
        }

        $test_reflection = new ReflectionClass("Test");

        echo $test_reflection->getConstants();
        """)

        assert output[0].dct_w.keys() == ['VALUE_1', 'VALUE_2']
        assert output[0].dct_w.values() == [self.space.wrap("1"), self.space.wrap("2")]

    def test_get_default_properties(self):

        output = self.run("""
            class Bar {
                protected $inheritedProperty = 'inheritedDefault';
            }

            class Foo extends Bar {
                public $property = 'property';
                private $privateProperty = 'privatePropertyDefault';
                public static $staticProperty = 'staticProperty';
                public $defaultlessProperty;
            }

            $reflectionClass = new ReflectionClass('Foo');
            $properties = $reflectionClass->getDefaultProperties();

            echo $properties;

        """)

        properties = output[0].dct_w

        assert len(properties) == 5

        assert properties['staticProperty'] == self.space.wrap('staticProperty')
        assert properties['property'] == self.space.wrap('property')
        assert properties['privateProperty'] == self.space.wrap('privatePropertyDefault')
        assert properties['defaultlessProperty'] == self.space.w_Null
        assert properties['inheritedProperty'] == self.space.wrap('inheritedDefault')

    def test_get_doc_comment(self):
        pytest.xfail("Not implemented")
        
        output = self.run("""
            /**
            * A test class
            *
            * @param  foo bar
            * @return baz
            */
            class TestClass { }

            $rc = new ReflectionClass('TestClass');
            echo $rc->getDocComment();
        """)

        assert self.space.str_w(output[0]) == '/**\n* A test class\n*\n* @param  foo bar\n* @return baz\n*/'

    def test_get_end_line(self):

        output = self.run("""
            class TestClass {
            }
            $rc = new ReflectionClass('TestClass');
            echo $rc->getEndLine();
            class TestClass2 {
                function __construct ($x) {
                    $this->x = $x;
                }
            }

            $rc = new ReflectionClass('TestClass2');
            echo $rc->getEndLine();

        """)

        assert self.space.int_w(output[0]) == 4
        assert self.space.int_w(output[1]) == 11

    def test_get_interface_names(self):

        output = self.run("""
            interface Foo { }

            interface Bar { }

            class Baz implements Foo, Bar { }

            $rc = new ReflectionClass("Baz");
            $interfaces = $rc->getInterfaceNames();
            echo count($interfaces);
            echo $interfaces[0];
            echo $interfaces[1];

        """)

        assert self.space.int_w(output[0]) == 2
        assert self.space.str_w(output[1]) == "Foo"
        assert self.space.str_w(output[2]) == "Bar"

    def test_get_modifiers(self):

        output = self.run("""
            abstract class AbstractClass
            {
                abstract function getValue();
            }

            $rc = new ReflectionClass("AbstractClass");
            $modifiers = $rc->getModifiers();

            echo $modifiers === (ReflectionClass::IS_IMPLICIT_ABSTRACT | ReflectionClass::IS_EXPLICIT_ABSTRACT);

        """)

        assert output[0] == self.space.w_True

        output = self.run("""
            final class AbstractClass
            {
            }

            $rc = new ReflectionClass("AbstractClass");
            $modifiers = $rc->getModifiers();

            echo $modifiers === ReflectionClass::IS_FINAL;

        """)

        assert output[0] == self.space.w_True

    def test_get_name(self):

        output = self.run("""
            class Test {
                const VALUE = "1";
            }

            $rc = new ReflectionClass("Test");
            echo $rc->getName();

        """)

        assert self.space.str_w(output[0]) == "Test"

    def test_get_start_line(self):

        output = self.run("""#
        #
            class TestClass2 {
                    function __construct ($x) {
                            $this->x = $x;
                    }
            }

            $rc = new ReflectionClass('TestClass2');
            echo $rc->getStartLine();
        """)

        assert self.space.int_w(output[0]) == 4

    def test_get_filename(self):

        output = self.run("""
            class TestClass {
                    function __construct ($x) {
                            $this->x = $x;
                    }
            }

            $rc = new ReflectionClass('TestClass');
            echo $rc->getFileName();
        """)

        name = self.space.str_w(output[0])
        # PHP and hippy
        assert name.startswith('/tmp/') or name.endswith("<input>")

    def test_is_subclass_of(self):

        output = self.run("""

            class TestClass_b {}

            class TestClass_a_1 {}
            class TestClass_a_2 extends TestClass_a_1 {}

            class TestClass extends TestClass_a_2 {}

            $rc = new ReflectionClass('TestClass');
            echo $rc->isSubclassOf('TestClass_a_2');
            echo $rc->isSubclassOf('TestClass_a_1');
            echo $rc->isSubclassOf('TestClass_b');
        """)

        assert output[0] == self.space.w_True
        assert output[1] == self.space.w_True
        assert output[2] == self.space.w_False

    def test_has_method(self):

        output = self.run("""
            Class C {
                public function publicFoo() {
                    return true;
                }

                protected function protectedFoo() {
                    return true;
                }

                private function privateFoo() {
                    return true;
                }

                static function staticFoo() {
                    return true;
                }
            }

            $rc = new ReflectionClass("C");

            echo $rc->hasMethod('publicFoo');

            echo $rc->hasMethod('protectedFoo');

            echo $rc->hasMethod('privateFoo');

            echo $rc->hasMethod('staticFoo');

            // C should not have method bar
            echo $rc->hasMethod('bar');

            // Method names are case insensitive
            echo $rc->hasMethod('PUBLICfOO');
        """)

        assert output == [
            self.space.w_True,
            self.space.w_True,
            self.space.w_True,
            self.space.w_True,
            self.space.w_False,
            self.space.w_True,
        ]

    def test_is_abstract(self):

        output = self.run("""
            class          TestClass { }
            abstract class TestAbstractClass { }

            $testClass     = new ReflectionClass('TestClass');
            $abstractClass = new ReflectionClass('TestAbstractClass');

            echo $testClass->isAbstract();
            echo $abstractClass->isAbstract();
        """)

        assert output == [self.space.w_False, self.space.w_True]

    def test_get_constructor(self):

        output = self.run("""
            class TestClass {
                public function __construct() {

                }
            }

            $testClass = new ReflectionClass('TestClass');
            $method = $testClass->getConstructor();

            echo get_class($method);
            echo $method->class;
            echo $method->name;
        """)


        assert self.space.str_w(output[0]) == "ReflectionMethod"
        assert self.space.str_w(output[1]) == "TestClass"
        assert self.space.str_w(output[2]) == "__construct"


    def test_get_method(self):

        output = self.run("""
            class TestClass {
                public function test() {
                return true;
                }
            }

            $testClass = new ReflectionClass('TestClass');
            $method = $testClass->getMethod('test');

            echo get_class($method);
            echo $method->class;
            echo $method->name;
        """)


        assert self.space.str_w(output[0]) == "ReflectionMethod"
        assert self.space.str_w(output[1]) == "TestClass"
        assert self.space.str_w(output[2]) == "test"

        output = self.run("""
            class TestClass {
                public function test() {
                return true;
                }
            }


            $testClass = new ReflectionClass('TestClass');

            try {
                $method = $testClass->getMethod('test_1');
            } catch (Exception $e) {
                echo $e->getMessage();
            }
        """)

        assert self.space.str_w(output[0]) == 'Method test_1 does not exist'

    def test_get_methods(self):

        output = self.run("""
            class TestClass {

                public function test_1() {
                    return true;
                }

                public function test_2() {
                    return true;
                }

            }

            $testClass = new ReflectionClass('TestClass');
            $methods = $testClass->getMethods();

            echo $methods[0]->name;
            echo $methods[1]->name;

        """)

        assert self.space.str_w(output[0]) == "test_1"
        assert self.space.str_w(output[1]) == "test_2"

    def test_is_instantiable(self):

        output = self.run("""
            class C { }

            interface iface {
                function f1();
            }

            class ifaceImpl implements iface {
                function f1() {}
            }

            abstract class abstractClass {
                function f1() { }
                abstract function f2();
            }

            class D extends abstractClass {
                function f2() { }
            }

            class privateConstructor {
                private function __construct() { }
            }

            $classes = array(
                "C",
                "iface",
                "ifaceImpl",
                "abstractClass",
                "D",
                "privateConstructor",
            );

            foreach($classes  as $class ) {
                $reflectionClass = new ReflectionClass($class);
                echo $reflectionClass->IsInstantiable();
            }
        """)

        assert output[0] == self.space.w_True
        assert output[1] == self.space.w_False
        assert output[2] == self.space.w_True
        assert output[3] == self.space.w_False
        assert output[4] == self.space.w_True
        assert output[5] == self.space.w_False


class TestReflectionMethod(BaseTestInterpreter):

    def test_construct(self):

        output = self.run("""
            class TestClass {
                public function test() {
                return true;
                }
            }

            $method = new ReflectionMethod('TestClass', 'test');

            echo get_class($method);

            echo $method->class;
            echo $method->name;
        """)

        assert self.space.str_w(output[0]) == "ReflectionMethod"
        assert self.space.str_w(output[1]) == "TestClass"
        assert self.space.str_w(output[2]) == "test"

    def test_is_public(self):

        output = self.run("""
            class TestClass {
                public function test() {
                return true;
                }
            }

            $method = new ReflectionMethod('TestClass', 'test');
            echo $method->isPublic();
        """)

        assert output[0] == self.space.w_True

    def test_get_name(self):

        output = self.run("""
            class TestClass {
                public function test() {
                return true;
                }
            }

            $method = new ReflectionMethod('TestClass', 'test');
            echo $method->getName();
        """)

        assert self.space.str_w(output[0]) == "test"

    def test_get_parameters(self):
        output = self.run("""
            class TestClass {
                public function test($a, $b) {
                    return true;
                }
            }

            $method = new ReflectionMethod('TestClass', 'test');
            $parameters = $method->getParameters();

            foreach ($parameters as $p) {
                echo $p->getName();
            }
        """)

        assert self.space.str_w(output[0]) == "a"
        assert self.space.str_w(output[1]) == "b"

    def test_get_doc_comment(self):
        pytest.xfail("getDocComment not implemented")

        output = self.run("""
            class TestClass {
                /** and end with */
                public function test($a, $b) {
                    return true;
                }
            }

            $method = new ReflectionMethod('TestClass', 'test');
            echo $method->getDocComment();

        """)

        assert self.space.str_w(output[0]) == "/** and end with */"

    def test_get_declaring_class(self):

        output = self.run("""
            class TestClass {
                public function test($a, $b) {
                    return true;
                }
            }

            $method = new ReflectionMethod('TestClass', 'test');
            $class = $method->getDeclaringClass();

            echo get_class($class);
            echo $class->getName();

        """)

        assert self.space.str_w(output[0]) == "ReflectionClass"
        assert self.space.str_w(output[1]) == "TestClass"

    def test_is_static(self):

        output = self.run("""
            class TestClass {
                public static function test1($a, $b) {
                    return true;
                }
                public function test2($a, $b) {
                    return true;
                }

            }

            $method = new ReflectionMethod('TestClass', 'test1');
            echo $method->isStatic();

            $method = new ReflectionMethod('TestClass', 'test2');
            echo $method->isStatic();


        """)

        assert output[0] == self.space.w_True
        assert output[1] == self.space.w_False


class TestReflectionFunction(BaseTestInterpreter):

    def test_construct(self):

        output = self.run("""
            function test() {
                static $c = 0;
                return ++$c;
            }

            $fun = new ReflectionFunction('test');
            echo get_class($fun);
        """)

        assert self.space.str_w(output[0]) == "ReflectionFunction"

        output = self.run("""
            $test = function() {
                static $c = 0;
                return ++$c;
            };

            $fun = new ReflectionFunction($test);
            echo get_class($fun);
        """)

        assert self.space.str_w(output[0]) == "ReflectionFunction"

    def test_get_name(self):

        output = self.run("""
            function test() {}

            $fun = new ReflectionFunction('test');
            echo $fun->getName();
        """)

        assert self.space.str_w(output[0]) == "test"

        output = self.run("""
            $test = function() {};

            $fun = new ReflectionFunction($test);
            echo $fun->getName();
        """)

        assert self.space.str_w(output[0]) == "{closure}"

    def test_get_parameters(self):

        output = self.run("""
            function test($a, $b) {}

            $fun = new ReflectionFunction('test');
            $parameters = $fun->getParameters();

            foreach ($parameters as $p) {
                echo $p->getName();
            }
        """)

        assert self.space.str_w(output[0]) == "a"
        assert self.space.str_w(output[1]) == "b"

    def test_get_doc_comment(self):
        pytest.xfail("getDocComment not implemented")

        output = self.run("""
            /** and end with */
            function test($a, $b) {}

            $fun = new ReflectionFunction('test');
            echo $fun->getDocComment();

        """)

        assert self.space.str_w(output[0]) == "/** and end with */"


class TestReflectionParameter(BaseTestInterpreter):

    def test_construct(self):

        output = self.run("""
            function foo($a, $b, $c) { }
            $parameter = new ReflectionParameter('foo', 1);

            echo get_class($parameter);
        """)

        assert self.space.str_w(output[0]) == "ReflectionParameter"

        output = self.run("""
            class Test{
                public function test($a, $b) {
                return true;
                }
            }

            $parameter = new ReflectionParameter(array('Test', 'test'), 1);
            echo get_class($parameter);
        """)

        assert self.space.str_w(output[0]) == "ReflectionParameter"

    def test_get_name(self):

        output = self.run("""
            function foo($a, $b, $c) { }
            $parameter = new ReflectionParameter('foo', 0);

            echo $parameter->getName();
        """)

        assert self.space.str_w(output[0]) == "a"

        output = self.run("""
            class Test{
                public function test($a, $b) {
                return true;
                }
            }

            $parameter = new ReflectionParameter(array('Test', 'test'), 0);
            echo $parameter->getName();
        """)

        assert self.space.str_w(output[0]) == "a"



class TestReflectionProperty(BaseTestInterpreter):

    def test_constants(self):
        output = self.run('''

        echo ReflectionProperty::IS_STATIC;
        echo ReflectionProperty::IS_PUBLIC;
        echo ReflectionProperty::IS_PROTECTED;
        echo ReflectionProperty::IS_PRIVATE;

        ''')
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 256
        assert self.space.int_w(output[2]) == 512
        assert self.space.int_w(output[3]) == 1024

    def test_is_public(self):
        output = self.run('''
        class String
        {
            public $length = 5;
        }

        $prop = new ReflectionProperty('String', 'length');
        echo $prop->isPublic();
        ''')
        assert output[0] == self.space.w_True

    def test_get_name(self):
        output = self.run('''
        class String
        {
            public $length = 5;
        }

        $prop = new ReflectionProperty('String', 'length');
        echo $prop->getName();
        ''')
        assert self.space.str_w(output[0]) == 'length'

    def test_value(self):
        output = self.run('''
        class String
        {
            public $length = 5;
        }

        $prop = new ReflectionProperty('String', 'length');

        $obj = new String();

        echo $prop->getValue($obj);
        $prop->setValue($obj, 10);
        echo $prop->getValue($obj);
        ''')
        assert self.space.int_w(output[0]) == 5
        assert self.space.int_w(output[1]) == 10

    def test_private_access_error(self):
        output = self.run('''
        class String
        {
            private $length = 5;
        }

        $prop = new ReflectionProperty('String', 'length');

        $obj = new String();
        try {
            echo $prop->getValue($obj);
        } catch (ReflectionException $e) {
            echo $e->getMessage();
        }

        ''')
        assert self.space.str_w(output[0]) == "Cannot access non-public member String::length"

    @hippy_fail(reason="setAccessible not implemented")
    def test_accessible_private(self):
        output = self.run('''
        class String
        {
            private $length = 5;
        }

        $prop = new ReflectionProperty('String', 'length');

        $obj = new String();
        $prop->setAccessible(true);
        echo $prop->getValue($obj);
        ''')
        assert self.space.int_w(output[0]) == 5
