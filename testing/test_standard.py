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

    def test_exec(self):
        output = self.run('''
        echo exec('doesnotexist');
        echo exec('echo a && echo b');
        ''')
        assert output[0] == self.space.wrap('')
        assert self.space.str_w(output[1]) == "b"

    def test_exec_error(self):
        with self.warnings([
                'Warning: exec(): Cannot execute a blank command']):
            output = self.run('''
            echo exec('');
            echo exec(123);
            ''')
        assert output == [self.space.w_False, self.space.wrap('')]

    def test_exec_2(self):
        output = self.run('''
        $arr = array('foo');
        echo exec('echo a && echo b', $arr);
        echo $arr;
        ''')
        assert map(self.space.str_w, output[1].as_list_w()) == ['foo', 'a', 'b']
