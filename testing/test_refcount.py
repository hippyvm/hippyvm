import py
from hippy.objects.base import W_Root
from testing.test_interpreter import BaseTestInterpreter


class TestRefCount(BaseTestInterpreter):

    @py.test.yield_fixture(autouse=True)
    def note_copies(self):
        def note_making_a_copy(array):
            self.space.ec.interpreter.writestr(array.var_dump(self.space, indent='', recursion={}))
        old_func = W_Root.__dict__['_note_making_a_copy']
        W_Root._note_making_a_copy = note_making_a_copy
        yield
        W_Root._note_making_a_copy = old_func

    def test_no_copies(self):
        output = self.run("$a = array(5, 6, 7);")
        assert output == []

    def test_no_copies_2(self):
        output = self.run("$x = 7; $a = array(5, 6, $x);")
        assert output == []

    def test_one_copy(self):
        output = self.run("$a = array(5, 6, 7); $b = $a; $b[] = 8;")
        assert ''.join(output) == """\
array(3) {
  [0]=>
  int(5)
  [1]=>
  int(6)
  [2]=>
  int(7)
}
"""

    def test_inplace_append_from_immut(self):
        output = self.run("$a = array(5, 6, 7); $a[] = 8; $a[] = 9;")
        assert ''.join(output) == """\
array(3) {
  [0]=>
  int(5)
  [1]=>
  int(6)
  [2]=>
  int(7)
}
"""

    def test_inplace_append(self):
        output = self.run("$x = 7; $a = array(5, 6, $x); $a[] = 8;")
        assert output == []

    def test_append_needs_copy(self):
        output = self.run("$x = 7; $a = array(5, 6, $x); $b = $a; $a[] = 8;")
        assert ''.join(output) == """\
array(3) {
  [0]=>
  int(5)
  [1]=>
  int(6)
  [2]=>
  int(7)
}
"""

    def test_array_updates_in_function(self):
        output = self.run('''
        function f($a) {
            $a[0] = $a[1];   // copy
            $a[1] = $a[2];   // no more copies afterward
            $a[2] = $a[3];
            $a[3] = $a[4];
        }
        f(array(5, 6, 7, 8, 9));
        ''')
        assert ''.join(output) == """\
array(5) {
  [0]=>
  int(5)
  [1]=>
  int(6)
  [2]=>
  int(7)
  [3]=>
  int(8)
  [4]=>
  int(9)
}
"""

    def test_string_copies(self):
        output = self.run('''
        $a = "abc";
        $b = $a;
        $c = $b;
        $c[0] = 1;
        $a[0] = 5;
        ''')
        assert ''.join(output) == """\
string(3) "abc"
string(3) "abc"
"""

    def test_string_copies2(self):
        output = self.run('''
        $a = "abc";
        $a[0] = "3";
        $b = $a;
        $c = $b[0];
        ''')
        assert ''.join(output) == """\
string(3) "abc"
"""

    def test_string_copies3(self):
        output = self.run('''
        $a = "abc";
        $a[0] = "3";
        $b = $a;
        $a[0] = "4";
        ''')
        assert ''.join(output) == """\
string(3) "abc"
string(3) "3bc"
"""

    def test_instance_array(self):
        output = self.run('''
        class A { }
        $a = new A;
        $n = 7;
        $a->x = array(9, 8, $n);
        $a->x[] = 6;      # does a copy the first time
        $a->x[] = 5;      # not a copy any more afterwards
        ''')
        assert ''.join(output) == """\
array(3) {
  [0]=>
  int(9)
  [1]=>
  int(8)
  [2]=>
  int(7)
}
"""

    def test_instance_array_2(self):
        output = self.run('''
        class A { }
        $a = new A;
        $n = 7;
        $a->x = array(9, 8, $n);
        $a->x[] = 6;      # does a copy the first time
        $b = $a->x;
        $a->x[] = 5;      # another copy
        ''')
        assert ''.join(output) == """\
array(3) {
  [0]=>
  int(9)
  [1]=>
  int(8)
  [2]=>
  int(7)
}
array(4) {
  [0]=>
  int(9)
  [1]=>
  int(8)
  [2]=>
  int(7)
  [3]=>
  int(6)
}
"""

    def test_instance_array_3(self):
        output = self.run('''
        class A { }
        $a = new A;
        $a->x = array(9, 8, 7);
        $a->x[] = 6;      # does a copy the first time
        $n = 6;
        $a->x = array($n, $n, $n);     # replaces the W_Reference
        $a->x[] = 5;      # not a copy any more afterwards
        ''')
        assert ''.join(output) == """\
array(3) {
  [0]=>
  int(9)
  [1]=>
  int(8)
  [2]=>
  int(7)
}
"""

    def test_function_call(self):
        output = self.run('''
        function f($a) { }
        $a = array(5, 6, 7);
        f($a);
        ''')
        assert ''.join(output) == ""

    def test_function_call_by_ref(self):
        output = self.run('''
        function f(&$a) { $a[] = 8; }
        $x = 7;
        $a = array(5, 6, $x);
        f($a);
        ''')
        assert ''.join(output) == ""

    def test_call_builtin_count(self):
        output = self.run('''
        $a = array(5, 6, 7);
        count($a);
        ''')
        assert ''.join(output) == ""
