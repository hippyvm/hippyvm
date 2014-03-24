
from testing.test_interpreter import BaseTestInterpreter

class TestStandardModule(BaseTestInterpreter):
    def test_escapeshellarg(self):
        output = self.run('''
        echo escapeshellarg("xyz");
        echo escapeshellarg('$X');
        echo escapeshellarg("'");
        echo escapeshellarg("x'y\\"z");
        echo escapeshellarg("\\\\");
        ''')
        assert self.unwrap(output[0]) == "'xyz'"
        assert self.unwrap(output[1]) == "'$X'"
        assert self.unwrap(output[2]) == "''\\'''"
        assert self.unwrap(output[3]) == "'x'\\''y\"z'"
        assert self.unwrap(output[4]) == "'\\'"
