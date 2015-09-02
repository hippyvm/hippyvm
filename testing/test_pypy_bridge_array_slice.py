from testing.test_interpreter import BaseTestInterpreter, SeqAssert


class TestPyPyBridgeSlicePHPArray(BaseTestInterpreter):
    """Tests Python's ability to slice PHP arrays"""

    def test_slice_results_in_list_like001(self, php_space):
        output = self.run(r'''
        $pysrc = <<<EOD
        def f(a):
            nl = a.as_list()[1:3]
            return isinstance(nl, list)
        EOD;
        $f = compile_py_func($pysrc);
        echo $f([1,2,3]);
        ''')
        assert php_space.is_true(output[0])

    def test_slice_no_bounds_or_step001(self, php_space):
        output = self.run(r'''
        $pysrc = "def f(a): return a.as_list()[:]";
        $f = compile_py_func($pysrc);

        $a = ["a", "b", "c", "d"];
        $b = $f($a);

        echo count($a);
        echo count($b);
        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 4)
        sa.asrt(int, 4)

        sa.asrt(str, "a")
        sa.asrt(str, "b")
        sa.asrt(str, "c")
        sa.asrt(str, "d")

    def test_slice_no_bounds_or_step002(self, php_space):
        output = self.run(r'''
        $pysrc = "def f(a): return a.as_list()[::]";
        $f = compile_py_func($pysrc);

        $a = ["a", "b", "c", "d"];
        $b = $f($a);

        echo count($a);
        echo count($b);
        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 4)
        sa.asrt(int, 4)

        sa.asrt(str, "a")
        sa.asrt(str, "b")
        sa.asrt(str, "c")
        sa.asrt(str, "d")

    def test_slice_lower_bound_no_step001(self, php_space):
        output = self.run(r'''
        $pysrc = "def f(a): return a.as_list()[1:]";
        $f = compile_py_func($pysrc);

        $a = ["a", "b", "c", "d"];
        $b = $f($a);

        echo count($a);
        echo count($b);
        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 4)
        sa.asrt(int, 3)

        sa.asrt(str, "b")
        sa.asrt(str, "c")
        sa.asrt(str, "d")

    def test_slice_lower_bound_no_step002(self, php_space):
        output = self.run(r'''
        $pysrc = "def f(a): return a.as_list()[-2:]";
        $f = compile_py_func($pysrc);

        $a = ["a", "b", "c", "d"];
        $b = $f($a);

        echo count($a);
        echo count($b);
        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 4)
        sa.asrt(int, 2)

        sa.asrt(str, "c")
        sa.asrt(str, "d")

    def test_slice_lower_bound_and_step001(self, php_space):
        output = self.run(r'''
        $pysrc = "def f(a): return a.as_list()[1::-1]";
        $f = compile_py_func($pysrc);

        $a = ["a", "b", "c", "d"];
        $b = $f($a);

        echo count($a);
        echo count($b);
        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 4)
        sa.asrt(int, 2)

        sa.asrt(str, "b")
        sa.asrt(str, "a")

    def test_slice_lower_bound_and_step002(self, php_space):
        output = self.run(r'''
        $pysrc = "def f(a): return a.as_list()[1::1]";
        $f = compile_py_func($pysrc);

        $a = ["a", "b", "c", "d"];
        $b = $f($a);

        echo count($a);
        echo count($b);
        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 4)
        sa.asrt(int, 3)

        sa.asrt(str, "b")
        sa.asrt(str, "c")
        sa.asrt(str, "d")

    def test_slice_upper_bound_no_step001(self, php_space):
        output = self.run(r'''
        $pysrc = "def f(a): return a.as_list()[:-1]";
        $f = compile_py_func($pysrc);

        $a = ["a", "b", "c", "d"];
        $b = $f($a);

        echo count($a);
        echo count($b);
        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 4)
        sa.asrt(int, 3)

        sa.asrt(str, "a")
        sa.asrt(str, "b")
        sa.asrt(str, "c")

    def test_slice_upper_bound_and_step001(self, php_space):
        output = self.run(r'''
        $pysrc = "def f(a): return a.as_list()[:2:1]";
        $f = compile_py_func($pysrc);

        $a = ["a", "b", "c", "d"];
        $b = $f($a);

        echo count($a);
        echo count($b);
        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 4)
        sa.asrt(int, 2)

        sa.asrt(str, "a")
        sa.asrt(str, "b")

    def test_slice_upper_bound_and_step002(self, php_space):
        output = self.run(r'''
        $pysrc = "def f(a): return a.as_list()[:2:-1]";
        $f = compile_py_func($pysrc);

        $a = ["a", "b", "c", "d"];
        $b = $f($a);

        echo count($a);
        echo count($b);
        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 4)
        sa.asrt(int, 1)

        sa.asrt(str, "d")

    def test_slice_both_bounds_no_step001(self, php_space):
        output = self.run(r'''
        $pysrc = "def f(a): return a.as_list()[1:3]";
        $f = compile_py_func($pysrc);

        $a = ["a", "b", "c", "d"];
        $b = $f($a);

        echo count($a);
        echo count($b);
        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 4)
        sa.asrt(int, 2)

        sa.asrt(str, "b")
        sa.asrt(str, "c")

    def test_slice_both_bounds_no_step002(self, php_space):
        output = self.run(r'''
        $pysrc = "def f(a): return a.as_list()[0:5]";
        $f = compile_py_func($pysrc);

        $a = ["a", "b", "c", "d"];
        $b = $f($a);

        echo count($a);
        echo count($b);
        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 4)
        sa.asrt(int, 4)

        sa.asrt(str, "a")
        sa.asrt(str, "b")
        sa.asrt(str, "c")
        sa.asrt(str, "d")

    def test_slice_both_bounds_no_step003(self, php_space):
        output = self.run(r'''
        $pysrc = "def f(a): return a.as_list()[78:90]";
        $f = compile_py_func($pysrc);

        $a = [];
        $b = $f($a);

        echo count($a);
        echo count($b);
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 0)
        sa.asrt(int, 0)

    def test_slice_both_bounds_and_step001(self, php_space):
        output = self.run(r'''
        $pysrc = "def f(a): return a.as_list()[0:5:2]";
        $f = compile_py_func($pysrc);

        $a = ["a", "b", "c", "d"];
        $b = $f($a);

        echo count($a);
        echo count($b);
        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 4)
        sa.asrt(int, 2)

        sa.asrt(str, "a")
        sa.asrt(str, "c")

    def test_slice_both_bounds_and_step002(self, php_space):
        output = self.run(r'''
        $pysrc = "def f(a): return a.as_list()[0:5:10]";
        $f = compile_py_func($pysrc);

        $a = ["a", "b", "c", "d"];
        $b = $f($a);

        echo count($a);
        echo count($b);
        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 4)
        sa.asrt(int, 1)

        sa.asrt(str, "a")

    def test_slice_only_step001(self, php_space):
        output = self.run(r'''
        $pysrc = "def f(a): return a.as_list()[::1]";
        $f = compile_py_func($pysrc);

        $a = ["a", "b", "c", "d"];
        $b = $f($a);

        echo count($a);
        echo count($b);
        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 4)
        sa.asrt(int, 4)

        sa.asrt(str, "a")
        sa.asrt(str, "b")
        sa.asrt(str, "c")
        sa.asrt(str, "d")

    def test_slice_only_step002(self, php_space):
        output = self.run(r'''
        $pysrc = "def f(a): return a.as_list()[::-1]";
        $f = compile_py_func($pysrc);

        $a = ["a", "b", "c", "d"];
        $b = $f($a);

        echo count($a);
        echo count($b);
        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 4)
        sa.asrt(int, 4)

        sa.asrt(str, "d")
        sa.asrt(str, "c")
        sa.asrt(str, "b")
        sa.asrt(str, "a")

    def test_slice_only_step003(self, php_space):
        output = self.run(r'''
        $pysrc = "def f(a): return a.as_list()[::-2]";
        $f = compile_py_func($pysrc);

        $a = ["a", "b", "c", "d"];
        $b = $f($a);

        echo count($a);
        echo count($b);
        for ($i = 0; $i < count($b); $i++) {
            echo $b[$i];
        }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 4)
        sa.asrt(int, 2)

        sa.asrt(str, "d")
        sa.asrt(str, "b")
