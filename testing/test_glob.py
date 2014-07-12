import py
import tempfile
from testing.test_interpreter import BaseTestInterpreter


class TestGlob(BaseTestInterpreter):

    def test_usage(self):
        tempdir = tempfile.mkdtemp()
        f = py.path.local(tempdir).join('foo.txt')
        f.write('Test File 1')
        f = py.path.local(tempdir).join('bar.txt')
        f.write('Test File 2')
        f = py.path.local(tempdir).join('baz.php')
        f.write('Test File 3')
        output = self.run('''
        $dir = '%s';
        foreach (glob($dir . '/*.txt') as $filename) {
            echo $filename;
        }
        ''' % tempdir)
        assert len(output) == 2
        assert self.space.str_w(output[0]) == tempdir + '/bar.txt'
        assert self.space.str_w(output[1]) == tempdir + '/foo.txt'

    def test_basic_funcs(self):
        tempdir = tempfile.mkdtemp()
        f = py.path.local(tempdir).join('foo')
        f.write('Test File 1')
        f = py.path.local(tempdir).join('bar.txt')
        f.write('Test File 2')
        f = py.path.local(tempdir).join('baz.text')
        f.write('Test File 3')

        output = self.run('''
        $dirname = '%s';

        sort_var_dump( glob($dirname."/*.?") );

        function sort_var_dump($results) {
            sort($results);
            foreach ($results as $filename){
                echo $filename;
            }
        }
        ''' % tempdir)
        assert len(output) == 0

    def test_str_error(self):
        tempdir = tempfile.mkdtemp()
        f = py.path.local(tempdir).join('foo')
        f.write('Test File 1')
        with self.warnings(['Warning: glob() expects parameter 1 to be a valid path, string given']):
            self.run('''
            $dirname = '%s';
            glob($dirname."/fo\0");
            ''' % tempdir)
