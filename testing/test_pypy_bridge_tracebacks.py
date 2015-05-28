from testing.test_interpreter import BaseTestInterpreter, SeqAssert
import pytest

class TestPyPyBridgeTraceBacks(BaseTestInterpreter):
    """NOTE:
    The hippy test suite strips blank lines from the input passed to
    self.run. Also note that an implicit first line is added '<?'.
    This is why the line numbers may not appear as expected at first.
    """

    @pytest.fixture
    def php_space(self):
        return self.space

    def test_simple1(self, php_space):
        output = self.run('''
            $src = "def f(): raise AttributeError('ouch')";
            compile_py_func_global($src);

            try {
                f();
            } catch (PyException $e) {
                $ts = $e->getTrace();
                echo count($ts);
                foreach ($ts as $t) {
                    echo $t["file"];
                    echo $t["line"];
                    echo $t["function"];
                    echo $t["args"];
                }
            }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 2)

        sa.asrt(str, "<python_box>")
        sa.asrt(int, 1)
        sa.asrt(str, "f")
        sa.asrt(str, "")

        sa.asrt(str, "<input>")
        sa.asrt(int, 5)
        sa.asrt(str, "<main>")
        sa.asrt(str, "")

    def test_simple2(self, php_space):
        output = self.run('''
            $src = "def f(): raise AttributeError('ouch')";
            compile_py_func_global($src, "myfile.php", 10);

            try {
                f();
            } catch (PyException $e) {
                $ts = $e->getTrace();
                echo count($ts);
                foreach ($ts as $t) {
                    echo $t["file"];
                    echo $t["line"];
                    echo $t["function"];
                    echo $t["args"];
                }
            }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 2)

        sa.asrt(str, "myfile.php")
        sa.asrt(int, 11)
        sa.asrt(str, "f")
        sa.asrt(str, "")

        sa.asrt(str, "<input>")
        sa.asrt(int, 5)
        sa.asrt(str, "<main>")
        sa.asrt(str, "")

    def test_simple3(self, php_space):
        output = self.run('''
            $src = "def f(): raise AttributeError('ouch')";
            $f = compile_py_func($src);

            try {
                $f();
            } catch (PyException $e) {
                $ts = $e->getTrace();
                echo count($ts);
                foreach ($ts as $t) {
                    echo $t["file"];
                    echo $t["line"];
                    echo $t["function"];
                    echo $t["args"];
                }
            }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 2)

        sa.asrt(str, "<python_box>")
        sa.asrt(int, 1)
        sa.asrt(str, "f")
        sa.asrt(str, "")

        sa.asrt(str, "<input>")
        sa.asrt(int, 5)
        sa.asrt(str, "<main>")
        sa.asrt(str, "")

    def test_simple4(self, php_space):
        output = self.run('''
            $src = "def f(): raise AttributeError('ouch')";
            $f = compile_py_func($src, "afile.php", 666);

            try {
                $f();
            } catch (PyException $e) {
                $ts = $e->getTrace();
                echo count($ts);
                foreach ($ts as $t) {
                    echo $t["file"];
                    echo $t["line"];
                    echo $t["function"];
                    echo $t["args"];
                }
            }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 2)

        sa.asrt(str, "afile.php")
        sa.asrt(int, 667)
        sa.asrt(str, "f")
        sa.asrt(str, "")

        sa.asrt(str, "<input>")
        sa.asrt(int, 5)
        sa.asrt(str, "<main>")
        sa.asrt(str, "")

    def test_php_py_php_raise(self, php_space):
        output = self.run('''
            function g() { throw new LogicException("eek"); }

            $src = "def f(): g()";
            $f = compile_py_func($src);

            try {
                $f();
            } catch (LogicException $e) {
                $ts = $e->getTrace();
                echo count($ts);
                echo $e->getMessage();

                foreach ($ts as $t) {
                    echo $t["file"];
                    echo $t["line"];
                    echo $t["function"];
                    echo $t["args"];
                }
            }
        ''')
        sa = SeqAssert(php_space, output)
        sa.asrt(int, 3)
        sa.asrt(str, "eek")

        sa.asrt(str, "<input>")
        sa.asrt(int, 2)
        sa.asrt(str, "g")
        sa.asrt(str, "")

        sa.asrt(str, "<python_box>")
        sa.asrt(int, 1)
        sa.asrt(str, "f")
        sa.asrt(str, "")

        sa.asrt(str, "<input>")
        sa.asrt(int, 6)
        sa.asrt(str, "<main>")
        sa.asrt(str, "")

    def test_php_py_php_py_raise(self, php_space):
        output = self.run('''
            $src = "def h(): raise AttributeError('eek')";
            compile_py_func_global($src);

            function g() { h(); }

            $src = "def f(): g()";
            $f = compile_py_func($src);

            try {
                $f();
            } catch (PyException $e) {
                $ts = $e->getTrace();
                echo count($ts);
                echo $e->getMessage();

                foreach ($ts as $t) {
                    echo $t["file"];
                    echo $t["line"];
                    echo $t["function"];
                    echo $t["args"];
                }
            }
        ''')
        sa = SeqAssert(php_space, output)

        sa.asrt(int, 4)
        sa.asrt(str, "AttributeError: eek")

        sa.asrt(str, "<python_box>")
        sa.asrt(int, 1)
        sa.asrt(str, "h")
        sa.asrt(str, "")

        sa.asrt(str, "<input>")
        sa.asrt(int, 4)
        sa.asrt(str, "g")
        sa.asrt(str, "")

        sa.asrt(str, "<python_box>")
        sa.asrt(int, 1)
        sa.asrt(str, "f")
        sa.asrt(str, "")

        sa.asrt(str, "<input>")
        sa.asrt(int, 8)
        sa.asrt(str, "<main>")
        sa.asrt(str, "")

    def test_php_py_php_php_py_raise(self, php_space):
        output = self.run('''
            $src = "def h(): raise AttributeError('eek')";
            compile_py_func_global($src);

            function g2() { h(); }
            function g() { g2(); }

            $src = "def f(): g()";
            $f = compile_py_func($src);

            try {
                $f();
            } catch (PyException $e) {
                $ts = $e->getTrace();
                echo count($ts);
                echo $e->getMessage();

                foreach ($ts as $t) {
                    echo $t["file"];
                    echo $t["line"];
                    echo $t["function"];
                    echo $t["args"];
                }
            }
        ''')
        sa = SeqAssert(php_space, output)

        sa.asrt(int, 5)
        sa.asrt(str, "AttributeError: eek")

        sa.asrt(str, "<python_box>")
        sa.asrt(int, 1)
        sa.asrt(str, "h")
        sa.asrt(str, "")

        sa.asrt(str, "<input>")
        sa.asrt(int, 4)
        sa.asrt(str, "g2")
        sa.asrt(str, "")

        sa.asrt(str, "<input>")
        sa.asrt(int, 5)
        sa.asrt(str, "g")
        sa.asrt(str, "")

        sa.asrt(str, "<python_box>")
        sa.asrt(int, 1)
        sa.asrt(str, "f")
        sa.asrt(str, "")

        sa.asrt(str, "<input>")
        sa.asrt(int, 9)
        sa.asrt(str, "<main>")
        sa.asrt(str, "")

    def test_php_py_py_php_php_py_raise(self, php_space):
        output = self.run('''
            $src = "def h(): raise AttributeError('eek')";
            compile_py_func_global($src);

            function g2() { h(); }
            function g() { g2(); }

            $src = "def f2(): g()";
            $f2 = compile_py_func($src);

            $src = "def f(): f2()";
            $f = compile_py_func($src);

            try {
                $f();
            } catch (PyException $e) {
                $ts = $e->getTrace();
                echo count($ts);
                echo $e->getMessage();

                foreach ($ts as $t) {
                    echo $t["file"];
                    echo $t["line"];
                    echo $t["function"];
                    echo $t["args"];
                }
            }
        ''')
        sa = SeqAssert(php_space, output)

        sa.asrt(int, 6)
        sa.asrt(str, "AttributeError: eek")

        sa.asrt(str, "<python_box>")
        sa.asrt(int, 1)
        sa.asrt(str, "h")
        sa.asrt(str, "")

        sa.asrt(str, "<input>")
        sa.asrt(int, 4)
        sa.asrt(str, "g2")
        sa.asrt(str, "")

        sa.asrt(str, "<input>")
        sa.asrt(int, 5)
        sa.asrt(str, "g")
        sa.asrt(str, "")

        sa.asrt(str, "<python_box>")
        sa.asrt(int, 1)
        sa.asrt(str, "f2")
        sa.asrt(str, "")

        sa.asrt(str, "<python_box>")
        sa.asrt(int, 1)
        sa.asrt(str, "f")
        sa.asrt(str, "")

        sa.asrt(str, "<input>")
        sa.asrt(int, 11)
        sa.asrt(str, "<main>")
        sa.asrt(str, "")

    def test_php_py_py_raise(self, php_space):
        output = self.run('''
            $src = "def f2(): raise AttributeError('ouch')";
            $f2 = compile_py_func($src);

            $src = "def f(): f2()";
            $f = compile_py_func($src);

            try {
                $f();
            } catch (PyException $e) {
                $ts = $e->getTrace();
                echo count($ts);
                echo $e->getMessage();

                foreach ($ts as $t) {
                    echo $t["file"];
                    echo $t["line"];
                    echo $t["function"];
                    echo $t["args"];
                }
            }
        ''')
        sa = SeqAssert(php_space, output)

        sa.asrt(int, 3)
        sa.asrt(str, "AttributeError: ouch")

        sa.asrt(str, "<python_box>")
        sa.asrt(int, 1)
        sa.asrt(str, "f2")
        sa.asrt(str, "")

        sa.asrt(str, "<python_box>")
        sa.asrt(int, 1)
        sa.asrt(str, "f")
        sa.asrt(str, "")

        sa.asrt(str, "<input>")
        sa.asrt(int, 7)
        sa.asrt(str, "<main>")
        sa.asrt(str, "")

    def test_php_py_nest_php_raise(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f():
                phsrc = "function g() { throw new LogicException('erf'); }"
                g = compile_php_func(phsrc)
                g()
            EOD;
            compile_py_func_global($src);

            try {
                f();
            } catch (LogicException $e) {
                $ts = $e->getTrace();
                echo count($ts);
                echo $e->getMessage();
                foreach ($ts as $t) {
                    echo $t["file"];
                    echo $t["line"];
                    echo $t["function"];
                    echo $t["args"];
                }
            }
        ''')

        sa = SeqAssert(php_space, output)

        sa.asrt(int, 3)
        sa.asrt(str, "erf")

        sa.asrt(str, "<php_box>")
        sa.asrt(int, 1)
        sa.asrt(str, "g")
        sa.asrt(str, "")

        sa.asrt(str, "<python_box>")
        sa.asrt(int, 4)
        sa.asrt(str, "f")
        sa.asrt(str, "")

        sa.asrt(str, "<input>")
        sa.asrt(int, 10)
        sa.asrt(str, "<main>")
        sa.asrt(str, "")

    def test_php_py_nest_php_raise2(self, php_space):
        output = self.run('''
            $src = <<<EOD
            def f():
                phsrc = "function g() { throw new LogicException('erf'); }"
                g = compile_php_func(phsrc,"hi.php", 88)
                g()
            EOD;
            compile_py_func_global($src);

            try {
                f();
            } catch (LogicException $e) {
                $ts = $e->getTrace();
                echo count($ts);
                echo $e->getMessage();
                foreach ($ts as $t) {
                    echo $t["file"];
                    echo $t["line"];
                    echo $t["function"];
                    echo $t["args"];
                }
            }
        ''')

        sa = SeqAssert(php_space, output)

        sa.asrt(int, 3)
        sa.asrt(str, "erf")

        sa.asrt(str, "hi.php")
        sa.asrt(int, 89)
        sa.asrt(str, "g")
        sa.asrt(str, "")

        sa.asrt(str, "<python_box>")
        sa.asrt(int, 4)
        sa.asrt(str, "f")
        sa.asrt(str, "")

        sa.asrt(str, "<input>")
        sa.asrt(int, 10)
        sa.asrt(str, "<main>")
        sa.asrt(str, "")
