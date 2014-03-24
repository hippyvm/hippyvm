
import py
import tempfile
from testing.test_interpreter import BaseTestInterpreter


class TestSPL(BaseTestInterpreter):
    def test_array_iterator_iter(self):
        py.test.skip("xxx")
        output = self.run("""
        $x = new ArrayIterator(array(1, 2, 3, 4));
        foreach ($x as $a) {
            echo $a;
        }
        """)
        assert [self.space.int_w(output[i]) for i in range(4)] == [1, 2, 3, 4]


class TestSplFileInfo(BaseTestInterpreter):
    def test_name(self):
        output = self.run('''
        $info = new SplFileInfo('/tmp/file.txt');
        echo $info->getExtension();
        echo $info->getFilename();
        echo $info->getPath();
        echo $info->getPathname();
        ''')
        assert self.space.str_w(output[0]) == 'txt'
        assert self.space.str_w(output[1]) == 'file.txt'
        assert self.space.str_w(output[2]) == '/tmp'
        assert self.space.str_w(output[3]) == '/tmp/file.txt'

    def test_name_none(self):
        output = self.run('''
        $info = new SplFileInfo('');
        echo $info->getFilename();
        echo $info->getExtension();
        echo $info->getGroup();
        echo $info->getInode();
        echo $info->getOwner();
        echo $info->getPerms();
        echo $info->getSize();
        echo $info->getType();
        echo $info->isDir();
        echo $info->isExecutable();
        echo $info->isLink();
        ''')
        assert self.space.str_w(output.pop(0)) == ''
        assert self.space.str_w(output.pop(0)) == ''
        for o in output:
            assert o == self.space.w_False

    def test_get_basename(self):
        output = self.run('''
        $info = new SplFileInfo('file1.txt');
        echo $info->getBasename();

        $info = new SplFileInfo('/tmp/file1.txt');
        echo $info->getBasename();

        $info = new SplFileInfo('/tmp/file1.txt');
        echo $info->getBasename('.txt');

        $info = new SplFileInfo('');
        echo $info->getBasename();
        ''')
        assert self.space.str_w(output[0]) == 'file1.txt'
        assert self.space.str_w(output[1]) == 'file1.txt'
        assert self.space.str_w(output[2]) == 'file1'
        assert self.space.str_w(output[3]) == ''

    def test_get_info(self):
        f = tempfile.mkstemp()[1]
        output = self.run('''
        $info = new SplFileInfo('%s');
        echo $info->getGroup();
        echo $info->getInode();
        echo $info->getOwner();
        echo $info->getPerms();
        echo $info->getSize();
        ''' % f)
        assert output[0].tp == self.space.tp_int
        assert output[1].tp == self.space.tp_int
        assert output[2].tp == self.space.tp_int
        assert output[3].tp == self.space.tp_int
        assert output[4].tp == self.space.tp_int

    def test_get_type(self):
        f = tempfile.mkstemp()[1]
        output = self.run('''
        $info = new SplFileInfo('%s');
        echo $info->getType();

        $info = new SplFileInfo(dirname('%s'));
        echo $info->getType();
        ''' % (f, f))
        assert self.space.str_w(output[0]) == 'file'
        assert self.space.str_w(output[1]) == 'dir'

    def test_is_dir(self):
        f = tempfile.mkstemp()[1]
        output = self.run('''
        $d = new SplFileInfo(dirname('%s'));
        echo $d->isDir();

        $d = new SplFileInfo('%s');
        echo $d->isDir();
        ''' % (f, f))
        assert output[0] == self.space.w_True
        assert output[1] == self.space.w_False

    def test_is_executable(self):
        output = self.run('''
        $info = new SplFileInfo('/usr/bin/php');
        echo $info->isExecutable();

        $info = new SplFileInfo('/usr/bin');
        echo $info->isExecutable();

        $info = new SplFileInfo('foo');
        echo $info->isExecutable();
        ''')
        assert output[0] == self.space.w_True
        assert output[1] == self.space.w_True
        assert output[2] == self.space.w_False

    def test_is_file(self):
        f = tempfile.mkstemp()[1]
        output = self.run('''
        $info = new SplFileInfo('%s');
        echo $info->isFile();

        $info = new SplFileInfo(dirname('%s'));
        echo $info->isFile();
        ''' % (f, f))
        assert output[0] == self.space.w_True
        assert output[1] == self.space.w_False

    def test_to_string(self):
        output = self.run('''
        $info = new SplFileInfo('foo');
        echo $info->__toString();
        echo strval($info);

        $info = new SplFileInfo('/usr/bin/php');
        echo $info->__toString();
        echo strval($info);
        ''')
        assert self.space.str_w(output[0]) == 'foo'
        assert self.space.str_w(output[1]) == 'foo'
        assert self.space.str_w(output[2]) == '/usr/bin/php'
        assert self.space.str_w(output[3]) == '/usr/bin/php'

    def test_readable_writable(self):
        f = tempfile.mkstemp()[1]
        output = self.run('''
        $info = new SplFileInfo('%s');
        echo $info->isReadable();
        echo $info->isWritable();

        $info = new SplFileInfo('/tmp/foo');
        echo $info->isReadable();
        echo $info->isWritable();
        ''' % f)
        assert output[0] == self.space.w_True
        assert output[1] == self.space.w_True
        assert output[2] == self.space.w_False
        assert output[3] == self.space.w_False

    def test_openFile(self):
        f = tempfile.mkstemp()[1]
        output = self.run('''
        $fileinfo = new SplFileInfo('%s');
        if ($fileinfo->isWritable()) {
            $fileobj = $fileinfo->openFile('a');
            echo get_class($fileobj);
            echo $fileobj->fwrite("Foo");
        }
        ''' % f)
        assert self.space.str_w(output[0]) == 'SplFileObject'
        assert self.space.int_w(output[1]) == 3

    def test_openFile_error(self):
        f = tempfile.mkstemp()[1]
        output = self.run('''
        $x = new SplFileInfo('%s');
        try {
            $x->openFile(NULL, NULL);
        } catch (Exception $e) {
        echo get_class($e);
        }
        ''' % f)
        assert self.space.str_w(output[0]) == 'RuntimeException'

    def test_openFile_error_2(self):
        f = tempfile.mkstemp()[1]
        output = self.run('''
        $x = new SplFileInfo('%s');
        try {
            $x->openFile(NULL, NULL, NULL);
        } catch (Exception $e) {
        echo get_class($e);
        }
        ''' % f)
        assert self.space.str_w(output[0]) == 'RuntimeException'


class TestSplFileObject(BaseTestInterpreter):
    def test_subclass(self):
        f = py.path.local(tempfile.mkstemp()[1])
        f.write('$a = 1')
        output = self.run('''
        $file = new SplFileObject("%s");
        echo get_class($file);
        echo is_subclass_of($file, 'SplFileInfo');
        ''' % f)
        assert self.space.str_w(output[0]) == 'SplFileObject'
        assert output[1] == self.space.w_True

    def test_construct(self):
        f = py.path.local(tempfile.mkstemp()[1])
        f.write('$a = 1')
        output = self.run('''
        $file = new SplFileObject("%s");
        $file->rewind();
        foreach ($file as $line_num => $line) {
            echo "$line_num: $line";
        }
        ''' % f)
        assert self.space.str_w(output[0]) == "0: $a = 1"

    def test_current_tostring_key(self):
        f = py.path.local(tempfile.mkstemp()[1])
        f.write('$a = 1')
        output = self.run('''
        $file = new SplFileObject("%s");
        echo $file->current();
        echo strval($file);
        echo $file->__toString();
        ''' % f)
        assert self.space.str_w(output[0]) == "$a = 1"
        assert self.space.str_w(output[1]) == "$a = 1"
        assert self.space.str_w(output[2]) == "$a = 1"

    def test_eof_fgets(self):
        f = py.path.local(tempfile.mkstemp()[1])
        f.write('Test file.\nBlah')
        output = self.run('''
        $file = new SplFileObject("%s");
        while ( ! $file->eof()) {
            echo $file->fgets();
        }
        ''' % f)
        assert self.space.str_w(output[0]) == "Test file.\n"
        assert self.space.str_w(output[1]) == "Blah"

    def test_fwrite_fflush(self):
        f = py.path.local(tempfile.mkstemp()[1])
        output = self.run('''
        $file = new SplFileObject("%s", "r+");
        $file->fwrite("Foo\nBar");
        echo $file->fflush();
        foreach ($file as $k => $line) {
            echo ($file->key()) . ': ' . $file->current();
        }
        ''' % f)
        assert output[0] == self.space.w_True
        assert self.space.str_w(output[1]) == "0: Foo\n"
        assert self.space.str_w(output[2]) == "1: Bar"

    def test_fgetc(self):
        f = py.path.local(tempfile.mkstemp()[1])
        f.write('Foo')
        output = self.run('''
        $file = new SplFileObject('%s');
        while (false !== ($char = $file->fgetc())) {
            echo "$char";
        }
        ''' % f)
        assert self.space.str_w(output[0]) == "F"
        assert self.space.str_w(output[1]) == "o"
        assert self.space.str_w(output[2]) == "o"

    def test_rewind(self):
        f = py.path.local(tempfile.mkstemp()[1])
        output = self.run('''
        $file = new SplFileObject('%s', 'w+');
        echo $file->fwrite("Foo");
        $file->rewind();
        echo $file->current();
        ''' % f)
        assert self.space.int_w(output[0]) == 3
        assert self.space.str_w(output[1]) == "Foo"

    def test_ftruncate(self):
        f = py.path.local(tempfile.mkstemp()[1])
        output = self.run('''
        $file = new SplFileObject('%s', 'w+');
        $file->fwrite("Hello World!");
        $file->ftruncate(5);
        $file->rewind();
        echo $file->fgets();
        ''' % f)
        assert self.space.str_w(output[0]) == "Hello"

    def test_ftell(self):
        f = py.path.local(tempfile.mkstemp()[1])
        output = self.run('''
        $file = new SplFileObject('%s', 'w+');
        $file->fwrite("Hello World!");
        $x = $file->fgets();
        echo $file->ftell();
        ''' % f)
        assert self.space.int_w(output[0]) == 12

    def test_valid(self):
        f = py.path.local(tempfile.mkstemp()[1])
        f.write('Foo')
        output = self.run('''
        $file = new SplFileObject('%s');
        if ($file->valid()) {
            echo $file->current();
        }
        echo $file->valid();
        ''' % f)
        assert self.space.str_w(output[0]) == "Foo"
        assert output[1] == self.space.w_False

    def test_has_children(self):
        f = py.path.local(tempfile.mkstemp()[1])
        output = self.run('''
        $file = new SplFileObject('%s');
        echo $file->hasChildren();
        ''' % f)
        assert output[0] == self.space.w_False

    def test_get_children(self):
        f = py.path.local(tempfile.mkstemp()[1])
        output = self.run('''
        $file = new SplFileObject('%s');
        echo $file->getChildren();
        ''' % f)
        assert output[0] == self.space.w_Null

    def test_fstat(self):
        f = py.path.local(tempfile.mkstemp()[1])
        output = self.run('''
        $file = new SplFileObject('%s');
        $stat = $file->fstat();
        echo is_array($stat);
        ''' % f)
        assert output[0] == self.space.w_True

    def test_getflags(self):
        f = py.path.local(tempfile.mkstemp()[1])
        output = self.run('''
        $file = new SplFileObject('%s');
        echo $file->getFlags();
        ''' % f)
        assert self.space.int_w(output[0]) == 0

    def test_sfo_current_gets(self):
        f = py.path.local(tempfile.mkstemp()[1])
        f.write('1\n2\n3\n')
        output = self.run('''
        $file = new SplFileObject('%s');
        echo $file->current();
        echo $file->fgets();
        echo $file->current();
        ''' % f)
        assert self.space.str_w(output[0]) == "1\n"
        assert self.space.str_w(output[1]) == "2\n"
        assert self.space.str_w(output[2]) == "2\n"

    def test_sfo_current_next(self):
        f = py.path.local(tempfile.mkstemp()[1])
        f.write('1\n2\n3\n')
        output = self.run('''
        $file = new SplFileObject('%s');
        echo $file->current();
        $file->next();
        echo $file->current();
        $file->next();
        echo $file->current();
        ''' % f)
        assert self.space.str_w(output[0]) == "1\n"
        assert self.space.str_w(output[1]) == "2\n"
        assert self.space.str_w(output[2]) == "3\n"

    def test_sfo_current_next_next(self):
        f = py.path.local(tempfile.mkstemp()[1])
        f.write('1\n2\n3\n4\n')
        output = self.run('''
        $file = new SplFileObject('%s');
        echo $file->current();
        $file->next();
        $file->next();
        $file->next();
        $file->next();
        $file->next();
        $file->next();
        $file->next();
        $file->next();
        $file->next();
        $file->next();
        echo $file->current();
        ''' % f)
        assert self.space.str_w(output[0]) == "1\n"
        assert self.space.str_w(output[1]) == "2\n"

    def test_sfo_current_rewind(self):
        f = py.path.local(tempfile.mkstemp()[1])
        f.write('1\n2\n3\n')
        output = self.run('''
        $file = new SplFileObject('%s');
        echo $file->current();
        echo $file->fgets();
        echo $file->current();
        $file->rewind();
        echo $file->ftell();
        echo $file->current();
        echo $file->ftell();

        ''' % f)
        assert self.space.str_w(output[0]) == "1\n"
        assert self.space.str_w(output[1]) == "2\n"
        assert self.space.str_w(output[2]) == "2\n"
        assert self.space.str_w(output[3]) == "0"
        assert self.space.str_w(output[4]) == "1\n"
        assert self.space.str_w(output[5]) == "2"

    def test_sfo_current_feof(self):
        f = py.path.local(tempfile.mkstemp()[1])
        f.write('Test')
        output = self.run('''
        $file2 = new SplFileObject('%s');
        echo "ftell ".$file2->ftell();
        echo "eof ".$file2->eof();
        echo "current ".$file2->current();
        echo "ftell ".$file2->ftell();
        echo "eof ".$file2->eof();
        echo "current ".$file2->current();
        ''' % f)
        assert self.space.str_w(output[0]) == "ftell 0"
        assert self.space.str_w(output[1]) == "eof "
        assert self.space.str_w(output[2]) == "current Test"
        assert self.space.str_w(output[3]) == "ftell 4"
        assert self.space.str_w(output[4]) == "eof 1"
        assert self.space.str_w(output[5]) == "current Test"

    def test_sfo_write_current_feof(self):
        f = py.path.local(tempfile.mkstemp()[1])
        f.write('Test')
        output = self.run('''
        $file2 = new SplFileObject('%s', 'r+');
        echo "ftell ".$file2->ftell();
        echo "eof ".$file2->eof();
        echo "current ".$file2->current();
        echo "write ".$file2->fwrite('PHP');
        echo "ftell ".$file2->ftell();
        echo "eof ".$file2->eof();
        echo "current ".$file2->current();
        echo "next ".$file2->next();
        ''' % f)
        assert self.space.str_w(output[0]) == "ftell 0"
        assert self.space.str_w(output[1]) == "eof "
        assert self.space.str_w(output[2]) == "current Test"
        assert self.space.str_w(output[3]) == "write 3"
        assert self.space.str_w(output[4]) == "ftell 7"
        assert self.space.str_w(output[5]) == "eof 1"
        assert self.space.str_w(output[6]) == "current Test"
        assert self.space.str_w(output[7]) == "next "

    def test_sfo_writeline_current_feof(self):
        f = py.path.local(tempfile.mkstemp()[1])
        f.write('Test')
        output = self.run('''
        $file2 = new SplFileObject('%s', 'r+');
        echo "ftell ".$file2->ftell();
        echo "eof ".$file2->eof();
        echo "current ".$file2->current();
        echo "write ".$file2->fwrite('\nPHP\n');
        $file2->fflush();
        echo "ftell ".$file2->ftell();
        echo "eof ".$file2->eof();
        echo "current ".$file2->current();
        echo "next ".$file2->next();
        echo "rewind ".$file2->rewind();
        echo "current ".$file2->current();
        echo "next ".$file2->next();
        echo "fgets ".$file2->fgets();
        ''' % f)
        assert self.space.str_w(output[0]) == "ftell 0"
        assert self.space.str_w(output[1]) == "eof "
        assert self.space.str_w(output[2]) == "current Test"
        assert self.space.str_w(output[3]) == "write 5"
        assert self.space.str_w(output[4]) == "ftell 9"
        assert self.space.str_w(output[5]) == "eof 1"
        assert self.space.str_w(output[6]) == "current Test"
        assert self.space.str_w(output[7]) == "next "
        assert self.space.str_w(output[8]) == "rewind "
        assert self.space.str_w(output[9]) == "current Test\n"
        assert self.space.str_w(output[10]) == "next "
        assert self.space.str_w(output[11]) == "fgets PHP\n"

    def test_iterate(self):
        f = py.path.local(tempfile.mkstemp()[1])
        f.write('a\nb\nc\n')
        output = self.run('''
        $file = new SplFileObject('%s');
        foreach($file as $n => $l)
        {
           echo $n; echo $l;
        }
        ''' % f)
        assert self.space.str_w(output[0]) == "0"
        assert self.space.str_w(output[1]) == "a\n"

        assert self.space.str_w(output[2]) == "1"
        assert self.space.str_w(output[3]) == "b\n"

        assert self.space.str_w(output[4]) == "2"
        assert self.space.str_w(output[5]) == "c\n"

        assert self.space.str_w(output[6]) == "3"
        assert self.space.str_w(output[7]) == ""
