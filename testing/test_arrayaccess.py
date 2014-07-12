from testing.test_interpreter import BaseTestInterpreter, hippy_fail


class TestArrayAccess(BaseTestInterpreter):

    def test_arrayaccess_interface(self):
        with self.warnings([
            'Fatal error: Class X contains 4 abstract methods and must '
            'therefore be declared abstract or implement the remaining '
            'methods (ArrayAccess::offsetExists, ArrayAccess::offsetGet, '
            'ArrayAccess::offsetSet, ...)'
            ]):
            self.run('''
            class X implements ArrayAccess {}
            ''')

    def test_arrayaccess_basic_usage(self):
        output = self.run('''
        class obj implements ArrayAccess {
            private $container = array();
            public function __construct() {
                $this->container = array(
                    "one" => 1,
                    "two" => 2,
                    "three" => 3,
                );
            }
            public function offsetSet($offset, $value) {
                if (is_null($offset)) {
                    $this->container[] = $value;
                } else {
                    $this->container[$offset] = $value;
                }
            }
            public function offsetExists($offset) {
                return isset($this->container[$offset]);
            }
            public function offsetUnset($offset) {
                unset($this->container[$offset]);
            }
            public function offsetGet($offset) {
                return isset($this->container[$offset]) ? $this->container[$offset] : null;
            }
        }

        $obj = new obj;

        echo isset($obj["two"]);
        echo $obj["two"];
        unset($obj["two"]);
        echo isset($obj["two"]);
        $obj["two"] = "A value";
        echo $obj["two"];
        $obj[] = "Append 1";
        $obj[] = "Append 2";
        echo $obj[0];
        echo $obj[1];
        ''')
        assert self.space.is_true(output[0])
        assert self.space.int_w(output[1]) == 2
        assert not self.space.is_true(output[2])
        assert self.space.str_w(output[3]) == "A value"
        assert self.space.str_w(output[4]) == "Append 1"
        assert self.space.str_w(output[5]) == "Append 2"

    def test_empty(self):
        output = self.run('''
        class object implements ArrayAccess {

                public $a = array('1st', 1, 2=>'3rd', '4th'=>4);

                function offsetExists($index) {
                        echo __METHOD__ . "($index)";
                        return array_key_exists($index, $this->a);
                }
                function offsetGet($index) {
                        echo __METHOD__ . "($index)";
                        return $this->a[$index];
                }
                function offsetSet($index, $newval) {
                        echo __METHOD__ . "($index,$newval)";
                        return $this->a[$index] = $newval;
                }
                function offsetUnset($index) {
                        echo __METHOD__ . "($index)";
                        unset($this->a[$index]);
                }
        }
        $obj = new Object;
        echo empty($obj[0]);
        echo empty($obj[2]);
        echo empty($obj['4th']);
        echo empty($obj['5th']);
        ''')
        assert len(output) == 11
        assert self.space.str_w(output[0]) == 'object::offsetExists(0)'
        assert self.space.str_w(output[1]) == 'object::offsetGet(0)'
        assert output[2] == self.space.w_False
        assert self.space.str_w(output[3]) == 'object::offsetExists(2)'
        assert self.space.str_w(output[4]) == 'object::offsetGet(2)'
        assert output[5] == self.space.w_False
        assert self.space.str_w(output[6]) == 'object::offsetExists(4th)'
        assert self.space.str_w(output[7]) == 'object::offsetGet(4th)'
        assert output[8] == self.space.w_False
        assert self.space.str_w(output[9]) == 'object::offsetExists(5th)'
        assert output[10] == self.space.w_True

    def test_isset(self):
        output = self.run('''
        class object implements ArrayAccess {

                public $a = array('1st', 1, 2=>'3rd', '4th'=>4);

                function offsetExists($index) {
                        echo __METHOD__ . "($index)";
                        return array_key_exists($index, $this->a);
                }
                function offsetGet($index) {
                        echo __METHOD__ . "($index)";
                        return $this->a[$index];
                }
                function offsetSet($index, $newval) {
                        echo __METHOD__ . "($index,$newval)";
                        return $this->a[$index] = $newval;
                }
                function offsetUnset($index) {
                        echo __METHOD__ . "($index)";
                        unset($this->a[$index]);
                }
        }
        $obj = new Object;
        echo isset($obj[0]);
        echo isset($obj[2]);
        echo isset($obj['4th']);
        echo isset($obj['5th']);
        ''')
        assert len(output) == 8
        assert self.space.str_w(output[0]) == 'object::offsetExists(0)'
        assert output[1] == self.space.w_True
        assert self.space.str_w(output[2]) == 'object::offsetExists(2)'
        assert output[3] == self.space.w_True
        assert self.space.str_w(output[4]) == 'object::offsetExists(4th)'
        assert output[5] == self.space.w_True
        assert self.space.str_w(output[6]) == 'object::offsetExists(5th)'
        assert output[7] == self.space.w_False

    @hippy_fail(reason='Both STORE and SUFFIX_PLUSPLUS call pointer '
                        'store in the same way, there is no way to separate '
                        'implementation of the ++ case to raise a notice')
    def test_inplace_modification(self):
        with self.warnings([
                'Notice: Indirect modification of overloaded element of '
                'object has no effect']):
            output = self.run('''
            class object implements ArrayAccess {

                    public $a = array('1st', 1, 2=>'3rd', '4th'=>4);

                    function offsetExists($index) {
                            echo __METHOD__ . "($index)";
                            return array_key_exists($index, $this->a);
                    }
                    function offsetGet($index) {
                            echo __METHOD__ . "($index)";
                            static $a=1;
                            return $a;
                    }
                    function offsetSet($index, $newval) {
                            echo __METHOD__ . "($index,$newval)";
                            return $this->a[$index] = $newval;
                    }
                    function offsetUnset($index) {
                            echo __METHOD__ . "($index)";
                            unset($this->a[$index]);
                    }
            }

            $obj = new Object;

            var_dump($obj[2]);
            echo $obj[2]++;
            var_dump($obj[2]);
            ''')
        assert len(output) == 6
        assert self.space.str_w(output[0]) == 'object::offsetGet(2)'
        assert self.space.int_w(output[1]) == 1
        assert self.space.str_w(output[2]) == 'object::offsetGet(2)'
        assert self.space.int_w(output[3]) == 1
        assert self.space.str_w(output[4]) == 'object::offsetGet(2)'
        assert self.space.int_w(output[5]) == 1

    def test_notice_indirect_modification(self):
        with self.warnings([
            'Notice: Indirect modification of overloaded element of object has'
            ' no effect']):
            output = self.run('''
            class object implements ArrayAccess {
                    function offsetExists($index) { echo __METHOD__; }
                    function offsetGet($index) { return 1; }
                    function offsetSet($index, $newval) { }
                    function offsetUnset($index) { }
            }
            $obj = new Object;
            $x =& $obj[2];
            ''')
        assert not output

    def test_array_proxy(self):
        output = self.run('''
        interface ArrayProxyAccess extends ArrayAccess
        {
            function proxyGet($element);
            function proxySet($element, $index, $value);
            function proxyUnset($element, $index);
        }

        class ArrayProxy implements ArrayAccess
        {
            private $object;
            private $element;
            function __construct(ArrayProxyAccess $object, $element)
            {
                if (!$object->offsetExists($element))
                {
                    $object[$element] = array();
                }
                $this->object = $object;
                $this->element = $element;
            }

            function offsetExists($index) {
                echo __METHOD__ . "($this->element, $index)";
                return array_key_exists($index, $this->object->proxyGet($this->element));
            }

            function offsetGet($index) {
                echo __METHOD__ . "($this->element, $index)";
                $tmp = $this->object->proxyGet($this->element);
                return isset($tmp[$index]) ? $tmp[$index] : NULL;
            }

            function offsetSet($index, $value) {
                echo __METHOD__ . "($this->element, $index, $value)";
                $this->object->proxySet($this->element, $index, $value);
            }

            function offsetUnset($index) {
                echo __METHOD__ . "($this->element, $index)";
                $this->object->proxyUnset($this->element, $index);
            }
        }

        class Peoples implements ArrayProxyAccess
        {
            public $person;

            function __construct()
            {
                $this->person = array(array('name'=>'Foo'));
            }

            function offsetExists($index)
            {
                return array_key_exists($index, $this->person);
            }

            function offsetGet($index)
            {
                return new ArrayProxy($this, $index);
            }

            function offsetSet($index, $value)
            {
                $this->person[$index] = $value;
            }

            function offsetUnset($index)
            {
                unset($this->person[$index]);
            }

            function proxyGet($element)
            {
                return $this->person[$element];
            }

            function proxySet($element, $index, $value)
            {
                $this->person[$element][$index] = $value;
            }

            function proxyUnset($element, $index)
            {
                unset($this->person[$element][$index]);
            }
        }

        $people = new Peoples;

        echo $people->person[0]['name'];
        $people->person[0]['name'] = $people->person[0]['name'] . 'Bar';
        echo $people->person[0]['name'];
        $people->person[0]['name'] .= 'Baz';
        echo $people->person[0]['name'];

        $people = new Peoples;

        echo get_class($people[0]);
        echo $people[0]['name'];
        $people[0]['name'] = 'FooBar';
        echo $people[0]['name'];
        $people[0]['name'] = $people->person[0]['name'] . 'Bar';
        echo $people[0]['name'];
        $people[0]['name'] .= 'Baz';
        echo $people[0]['name'];
        unset($people[0]['name']);
        echo $people[0]['name'];
        $people[0]['name'] = 'BlaBla';
        echo $people[0]['name'];
        ''')
        assert len(output) == 22
        assert self.space.str_w(output[0]) == 'Foo'
        assert self.space.str_w(output[1]) == 'FooBar'
        assert self.space.str_w(output[2]) == 'FooBarBaz'
        assert self.space.str_w(output[3]) == 'ArrayProxy'
        assert self.space.str_w(output[4]) == 'ArrayProxy::offsetGet(0, name)'
        assert self.space.str_w(output[5]) == 'Foo'
        assert self.space.str_w(output[6]) == 'ArrayProxy::offsetSet(0, name, FooBar)'
        assert self.space.str_w(output[7]) == 'ArrayProxy::offsetGet(0, name)'
        assert self.space.str_w(output[8]) == 'FooBar'
        assert self.space.str_w(output[9]) == 'ArrayProxy::offsetSet(0, name, FooBarBar)'
        assert self.space.str_w(output[10]) == 'ArrayProxy::offsetGet(0, name)'
        assert self.space.str_w(output[11]) == 'FooBarBar'
        assert self.space.str_w(output[12]) == 'ArrayProxy::offsetGet(0, name)'
        assert self.space.str_w(output[13]) == 'ArrayProxy::offsetSet(0, name, FooBarBarBaz)'
        assert self.space.str_w(output[14]) == 'ArrayProxy::offsetGet(0, name)'
        assert self.space.str_w(output[15]) == 'FooBarBarBaz'
        assert self.space.str_w(output[16]) == 'ArrayProxy::offsetUnset(0, name)'
        assert self.space.str_w(output[17]) == 'ArrayProxy::offsetGet(0, name)'
        assert output[18] == self.space.w_Null
        assert self.space.str_w(output[19]) == 'ArrayProxy::offsetSet(0, name, BlaBla)'
        assert self.space.str_w(output[20]) == 'ArrayProxy::offsetGet(0, name)'
        assert self.space.str_w(output[21]) == 'BlaBla'

    @hippy_fail(reason="There's an extra call to __construct() we "
                       "haven't fully investigated yet.")
    def test_construct(self):
        output = self.run('''
        interface ArrayProxyAccess extends ArrayAccess
        {
            function proxyGet($element);
            function proxySet($element, $index, $value);
            function proxyUnset($element, $index);
        }

        class ArrayProxy implements ArrayAccess
        {
            private $object;
            private $element;
            function __construct(ArrayProxyAccess $object, $element)
            {
                echo __METHOD__ . "($element)";
                if (!$object->offsetExists($element))
                {
                    $object[$element] = array();
                }
                $this->object = $object;
                $this->element = $element;
            }

            function offsetExists($index) {
                return array_key_exists($index, $this->object->proxyGet($this->element));
            }

            function offsetGet($index) {
                $tmp = $this->object->proxyGet($this->element);
                return isset($tmp[$index]) ? $tmp[$index] : NULL;
            }

            function offsetSet($index, $value) {
                $this->object->proxySet($this->element, $index, $value);
            }

            function offsetUnset($index) {
                $this->object->proxyUnset($this->element, $index);
            }
        }

        class Peoples implements ArrayProxyAccess
        {
            public $person;

            function __construct()
            {
                $this->person = array(array('name'=>'Foo'));
            }

            function offsetExists($index)
            {
                return array_key_exists($index, $this->person);
            }

            function offsetGet($index)
            {
                return new ArrayProxy($this, $index);
            }

            function offsetSet($index, $value)
            {
                $this->person[$index] = $value;
            }

            function offsetUnset($index)
            {
                unset($this->person[$index]);
            }

            function proxyGet($element)
            {
                return $this->person[$element];
            }

            function proxySet($element, $index, $value)
            {
                $this->person[$element][$index] = $value;
            }

            function proxyUnset($element, $index)
            {
                unset($this->person[$element][$index]);
            }
        }

        $people = new Peoples;
        echo get_class($people[0]);
        echo $people[0]['name'];
        $people[0]['name'] = 'FooBar';
        echo $people[0]['name'];
        $people[0]['name'] = $people->person[0]['name'] . 'Bar';
        echo $people[0]['name'];
        $people[0]['name'] .= 'Baz';
        ''')
        assert len(output) == 11
        assert self.space.str_w(output[0]) == 'ArrayProxy::__construct(0)'
        assert self.space.str_w(output[1]) == 'ArrayProxy'
        assert self.space.str_w(output[2]) == 'ArrayProxy::__construct(0)'
        assert self.space.str_w(output[3]) == 'Foo'
        assert self.space.str_w(output[4]) == 'ArrayProxy::__construct(0)'
        assert self.space.str_w(output[5]) == 'ArrayProxy::__construct(0)'
        assert self.space.str_w(output[6]) == 'FooBar'
        assert self.space.str_w(output[7]) == 'ArrayProxy::__construct(0)'
        assert self.space.str_w(output[8]) == 'ArrayProxy::__construct(0)'
        assert self.space.str_w(output[9]) == 'FooBarBar'
        assert self.space.str_w(output[10]) == 'ArrayProxy::__construct(0)'
