
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

    def test_shell_exec(self):
        output = self.run('''
        echo shell_exec('doesnotexist');
        echo shell_exec('echo 0');
        ''')
        assert output[0] == self.space.w_Null
        assert self.space.str_w(output[1]) == "0\n"
