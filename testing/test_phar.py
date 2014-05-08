import tempfile
from testing.test_interpreter import BaseTestInterpreter


class TestPhar(BaseTestInterpreter):

    def test_create_phar(self):
        output = self.run('''
            if (Phar::canWrite()) {
            $p = new Phar('newphar.tar.phar', 0, 'newphar.tar.phar');
            $p->startBuffering();
            $p['file1.txt'] = 'Information';
            $p->stopBuffering();
            }

            $p2 = new Phar('newphar.tar.phar', 0);
            foreach (new RecursiveIteratorIterator($p2) as $file) {
                echo $file->getFileName();
                echo file_get_contents($file->getPathName());
            }
        ''')
        assert len(output) == 2
        assert self.space.str_w(output[0]) == 'file1.txt'
        assert self.space.str_w(output[1]) == 'Information'

    def test_add_empty_dir(self):
        tempdir = tempfile.mkdtemp()
        output = self.run('''
            if (Phar::canWrite()) {
            $p = new Phar('newphar.tar.phar', 0, 'newphar.tar.phar');
            $p->startBuffering();
            $p['file1.txt'] = 'Information';
            $p->stopBuffering();
            }

            $p2 = new Phar('newphar.tar.phar', 0);
            $p2->addEmptyDir('%s');
            echo $p2['%s']->isDir();        # TODO: Catch exception on failure
            ''' % (tempdir, tempdir))
        assert output[0] == self.space.w_True
