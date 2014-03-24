from testing.test_interpreter import BaseTestInterpreter
import random, os


class TestFileObject(BaseTestInterpreter):

    def test_file(self):
        num = random.randrange(0, 10**8)
        filename = "/tmp/test_file_%d.txt" % num
        try:
            f = open(filename, 'w')
            f.write('hello world\n')
            f.write('hello php')
            f.close()
            output = self.run('''
            $f = file("/tmp/test_file_%d.txt");
            echo $f[0];
            echo $f[1];
            ''' % num)
            assert self.space.str_w(output[0]) == "hello world\n"
            assert self.space.str_w(output[1]) == "hello php"
        finally:
            try:
                os.unlink(filename)
            except OSError:
                pass
