from testing.test_interpreter import BaseTestInterpreter
import pytest

class TestPyPyBridgeTraceBacks(BaseTestInterpreter):

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
        assert php_space.int_w(output[0]) == 2

        assert php_space.str_w(output[1]) == "<python_box>"
        assert php_space.int_w(output[2]) == 1
        assert php_space.str_w(output[3]) == "f"
        assert php_space.str_w(output[4]) == ""

        assert php_space.str_w(output[5]) == "<input>"
        assert php_space.int_w(output[6]) == 5
        assert php_space.str_w(output[7]) == "<main>"
        assert php_space.str_w(output[8]) == ""

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
        assert php_space.int_w(output[0]) == 2

        assert php_space.str_w(output[1]) == "myfile.php"
        assert php_space.int_w(output[2]) == 11
        assert php_space.str_w(output[3]) == "f"
        assert php_space.str_w(output[4]) == ""

        assert php_space.str_w(output[5]) == "<input>"
        assert php_space.int_w(output[6]) == 5
        assert php_space.str_w(output[7]) == "<main>"
        assert php_space.str_w(output[8]) == ""

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
        assert php_space.int_w(output[0]) == 2

        assert php_space.str_w(output[1]) == "<python_box>"
        assert php_space.int_w(output[2]) == 1
        assert php_space.str_w(output[3]) == "f"
        assert php_space.str_w(output[4]) == ""

        assert php_space.str_w(output[5]) == "<input>"
        assert php_space.int_w(output[6]) == 5
        assert php_space.str_w(output[7]) == "<main>"
        assert php_space.str_w(output[8]) == ""

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
        assert php_space.int_w(output[0]) == 2

        assert php_space.str_w(output[1]) == "afile.php"
        assert php_space.int_w(output[2]) == 667
        assert php_space.str_w(output[3]) == "f"
        assert php_space.str_w(output[4]) == ""

        assert php_space.str_w(output[5]) == "<input>"
        assert php_space.int_w(output[6]) == 5
        assert php_space.str_w(output[7]) == "<main>"
        assert php_space.str_w(output[8]) == ""
