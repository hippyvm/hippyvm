from testing.test_interpreter import BaseTestInterpreter
from hippy.error import FatalError
import pytest

class TestPyPyBridgeScope(BaseTestInterpreter):
    def test_str(self):
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
        print output
        assert self.space.str_w(output[0]) == "C.__toString"
