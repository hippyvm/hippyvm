import py
from testing.test_interpreter import (
    BaseTestInterpreter, hippy_fail, MockServerEngine)
from hippy.objects.intobject import W_IntObject
from hippy.objects.instanceobject import W_InstanceObject
from hippy import consts
from hippy.objspace import getspace
from hippy.interpreter import Interpreter
from hippy.builtin import wrap_method
from hippy.builtin_klass import new_abstract_method, GetterSetterWrapper
from hippy.klass import BuiltinClass, ClassDeclarationError, all_builtin_classes

def test_BuiltinClass():
    k_Test = BuiltinClass('Test')
    assert k_Test.name == 'Test'
    assert not k_Test.methods
    assert not k_Test.properties
    assert not k_Test.constants_w

def test_BuiltinClass_extends():
    @wrap_method([], 'Base::Foo')
    def Foo():
        return W_IntObject(42)
    k_Base = BuiltinClass('Base', [Foo])

    assert k_Base.name == 'Base'
    assert k_Base.methods.keys() == ['foo']

    k_Test = BuiltinClass('Test', extends=k_Base)
    assert k_Test.methods.keys() == ['foo']
    assert k_Test.methods['foo'] is k_Base.methods['foo']

def test_BuiltinClass_extends_custom():
    @wrap_method([], 'Base::Foo')
    def Foo():
        return W_IntObject(42)
    k_Base = BuiltinClass('Base', [Foo])

    assert k_Base.name == 'Base'
    assert k_Base.methods.keys() == ['foo']

    class W_Test(W_InstanceObject):
        pass
    k_Test = BuiltinClass('Test', extends=k_Base, instance_class=W_Test)
    assert k_Test.custom_instance_class is W_Test
    assert k_Test.methods.keys() == ['foo']
    assert k_Test.methods['foo'] is k_Base.methods['foo']
    k_Test.validate()

    class W_Test2(W_Test):
        pass
    k_Test2 = BuiltinClass('Test2', extends=k_Test, instance_class=W_Test2)
    assert k_Test2.custom_instance_class is W_Test2
    k_Test2.validate()

    class W_Test3(W_InstanceObject):
        pass
    with py.test.raises(AssertionError):
        BuiltinClass('Test2', extends=k_Test, instance_class=W_Test3)

def test_BuiltinClass_implements():
    k_IFoo = BuiltinClass('IFoo',
        [new_abstract_method(['interp'], name="IFoo::Foo")],
        flags=consts.ACC_INTERFACE | consts.ACC_ABSTRACT)

    @wrap_method([], 'Foo::Foo')
    def Foo():
        return W_IntObject(42)
    k_Foo = BuiltinClass('Foo', [Foo], implements=[k_IFoo])
    assert k_IFoo in k_Foo.immediate_parents
    k_Foo.validate()

    with py.test.raises(ClassDeclarationError):
        k_Test = BuiltinClass('Test', [], implements=[k_IFoo])
        k_Test.validate()

def test_BuiltinClass_dummy_method():
    k_Test = BuiltinClass('Test', ['foo', 'bar'])
    assert k_Test.methods['foo'] is None

def test_def_method():
    k_Test = BuiltinClass('Test', ['foo', 'Bar'])

    @k_Test.def_method([str])
    def Foo(x):
        return x
    assert k_Test.methods['foo'].repr() == 'Test::Foo()'

    @k_Test.def_method([str], name='bar')
    def xxx(x):
        return x
    assert k_Test.methods['bar'].repr() == 'Test::bar()'

    with py.test.raises(ValueError):
        @k_Test.def_method([str])
        def Baz(x):
            return x

    with py.test.raises(ValueError) as excinfo:
        @k_Test.def_method([str])
        def FoO(x):
            return x
    assert (excinfo.value.message ==
            "Duplicate implementation for method Test::FoO()!")

def test_def_method_ctor():
    k_Test = BuiltinClass('Test', ['__construct'])

    @k_Test.def_method([str])
    def __construct(x):
        return x
    assert k_Test.constructor_method.method_func.runner.ll_func is __construct


def test_subclass_builtin():
    class W_BaseStuff(W_InstanceObject):
        def setup(self, interp):
            self.name = 'base'

    class W_DerivedStuff(W_BaseStuff):
        def setup(self, interp):
            W_BaseStuff.setup(self, interp)
            self.name2 = 'derived'

    def get_name(interp, this):
        return interp.space.newstr(this.name)

    def set_name(interp, this, w_value):
        this.name = interp.space.str_w(w_value)

    def get_name2(interp, this):
        return interp.space.newstr(this.name2)

    def set_name2(interp, this, w_value):
        this.name2 = interp.space.str_w(w_value)

    k_BaseStuff = BuiltinClass('BaseStuff',
        properties=[GetterSetterWrapper(get_name, set_name,
                                        'name', consts.ACC_PRIVATE)],
        instance_class=W_BaseStuff)
    k_DerivedStuff = BuiltinClass('DerivedStuff',
        properties=[GetterSetterWrapper(get_name2, set_name2,
                                        'name2', consts.ACC_PRIVATE)],
        extends=k_BaseStuff,
        instance_class=W_DerivedStuff)
    interp = Interpreter(getspace())
    w_obj = k_DerivedStuff.call_args(interp, [])
    names = []
    w_obj.enum_properties(interp, names, [])
    assert '\0BaseStuff\0name' in names


def test_validate_builtin_classes():
    assert len(all_builtin_classes) > 20  # make sure we've actually loaded the classes
    for klass in all_builtin_classes.itervalues():
        klass.validate()


class TestKlass(BaseTestInterpreter):

    def test_undefined_property_1(self):
        with self.warnings(['Notice: Undefined property: A::$fooBaz']):
            self.run('''
            class A {}
            $a = new A;
            $a->fooBaz;
            ''')

    def test_undefined_property_2(self):
        self.run('''
        class A {}
        $a = new A;
        $x =& $a->fooBaz;
        ''', [])    # no warning

    def test_append_fatal(self):
        with self.warnings(['Fatal error: '
                'Cannot use object of type A as array']):
            self.run('''
            class A {}
            $a = new A;
            $a[] = 1;
            ''')

    def test_append_undefined_property(self):
        with self.warnings(['Hippy warning: Creating array from empty value']):
            output = self.run('''
            class A {}
            $a = new A;
            $a->foo[] = 1;
            echo $a->foo[0];
            ''')
        assert self.space.int_w(output[0]) == 1

    def test_getattr_ordering(self):
        output = self.run('''
        class A {};
        $a = new A; $a->bar = 0;
        $b = new A; $b->bar = 1;
        function f() {
            global $a, $b;
            $a = $b;
            return "bar";
        }
        echo $a->{f()};
        ''')
        assert self.space.int_w(output[0]) == 1

    def test_setattr_ordering_1(self):
        output = self.run('''
        class A {};
        $a = new A; $a->bar = 0;
        $b = new A; $b->bar = 1;
        function f() {
            global $a, $b;
            $a = $b;
            return "bar";
        }
        echo $a->{f()} = 10;
        echo $b->bar;
        ''')
        assert [self.space.int_w(i) for i in output] == [10, 10]

    def test_setattr_ordering_2(self):
        output = self.run('''
        class A {};
        $a = new A; $a->bar1 = 1; $a->bar2 = 2;
        $n = "bar1";
        echo $a->{++$n} = $n;
        echo $a->bar1, $a->bar2;
        ''')
        assert [self.space.str_w(i) for i in output] == ["bar2", "1", "bar2"]

    @hippy_fail(reason="obscure ordering issue, ignoring it is probably fine")
    def test_setattr_ordering_3(self):
        output = self.run('''
        class A {};
        $a = new A; $a->bar1 = 1; $a->bar2 = 2;
        $n = "bar1";
        echo $a->{$n} = ++$n;
        echo $a->bar1, $a->bar2;
        ''')
        assert [self.space.str_w(i) for i in output] == ["bar2", "1", "bar2"]

    def test_setattr_ordering_4(self):
        output = self.run('''
        class A {};
        $a = new A; $a->bar1 = 1; $a->bar2 = 2;
        $n = "bar0";
        echo $a->{++$n} = ++$n;
        echo $a->bar1, $a->bar2;
        ''')
        assert [self.space.str_w(i) for i in output] == ["bar2", "bar2", "2"]

    def test_attr_ref(self):
        output = self.run('''
        class X {};
        $x = new X;
        $y = &$x->foo;
        $y = 42;
        echo $x->foo;
        ''')
        assert self.space.int_w(output[0]) == 42

    def test_setattr_setitem(self):
        output = self.run('''
        class X {};
        $x = new X;
        $x->a = array(10, 20, 30);
        echo $x->a[1];
        $x->a[1] = 100;
        echo $x->a[1];
        echo --$x->a[2];
        echo $x->a[2];
        ''')
        assert [self.space.int_w(i) for i in output] == [20, 100, 29, 29]

    def test_setattr_scalar(self):
        with self.warnings(['Warning: '
                'Attempt to assign property of non-object'] * 3):
            output = self.run('''
            $a = 1;
            echo $a->x = 5;
            echo $a;
            $b = 1.;
            echo $b->x = 5;
            echo $b;
            $c = '0';
            echo $c->x = 5;
            echo $c;
            ''')
        space = self.space
        for out, expected in zip(output, [space.w_Null, space.newint(1),
                space.w_Null, space.newfloat(1.),
                space.w_Null, space.wrap('0')]):
            assert space.is_w(out, expected)

    def test_setattr_byref_scalar(self):
        with self.warnings(['Warning: '
                'Attempt to modify property of non-object'] * 3):
            output = self.run('''
            $a = 1;
            $x = 5;
            echo $a->x =& $x;
            echo $a;
            $b = 1.;
            echo $b->x =& $x;
            echo $b;
            $c = '0';
            echo $c->x =& $x;
            echo $c;
            ''')
        space = self.space
        for out, expected in zip(output, [space.w_Null, space.newint(1),
                space.w_Null, space.newfloat(1.),
                space.w_Null, space.wrap('0')]):
            assert space.is_w(out, expected)

    def test_setattr_creates_stdClass(self):
        with self.warnings(['Warning: '
                'Creating default object from empty value'] * 3):
            output = self.run('''
            $x->foo = 5;
            echo $x;
            $y = false;
            $y->foo = 6;
            echo $y;
            $z = '';
            $z->foo = 7;
            echo $z;
            ''')
        assert self.is_object(output[0], 'stdClass',
                [('foo', self.space.newint(5))])
        assert self.is_object(output[1], 'stdClass',
                [('foo', self.space.newint(6))])
        assert self.is_object(output[2], 'stdClass',
                [('foo', self.space.newint(7))])

    def test_setattr_via_ref_creates_stdClass(self):
        with self.warnings(['Hippy warning: '
                'Creating default object from empty value']):
            output = self.run('''
            function f(&$x) {
                $x = 5;
            }
            f($x->foo);
            echo $x;
            ''')
        assert self.is_object(output[0], 'stdClass',
                [('foo', self.space.newint(5))])

    def test_setattr_byref_creates_stdClass(self):
        with self.warnings(['Hippy warning: '
                'Creating default object from empty value'] * 3):
            output = self.run('''
            $a = 0;
            $x->foo =& $a;
            $a++;
            echo $x;
            $b = 0;
            $y = false;
            $y->foo =& $b;
            $b++;
            echo $y;
            $c = 0;
            $z = '';
            $z->foo =& $c;
            $c++;
            echo $z;
            ''')
        assert self.is_object(output[0], 'stdClass',
                [('foo', self.space.newint(1))])
        assert self.is_object(output[1], 'stdClass',
                [('foo', self.space.newint(1))])
        assert self.is_object(output[2], 'stdClass',
                [('foo', self.space.newint(1))])

    def test_getattr_getitem_ref(self):
        output = self.run('''
        class X {};
        $x = new X;
        $x->a = array(10, 20, 30);
        $b = &$x->a[1];
        $b = 50;
        echo $x->a[1];
        $x->a[1] = 60;
        echo $b;
        ''')
        assert [self.space.int_w(i) for i in output] == [50, 60]

    def test_getattr_is_byref(self):
        output = self.run('''
        class X {};
        $x = new X;
        function f(&$x) { $x = 5; }
        f($x->a);
        echo $x->a;
        echo ++$x->a;
        echo $x->a;
        ''')
        assert [self.space.int_w(i) for i in output] == [5, 6, 6]

    def test_getattr_getitem_is_byref(self):
        output = self.run('''
        class X {};
        $x = new X;
        $x->a = array(-1);
        function f(&$x) { $x = 5; }
        f($x->a[0]);
        echo $x->a[0];
        echo ++$x->a[0];
        echo $x->a[0];
        ''')
        assert [self.space.int_w(i) for i in output] == [5, 6, 6]

    def test_getattr_byref_scalar(self):
        with self.warnings(['Warning: '
                'Attempt to modify property of non-object'] * 3):
            output = self.run('''
            $a = 1;
            echo $x =& $a->x;
            echo $a;
            $b = 1.;
            echo $x =& $b->x;
            echo $b;
            $c = '0';
            echo $x =& $c->x;
            echo $c;
            ''')
        space = self.space
        for out, expected in zip(output, [space.w_Null, space.newint(1),
                space.w_Null, space.newfloat(1.),
                space.w_Null, space.wrap('0')]):
            assert space.is_w(out, expected)

    def test_getattr_byref_creates_stdClass(self):
        with self.warnings(['Hippy warning: '
                'Creating default object from empty value'] * 3):
            output = self.run('''
            $a =& $x->foo;
            $a = 1;
            echo $x;
            $y = false;
            $b =& $y->foo;
            $b = 1;
            echo $y;
            $z = '';
            $c =& $z->foo;
            $c = 1;
            echo $z;
            ''')
        assert self.is_object(output[0], 'stdClass',
                [('foo', self.space.newint(1))])
        assert self.is_object(output[1], 'stdClass',
                [('foo', self.space.newint(1))])
        assert self.is_object(output[2], 'stdClass',
                [('foo', self.space.newint(1))])

    def test_bogus_getattr(self):
        with self.warnings(['Notice: '
                'Trying to get property of non-object'] * 2):
            output = self.run('''
            $a = 1;
            echo $a->foo;
            echo $b = $a->foo;
            echo $a;
            echo $b;
            ''')
        space = self.space
        for out, expected in zip(output,
                [space.w_Null, space.w_Null, space.newint(1), space.w_Null]):
            assert space.is_w(out, expected)

    @hippy_fail(reason="wrong warnings")
    def test_inplace_ops_on_bogus_getattr(self):
        with self.warnings() as w:
            output = self.run('''
            $a = 1;
            echo $a->foo++;
            echo ++$a->foo;
            echo $a->foo--;
            echo --$a->foo;
            echo $a->foo += 2;
            echo $a;
            ''')
        for out in output[:-1]:
            assert self.space.is_w(out, self.space.w_Null)
        assert self.space.is_w(output[-1], self.space.newint(1))
        msg = (
        4*['Warning: Attempt to increment/decrement property of non-object']+
            ['Warning: Attempt to assign property of non-object'])
        assert w == msg

    def test_call_method_minimal(self):
        output = self.run('''
        class X { function foo() { return 42; } }
        $x = new X;
        echo $x->foo();
        ''')
        assert self.space.int_w(output[0]) == 42

    def test_call_method_lowerupper(self):
        output = self.run('''
        class X { function Foo() { return 42; } }
        $x = new X;
        echo $x->foo();
        echo $x->Foo();
        ''')
        assert [self.space.int_w(i) for i in output] == [42, 42]

    def test_call_method_this(self):
        output = self.run('''
        class X { function foo() { return $this->value * 7; } }
        $x = new X;
        $x->value = 6;
        echo $x->foo();
        ''')
        assert self.space.int_w(output[0]) == 42

    def test_call_method_ordering_1(self):
        output = self.run('''
        class X { function foo($ignored) { return $this->value * 7; } }
        $x = new X; $x->value = 6;
        $y = new X; $y->value = 600;
        echo $x->foo($x=&$y);
        ''')
        assert self.space.int_w(output[0]) == 42

    def test_call_method_ordering_2(self):
        output = self.run('''
        class X { function foo($m) { return $this->value * $m; } }
        $x = new X; $x->value = 6;
        echo $x->foo($x=7);
        ''')
        assert self.space.int_w(output[0]) == 42

    def test_call_method_too_many_args(self):
        output = self.run('''
        class X { function foo($x, $y) { return ($x - $y) * $this->z; } }
        $x = new X; $x->z = 7;
        echo $x->foo(10, 4, 999, 888);
        ''')
        assert self.space.int_w(output[0]) == 42

    def test_call_method_inherited_1(self):
        output = self.run('''
        class X { function foo($x) { return $x * 6; } }
        class Y extends X { }
        $y = new Y;
        echo $y->foo(7);
        ''')
        assert self.space.int_w(output[0]) == 42

    def test_call_method_inherited_2(self):
        output = self.run('''
        class X {
            function foo($x) { return $this->bar($x); }
            function bar($x) { explode; }
        }
        class Y extends X {
            function bar($x) { return $x * 6; }
        }
        $y = new Y;
        echo $y->foo(7);
        ''')
        assert self.space.int_w(output[0]) == 42

    def test_call_method_protected_1(self):
        output = self.run('''
        class X {
            protected function foo($y) { return $this->x * $y; }
            public function bar($y) { return $this->a + $this->foo($y); }
        }
        $x = new X; $x->x = 100; $x->a = 10;
        echo $x->bar(3);
        ''')
        assert self.space.int_w(output[0]) == 10 + (100 * 3)

    def test_call_method_protected_2(self):
        output = self.run('''
        class Base {
            protected function foo($y) { return $this->x * $y; }
        }
        class X extends Base {
            public function bar($y) { return $this->a + $this->foo($y); }
        }
        $x = new X; $x->x = 100; $x->a = 10;
        echo $x->bar(3);
        ''')
        assert self.space.int_w(output[0]) == 10 + (100 * 3)

    def test_call_method_protected_3(self):
        self.run('''
        class X {
            protected function foo($y) { return $this->x * $y; }
        }
        $x = new X;
        $x->foo(3);
        ''', ["Fatal error: Call to protected method X::foo() "
              "from context ''"])

    def test_call_method_protected_4(self):
        self.run('''
        class X {
            protected function foo($y) { return $this->x * $y; }
        }
        class Y {
            public function bar($x, $y) { return $x->foo($y); }
        }
        $y = new Y;
        $y->bar(new X, 3);
        ''', ["Fatal error: Call to protected method X::foo() "
              "from context 'Y'"])

    def test_call_method_private_1(self):
        output = self.run('''
        class X {
            private function foo($y) { return $this->x * $y; }
            public function bar($y) { return $this->a + $this->foo($y); }
        }
        $x = new X; $x->x = 100; $x->a = 10;
        echo $x->bar(3);
        ''')
        assert self.space.int_w(output[0]) == 10 + (100 * 3)

    def test_call_method_private_2(self):
        output = self.run('''
        class X {
            private function foo($y) { return $this->x * $y; }
            public function bar($y) { return $this->a + $this->foo($y); }
        }
        class Y extends X {
            private function foo($z) { explode; }
        }
        $y = new Y; $y->x = 100; $y->a = 10;
        echo $y->bar(3);
        ''')
        assert self.space.int_w(output[0]) == 10 + (100 * 3)

    def test_call_method_private_3(self):
        self.run('''
        class X {
            public function bar($y) { return $this->a + $this->foo($y); }
        }
        class Y extends X {
            private function foo($z) { explode; }
        }
        $y = new Y; $y->x = 100; $y->a = 10;
        echo $y->bar(3);
        ''', ["Fatal error: Call to private method Y::foo() from context 'X'"])

    def test_call_method_private_4(self):
        self.run('''
        class A {
            private function foo($z) { explode; }
        }
        class B extends A {
        }
        $b = new B;
        echo $b->foo(3);
        ''', ["Fatal error: Call to private method A::foo() from context ''"])

    def test_call_method_undefined(self):
        self.run('''
        class A { }
        $a = new A;
        $a->foo(3);
        ''', ["Fatal error: Call to undefined method A::foo()"])

    @py.test.mark.parametrize('value',
            ['true', 'false', 'null', '1', '1.', '"abc"', 'array(1, 2)'])
    def test_call_method_nonobject(self, value):
        with self.warnings(["Fatal error: "
            "Call to a member function foo() on a non-object"]):
            self.run('''
            $x = %s;
            $x->foo();
            ''' % value)

    def test_bogus_getmeth1(self):
        with self.warnings(['Fatal error: Cannot use [] for reading']):
            output = self.run('''
            $x[]->foo();
            ''')

    def test_bogus_getmeth2(self):
        with self.warnings(['Notice: Undefined variable: x',
                'Fatal error: Call to a member function foo() on a non-object']):
            output = self.run('''
            $x[1]->foo();
            ''')

    def test_bogus_getmeth3(self):
        with self.warnings(['Notice: Undefined variable: x',
                'Notice: Trying to get property of non-object',
                'Fatal error: Call to a member function foo() on a non-object']):
            output = self.run('''
            $x->y->foo();
            ''')

    def test_method_of_attr(self):
        output = self.run('''
        class A {
            function foo() {return 5;}
        }
        $x = new A;
        echo $x->foo();
        $x->y = new A;
        echo $x->y->foo();
        ''')
        assert map(self.space.int_w, output) == [5, 5]

    def test_call_method_indirect(self):
        output = self.run('''
        class A { function f() { return 42; } }
        $n = "f";
        $a = new A;
        echo $a->$n();
        ''')
        assert self.space.int_w(output[0]) == 42

    def test_call_method_static_1(self):
        output = self.run('''
        class A { static function f() { return $this; } }
        echo A::f();
        $a = new A;
        echo $a->f();
        ''', [
            'Notice: Undefined variable: this',
            'Notice: Undefined variable: this'])
        assert output[0] == self.space.w_Null
        assert output[1] == self.space.w_Null

    def test_call_method_static_2(self):
        output = self.run('''
        class A { function f() { return $this; } }    // no "static"!
        echo A::f();
        ''', ['Strict Standards: Non-static method A::f() should not '
              'be called statically',
              'Notice: Undefined variable: this'])
        assert output[0] == self.space.w_Null

    def test_call_method_static_3(self):
        with self.warnings(['Strict Standards: '
                'Non-static method A::f() should not be called statically',
                "Fatal error: Using $this when not in object context"]):
            self.run('''
            class A { function f() { $this->x = 5; } }
            A::f();
            ''')

    def test_call_method_static_4(self):
        output = self.run('''
        class A { static function f() { return 42; } }
        $c = "A";
        $n = "f";
        echo A::f(), $c::f(), A::$n(), $c::$n();
        ''')
        assert [self.space.int_w(i) for i in output] == [42, 42, 42, 42]

    def test_call_method_static_5(self):
        output = self.run('''
        class A { function f() { return $this->x; } }
        class B { function g() { return A::f(); } }
        $b = new B;
        $b->x = 42;
        echo $b->g();
        ''', ['Strict Standards: Non-static method A::f() should not '
              'be called statically, assuming $this from incompatible '
              'context'])
        assert self.space.int_w(output[0]) == 42      # duh

    def test_static_this(self):
        output = self.run("""
        class A {
            static function test($this) {return $this;}
        }
        $x = 42;
        echo A::test($x);
        """)
        assert [self.space.int_w(out) for out in output] == [42]
        self.run("""
        class A {
            static function test($this) {return $this->x;}
        }
        $a = new A;
        """)  # no failure
        with self.warnings([
                "Fatal error: Using $this when not in object context"]):
            self.run("""
            class A {
                static function test($this) {return $this->x;}
            }
            $x = new stdClass;
            $x->x = 42;
            echo A::test($x);
            """)

    def test_call_method_static_private(self):
        self.run('''
        class A { private static function f() { } }
        A::f();
        ''', ["Fatal error: Call to private method A::f() from context ''"])
        self.run('''
        class A { private static function f() { }
                  public static function g() { A::f(); } }
        A::g();
        ''', [])
        output = self.run('''
        class A { private static function f() { echo "A"; }
                  public static function g() { A::f(); } }
        class B extends A { private static function f() { echo "B"; } }
        A::g();
        B::g();
        ''', [])
        assert [self.space.str_w(i) for i in output] == ["A", "A"]
        self.run('''
        class A { private static function f() { echo "A"; }
                  public static function g() { B::f(); } }
        class B extends A { private static function f() { echo "B"; } }
        $b = new B;
        $b->g();
        ''', ["Fatal error: Call to private method B::f() from context 'A'"])

    def test_call_method_static_protected(self):
        self.run('''
        class A { protected static function f() { } }
        A::f();
        ''', ["Fatal error: Call to protected method A::f() from context ''"])
        self.run('''
        class A { protected static function f() { }
                  public static function g() { A::f(); } }
        A::g();
        ''', [])

    def test_property_implicit(self):
        output = self.run('''
        class A { }
        $a = new A;
        $a->c = 18;
        echo $a;
        ''')
        assert self.is_object(output[0], 'A',
                              [('c', self.space.newint(18))])

    def test_property_public_1(self):
        output = self.run('''
        class A {
            public $a, $b=5;
        }
        $a = new A;
        $a->c = 18;
        echo $a;
        ''')
        assert self.is_object(output[0], 'A',
                              [('a', self.space.w_Null),
                               ('b', self.space.newint(5)),
                               ('c', self.space.newint(18))])

    def test_property_public_2(self):
        output = self.run('''
        class A { public $a=2; }
        class B extends A { public $b=4; }
        class C extends B { public $c=6; }
        $c = new C;
        echo $c;
        ''')
        assert self.is_object(output[0], 'C',
                              [('c', self.space.newint(6)),
                               ('b', self.space.newint(4)),
                               ('a', self.space.newint(2))])

    def test_property_protected_1(self):
        output = self.run('''
        class A { protected $a=5; }
        $a = new A;
        echo $a;
        ''')
        assert self.is_object(output[0], 'A',
                              [('\x00*\x00a', self.space.newint(5))])

    def test_property_protected_2(self):
        output = self.run('''
        class A {
            protected $a;
            function foo() { $this->a=5; return $this->a * 2; }
        }
        $a = new A;
        echo $a->foo();
        echo $a;
        ''')
        assert self.space.is_w(output[0], self.space.newint(10))
        assert self.is_object(output[1], 'A',
                              [('\x00*\x00a', self.space.newint(5))])

    def test_property_protected_3(self):
        output = self.run('''
        class A { protected $a; }
        class B extends A {
            function foo() { $this->a=5; return $this->a * 2; }
        }
        $b = new B;
        echo $b->foo();
        echo $b;
        ''')
        assert self.space.is_w(output[0], self.space.newint(10))
        assert self.is_object(output[1], 'B',
                              [('\x00*\x00a', self.space.newint(5))])

    def test_property_protected_4(self):
        output = self.run('''
        class A { protected $a; }
        $a = new A;
        $a->a = 42;
        ''', ["Fatal error: Cannot access protected property A::$a"])

    def test_property_private_1(self):
        output = self.run('''
        class A { private $bar=5; }
        $a = new A;
        echo $a;
        ''')
        assert self.is_object(output[0], 'A',
                              [('\x00A\x00bar', self.space.newint(5))])

    def test_property_private_2(self):
        output = self.run('''
        class A {
            private $a;
            function foo() { $this->a=5; return $this->a * 2; }
        }
        $a = new A;
        echo $a->foo();
        echo $a;
        ''')
        assert self.space.is_w(output[0], self.space.newint(10))
        assert self.is_object(output[1], 'A',
                              [('\x00A\x00a', self.space.newint(5))])

    def test_property_private_3(self):
        output = self.run('''
        class A {
            private $a = 3;
            function foo() { $this->a=5; return $this->a * 2; }
        }
        class B extends A {
            private $a = 12;
            function bar() { $this->a=15; return $this->a * 2; }
        }
        $b = new B;
        echo $b;
        $b = new B;
        echo $b->foo();
        echo $b;
        $b = new B;
        $b->foo();
        echo $b->bar();
        echo $b;
        ''')
        assert self.is_object(output[0], 'B',
                              [('\x00B\x00a', self.space.newint(12)),
                               ('\x00A\x00a', self.space.newint(3))])
        assert self.space.is_w(output[1], self.space.newint(10))
        assert self.is_object(output[2], 'B',
                              [('\x00B\x00a', self.space.newint(12)),
                               ('\x00A\x00a', self.space.newint(5))])
        assert self.space.is_w(output[3], self.space.newint(30))
        assert self.is_object(output[4], 'B',
                              [('\x00B\x00a', self.space.newint(15)),
                               ('\x00A\x00a', self.space.newint(5))])

    def test_property_unset(self):
        output = self.run('''
        class B {
            protected $baz, $bar = "bar1";
            public function kill_bar() {
                unset($this->bar);
            }
        }
        $b = new B;
        $b->kill_bar();
        echo $b;
        ''')
        assert self.is_object(output[0], 'B',
                              [('\x00*\x00baz', self.space.w_Null)])

    def test_property_unset_protected(self):
        output = self.run('''
        class A { protected $a; }
        $a = new A;
        unset($a->a);
        ''', ["Fatal error: Cannot access protected property A::$a"])

    def test_property_sample_1(self):
        output = self.run('''
        class Base {
            private $bar;
            public function stuff($a, $b) {
                $a->bar = $b;
            }
        }
        class C extends base {
            protected $bar;
            public function set($x) {
                $this->bar = $x;
            }
        }
        class D extends C {
            public $bar;
        }
        class Unrelated { public $bar; }

        $d = new D;
        $u = new unrelated;
        $d->stuff($u, 40);
        $d->stuff($d, 20);
        $d->set("hi");
        echo $d, $u;
        ''')
        assert self.is_object(output[0], 'D',
                              [('bar', self.space.newstr("hi")),
                               ('\x00Base\x00bar', self.space.newint(20))])
        assert self.is_object(output[1], 'Unrelated',
                              [('bar', self.space.newint(40))])

    def test_property_sample_2(self):
        output = self.run('''
        class SuperBase {
        }
        class Base extends SuperBase {
            private $bar;
            public function foo($a) {
                $a->bar = 42;
            }
        }
        $a = new Base;
        $b = new SuperBase;
        $a->foo($b);
        echo $b;
        ''')
        assert self.is_object(output[0], 'SuperBase',
                              [('bar', self.space.newint(42))])

    def test_property_sample_3(self):
        output = self.run('''
        class B {
        }
        class C extends B {
            private $bar;
            public function foo($x) {
                unset($x->bar);
                $x->bar = 42;
            }
        }
        class D extends C {
        }
        $d = new D;
        $c = new C;
        $c->foo($d);
        echo $d;
        ''')
        assert self.is_object(output[0], 'D',
                              [('\x00C\x00bar', self.space.newint(42))])

    def test_property_static_1(self):
        output = self.run('''
        class A { static $num = 10; }
        $a = new A;
        echo $a;
        ''')
        assert self.is_object(output[0], 'A', [])

    def test_property_static_2(self):
        output = self.run('''
        class A { static $num = 10; }
        echo A::$num;
        ''')
        assert self.space.int_w(output[0]) == 10

    def test_property_static_3(self):
        output = self.run('''
        class A {
            private static $num = 10;
            public function foo() {
                echo A::$num;
                return ++A::$num;
            }
        }
        $a = new A;
        $a->foo();
        $a->foo();
        echo $a->foo();
        ''')
        assert [self.space.int_w(i) for i in output] == [10, 11, 12, 13]

    def test_property_static_4(self):
        output = self.run('''
        class A { public static $num = 3; }
        $a = 10;
        A::$num =& $a;
        A::$num++;
        echo $a;
        ''')
        assert self.space.int_w(output[0]) == 11

    def test_separate_static_property(self):
        output = self.run('''
        class Base { public static $x = 5; }
        class Derived extends Base {}
        echo Derived::$x;
        Derived::$x = 6;
        echo Base::$x;
        $new_x = 7;
        Derived::$x =& $new_x;
        echo Base::$x;
        echo Derived::$x;
        ''')
        for w_res, n in zip(output, [5, 6, 6, 7]):
            assert w_res == W_IntObject(n)

    def test_property_double_dollar(self):
        output = self.run('''
        class A { }
        $a = new A;
        $x = "foobar";
        $a->$x = 42;
        echo $a->foobar;
        echo $a->$x;
        $a->{"ab" . "c"} = 43;
        echo $a->abc;
        echo $a->{"a" . "bc"};
        ''')
        assert [self.space.int_w(i) for i in output] == [42, 42, 43, 43]

    def test_property_static_double_dollar(self):
        output = self.run('''
        class A { public static $num = 3; }
        $name = "num";
        echo A::$$name++;
        echo A::$$name;
        echo ++A::$$name;
        ''')
        assert [self.space.int_w(i) for i in output] == [3, 4, 5]

    def test_property_static_variable_class(self):
        output = self.run('''
        class A { public static $num = 5; }
        class B { public static $num = 15; }
        $name = "A";
        echo $name::$num++, $name::$num;
        $name = "B";
        echo $name::$num++, $name::$num;
        ''')
        assert [self.space.int_w(i) for i in output] == [5, 6, 15, 16]

    def test_object_identity(self):
        output = self.run('''
        class A { }
        $a1 = new A;
        $a2 = new A;
        echo $a1 === $a1, $a1 === $a2;
        ''')
        assert [self.space.int_w(i) for i in output] == [1, 0]

    def test_object_equality_1(self):
        output = self.run('''
        class A { }
        $a1 = new A;
        $a2 = new A;
        echo $a1 == $a2;
        $a1->x = 42;
        echo $a1 == $a2;
        $a2->x = 40 + 2;
        echo $a1 == $a2;
        ''')
        assert [self.space.int_w(i) for i in output] == [1, 0, 1]

    def test_object_equality_2(self):
        output = self.run('''
        class A { }
        class B { }
        $a = new A;
        $b = new B;
        echo $a == $a, $a == $b;
        ''')
        assert [self.space.int_w(i) for i in output] == [1, 0]

    def test_object_equality_3(self):
        output = self.run('''
        class A { }
        $a1 = new A;
        $a2 = new A;
        $a1->x = 42; $a1->y = 42;
        $a2->y = 42; $a2->x = 42;
        echo $a1 == $a2;
        ''')
        assert [self.space.int_w(i) for i in output] == [1]

    def test_stdClass(self):
        output = self.run('''
        $a = (object)42.5;
        echo $a;
        ''')
        assert self.is_object(output[0], 'stdClass',
                              [('scalar', self.space.newfloat(42.5))])

    def test_stdClass_from_object(self):
        output = self.run('''
        class A { }
        $a = new A;
        echo $a === (object)$a;
        ''')
        assert self.space.int_w(output[0]) == 1

    def test_stdClass_from_array(self):
        output = self.run('''
        $b = array(5, "a"=>"c");
        $a = (object)$b;
        echo $a;
        ''')
        assert self.is_object(output[0], 'stdClass',
                              [('0', self.space.newint(5)),
                               ('a', self.space.newstr('c'))])

    def test_stdClass_from_null(self):
        output = self.run('''
        $a = (object)NULL;
        echo $a;
        ''')
        assert self.is_object(output[0], 'stdClass', [])

    def test_magic_name_new(self):
        output = self.run('''
        class A {
            function f1() { return new self; }      // A
            function f2() { return new static; }    // $myclass
        }
        class B extends A {
            function f3() { return new parent; }    // A
        }
        $a = new A;
        echo $a->f1(), $a->f2();
        $b = new B;
        echo $b->f1(), $b->f2(), $b->f3();
        ''')
        assert self.is_object(output[0], 'A', [])
        assert self.is_object(output[1], 'A', [])
        assert self.is_object(output[2], 'A', [])
        assert self.is_object(output[3], 'B', [])
        assert self.is_object(output[4], 'A', [])

    def test_magic_name_super_method(self):
        output = self.run('''
        class A {
            function f() { return 6; }
        }
        class B extends A {
            function f() { return parent::f() * 7; }
        }
        $b = new B;
        echo $b->f();
        ''')
        assert self.space.int_w(output[0]) == 42

    def test_magic_name_fixed_method(self):
        output = self.run('''
        class A {
            function f1() { return self::g(); }    // A::g()
            function f2() { return static::g(); }  // $class::g()
            function g() { return 6; }
        }
        class B extends A {
            function g() { return 7; }
        }
        $b = new B;
        echo $b->f1(), $b->f2();
        ''')
        assert [self.space.int_w(i) for i in output] == [6, 7]

    def test_magic_name_static_member(self):
        output = self.run('''
        class A {
            static $num = 10;
            function f1() { return self::$num; }    // A::$num
            function f2() { return static::$num; }  // $myclass::$num
        }
        class B extends A {
            static $num = 40;
            function f3() { return parent::$num; }  // A::$num
        }
        $a = new A;
        echo $a->f1(), $a->f2();
        $b = new B;
        echo $b->f1(), $b->f2(), $b->f3();
        ''')
        assert [self.space.int_w(i) for i in output] == [10, 10, 10, 40, 10]

    def test_magic_name_static_method(self):
        output = self.run('''
        class A {
            static $num = 10;
            static function f() { return static::$num; }
        }
        class B extends A {
            static $num = 40;
        }
        echo A::f(), B::f();
        ''')
        assert [self.space.int_w(i) for i in output] == [10, 40]

    def test_magic_name_error(self):
        self.run('self::$num;',
                 ["Fatal error: Cannot access self:: when no class scope "
                  "is active"])
        self.run('parent::$num;',
                 ["Fatal error: Cannot access parent:: when no class scope "
                  "is active"])
        self.run('static::$num;',
                 ["Fatal error: Cannot access static:: when no class scope "
                  "is active"])
        self.run('''
        class A { function f() { return parent::$num; } }
        $a = new A;
        $a->f();
        ''', ["Fatal error: Cannot access parent:: when current class scope "
              "has no parent"])
        self.run('class self { }',
                 ["Fatal error: Cannot use 'self' as class name as it is "
                  "reserved"])
        self.run('class parent { }',
                 ["Fatal error: Cannot use 'parent' as class name as it is "
                  "reserved"])
        self.run('class A {}; class A {}',
                 ["Fatal error: Cannot redeclare class A"])

    def test_this_strangeness(self):
        output = self.run('''
        class X {
            function foo() {
                $a = "this";
                $$a = 42;
                $this += 2;
                echo $this;
                $this->attr = 42;
            }
        };
        $x = new X;
        $x->foo();
        echo $x;
        ''')
        assert self.space.int_w(output[0]) == 44
        assert self.is_object(output[1], 'X',
                              [('attr', self.space.newint(42))])

    def test_shadow_this_method(self):
        output = self.run('''
        class X {
            function foo() {
                $a = "this";
                $$a = 42;
                echo $this->bar();
            }
            function bar() {
                return 5;
            }
        }
        $x = new X();
        $x->foo();
        ''')
        assert self.space.int_w(output[0]) == 5

    def test_const_on_class(self):
        output = self.run('''
        class Base {
            const x = 41;
        }
        class A extends Base {
            const x = 42;
            function foo() {
                echo B::x;
                echo Base::x;
                echo self::x;
                echo static::x;
                echo parent::x;
            }
        }
        class B extends A {
        }
        class C extends B {
            const x = 43;
        }
        $a = new A;
        $a->foo();
        $b = new B;
        $b->foo();
        $c = new C;
        $c->foo();
        ''')
        assert [self.space.int_w(i) for i in output] == [42, 41, 42, 42, 41,
                                                         42, 41, 42, 42, 41,
                                                         42, 41, 42, 43, 41]

    def test_new_indirect_1(self):
        output = self.run('''
        class A { }
        $name = "A";
        $a = new $name;
        echo $a;
        ''')
        assert self.is_object(output[0], 'A', [])

    def test_new_indirect_2(self):
        output = self.run('''
        class A { }
        $a = new A; $a->x = 42;
        $b = new $a;
        echo $b;
        ''')
        assert self.is_object(output[0], 'A', [])

    def test_new_constructor_1(self):
        output = self.run('''
        class A { function __construct($a) { $this->a = $a * 6; } }
        $a = new A(7);
        echo $a;
        ''')
        assert self.is_object(output[0], 'A',
                              [('a', self.space.newint(42))])

    def test_new_constructor_2(self):
        output = self.run('''
        class A {
            private function __construct($a) { $this->a = $a * 6; }
            static public function Amakeit() {
                return new A(7);
            }
            static public function Bmakeit() {
                return new B(7);
            }
        }
        class B extends A {
            public function __construct($a) { $this->a = -$a; }
        }
        echo new B(7);
        $a = A::Amakeit();
        echo $a;
        echo A::Bmakeit();
        echo $a->Amakeit();
        echo $a->Bmakeit();
        ''')
        assert self.is_object(output[0], 'B',
                              [('a', self.space.newint(-7))])
        assert self.is_object(output[1], 'A',
                              [('a', self.space.newint(42))])
        assert self.is_object(output[2], 'B',
                              [('a', self.space.newint(-7))])
        assert self.is_object(output[3], 'A',
                              [('a', self.space.newint(42))])
        assert self.is_object(output[4], 'B',
                              [('a', self.space.newint(-7))])

    def test_new_constructor_3(self):
        output = self.run('''
        class A { public function B() { echo "foo"; } }
        class B extends A { }
        $b = new B;
        echo "ok";
        ''')
        assert [self.space.str_w(i) for i in output] == ["ok"]

    def test_new_constructor_4(self):
        self.run('''
        class A { private function __construct() { } }
        $a = new A;
        ''', ["Fatal error: Call to private A::__construct() "
              "from invalid context"])
        #
        self.run('''
        class A { protected function __construct() { } }
        $a = new A;
        ''', ["Fatal error: Call to protected A::__construct() "
              "from invalid context"])
        #
        self.run('''
        class A { private function A() { } }
        $a = new A;
        ''', ["Fatal error: Call to private A::A() from invalid context"])
        #
        self.run('''
        class A { protected function A() { } }
        $a = new A;
        ''', ["Fatal error: Call to protected A::A() from invalid context"])
        #
        self.run('''
        class A { protected function A() { } }
        class B extends A { }
        $b = new B;
        ''', ["Fatal error: Call to protected A::A() from invalid context"])

    def test_new_constructor_5(self):
        output = self.run('''
        class A { protected function A() { } }
        class B extends A { static function doit() { return new B; } }
        $b = B::doit();
        echo $b;
        ''')
        assert self.is_object(output[0], 'B', [])

    def test_new_constructor_6(self):
        output = self.run('''
        class A { static function doit() { return new B; } }
        class B extends A { protected function B() { } }
        $b = A::doit();
        echo $b;
        ''')
        assert self.is_object(output[0], 'B', [])

    def test_new_constructor_7(self):
        output = self.run('''
        class A { function __construct(&$a) { $a *= 7; } }
        $x = 6;
        new A($x);
        echo $x;
        ''')
        assert self.space.int_w(output[0]) == 42

    def test_instanceof_1(self):
        output = self.run('''
        class A { }
        class B { }
        class C extends A { }
        $a = new A;
        echo $a instanceof A;
        echo $a instanceof B;
        echo $a instanceof C;
        echo $a instanceof NoSuchClass;
        $b = new B;
        echo $b instanceof A;
        echo $b instanceof B;
        echo $b instanceof C;
        echo $b instanceof NoSuchClass;
        $c = new C;
        echo $c instanceof A;
        echo $c instanceof B;
        echo $c instanceof C;
        echo $c instanceof NoSuchClass;
        ''')
        assert [self.space.int_w(i) for i in output] == [1, 0, 0, 0,
                                                         0, 1, 0, 0,
                                                         1, 0, 1, 0]

    def test_instanceof_2(self):
        output = self.run('''
        class A { }
        class B { }
        $a = new A;
        $a2 = new A;
        $b2 = new B;
        echo $a instanceof $a2;
        echo $a instanceof $b2;
        $a3 = "A";
        $b3 = "B";
        $c3 = "NoSuchClass";
        echo $a instanceof $a3;
        echo $a instanceof $b3;
        echo $a instanceof $b3;
        ''')
        assert [self.space.int_w(i) for i in output] == [1, 0,
                                                         1, 0, 0]

    def test_instanceof_3(self):
        output = self.run("""
        class A { }
        echo array() instanceof A;
        """)
        assert not self.space.is_true(output[0])

    def test_abstract_class(self):
        self.run('''
        abstract class X { }
        new X;
        ''', ["Fatal error: Cannot instantiate abstract class X"])
        #
        self.run('''
        abstract class X { abstract function f(); }
        abstract class Y extends X { }
        class Z extends Y { }
        ''', ["Fatal error: Class Z contains 1 abstract method and must "
              "therefore be declared abstract or implement "
              "the remaining methods (X::f)"])

    def test_final_class(self):
        self.run('''
        final class A { }
        class B extends A { }
        ''', ["Fatal error: Class B may not inherit from final class (A)"])
        #
        self.run('''
        class A { final function f() { } }
        class B extends A { function f() { } }
        ''', ["Fatal error: Cannot override final method A::f()"])

    def test_clone_1(self):
        output = self.run('''
        class A { public $v = 40; }
        $a = new A;
        $a->v++;
        $b = clone $a;
        echo $b;
        ''')
        assert self.is_object(output[0], 'A', [('v', self.space.newint(41))])

    def test_clone_2(self):
        output = self.run('''
        class A {
            public $v = 40;
            function __clone() {
                $this->v += 100;
            }
        }
        $a = new A;
        $a->v++;
        $b = clone $a;
        $c = clone $b;
        echo $c;
        ''')
        assert self.is_object(output[0], 'A', [('v', self.space.newint(241))])

    def test_clone_3(self):
        output = self.run('''
        class A { function __construct($n) { $this->n = $n; } }
        $a = new A(109);
        $a->b = new A(21);
        $a->b->c = new A(434);
        $aa = clone $a;
        $aa->b = 5;
        echo $a->b->n;
        ''')
        assert self.space.int_w(output[0]) == 21

    def test_clone_4(self):
        output = self.run('''
        class A { function __construct($n) { $this->n = $n; } }
        $a = new A(109);
        $a->b = new A(21);
        $aa = clone $a;
        $aa->b->n++;
        echo $a->b->n;   // $a->b was not cloned, so there is only one obj
        ''')
        assert self.space.int_w(output[0]) == 22

    def test_clone_nonreference_copied_by_value(self):
        """The difference between this test and the next one is a documented
        feature of PHP,
        see e.g. http://www.php.net/manual/en/language.oop5.cloning.php#91323
        """
        output = self.run('''
        class A {
            function __construct($n) { $this->n = $n; }
            function init($n) {$this->b = new A ($n);}
        }
        $a = new A(109);
        $b = new A(21);
        $a->b =& $b;
        unset($b);
        $aa = clone $a;
        $aa->init(22);
        echo $a->b->n;
        echo $aa->b->n;
        ''')
        assert self.space.int_w(output[0]) == 21
        assert self.space.int_w(output[1]) == 22

    @hippy_fail(reason="PHP is stupid")
    def test_clone_reference_copied_by_reference(self):
        output = self.run('''
        class A {
            function __construct($n) { $this->n = $n; }
            function init($n) {$this->b = new A ($n);}
        }
        $a = new A(109);
        $b = new A(21);
        $a->b =& $b;
        $aa = clone $a;
        $aa->init(22);
        echo $a->b->n;
        echo $aa->b->n;
        ''')
        assert self.space.int_w(output[0]) == 22
        assert self.space.int_w(output[1]) == 22

    def test_accepting_nonsense_to_assign_to_object_returned_by_value(self):
        self.run('''
        class A { function f() { } }
        $a = new A;
        $a->f()->b = 5;
        ''', ['Warning: Creating default object from empty value'])

    def test_simple_object_iteration_1(self):
        output = self.run('''
        class A {
            public $x = 4;
            protected $y = 5;
            private $z = 6;

            function Adoiter() {
                foreach ($this as $value) {
                    echo $value;
                }
                foreach ($this as $key => $value) {
                    echo $key;
                }
            }
        }
        class B extends A {
            function Bdoiter() {
                foreach ($this as $value) {
                    echo $value;
                }
                foreach ($this as $key => $value) {
                    echo $key;
                }
            }
        }
        $a = new A;
        $a->other = 7;
        foreach ($a as $value) {
            echo $value;
        }
        foreach ($a as $key => $value) {
            echo $key;
        }
        $a->Adoiter();
        $b = new B;
        $b->other = 8;
        $b->Adoiter();
        $b->Bdoiter();
        ''')
        assert [self.space.str_w(i) for i in output] == [
            "4", "7", "x", "other",
            "4", "5", "6", "7", "x", "y", "z", "other",
            "4", "5", "6", "8", "x", "y", "z", "other",
            "4", "5", "8", "x", "y", "other"]

    def test_simple_object_iteration_2(self):
        output = self.run('''
        class A {
            public $x = 4;
            protected $y = 5;
            private $z = 6;

            function Adoiter() {
                foreach ($this as &$value) {
                    echo $value += 10;
                }
                foreach ($this as $key => &$value2) {
                    echo $key, $value2;
                }
            }
        }
        class B extends A {
            function Bdoiter() {
                foreach ($this as &$value) {
                    echo $value += 100;
                }
                foreach ($this as $key => &$value2) {
                    echo $key, $value2;
                }
            }
        }
        $a = new A;
        $a->other = 7;
        foreach ($a as &$value) {
            echo $value += 1000;
        }
        foreach ($a as $key => &$value2) {
            echo $key, $value2;
        }
        $a->Adoiter();
        $b = new B;
        $b->other = 8;
        $b->Bdoiter();
        $b->Adoiter();
        ''')
        assert [self.space.str_w(i) for i in output] == [
            "1004", "1007", "x", "1004", "other", "1007",
            "1014", "15", "16", "1017",
                "x", "1014", "y", "15", "z", "16", "other", "1017",
            "104", "105", "108",
                "x", "104", "y", "105", "other", "108",
            "114", "115", "16", "118",
                "x", "114", "y", "115", "z", "16", "other", "118"]

    def test_overloading_get_1(self):
        output = self.run('''
        class X {
            private $foo = 42;
            public function __get($name) { return $this->foo; }
        }
        $x = new X;
        $y = &$x->foobar;
        echo $y++;
        $z = &$x->foobar;
        echo $z++;
        ''', 2 * ['Notice: Indirect modification of overloaded property '
                  'X::$foobar has no effect'])
        assert [self.space.int_w(i) for i in output] == [42, 42]

    def test_overloading_get_2(self):
        # note the "&__get" below
        output = self.run('''
        class X {
            private $foo = 42;
            public function &__get($name) { return $this->foo; }
        }
        $x = new X;
        $y = &$x->foobar;
        echo $y++;
        $z = &$x->foobar;
        echo $z++;
        ''')
        assert [self.space.int_w(i) for i in output] == [42, 43]

    def test_overloading_set(self):
        output = self.run('''
        class X {
            public $foo, $bar;
            public function __set($name, $value) {
                $this->foo = $name;
                $this->bar = $value;
            }
        }
        $x = new X;
        $x->testing = 42;
        echo $x;
        ''')
        assert self.is_object(output[0], 'X',
                              [('foo', self.space.newstr("testing")),
                               ('bar', self.space.newint(42))])

    def test_overloading_rec_1(self):
        output = self.run('''
        class X {
            public function __get($name) {
                echo $name;
                if ($name != "testing3")
                    $name++;
                else
                    $name = "testing1";
                return $this->$name;
            }
        }
        $x = new X;
        echo $x->testing0 === NULL;
        ''', [
            'Notice: Undefined property: X::$testing1'])
        assert [self.space.str_w(i) for i in output] == [
            "testing0", "testing1", "testing2", "testing3", "1"]

    def test_overloading_rec_2(self):
        output = self.run('''
        class Y {
            protected $testing;
            public function __set($name, $value) {
                echo "$name: $value";
                $this->{$name} = $value;
            }
        }
        $y = new Y;
        $y->testing = 42;
        $y->foobar = 43;
        $y->foobar = 44;
        $y->testing = 45;
        ''')
        assert self.space.str_w(output[0]) == "testing: 42"
        assert self.space.str_w(output[1]) == "foobar: 43"
        assert self.space.str_w(output[2]) == "testing: 45"

    @hippy_fail(reason="later")
    def test_overloading_rec_3(self):
        with self.warnings(['Notice: Undefined property: Y::$testing']*2):
            output = self.run('''
            class Y {
                protected $testing;
                public function f() { unset($this->testing); }
                public function __set($name, $value) {
                    echo "$name: $value";
                    $this->testing = $this->testing + 1;
                }
            }
            $y = new Y;
            $y->f();
            $y->testing = 42;
            echo $y;
            $y->testing = 43;
            echo $y;
            ''')
        assert self.space.str_w(output[0]) == "testing: 42"
        assert self.space.str_w(output[1]) == "testing: 1"
        assert self.is_object(output[2], 'Y',
                              [('\x00*\x00testing', self.space.newint(1))])
        assert self.space.str_w(output[3]) == "testing: 43"
        assert self.is_object(output[4], 'Y',
                              [('\x00*\x00testing', self.space.newint(2))])

    def test_store_ref(self):
        output = self.run('''
        class X { }
        $x = new X;
        $a = 42;
        $x->foo = &$a;
        $a++;
        echo $x->foo;
        ''')
        assert self.space.int_w(output[0]) == 43

    def test_overloading_unset(self):
        output = self.run('''
        class X {
            public function __unset($name) {
                echo $name;
            }
        }
        $x = new X;
        unset($x->baz);
        ''')
        assert self.space.str_w(output[0]) == "baz"

    def test_overloading_isset(self):
        output = self.run('''
        class X {
            public function __isset($name) {
                echo -9;
                return FALSE;
            }
        }
        $x = new X;
        echo isset($x->baz);
        echo empty($x->baz);
        $x->baz = 42;
        echo isset($x->baz);
        echo empty($x->baz);
        $x->baz = NULL;
        echo isset($x->baz);
        echo empty($x->baz);
        ''')
        assert [self.space.int_w(i) for i in output] == [-9, 0, -9, 1,
                                                         1, 0,
                                                         0, 1]

    def test_interface_simple(self):
        output = self.run('''
        interface I { function foo($x); }
        class A implements I { function foo($x) { return $x+1; } }
        $x = new A;
        echo $x->foo(41);
        ''')
        assert self.space.int_w(output[0]) == 42

    def test_interface_const(self):
        output = self.run('''
        interface I1 { const x = 5; }
        interface I2 extends I1 { const y = 6; }
        interface I3 extends I1 { const z = 7; }
        interface I4 extends I2, I3 { }
        class A implements I4 { }
        class B extends A { const x = 42; }
        echo A::x;
        echo A::y;
        echo A::z;
        echo B::x;
        echo B::y;
        echo B::z;
        ''')
        assert [self.space.int_w(i) for i in output] == [5, 6, 7,
                                                         42, 6, 7]

    def test_interface_forbidden_operations(self):
        self.run('interface I { }; $x = new I;',
                 ["Fatal error: Cannot instantiate interface I"])
        self.run('interface I { function foo($x); } class A implements I { }',
                 ["Fatal error: Class A contains 1 abstract method and must "
                  "therefore be declared abstract or implement the remaining "
                  "methods (I::foo)"])
        self.run('interface I {const x=2;} class A implements I {const x=2;}',
                 ["Fatal error: Cannot inherit previously-inherited or "
                  "override constant x from interface I"])
        self.run('interface J {const x=2;} '
                 'class A {const x=2;} '
                 'class B extends A implements J {}',
                 ["Fatal error: Cannot inherit previously-inherited or "
                  "override constant x from interface J"])
        self.run('interface I {const x=2;} interface J extends I {const x=2;}',
                 ["Fatal error: Cannot inherit previously-inherited or "
                  "override constant x from interface I"])
        self.run('interface I { function f1(); function f2(); function f3(); }'
                 'class A implements I { }',
                 ["Fatal error: Class A contains 3 abstract methods and must "
                  "therefore be declared abstract or implement the remaining "
                  "methods (I::f1, I::f2, I::f3)"])
        self.run('interface I { function f1(); function f2(); function f3();'
                 'function f4(); } class A implements I { }',
                 ["Fatal error: Class A contains 4 abstract methods and must "
                  "therefore be declared abstract or implement the remaining "
                  "methods (I::f1, I::f2, I::f3, ...)"])

    def test_interface_instanceof(self):
        output = self.run('''
        interface I1 { }
        interface I2 extends I1 { }
        class A { }
        class B extends A implements I2 { }
        class C extends B { }
        $a = new A;
        $b = new B;
        $c = new C;
        echo $a instanceof I1;
        echo $b instanceof I1;
        echo $c instanceof I1;
        ''')
        assert [self.space.int_w(i) for i in output] == [0, 1, 1]

    def test_is_a_1(self):
        output = self.run("""
        interface I1 { }
        interface I2 { }
        class A1 implements I1 { }
        class B1 extends A1 { }
        class A2 implements I2 { }
        $a1 = new A1;
        $b1 = new B1;
        $a2 = new A2;
        echo is_a($a1, 'I1');
        echo is_a($a1, 'I2');
        echo is_a($a1, 'A1');
        echo is_a($a1, 'B1');
        echo is_a($a1, 'A2', 1);
        echo is_a($b1, 'I1');
        echo is_a($b1, 'I2');
        echo is_a($b1, 'A1', 1);
        echo is_a($b1, 'B1');
        echo is_a($b1, 'A2');
        echo is_a($a2, 'I1');
        echo is_a($a2, 'I2');
        echo is_a($a2, 'A1', 1);
        echo is_a($a2, 'B1');
        echo is_a($a2, 'A2');
        """)
        assert [self.space.int_w(i) for i in output] == [1, 0, 1, 0, 0,
                                                         1, 0, 1, 1, 0,
                                                         0, 1, 0, 0, 1]

    def test_is_a_2(self):
        output = self.run("""
        interface I1 { }
        class A1 implements I1 { }
        class B1 extends A1 { }
        echo is_a('A1', 'A1');
        echo is_a('foaddofio', 'B1', 1);
        echo is_a('A1', 'adidixunix', 1);
        echo is_a('I1', 'I1', 1);
        echo is_a('A1', 'I1', 1);
        echo is_a('B1', 'I1', 1);
        echo is_a('i1', 'A1', 1);
        echo is_a('A1', 'A1', 1);
        echo is_a('B1', 'a1', 1);
        echo is_a('I1', 'B1', 1);
        echo is_a('A1', 'B1', 1);
        echo is_a('B1', 'b1', 1);
        """)
        assert [self.space.int_w(i) for i in output] == [0, 0, 0,
                                                         1, 1, 1,
                                                         0, 1, 1,
                                                         0, 0, 1]

    def test_is_subclass_of(self):
        output = self.run("""
        class A { }
        class B extends A { }
        $a = new A;
        $b = new B;
        echo is_subclass_of($b, 'B');
        echo is_subclass_of($b, 'A');
        echo is_subclass_of($a, 'B');
        echo is_subclass_of('B', 'B', 1);
        echo is_subclass_of('B', 'A', 1);
        echo is_subclass_of('A', 'B', 1);
        """)
        assert [self.space.int_w(i) for i in output] == [0, 1, 0, 0, 1, 0]

    def test_cannot_call_abstract_method(self):
        self.run('''
        abstract class A { abstract function fOo(); }
        class B extends A { function f() { A::foo(); } function fOo() { } }
        $b = new B;
        $b->f();
        ''', ["Fatal error: Cannot call abstract method A::fOo()"])

    def test_typehints_array(self):
        self.run('''
        function F(array $a) { }
        F(array());
        ''')
        self.run('''
        function F(array $a) { }
        F(42);
        ''', ["Catchable fatal error: Argument 1 passed to F() must be "
              "of the type array, integer given, called in ... and defined"])
        self.run('''
        function f(array $a) { }
        F(NULL);
        ''', ["Catchable fatal error: Argument 1 passed to f() must be "
              "of the type array, null given, called in ... and defined"])
        self.run('''
        function F(array $a=NULL) { }
        f(42);
        ''', ["Catchable fatal error: Argument 1 passed to F() must be "
              "of the type array, integer given, called in ... and defined"])
        self.run('''
        function F(array $a=NULL) { }
        F(array());
        F(NULL);
        ''')

    def test_typehints_class(self):
        self.run('''
        class Abc { }
        function F(Abc $a) { }
        F(new Abc);
        ''')
        self.run('''
        function F(Abc $a) { }
        F(42);
        ''', ["Catchable fatal error: Argument 1 passed to F() must be "
              "an instance of Abc, integer given, called in ... and defined"])
        self.run('''
        function f(Abc $a) { }
        F(NULL);
        ''', ["Catchable fatal error: Argument 1 passed to f() must be "
              "an instance of Abc, null given, called in ... and defined"])
        self.run('''
        function F(Abc $a=NULL) { }
        f(42);
        ''', ["Catchable fatal error: Argument 1 passed to F() must be "
              "an instance of Abc, integer given, called in ... and defined"])
        self.run('''
        class Abc { }
        function F(Abc $a=NULL) { }
        F(new Abc);
        F(NULL);
        ''')
        self.run('''
        class Def { }
        function F(Abc $a=NULL) { }
        f(new Def);
        ''', ["Catchable fatal error: Argument 1 passed to F() must be "
              "an instance of Abc, instance of Def given, "
              "called in ... and defined"])

    def test_autoload_stdclass(self):
        self.run('class X extends stdClass { }')

    def test_no_such_class(self):
        self.run('class X extends Y { }',
                 ["Fatal error: Class 'Y' not found"])
        self.run('class X implements Y { }',
                 ["Fatal error: Interface 'Y' not found"])

    def test_autoload_new(self):
        output = self.run('''
        function __autoload($name) {
            echo $name;
            class y { public $x=42; }
        }
        $y = new Y;
        echo $y->x;
        ''')
        assert [self.space.str_w(i) for i in output] == ["Y", "42"]

    def test_autoload_static_property(self):
        output = self.run('''
        function __autoload($name) {
            echo $name;
            if ($name == "y") {
                class Y {
                    private static $__z = null;
                    public static function foo() {
                        if (is_null(self::$__z))
                            self::$__z = new Z;
                        return self::$__z;
                    }
                }
            }
            else {
                class Z { public function bar() { return 42; } }
            }
        }
        echo y::foo()->bar();
        ''')
        assert [self.space.str_w(i) for i in output] == ["y", "Z", "42"]

    def test_autoload_subclass(self):
        output = self.run('''
        function __autoload($name) {
            echo $name;
            class y { }
        }
        class X extends Y { }
        ''')
        assert [self.space.str_w(i) for i in output] == ['Y']

    def test_autoload_recursive(self):
        output = self.run('''
        function __autoload($name) {
            echo $name;
            new Z;
        }
        class X extends Y { }
        ''', ["Fatal error: Class 'Z' not found"])
        assert [self.space.str_w(i) for i in output] == ['Y', 'Z']

    def test_autoload_is_a_1(self):
        output = self.run('''
        function __autoload($name) {
            echo 42;
            class X { }
        }
        class Y { }
        echo is_a("Y", "Y", 1);
        echo is_a("X", "Y", 1);
        ''')
        assert [self.space.int_w(i) for i in output] == [1, 42, 0]

    def test_autoload_is_a_2(self):
        output = self.run('''
        function __autoload($name) {
            echo 42;
            class X extends Y { }
        }
        class Y { }
        echo is_a("Y", "Y", TRUE);
        echo is_a("X", "Y", TRUE);
        ''')
        assert [self.space.int_w(i) for i in output] == [1, 42, 1]

    def test_autoload_is_a_3(self):
        output = self.run('''
        function __autoload($name) {
            echo 42;
            class X extends Y { }
        }
        class Y { }
        echo is_a("Y", "X", 1);
        ''')
        assert [self.space.int_w(i) for i in output] == [0]

    def test___call(self):
        output = self.run('''
        class MethodTest {
            public function __call($name, $arguments) {
                echo $name, $this->x;
                return $arguments[0] - $arguments[1];
            }
        }
        $a = new MethodTest;
        $a->x = 67;
        echo $a->runTest(45, 3);
        ''')
        assert [self.space.str_w(i) for i in output] == ['runTest', '67', '42']

    def test___callStatic(self):
        output = self.run('''
        class MethodTest {
            public static function __callStatic($name, $arguments) {
                echo $name;
                return $arguments[0] - $arguments[1];
            }
        }
        echo MethodTest::runTest(45, 3);
        ''')
        assert [self.space.str_w(i) for i in output] == ['runTest', '42']

    def test_call_private_from_superclass_1(self):
        output = self.run('''
        class A { private function foo() { echo "OK"; }
            public function test() { $this->foo(); }
        }
        class B extends A {}
        $b = new B();
        $b->test();
        ''')
        assert [self.space.str_w(i) for i in output] == ["OK"]

    def test_call_private_from_superclass_2(self):
        output = self.run('''
        class A { private function foo() { echo "OK"; }
            public function test() { $this->foo(); }
        }
        class B extends A {private function foo() {echo "wrong";} }
        $b = new B();
        $b->test();
        ''')
        assert [self.space.str_w(i) for i in output] == ["OK"]

    def test_call_private_from_superclass_3(self):
        output = self.run('''
        class A { private function foo() { echo "OK"; }
            public function test() { $this::foo(); }
        }
        class B extends A {}
        $b = new B();
        $b->test();
        ''')
        assert [self.space.str_w(i) for i in output] == ["OK"]

    def test_call_private_from_superclass_4(self):
        with self.warnings(["Fatal error: "
                "Call to private method B::foo() from context 'A'"]):
            output = self.run('''
            class A { private function foo() { echo "OK"; }
                public function test() { $this::foo(); }
            }
            class B extends A { private function foo() { echo "wrong"; } }
            $b = new B();
            $b->test();
            ''')
        assert not output

    def test_late_static_binding_1(self):
        output = self.run('''
        class A {
            public static function who() { echo "A"; }
            public static function test() { static::who(); }
        }
        class B extends A {
            public static function who() { echo "B"; }
        }
        B::test();
        ''')
        assert [self.space.str_w(i) for i in output] == ["B"]

    def test_late_static_binding_2(self):
        output = self.run('''
        class A { private function foo() { echo "OK"; }
            public function test() { static::foo(); }
        }
        class B extends A {
        }
        class C extends A {
            private function foo() { echo "never called"; }
        }
        $b = new B();
        $b->test();
        $c = new C();
        $c->test();   // the call to static::foo() fails
        ''', [
            "Fatal error: Call to private method C::foo() from context 'A'"])
        assert [self.space.str_w(i) for i in output] == ["OK"]

    def test_late_static_binding_3(self):
        output = self.run('''
        class A {
            public static function foo() { static::who(); }
            public static function who() { echo "A"; }
        }
        class B extends A {
            public static function test() {
                A::foo();
                parent::foo();
                self::foo();
            }
            public static function who() { echo "B"; }
        }
        class C extends B {
            public static function who() { echo "C"; }
        }

        C::test();''')
        assert [self.space.str_w(i) for i in output] == ["A", "C", "C"]

    def test_toString(self):
        # XXX: soda, this gonna be fixed asap
        self.run('(string)(new stdClass);', [
            "Catchable fatal error: Object of class stdClass could "
            "not be converted to string"])
        output = self.run('''
        class A { public function __toString() { return "hi there"; } }
        echo (string)(new A);
        ''')
        assert [self.space.str_w(i) for i in output] == ["hi there"]
        self.run('''
        class B { public function __toString() { return 42; } }
        echo (string)(new B);
        ''', [
            "Catchable fatal error: Method B::__toString() must "
            "return a string value"])

    def test_invoke(self):
        self.run('''
        class A { }
        $a = new A;
        $a(5, 6);
        ''', ["Fatal error: Function name must be a string"])
        #
        output = self.run('''
        class A { function __invoke() { return 42; } }
        $a = new A;
        echo $a();
        ''')
        assert [self.space.int_w(i) for i in output] == [42]
        #
        output = self.run('''
        class A {
            function __invoke($x, &$y) { $y *= $x; }
        }
        $a = new A;
        $res = 6;
        $a(7, $res);
        echo $res;
        ''')
        assert [self.space.int_w(i) for i in output] == [42]

    def test_get_class(self):
        output = self.run('''
        class bar {
            public function __construct() {
                echo get_class($this);
                echo get_class();
            }
        }
        class foo extends bar { }
        new foo;
        ''')
        assert [self.space.str_w(i) for i in output] == ["foo", "bar"]

    def test_get_called_class(self):
        output = self.run('''
        class foo {
            static public function test() {
                echo get_called_class();
            }
        }
        class bar extends foo {
        }
        foo::test();
        bar::test();
        ''')
        assert [self.space.str_w(i) for i in output] == ["foo", "bar"]

    def test_get_parent_class(self):
        output = self.run('''
        class A { }
        class B extends a {
            static function foo() { echo get_parent_class(); }
        }
        echo get_parent_class(new B);
        echo get_parent_class(new A);
        echo get_parent_class("B");
        echo get_parent_class("A");
        echo get_parent_class("aijdij");
        echo get_parent_class();
        B::foo();
        class C extends B { }
        C::foo();
        ''')
        assert self.space.str_w(output[0]) == "A"
        assert self.space.int_w(output[1]) == 0
        assert self.space.str_w(output[2]) == "A"
        assert self.space.int_w(output[3]) == 0
        assert self.space.int_w(output[4]) == 0
        assert self.space.int_w(output[5]) == 0
        assert self.space.str_w(output[6]) == "A"
        assert self.space.str_w(output[7]) == "A"

    def test_constant(self):
        output = self.run('''
        interface A { const test=42; }
        class B implements A { }
        class C extends B { }
        echo constant("A::test");
        echo constant("B::test");
        echo constant("C::test");
        echo constant("D::test") === NULL;   // class D does not exist
        echo constant("A::missing") === NULL;
        echo defined("A::test");
        echo defined("B::test");
        echo defined("C::test");
        echo defined("D::test");
        echo defined("A::missing");
        ''', ["Warning: constant(): Couldn't find constant D::test",
              "Warning: constant(): Couldn't find constant A::missing"])
        assert [self.space.int_w(i) for i in output] == [42, 42, 42, 1, 1,
                                                         1, 1, 1, 0, 0]

    def test_isset_attr_of_nonobject(self):
        output = self.run('''
        $a = 1;
        echo isset($a->foo);
        $a = true;
        echo isset($a->foo);
        $a = false;
        echo isset($a->foo);
        $a = array();
        echo isset($a->foo);
        ''')
        assert [self.space.int_w(i) for i in output] == [0, 0, 0, 0]

    def test_isset_fatal(self):
        with self.warnings(['Fatal error: Cannot use [] for reading']):
            self.run('''isset($a[]->foo);''')

    def test_isset_fatal_2(self):
        with self.warnings(['Fatal error: '
                'Cannot access private property A::$x']):
            self.run('''
            class A {private $x = 42;}
            $a = new A;
            isset($a->x->foo);
            ''')

    def test_empty_attr_of_nonobject(self):
        output = self.run('''
        $a = 1;
        echo empty($a->foo);
        $a = true;
        echo empty($a->foo);
        $a = false;
        echo empty($a->foo);
        $a = array();
        echo empty($a->foo);
        ''')
        assert [self.space.int_w(i) for i in output] == [1, 1, 1, 1]

    def test_empty_fatal(self):
        with self.warnings(['Fatal error: Cannot use [] for reading']):
            self.run('''empty($a[]->foo);''')

    def test_empty_fatal_2(self):
        with self.warnings(['Fatal error: '
                'Cannot access private property A::$x']):
            self.run('''
            class A {private $x = 42;}
            $a = new A;
            empty($a->x->foo);
            ''')

    def test_unset_attr_of_nonobject(self):
        output = self.run('''
        $a = 1;
        unset($a->foo);
        $a = true;
        unset($a->foo);
        $a = false;
        unset($a->foo);
        $a = array();
        unset($a->foo);
        ''')

    @hippy_fail(reason="Does not compile")
    def test_unset_fatal(self):
        with self.warnings(['Fatal error: Cannot use [] for unsetting']):
            self.run('''unset($a[]->foo);''')

    def test_unset_fatal_2(self):
        with self.warnings(['Fatal error: '
                'Cannot access private property A::$x']):
            self.run('''
            class A {private $x = 42;}
            $a = new A;
            unset($a->x->foo);
            ''')

    def test_member_array(self):
        output = self.run("""class X {
        public static $member = array(1, 2, 3);
        }
        X::$member[3] = 16;
        echo X::$member[3];
        """)
        assert self.space.int_w(output[0]) == 16

    def test_iterator_interface(self):
        with self.warnings(['Fatal error: Class X contains 5 abstract methods and must therefore be declared abstract or implement the remaining methods (Iterator::current, Iterator::next, Iterator::key, ...)']):
            self.run("""
            class X implements Iterator {
            }
            """)

    def test_iterator_iterating(self):
        output = self.run("""
        class myIterator implements Iterator {
            private $position = 0;
            private $array = array(
                "firstelement",
                "secondelement",
                "lastelement",
            );

            public function __construct() {
                $this->position = 0;
            }

            function rewind() {
                echo __METHOD__;
                $this->position = 0;
            }

            function current() {
                echo __METHOD__;
                return $this->array[$this->position];
            }

            function key() {
                echo __METHOD__;
                return $this->position;
            }

            function next() {
                echo __METHOD__;
                ++$this->position;
            }

            function valid() {
                echo __METHOD__;
                return isset($this->array[$this->position]);
            }
        }

        $it = new myIterator;

        foreach($it as $key => $value) {
            echo $key, $value;
        }
        """)
        space = self.space
        unwrapped = []
        for item in output:
            if isinstance(item, W_IntObject):
                unwrapped.append(space.int_w(item))
            else:
                unwrapped.append(space.str_w(item))
        assert unwrapped == [
            "myIterator::rewind",
            "myIterator::valid",
            "myIterator::current",
            "myIterator::key",
            0,
            "firstelement",
            "myIterator::next",
            "myIterator::valid",
            "myIterator::current",
            "myIterator::key",
            1,
            "secondelement",
            "myIterator::next",
            "myIterator::valid",
            "myIterator::current",
            "myIterator::key",
            2,
            "lastelement",
            "myIterator::next",
            "myIterator::valid",
        ]

    def test_iterator_iterating_2(self):
        output = self.run("""
        class myIterator implements Iterator {
            private $position = 0;
            private $array = array(
                "firstelement",
                "secondelement",
                "lastelement",
            );

            public function __construct() {
                $this->position = 0;
            }

            function rewind() {
                echo __METHOD__;
                $this->position = 0;
            }

            function current() {
                echo __METHOD__;
                return $this->array[$this->position];
            }

            function key() {
                echo __METHOD__;
                return $this->position;
            }

            function next() {
                echo __METHOD__;
                ++$this->position;
            }

            function valid() {
                echo __METHOD__;
                return isset($this->array[$this->position]);
            }
        }

        $it = new myIterator;

        foreach($it as $key) {
            echo $key;
        }
        """)
        space = self.space
        unwrapped = []
        for item in output:
            if isinstance(item, W_IntObject):
                unwrapped.append(space.int_w(item))
            else:
                unwrapped.append(space.str_w(item))
        assert unwrapped == [
            "myIterator::rewind",
            "myIterator::valid",
            "myIterator::current",
            "firstelement",
            "myIterator::next",
            "myIterator::valid",
            "myIterator::current",
            "secondelement",
            "myIterator::next",
            "myIterator::valid",
            "myIterator::current",
            "lastelement",
            "myIterator::next",
            "myIterator::valid",
        ]

    def test_iterator_aggregate(self):
        output = self.run('''

            class SubKlass {
                public $value;

                function __construct($value) {
                    $this->value = $value;
                }
            }

            class Klass implements IteratorAggregate {

                function __construct($aggregation) {
                    $this->aggregation = $aggregation;
                }

                function getIterator()
                {
                    return new ArrayIterator($this->aggregation);
                }
            }

            $values = array(
                new SubKlass(1),
                new SubKlass(2),
                new SubKlass(3)
            );

            $iter = new Klass($values);

            foreach ($iter as $element) {
                echo $element->value;
            }

        ''')

        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 2
        assert self.space.int_w(output[2]) == 3

    def test_iterator_aggregate_object(self):
        output = self.run('''

            class Klass implements IteratorAggregate {
                public $property1 = "Public property one";
                public $property2 = "Public property two";
                public $property3 = "Public property three";

                function __construct() {
                    $this->property4 = "last property";
                }

                function getIterator()
                {
                    return new ArrayIterator($this);
                }
            }

            $obj = new Klass;

            foreach($obj as $key => $value) {
                echo $key . ' -> ' . $value;
            }

        ''')

        assert self.space.str_w(output[0]) == 'property1 -> Public property one'
        assert self.space.str_w(output[1]) == 'property2 -> Public property two'
        assert self.space.str_w(output[2]) == 'property3 -> Public property three'
        assert self.space.str_w(output[3]) == 'property4 -> last property'

    def test_iterator_aggregate_error(self):
        with self.warnings(['Fatal error: Class X cannot implement both '
                            'Iterator and IteratorAggregate at the same time']):
            self.run('''
            abstract class X implements IteratorAggregate, Iterator {}
            ''')

    def test_instanceof_self(self):
        output = self.run("""

        class A {
            function method() {
                return $this instanceof self;
            }
        }

        $a = new A();
        echo $a->method();
        """)
        assert self.unwrap(output[0]) is True

    def test_property_exists(self):
        output = self.run("""
        class myClass {
            public $mine;
            private $xpto;
            static protected $test;

            static function test() {
                var_dump(property_exists('myClass', 'xpto')); //true
            }
        }

        echo property_exists('myClass', 'mine');
        echo property_exists(new myClass, 'mine');
        echo property_exists('myClass', 'xpto');
        echo property_exists('myClass', 'bar');
        echo property_exists('myClass', 'test');

        """)

        assert self.unwrap(output.pop(0))
        assert self.unwrap(output.pop(0))
        assert self.unwrap(output.pop(0))
        assert not self.unwrap(output.pop(0))
        assert self.unwrap(output.pop(0))

        output = self.run("""
            echo property_exists('myClass', 'mine');
        """)

        assert not self.unwrap(output.pop(0))

    def test_order_of_class_defs_0(self):
        output = self.run("""
        class A {public $x = 5;}
        class B extends A {}
        $b = new B;
        echo $b->x;
        """)
        assert self.unwrap(output[0]) == 5

    def test_order_of_class_defs_1(self):
        output = self.run("""
        class A {public $x = 5;}
        $b = new B;
        echo $b->x;
        class B extends A {}
        """)
        assert self.unwrap(output[0]) == 5

    def test_order_of_class_defs_2(self):
        output = self.run("""
        class B extends A {}
        class A {public $x = 5;}
        $b = new B;
        echo $b->x;
        """)
        assert self.unwrap(output[0]) == 5

    def test_order_of_class_defs_3(self):
        output = self.run("""
        class B extends A {}
        $b = new B;
        echo $b->x;
        class A {public $x = 5;}
        """)
        assert self.unwrap(output[0]) == 5

    def test_order_of_class_defs_4(self):
        output = self.run("""
        $b = new B;
        echo $b->x;
        class A {public $x = 5;}
        class B extends A {}
        """)
        assert self.unwrap(output[0]) == 5

    def test_order_of_class_defs_5(self):
        with self.warnings(["Fatal error: Class 'B' not found"]):
            output = self.run("""
            $b = new B;
            echo $b->x;
            class B extends A {}
            class A {public $x = 5;}
            """)
        assert not output

    def test_countable_interface(self):
        with self.warnings([
            'Fatal error: Class X contains 1 abstract method and must \
therefore be declared abstract or implement the remaining methods \
(Countable::count)'
            ]):
            self.run('''
            class X implements Countable {}
            ''')

    def test_countable_usage(self):
        output = self.run('''
        class CountMe implements Countable {
            protected $_myCount = 4;
            protected $x = 1;
            public function count() {
                return $this->_myCount;
            }
        }

        $c = new CountMe();
        echo count($c);
        echo sizeof($c);
        ''')
        assert self.space.int_w(output[0]) == 4
        assert self.space.int_w(output[1]) == 4

    def test_seekable_iterator_interface(self):
        with self.warnings([
            'Fatal error: Class X contains 6 abstract methods and must \
therefore be declared abstract or implement the remaining methods \
(SeekableIterator::seek, Iterator::current, Iterator::next, ...)'
            ]):
            self.run('''
            class X implements SeekableIterator {}
            ''')

    def test_seekable_iterator_usage(self):
        output = self.run('''
        class MySeekableIterator implements SeekableIterator {
            private $position=0;
            private $array = array(
                "first", "second", "third", "fourth"
            );

            public function seek($position) {
                if (!isset($this->array[$position])) {
                    throw new OutOfBoundsException("Invalid seek ($position)");
                }
                $this->position = $position;
            }

            public function rewind() {
                $this->position = 0;
            }

            public function current() {
                return $this->array[$this->position];
            }

            public function key() {
                return $this->position;
            }

            public function next() {
                ++$this->position;
            }

            public function valid() {
                return isset($this->array[$this->position]);
            }
        }

        try {
            $it = new MySeekableIterator;
            echo $it->current();

            $it->seek(2);
            echo $it->current();

            $it->seek(1);
            echo $it->current();

            $it->seek(10);

        } catch (OutOfBoundsException $e) {
            echo $e->getMessage();
        }
        ''')

        assert self.space.str_w(output[0]) == "first"
        assert self.space.str_w(output[1]) == "third"
        assert self.space.str_w(output[2]) == "second"
        assert self.space.str_w(output[3]) == "Invalid seek (10)"

    def test_recursive_iterator_interface(self):
        with self.warnings([
            'Fatal error: Class X contains 7 abstract methods and \
must therefore be declared abstract or implement the remaining methods \
(RecursiveIterator::hasChildren, RecursiveIterator::getChildren, \
Iterator::current, ...)'
            ]):
            self.run('''
            class X implements RecursiveIterator {}
            ''')

    def test_recursive_iterator_usage(self):
        output = self.run('''
        class MyRecursiveIterator implements RecursiveIterator
        {
            private $_data;
            private $_position = 0;

            public function __construct(array $data) {
                $this->_data = $data;
            }

            public function valid() {
                return isset($this->_data[$this->_position]);
            }

            public function hasChildren() {
                return is_array($this->_data[$this->_position]);
            }

            public function next() {
                $this->_position++;
            }

            public function current() {
                return $this->_data[$this->_position];
            }

            public function getChildren() {
                $child_it = new MyRecursiveIterator($this->_data[$this->_position]);
                return $child_it;
            }

            public function rewind() {
                $this->_position = 0;
            }

            public function key() {
                return $this->_position;
            }
        }

        $arr = array(0, 1, 2, 3, 4, 5 => array(10, 20, 30), 6, 7, 8, 9 => array(1, 2, 3));
        $mri = new MyRecursiveIterator($arr);

        foreach ($mri as $c => $v) {
            if ($mri->hasChildren()) {
                echo "$c has children";
                echo get_class($mri->getChildren());
            } else {
                echo "$v";
            }
        }
        ''')
        assert self.space.int_w(output[0]) == 0
        assert self.space.int_w(output[1]) == 1
        assert self.space.int_w(output[2]) == 2
        assert self.space.int_w(output[3]) == 3
        assert self.space.int_w(output[4]) == 4
        assert self.space.str_w(output[5]) == "5 has children"
        assert self.space.str_w(output[6]) == "MyRecursiveIterator"
        assert self.space.int_w(output[7]) == 6
        assert self.space.int_w(output[8]) == 7
        assert self.space.int_w(output[9]) == 8
        assert self.space.str_w(output[10]) == "9 has children"
        assert self.space.str_w(output[11]) == "MyRecursiveIterator"

    def test_private_protected_subclassing(self):
        output = self.run('''
        class foo {
            private $foo = 'foo';

            function foo() {
                return $this->foo;
            }
        }

        class bar extends foo {
            protected $foo = 'bar';
        }

        class baz extends bar {
            protected $foo = 'baz';
        }

        $x = new baz();
        echo $x->foo();
        ''')
        assert self.space.str_w(output[0]) == 'foo'

    def test_method_exists(self):
        output = self.run('''
        $directory = new Directory('.');
        echo method_exists($directory,'read');
        echo method_exists($directory,'READ');
        echo method_exists(5,'read');
        echo method_exists($directory,'r e a d');
        ''')
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 1
        assert self.space.int_w(output[2]) == 0
        assert self.space.int_w(output[3]) == 0

    def test_get_class_vars(self):
        output = self.run('''
        class myclass {

        var $var1; // this has no default value...
        var $var2 = "xyz";
        var $var3 = 100;
        private $var4; // PHP 5

        // constructor
        function myclass() {
        // change some properties
        $this->var1 = "foo";
        $this->var2 = "bar";
        return true;
        }

        }

        $my_class = new myclass();

        $class_vars = get_class_vars(get_class($my_class));

        foreach ($class_vars as $name => $value) {
        echo "$name : $value\n";
        }
        echo get_class_vars('not_existing_class');

        ''')
        assert self.space.str_w(output[0]) == 'var1 : \n'
        assert self.space.str_w(output[1]) == 'var2 : xyz\n'
        assert self.space.str_w(output[2]) == 'var3 : 100\n'
        assert self.space.int_w(output[3]) == 0

    def test_get_declared_classes(self):
        output = self.run('''
        class C {}
        echo in_array('C', get_declared_classes());
        interface I {}
        echo in_array('I', get_declared_classes());
        ''')
        assert self.space.str_w(output[0]) == '1'
        assert self.space.str_w(output[1]) == ''

    def test_get_declared_interfaces(self):
        output = self.run('''
        class C {}
        echo in_array('C', get_declared_interfaces());
        interface I {}
        echo in_array('I', get_declared_interfaces());
        ''')
        assert self.space.str_w(output[0]) == ''
        assert self.space.str_w(output[1]) == '1'


class TestKlassReinterpret(TestKlass):
    Engine = MockServerEngine
