from testing.test_interpreter import BaseTestInterpreter
import pytest

class TestFrameDebug(BaseTestInterpreter):

    def test_frame_debug(self, php_space):
        output = self.run('''
        $a = 1;
        $b = 2;
        $c = $a;
        $d =& $a;
        frame_dump();

        function f($k) {
            frame_dump();
        }

        f($a);
        ''')
        print(output)
