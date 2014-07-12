import py
import os
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

    def test_spl_autoload_register(self):
        output = self.run("""

            $a = spl_autoload_register(function ($class) {
                class DoesntExist_1{};

                echo "first_autoload";
            });

            function test_autoloader($class) {
                class DoesntExist_2{};

                echo "second_autoload";
            }

            $b = spl_autoload_register('test_autoloader');

            new DoesntExist_2;
            echo $a;
            echo $b;
        """)

        assert self.space.str_w(output.pop(0)) == "first_autoload"
        assert self.space.str_w(output.pop(0)) == "second_autoload"
        assert output.pop(0) == self.space.w_True
        assert output.pop(0) == self.space.w_True

    def test_spl_autoload_unregister(self):
        output = self.run("""
            $func_1 = function($class) {
                class DoesntExist_1{};
                echo "first_autoload";
            };

            $func_2 = function($class) {
                class DoesntExist_2{};
                echo "second_autoload";
            };

            spl_autoload_register($func_1);
            spl_autoload_register($func_2);

            echo count(spl_autoload_functions());

            spl_autoload_unregister($func_1);
            spl_autoload_unregister($func_2);

            echo count(spl_autoload_functions());
        """)

        assert self.space.int_w(output.pop(0)) == 2
        assert self.space.int_w(output.pop(0)) == 0

    def test_spl_autoload_functions(self):
        output = self.run("""

            spl_autoload_register(function ($class) {
                class DoesntExist_1{};
                echo "first_autoload";
            });

            spl_autoload_register(function ($class) {
                class DoesntExist_2{};
                echo "first_autoload";
            });

            spl_autoload_register(function ($class) {
                class DoesntExist_3{};
                echo "third_autoload";
            });

            echo count(spl_autoload_functions());

        """)

        # this test could be a bit better, not sure how to test functions though
        assert self.space.int_w(output.pop(0)) == 3

    def test_spl_autoload(self):
        tmpdir = py.path.local(tempfile.mkdtemp())
        tmpdir.join('test_a.inc').write('''<?php

            class Test_A {};

        ?>''')

        tmpdir.join('test_b.php').write('''<?php

            class Test_B {};

        ?>''')


        self.run('''

            set_include_path(get_include_path() . PATH_SEPARATOR . '%s');

            spl_autoload('Test_A');
            spl_autoload('Test_B');

            new Test_A;
            new Test_B;

        ''' % tmpdir)

    def test_spl_autoload_extensions_1(self):
        tmpdir = py.path.local(tempfile.mkdtemp())
        tmpdir.join('test_a.foo.bar').write('''<?php

            class Test_A {};

        ?>''')

        tmpdir.join('test_b.py').write('''<?php

            class Test_B {};

        ?>''')


        self.run('''

            set_include_path(get_include_path() . PATH_SEPARATOR . '%s');
            spl_autoload_extensions('.foo.bar,.py');

            spl_autoload('Test_A');
            spl_autoload('Test_B');

            new Test_A;
            new Test_B;

        ''' % tmpdir)

    def test_spl_autoload_extensions_2(self):

        output = self.run('''

            echo spl_autoload_extensions();
            echo spl_autoload_extensions('.foo.bar,.py');
            echo spl_autoload_extensions();

        ''')

        assert self.space.str_w(output.pop(0)) == ".inc,.php"
        assert self.space.str_w(output.pop(0)) == ".foo.bar,.py"
        assert self.space.str_w(output.pop(0)) == ".foo.bar,.py"

    def test_spl_autoload_call_1(self):

        tmpdir = py.path.local(tempfile.mkdtemp())
        tmpdir.join('test_a.inc').write('''<?php

            class Test_A{};

        ?>''')

        tmpdir.join('test_b.inc').write('''<?php

            class Test_B{};

        ?>''')

        # with self.warnings(["Fatal error: Class 'Ala' not found"]):
        self.run('''
            set_include_path(get_include_path() . PATH_SEPARATOR . '%s');
            echo spl_autoload_call('Test_A');
            echo spl_autoload_call('Test_B');

            new Test_A();
            new Test_B();
        ''' % tmpdir
        )

    def test_spl_autoload_call_2(self):

        tmpdir = py.path.local(tempfile.mkdtemp())
        tmpdir.join('test.inc').write('''<?php

            class Test extends TestBase {};

        ?>''')

        with self.warnings(["Fatal error: Class 'TestBase' not found"]):
            self.run('''
                set_include_path(get_include_path() . PATH_SEPARATOR . '%s');

                echo spl_autoload_call('Test');
            ''' % tmpdir
            )

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


class TestDirectoryIterator(BaseTestInterpreter):
    def test_construct(self):
        tempdir = py.path.local(tempfile.mkdtemp())
        f = tempdir.join('foo.txt')
        f.write('Test file 1')
        f = tempdir.join('bar.txt')
        f.write('Test file 2')
        output = self.run('''
        $dir = new DirectoryIterator(dirname('%s'));
        foreach ($dir as $fileinfo) {
            echo $fileinfo->getFilename();
        }
        ''' % f)
        assert len(output) == 4
        assert self.space.newstr('bar.txt') in output
        assert self.space.newstr('foo.txt') in output
        assert self.space.newstr('.') in output
        assert self.space.newstr('..') in output

    def test_current(self):
        tempdir = py.path.local(tempfile.mkdtemp())
        f = tempdir.join('foo.txt')
        f.write('Test file 1')
        f = tempdir.join('bar.txt')
        f.write('Test file 2')
        output = self.run('''
        $iterator = new DirectoryIterator(dirname('%s'));
        while($iterator->valid()) {
            $file = $iterator->current();
            echo $file->getFilename();
            $iterator->next();
        }
        echo $iterator->key();
        $iterator->next();
        echo $iterator->key();
        echo $iterator->getFilename();
        echo $iterator->getPath();
        ''' % f)
        assert len(output) == 8
        assert self.space.newstr('bar.txt') in output
        assert self.space.newstr('foo.txt') in output
        assert self.space.newstr('.') in output
        assert self.space.newstr('..') in output
        assert self.space.int_w(output[4]) == 4
        assert self.space.int_w(output[5]) == 5
        assert self.space.str_w(output[6]) == ''
        assert self.space.str_w(output[7]) == tempdir

    def test_get_basename(self):
        tempdir = py.path.local(tempfile.mkdtemp())
        f = tempdir.join('foo.txt')
        f.write('Test file 1')
        f = tempdir.join('bar.php')
        f.write('Test file 2')
        output = self.run('''
        $dir = new DirectoryIterator(dirname('%s'));
        foreach ($dir as $fileinfo) {
            if($fileinfo->isFile()) {
                echo $fileinfo->getBasename();
                echo $fileinfo->getBasename('.txt');
            }
        }
        echo $dir->getBasename();
        ''' % f)
        assert len(output) == 5
        assert self.space.newstr('foo.txt') in output
        assert self.space.newstr('foo') in output
        assert self.space.newstr('bar.php') in output
        assert self.space.newstr('bar.php') in output
        assert self.space.str_w(output[4]) == ''

    def test_get_extension(self):
        tempdir = py.path.local(tempfile.mkdtemp())
        f = tempdir.join('foo.txt')
        f.write('Test file 1')
        f = tempdir.join('bar.php')
        f.write('Test file 2')
        output = self.run('''
        $dir = new DirectoryIterator(dirname('%s'));
        foreach ($dir as $fileinfo) {
            if ($fileinfo->isFile()) {
                echo $fileinfo->getExtension();
             }
        }
        echo $dir->getExtension();
        echo $dir->isFile();
        ''' % f)
        assert len(output) == 4
        assert self.space.newstr('txt') in output
        assert self.space.newstr('php') in output
        assert self.space.str_w(output[2]) == ''
        assert output[3] == self.space.w_False

    def test_get_info(self):
        tempdir = py.path.local(tempfile.mkdtemp())
        f = tempdir.join('foo.txt')
        f.write('Test file 1')
        output = self.run('''
        $dir = new DirectoryIterator(dirname('%s'));
        echo $dir->getGroup();
        echo $dir->getInode();
        echo $dir->getOwner();
        echo $dir->getPerms();
        echo $dir->getSize();
        ''' % f)
        for o in output:
            assert o.tp == self.space.tp_int

    def test_get_path(self):
        tempdir = tempfile.mkdtemp()
        output = self.run('''
        $dir = new DirectoryIterator('%s');
        echo $dir->getPath();
        ''' % tempdir)
        assert self.space.str_w(output[0]) == tempdir

    def test_get_pathname(self):
        tempdir = tempfile.mkdtemp()
        f = py.path.local(tempdir).join('foo.txt')
        f.write('Test file')
        output = self.run('''
        $dir = new DirectoryIterator('%s');
        foreach ($dir as $fileinfo) {
            echo $fileinfo->getPathname();
        }
        echo $dir->getPathname();
        ''' % tempdir)
        assert len(output) == 4
        assert self.space.newstr(tempdir + '/foo.txt') in output
        assert self.space.newstr(tempdir + '/.') in output
        assert self.space.newstr(tempdir + '/..') in output
        assert output[3] == self.space.w_False

    def test_get_type(self):
        tempdir = tempfile.mkdtemp()
        f = py.path.local(tempdir).join('foo.txt')
        f.write('Test file')
        output = self.run('''
        $dir = new DirectoryIterator('%s');
        foreach ($dir as $fileinfo) {
            echo $fileinfo->getFilename() . " " . $fileinfo->getType();
        }
        echo $dir->getType();
        ''' % tempdir)
        assert len(output) == 4
        lines = map(self.space.str_w, output)
        assert 'foo.txt file' in lines
        assert '. dir' in lines
        assert '.. dir' in lines
        assert lines[3] == 'dir'

    def test_is_dir(self):
        tempdir = tempfile.mkdtemp()
        f = py.path.local(tempdir).join('foo.txt')
        f.write('Test file')
        output = self.run('''
        $dir = new DirectoryIterator('%s');
        foreach ($dir as $fileinfo) {
            if ($fileinfo->isDir()) {
                echo $fileinfo->getFilename();
            }
        }
        echo $dir->isDir();
        ''' % tempdir)
        assert len(output) == 3
        assert self.space.newstr('.') in output
        assert self.space.newstr('..') in output
        assert output[2] == self.space.w_True

    def test_is_dot(self):
        tempdir = tempfile.mkdtemp()
        f = py.path.local(tempdir).join('foo.txt')
        f.write('Test file')
        output = self.run('''
        $dir = new DirectoryIterator('%s');
        foreach ($dir as $fileinfo) {
            if ($fileinfo->isDot()) {
                echo $fileinfo->getFilename();
            }
        }
        echo $dir->isDot();
        ''' % tempdir)
        assert len(output) == 3
        assert self.space.newstr('.') in output
        assert self.space.newstr('..') in output
        assert output[2] == self.space.w_False

    def test_rewind(self):
        tempdir = tempfile.mkdtemp()
        f = py.path.local(tempdir).join('foo.txt')
        f.write('Test file')
        output = self.run('''
        $dir = new DirectoryIterator('%s');
        $dir->next();
        echo $dir->key();

        $dir->rewind();
        echo $dir->key();
        ''' % tempdir)
        assert len(output) == 2
        assert self.space.int_w(output[0]) == 1
        assert self.space.int_w(output[1]) == 0

    def test_seek(self):
        tempdir = py.path.local(tempfile.mkdtemp())
        f = tempdir.join('foo.txt')
        f.write('Test file 1')
        f = tempdir.join('bar.txt')
        f.write('Test file 2')
        output = self.run('''
        $iterator = new DirectoryIterator(dirname('%s'));
        $iterator->seek(3);
        echo $iterator->getFilename();
        $iterator->seek(0);
        echo $iterator->getFilename();
        $iterator->seek(2);
        echo $iterator->getFilename();
        $iterator->seek(1);
        echo $iterator->getFilename();
        $iterator->seek(10);
        echo $iterator->key();
        ''' % f)
        assert len(output) == 5
        assert self.space.newstr('bar.txt') in output
        assert self.space.newstr('foo.txt') in output
        assert self.space.newstr('.') in output
        assert self.space.newstr('..') in output
        assert self.space.int_w(output[4]) == 4

    def test_to_string(self):
        tempdir = py.path.local(tempfile.mkdtemp())
        f = tempdir.join('foo.txt')
        f.write('Test file 1')
        f = tempdir.join('bar.txt')
        f.write('Test file 2')
        output = self.run('''
        $dir = new DirectoryIterator(dirname('%s'));
        foreach ($dir as $fileinfo) {
            echo strval($fileinfo) . ", " . $fileinfo->__toString();
        }
        ''' % f)
        assert len(output) == 4
        lines = map(self.space.str_w, output)
        assert 'bar.txt, bar.txt' in lines
        assert 'foo.txt, foo.txt' in lines
        assert '., .' in lines
        assert '.., ..' in lines


class TestFilesystemIterator(BaseTestInterpreter):
    def test_fi_construct(self):
        tempdir = py.path.local(tempfile.mkdtemp())
        f = tempdir.join('foo.txt')
        f.write('test file 1')
        f = tempdir.join('bar.txt')
        f.write('test file 2')
        output = self.run('''
        $dir = new filesystemiterator(dirname('%s'));
        foreach ($dir as $fileinfo) {
            echo $fileinfo->getfilename();
        }
        ''' % f)
        assert len(output) == 2
        assert self.space.newstr('bar.txt') in output
        assert self.space.newstr('foo.txt') in output

    def test_current(self):
        tempdir = tempfile.mkdtemp()
        f = py.path.local(tempdir).join('foo.txt')
        f.write('test file 1')
        f = py.path.local(tempdir).join('bar.txt')
        f.write('test file 2')
        output = self.run('''
        $iterator = new filesystemiterator(dirname('%s'),
            FilesystemIterator::CURRENT_AS_PATHNAME);
        foreach ($iterator as $fileinfo) {
            echo $iterator->current();
        }
        ''' % f)
        assert len(output) == 2
        assert self.space.newstr(tempdir + '/bar.txt') in output
        assert self.space.newstr(tempdir + '/foo.txt') in output

    def test_key(self):
        tempdir = tempfile.mkdtemp()
        f = py.path.local(tempdir).join('foo.txt')
        f.write('test file 1')
        f = py.path.local(tempdir).join('bar.txt')
        f.write('test file 2')
        output = self.run('''
        $iter = new filesystemiterator(dirname('%s'),
            FilesystemIterator::KEY_AS_FILENAME);
        foreach ($iter as $fileinfo) {
            echo $iter->key();
        }
        ''' % f)
        assert len(output) == 2
        assert self.space.newstr('bar.txt') in output
        assert self.space.newstr('foo.txt') in output

    def test_next(self):
        tempdir = py.path.local(tempfile.mkdtemp())
        f = tempdir.join('foo.txt')
        f.write('test file 1')
        f = tempdir.join('bar.txt')
        f.write('test file 2')
        output = self.run('''
        $iter = new filesystemiterator(dirname('%s'));
        while ($iter->valid()) {
            echo $iter->getfilename();
            $iter->next();
        }
        ''' % f)
        assert len(output) == 2
        assert self.space.newstr('bar.txt') in output
        assert self.space.newstr('foo.txt') in output

    def test_rewind(self):
        tempdir = tempfile.mkdtemp()
        f = py.path.local(tempdir).join('foo.txt')
        f.write('test file 1')
        f = py.path.local(tempdir).join('bar.txt')
        f.write('test file 2')
        output = self.run('''
        $iter = new filesystemiterator(dirname('%s'),
            FilesystemIterator::KEY_AS_FILENAME);
        echo $iter->key();
        $iter->next();
        echo $iter->key();
        $iter->rewind();
        echo $iter->key();
        ''' % f)
        assert len(output) == 3
        assert output[0] == output[2]

    def test_get_set_flags(self):
        tempdir = tempfile.mkdtemp()
        f = py.path.local(tempdir).join('foo.txt')
        f.write('test file 1')
        f = py.path.local(tempdir).join('bar.txt')
        f.write('test file 2')
        output = self.run('''
        $iterator = new filesystemiterator(dirname('%s'),
            FilesystemIterator::KEY_AS_PATHNAME);
        echo $iterator->getFlags();
        foreach ($iterator as $key => $fileinfo) {
            echo $key;
        }

        $iterator->setFlags(FilesystemIterator::KEY_AS_FILENAME);
        echo $iterator->getFlags();
        foreach ($iterator as $key => $fileinfo) {
            echo $key;
        }

        $iterator->setFlags(-1);
        echo $iterator->getFlags();
        ''' % f)
        assert len(output) == 7
        assert self.space.int_w(output[0]) == 4096
        assert self.space.newstr(tempdir + '/foo.txt') in output[1:3]
        assert self.space.newstr(tempdir + '/bar.txt') in output[1:3]
        assert self.space.int_w(output[3]) == 256
        assert self.space.newstr('foo.txt') in output[4:6]
        assert self.space.newstr('bar.txt') in output[4:6]
        assert self.space.int_w(output[6]) == 16368



class TestRecursiveDirectoryIterator(BaseTestInterpreter):
    def test_construct(self):
        tempdir = py.path.local(tempfile.mkdtemp())
        f = tempdir.join('foo.txt')
        f.write('test file 1')
        f = tempdir.join('bar.txt')
        f.write('test file 2')
        output = self.run('''
        $dir = new recursivedirectoryiterator(dirname('%s'));
        foreach ($dir as $fileinfo) {
            echo $fileinfo->getfilename();
        }
        ''' % f)
        assert len(output) == 4
        assert self.space.newstr('bar.txt') in output
        assert self.space.newstr('foo.txt') in output
        assert self.space.newstr('.') in output
        assert self.space.newstr('..') in output

    def test_key(self):
        tempdir = tempfile.mkdtemp()
        f = py.path.local(tempdir).join('foo.txt')
        f.write('test file 1')
        f = py.path.local(tempdir).join('bar.txt')
        f.write('test file 2')
        output = self.run('''
        $iter = new recursivedirectoryiterator(dirname('%s'),
            FilesystemIterator::KEY_AS_FILENAME);
        foreach ($iter as $fileinfo) {
            echo $iter->key();
        }
        ''' % f)
        assert len(output) == 4
        assert self.space.newstr('bar.txt') in output
        assert self.space.newstr('foo.txt') in output
        assert self.space.newstr('.') in output
        assert self.space.newstr('..') in output

    def test_next(self):
        tempdir = py.path.local(tempfile.mkdtemp())
        f = tempdir.join('foo.txt')
        f.write('test file 1')
        f = tempdir.join('bar.txt')
        f.write('test file 2')
        output = self.run('''
        $iter = new recursivedirectoryiterator(dirname('%s'));
        while ($iter->valid()) {
            echo $iter->getfilename();
            $iter->next();
        }
        ''' % f)
        assert len(output) == 4
        assert self.space.newstr('bar.txt') in output
        assert self.space.newstr('foo.txt') in output
        assert self.space.newstr('.') in output
        assert self.space.newstr('..') in output

    def test_rewind(self):
        tempdir = tempfile.mkdtemp()
        f = py.path.local(tempdir).join('foo.txt')
        f.write('test file 1')
        f = py.path.local(tempdir).join('bar.txt')
        f.write('test file 2')
        output = self.run('''
        $iter = new recursivedirectoryiterator(dirname('%s'),
            FilesystemIterator::KEY_AS_FILENAME);
        echo $iter->key();
        $iter->next();
        echo $iter->key();
        $iter->rewind();
        echo $iter->key();
        ''' % f)
        assert len(output) == 3
        assert output[0] == output[2]

    def test_has_children(self):
        tempdir = tempfile.mkdtemp()
        testdir = os.path.join(tempdir, 'testdir')
        if not os.path.exists(testdir):
            os.makedirs(testdir)
        f = py.path.local(tempdir).join('foo.txt')
        f.write('Test file')
        output = self.run('''
        $dir = new recursivedirectoryiterator('%s');
        foreach ($dir as $fileinfo) {
            if ($dir->hasChildren()) {
                echo $fileinfo->getFilename();
            }
        }
        echo $dir->hasChildren();
        ''' % tempdir)
        assert len(output) == 2
        assert self.space.str_w(output[0]) == 'testdir'
        assert output[1] == self.space.w_False

    def test_get_children(self):
        tempdir = tempfile.mkdtemp()
        testdir = os.path.join(tempdir, 'testdir')
        if not os.path.exists(testdir):
            os.makedirs(testdir)
        f = py.path.local(tempdir).join('foo.txt')
        f.write('Test file')
        output = self.run('''
        $dir = new recursivedirectoryiterator('%s', FilesystemIterator::CURRENT_AS_PATHNAME);
        foreach ($dir as $fileinfo) {
            if ($dir->hasChildren()) {
                echo $dir->getChildren();
            }
        }
        echo $dir->getChildren();
        $dir = new recursivedirectoryiterator('%s');
        foreach ($dir as $fileinfo) {
            if ($dir->hasChildren()) {
                $child = $dir->getChildren();
                echo get_class($child);
                echo $child->getpathname();
            }
        }
        ''' % (tempdir, tempdir))
        assert len(output) == 4
        assert self.space.str_w(output[0]) == tempdir + '/testdir'
        assert self.space.str_w(output[1]) == tempdir + '/'
        assert self.space.str_w(output[2]) == 'RecursiveDirectoryIterator'
        assert self.space.str_w(output[3]) == tempdir + '/testdir/.'
