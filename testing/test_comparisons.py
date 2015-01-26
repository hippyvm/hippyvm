import pytest
from testing.test_interpreter import BaseTestInterpreter


class TestComparisons(BaseTestInterpreter):
    # Test PHP's "recursive" comparison scheme.
    # Implemented hippy iteratively to avoid exhausting the stack

    # XXX move into Base
    @pytest.fixture
    def php_space(self):
        return self.space

    def test_compare_int_eq_int(self, php_space):
        output = self.run("""
        $a = 1;
        $b = 1;
        echo $a == $b;
        """)
        assert php_space.is_true(output[0])

    def test_compare_int_arry_eq_int_arry(self, php_space):
        output = self.run("""
        $a = array(1, 6, 8);
        $b = array(1, 6, 8);
        echo $a == $b;
        """)
        assert php_space.is_true(output[0])

    def test_compare_nested_int_arry_eq_int_arry(self, php_space):
        output = self.run("""
        $a = array(1, array(8));
        $b = array(1, array(8));
        echo $a == $b;
        """)
        assert php_space.is_true(output[0])

    def test_compare_nested_int_arry_not_eq_int_arry(self, php_space):
        output = self.run("""
        $a = array(1, array(9));
        $b = array(0, array(9));
        echo $a == $b;
        """)
        assert not php_space.is_true(output[0])

    def test_object_eq_object(self, php_space):
        output = self.run("""
        class X {
            public $f1 = 2;
            public $f2 = 3;
        }

        $a = new X();
        $b = new X();

        echo $a == $b;
        """)
        assert php_space.is_true(output[0])

    def test_object_not_eq_object_strict(self, php_space):
        output = self.run("""
        class X {
            public $f1 = 2;
            public $f2 = 3;
        }

        $a = new X();
        $b = new X();

        echo $a === $b;
        """)
        assert not php_space.is_true(output[0])

    def test_object_not_eq_object_strict2(self, php_space):
        output = self.run("""
        class X {
            public $f1 = 2;
            public $f2 = 3;
        }

        class Y {
            public $f1 = 2;
            public $f2 = 3;
        }

        $a = new X();
        $b = new Y();

        echo $a === $b;
        """)
        assert not php_space.is_true(output[0])

    def test_object_diff_class_eq_object(self, php_space):
        output = self.run("""
        class X {
            public $f1 = 2;
            public $f2 = 3;
        }

        class Y {
            public $f1 = 2;
            public $f2 = 3;
        }

        $a = new X();
        $b = new Y();

        echo $a == $b;
        """)
        assert not php_space.is_true(output[0])

    def test_object_diff_class_not_eq_object(self, php_space):
        output = self.run("""
        class X {
            public $f1 = 2;
            public $f2 = 3;
        }

        class Y {
            public $f1 = 2;
            public $f2 = 3;
        }

        $a = new X();
        $a->f1 = 666;
        $b = new Y();

        echo $a == $b;
        """)
        assert not php_space.is_true(output[0])

    def test_object_not_eq_object(self, php_space):
        output = self.run("""
        class X {
            public $f1 = 2;
            public $f2 = 3;
        }

        $a = new X();
        $a->f1 = 666;
        $b = new X();

        echo $a == $b;
        """)
        assert not php_space.is_true(output[0])

    def test_nested_object_eq_object(self, php_space):
        output = self.run("""
        class Node {
            function __construct($l, $r) {
                $this->l = $l;
                $this->r = $r;
            }
        }

        $tree1 = new Node(
            new Node(
                new Node(1, 2),
                new Node(3, 4)
            ),
            new Node(
                new Node(5, new Node(6, 7)),
                8
            )
        );

        $tree2 = new Node(
            new Node(
                new Node(1, 2),
                new Node(3, 4)
            ),
            new Node(
                new Node(5, new Node(6, 7)),
                8
            )
        );

        echo $tree1 == $tree2;

        """)
        assert php_space.is_true(output[0])

    def test_nested_object_eq_object_strict(self, php_space):
        output = self.run("""
        class Node {
            function __construct($l, $r) {
                $this->l = $l;
                $this->r = $r;
            }
        }

        $tree1 = new Node(
            new Node(
                new Node(1, 2),
                new Node(3, 4)
            ),
            new Node(
                new Node(5, new Node(6, 7)),
                8
            )
        );

        $tree2 = $tree1;

        echo $tree1 === $tree2;
        """)
        assert php_space.is_true(output[0])

    def test_nested_object_not_eq_object_strict(self, php_space):
        output = self.run("""
        class Node {
            function __construct($l, $r) {
                $this->l = $l;
                $this->r = $r;
            }
        }

        $tree1 = new Node(
            new Node(
                new Node(1, 2),
                new Node(3, 4)
            ),
            new Node(
                new Node(5, new Node(6, 7)),
                8
            )
        );

        $tree2 = new Node(
            new Node(
                new Node(1, 2),
                new Node(3, 4)
            ),
            new Node(
                new Node(5, new Node(6, 7)),
                8
            )
        );

        echo $tree1 === $tree2;
        """)
        assert not php_space.is_true(output[0])

    def test_deferred_comparison(self, php_space):
        # tests an annoying comparison ordering quirk.
        # In short, when we see array $b has no key 3, we know the arrays
        # differ, but we still need to compare the common-keyed values
        # since they may differ with a different ordering outcome.
        output = self.run("""
            $a = array("0", "1", "2", "php");
            $b = array("0"=>"1", "1"=>"1", "2"=>"2", 4=>"php");

            echo $a < $b;
        """)
        assert php_space.is_true(output[0])

    def test_array_shortcuts1(self, php_space):
        output = self.run("""
            $a = array(0, 1, 2);

            echo $a == $b;
        """)
        assert php_space.is_true(output[0])

    def test_array_shortcuts1(self, php_space):
        output = self.run("""
            $a = array(0, 1, 2);
            $b = array(0, 1, 3);

            echo $a == $b;
        """)
        assert not php_space.is_true(output[0])

    def test_array_shortcuts2(self, php_space):
        output = self.run("""
            $a = array(0, 1, array(2, 3));
            $b = array(0, 1, array(2, 3));

            echo $a == $b;
        """)
        assert php_space.is_true(output[0])

    def test_array_shortcuts3(self, php_space):
        output = self.run("""
            $a = array(0, 1, array(2, 3));
            $b = array(0, 1, array(2, 4));

            echo $a == $b;
        """)
        assert not php_space.is_true(output[0])

    def test_order_comp(self, php_space):
        output = self.run("""
            $a = array(array(1, 2, 3), 1, 2);
            $b = array(array(1, 2, 3), 2, 1);

            echo $a < $b;
        """)
        assert php_space.is_true(output[0])
