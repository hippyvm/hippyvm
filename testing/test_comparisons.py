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

    def test_nested_objects_deep(self, php_space):
        output = self.run("""
        class N {
            function __construct($l) {
                $this->l = $l;
            }
        }

        $chain1 = NULL;
        $chain2 = NULL;
        for ($i = 0; $i < 1000; $i++) {
            $chain1 = new N($chain1);
            $chain2 = new N($chain2);
        }

        echo $chain1 == $chain2;
        echo $chain1 != $chain2;

        echo $chain1 < $chain2;
        echo $chain1 > $chain2;

        echo $chain1 <= $chain2;
        echo $chain1 >= $chain2;

        echo $chain1 === $chain2;
        echo $chain1 <> $chain2;

        // reverse args

        echo $chain1 == $chain2;
        echo $chain1 != $chain2;

        echo $chain1 < $chain2;
        echo $chain1 > $chain2;

        echo $chain1 <= $chain2;
        echo $chain1 >= $chain2;

        echo $chain1 === $chain2;
        echo $chain1 <> $chain2;
        """)
        assert php_space.is_true(output[0])
        assert not php_space.is_true(output[1])

        assert not php_space.is_true(output[2])
        assert not php_space.is_true(output[3])

        assert php_space.is_true(output[4])
        assert php_space.is_true(output[5])

        assert not php_space.is_true(output[6])
        assert not php_space.is_true(output[7])

        assert php_space.is_true(output[8])
        assert not php_space.is_true(output[9])

        assert not php_space.is_true(output[10])
        assert not php_space.is_true(output[11])

        assert php_space.is_true(output[12])
        assert php_space.is_true(output[13])

        assert not php_space.is_true(output[14])
        assert not php_space.is_true(output[15])

    def test_nested_objects_deep2(self, php_space):
        output = self.run("""
        class N {
            function __construct($l) {
                $this->l = $l;
            }
        }

        $chain1 = NULL;
        $chain2 = "not null";
        for ($i = 0; $i < 100; $i++) {
            $chain1 = new N($chain1);
            $chain2 = new N($chain2);
        }

        echo $chain1 == $chain2;
        echo $chain1 != $chain2;

        echo $chain1 < $chain2;
        echo $chain1 > $chain2;

        echo $chain1 <= $chain2;
        echo $chain1 >= $chain2;

        echo $chain1 === $chain2;
        echo $chain1 <> $chain2;

        // reverse args

        echo $chain2 == $chain1;
        echo $chain2 != $chain1;

        echo $chain2 < $chain1;
        echo $chain2 > $chain1;

        echo $chain2 <= $chain1;
        echo $chain2 >= $chain1;

        echo $chain2 === $chain1;
        echo $chain2 <> $chain1;
        """)
        assert not php_space.is_true(output[0]) # ==
        assert php_space.is_true(output[1]) # !=

        assert php_space.is_true(output[2]) # <
        assert not php_space.is_true(output[3]) # >

        assert php_space.is_true(output[4]) # <=
        assert not php_space.is_true(output[5]) # >=

        assert not php_space.is_true(output[6]) # ===
        assert php_space.is_true(output[7]) # <>

        assert not php_space.is_true(output[8]) # ==
        assert php_space.is_true(output[9]) # !=

        assert not php_space.is_true(output[10]) # <
        assert php_space.is_true(output[11]) # >

        assert not php_space.is_true(output[12]) # <=
        assert php_space.is_true(output[13]) # >=

        assert not php_space.is_true(output[14]) # ===
        assert php_space.is_true(output[15]) # <>

    def test_nested_object_and_arrays(self, php_space):
        output = self.run("""
        class Node {
            function __construct($l, $r) {
                $this->l = $l;
                $this->r = $r;
            }
        }

        $tree1 = new Node(
            new Node(
                new Node(array(8, "a"), 2),
                new Node(3, array(8, "a"))
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

        echo $tree1 != $tree2;
        echo $tree1 == $tree2;
        echo $tree1 < $tree2;
        echo $tree1 > $tree2;
        echo $tree1 <= $tree2;
        echo $tree1 >= $tree2;
        echo $tree1 === $tree2;

        // same in reverse
        echo $tree2 != $tree1;
        echo $tree2 == $tree1;
        echo $tree2 < $tree1;
        echo $tree2 > $tree1;
        echo $tree2 <= $tree1;
        echo $tree2 >= $tree1;
        echo $tree2 === $tree1;

        """)
        assert php_space.is_true(output[0])
        assert not php_space.is_true(output[1])
        assert not php_space.is_true(output[2])
        assert php_space.is_true(output[3])
        assert not php_space.is_true(output[4])
        assert php_space.is_true(output[5])
        assert not php_space.is_true(output[6])

        assert php_space.is_true(output[7])
        assert not php_space.is_true(output[8])
        assert php_space.is_true(output[9])
        assert not php_space.is_true(output[10])
        assert php_space.is_true(output[11])
        assert not php_space.is_true(output[12])
        assert not php_space.is_true(output[13])

    def test_deferred_comparison(self, php_space):
        # tests an annoying comparison ordering quirk.
        # In short, when we see array $b has no key 3, we know the arrays
        # differ, but we still need to compare the common-keyed values
        # since they may differ with a different ordering outcome.
        output = self.run("""
            $a = array("0", "1", "2", "php");
            $b = array("0"=>"1", "1"=>"1", "2"=>"2", 4=>"php");

            echo $a < $b;
            echo $b > $a;
        """)
        assert php_space.is_true(output[0])
        assert php_space.is_true(output[1])

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

            echo $a < $b;
            echo $a > $b;
            echo $a == $b;
        """)
        assert not php_space.is_true(output[0])
        assert not php_space.is_true(output[1])
        assert php_space.is_true(output[2])

    def test_array_shortcuts3(self, php_space):
        output = self.run("""
            $a = array(0, 1, array(2, 3));
            $b = array(0, 1, array(2, 4));

            echo $a == $b;
        """)
        assert not php_space.is_true(output[0])

    def test_array_shortcuts4(self, php_space):
        output = self.run("""
            $a = array(0, 1, array(2, 3), 4);
            $b = array(0, 1, array(2, 3), 5);

            echo $a < $b;
            echo $a == $b;
        """)
        assert php_space.is_true(output[0])
        assert not php_space.is_true(output[1])

    def test_array_shortcuts5(self, php_space):
        output = self.run("""
            $cmn = array(2, 3);
            $a = array(0, 1, $cmn, 4);
            $b = array(0, 1, $cmn, 4);

            echo $a < $b;
            echo $a > $b;
            echo $a == $b;
        """)
        assert not php_space.is_true(output[0])
        assert not php_space.is_true(output[1])
        assert php_space.is_true(output[2])

    def test_array_shortcuts6(self, php_space):
        output = self.run("""
            class Triple {
                function __construct($a, $b, $c) {
                    $this->a = $a;
                    $this->b = $b;
                    $this->c = $c;
                }
            }
            $t1 = new Triple(new Triple(new Triple(1, 2, 3), 2, 3), NULL, 0);
            $t2 = new Triple(new Triple(new Triple(1, 2, 3), 2, 3), NULL, 1);

            echo $t1 == $t2;
            echo $t1 != $t2;
        """)
        assert not php_space.is_true(output[0])
        assert php_space.is_true(output[1])

    def test_lr_order_comp_array(self, php_space):
        output = self.run("""
            $a = array(array(1, 2, 3), 1, 2);
            $b = array(array(1, 2, 3), 2, 1);

            echo $a < $b;
        """)
        assert php_space.is_true(output[0])

    def test_order_comp_obj(self, php_space):
        output = self.run("""
            class N {
                function __construct($l, $r) { $this->l = $l; $this->r = $r; }
            }

            $a = new N(New N(1, 1), New N(2, 2));
            $b = new N(New N(0, 0), New N(4, 4));

            echo $a > $b;
        """)
        assert php_space.is_true(output[0])

    # http://phpsadness.com/sad/47
    def test_odd_string_comparison(self, php_space):
        output = self.run('''echo "1e3" == "1000";''')
        assert php_space.is_true(output[0])


    # http://phpsadness.com/sad/52
    def test_nontransitive_comparisons(self, php_space):
        output = self.run('''
                          echo TRUE == "a";
                          echo "a" == 0;
                          echo TRUE == 0;
                          ''')
        assert php_space.is_true(output[0])
        assert php_space.is_true(output[1])
        assert not php_space.is_true(output[2])

    # http://phpsadness.com/sad/52
    def test_nontransitive_comparisons2(self, php_space):
        output = self.run('''
                          echo -INF < 0;
                          echo 0 < TRUE;
                          echo -INF < TRUE;
                          ''')
        assert php_space.is_true(output[0])
        assert php_space.is_true(output[1])
        assert not php_space.is_true(output[2])

    def test_cycles_id(self, php_space):
        output = self.run('''
                          class A { function __construct($x=NULL) { $this->x = $x; }}

                          $a = new A();
                          $b = new A($a);
                          $a->x = $b; // completes the loop

                          echo $a == $a;
                          ''')
        assert php_space.is_true(output[0]) # flukey pass due to id check.

    def test_cycles(self, php_space):
        pytest.skip("does not terminate")
        output = self.run('''
                          class A { function __construct($x=NULL) { $this->x = $x; }}

                          $a = new A();
                          $b = new A($a);
                          $a->x = $b; // completes the loop

                          echo $a == $b;
                          ''')
        # should terminate
