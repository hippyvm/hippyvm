from testing.test_interpreter import BaseTestInterpreter
from hippy.error import FatalError
import pytest

class TestPyPyBridgeSpecialMethods(BaseTestInterpreter):
    def test_str(self, php_space):
        output = self.run('''
            class C {
                function __toString() {
                    return "C.__toString";
                }
            }

            $src = "def f(): return str(C())";
            $f = embed_py_func($src);

            echo($f());
        ''')
        assert php_space.str_w(output[0]) == "C.__toString"
