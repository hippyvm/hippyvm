import py, os
from testing.test_interpreter import BaseTestInterpreter, hippy_fail


class TestFileOps(BaseTestInterpreter):
    @py.test.mark.skipif("config.option.runappdirect",
                         reason="we have <input> only on hippy")
    def test___file__(self):
        output = self.run('echo __FILE__;')
        assert self.space.str_w(output[0]) == "<input>"

    def test_require_1(self, tmpdir):
        f = tmpdir.join('x.php')
        f.write('''<?php
        $got = __FILE__;
        ?>''')
        output = self.run('''
        echo require("%s");
        echo $got;
        ''' % f)
        assert self.space.int_w(output[0]) == 1
        assert os.path.samefile(self.space.str_w(output[1]), str(f))

    def test_require_2(self, tmpdir):
        f = tmpdir.join('x.php')
        f.write('''<?php
        $b = -42;
        $olda = $a;
        $a = 63;
        ?>''')
        output = self.run('''
        $a = 21;
        require("%s");
        echo $olda, $a, $b;
        ''' % f)
        assert [self.space.int_w(i) for i in output] == [21, 63, -42]

    def test_require_with_return(self, tmpdir):
        f = tmpdir.join('x.php')
        f.write('''<?php
        return "42";
        ?>''')
        output = self.run('''
        echo require("%s");
        ''' % f)
        assert self.space.is_w(output[0], self.space.newstr("42"))

    def test_require_with_return_2(self, tmpdir):
        f = tmpdir.join('x.php')
        f.write('''<?php
        return;
        ?>''')
        output = self.run('''
        echo require("%s");
        ''' % f)
        assert self.space.is_w(output[0], self.space.w_Null)

    def test_require_with_ref(self, tmpdir):
        f = tmpdir.join('x.php')
        f.write('''<?php
        $b1 =& $a1;
        $b2 =& $a2;
        $c = $b2;
        $a2 =& $c;
        $olda1 = $b1;
        $olda2 = $b2;
        $a1 = 63;
        ?>''')
        output = self.run('''
        $a1 = 21;
        $a2 = &$a1;
        require("%s");
        echo $a1, $a2, $b1, $b2, $olda1, $olda2, $c;
        $c++;
        echo $a2;
        ''' % f)
        assert [self.space.int_w(i) for i in output] == [
            63, 21, 63, 63, 21, 21, 21, 22]

    def test_require_indirect_ref(self, tmpdir):
        f = tmpdir.join('x.php')
        f.write('''<?php
        $name = 'x';
        $$name =& $y;
        $y = 5;
        ?>''')
        out, = self.run('''
        require("%s");
        echo $x;
        ''' % f)
        assert self.space.int_w(out) == 5

    def test_require_globals_ref(self, tmpdir):
        f = tmpdir.join('x.php')
        f.write('''<?php
        $GLOBALS['y'] =& $x;
        $y = 5;
        ?>''')
        out, = self.run('''
        require('%s');
        echo $y;
        ''' % f)
        assert self.space.int_w(out) == 5

    def test_require_error(self):
        with self.warnings([
                'Warning: require(does_not_exist): '
                    'failed to open stream: No such file or directory',
                "Fatal error: require(): Failed opening required "
                    "'does_not_exist' (include_path=...)"]):
            output = self.run('''
            $x = require 'does_not_exist';
            ''')
        assert output == []
        with self.warnings([
                # PHP says 'Inappropriate ioctl for device' instead of the
                # expected 'Is a directory'.
                'Warning: require(...): failed to open stream: I...',
                "Fatal error: require(): Failed opening required "
                    "'..' (include_path=...)"]):
            output = self.run('''
            $x = require '..';
            ''')
        assert output == []

    def test_require_path(self, tmpdir):
        on_path = tmpdir.mkdir('on_path')
        on_path.join('a.php').write('''<?php
        return 'on_path';
        ''')
        some_dir = tmpdir.mkdir('some_dir')
        some_dir.join('a.php').write('''<?php
        return 'some_dir';
        ''')
        output = self.run("""
        set_include_path('%s');
        chdir('%s');
        $dir = include 'a.php'; // uses include_path
        echo $dir;
        $dir = include './a.php'; // relative to CWD
        echo $dir;
        """ % (on_path, some_dir))
        assert map(self.space.str_w, output) == ['on_path', 'some_dir']


    def test_require_once(self, tmpdir):
        f = tmpdir.join('x.php')
        f.write('''<?php
        $x += 1;
        return $x;
        ?>''')
        output = self.run('''
        $x = 5;
        $a = require_once '%(f)s';
        echo $x, $x;
        $b = require_once '%(f)s';
        echo $b, $x;
        ''' % locals())
        assert map(self.space.int_w, output) == [6, 6, 1, 6]

    def test_require_normalisation_1(self, tmpdir):
        subdir = tmpdir.mkdir('subdir')
        a = subdir.join('a.php')
        b = subdir.join('b.php')
        a.write('''<?php
        require_once '../subdir/b.php';
        function foo() {}
        ?>''')
        b.write('''<?php
        require_once '../subdir/a.php';
        ?>''')
        output = self.run("chdir('%s'); require_once '%s';" % (subdir, a))
        assert output == []

    def test_require_normalisation_2(self, tmpdir):
        dir1 = tmpdir.mkdir('dir1')
        a1 = dir1.join('a.php')
        dir2 = tmpdir.mkdir('dir2')
        a2 = dir2.join('a.php')
        a1.write('''<?php
        return 'in dir1';
        ?>''')
        a2.write('''<?php
        return 'in dir2';
        ?>''')
        output = self.run('''
        chdir('%s');
        $a = require_once 'a.php';
        echo $a;
        chdir('%s');
        $a = require_once 'a.php';
        echo $a;
        ''' % (dir1, dir2))
        assert map(self.space.str_w, output) == ['in dir1', 'in dir2']

    def test_include(self, tmpdir):
        f = tmpdir.join('x.php')
        f.write('''<?php
        $olda = $a;
        $a = 63;
        ?>''')
        output = self.run('''
        $a = 21;
        $b = include "%s";
        echo $olda, $a, $b;
        ''' % f)
        assert [self.space.int_w(i) for i in output] == [21, 63, 1]

    def test_include_error(self):
        with self.warnings([
                'Warning: include(does_not_exist): '
                    'failed to open stream: No such file or directory',
                "Warning: include(): Failed opening "
                    "'does_not_exist' for inclusion (include_path=...)"]):
            output = self.run('''
            $x = include 'does_not_exist';
            echo $x;
            ''')
        assert self.space.is_w(output[0], self.space.w_False)

    def test_include_once(self, tmpdir):
        f = tmpdir.join('x.php')
        f.write('''<?php
        $x += 1;
        return $x;
        ?>''')
        output = self.run('''
        $x = 5;
        $a = include_once '%(f)s';
        echo $x, $x;
        $b = include_once '%(f)s';
        echo $b, $x;
        ''' % locals())
        assert map(self.space.int_w, output) == [6, 6, 1, 6]

    def test_include_once_error(self):
        with self.warnings([
                'Warning: include_once(does_not_exist): '
                    'failed to open stream: No such file or directory',
                "Warning: include_once(): Failed opening "
                    "'does_not_exist' for inclusion (include_path=...)"]):
            output = self.run('''
            $x = include_once 'does_not_exist';
            echo $x;
            ''')
        assert self.space.is_w(output[0], self.space.w_False)

    def test_include_in_func(self, tmpdir):
        f = tmpdir.join('x.php')
        f.write('''<?php
        $olda = $a;
        $a = 63;
        ?>''')
        output = self.run('''
        function f() {
            $a = 21;
            $b = include "%s";
            echo $olda, $a, $b;
        }
        f();
        ''' % f)
        assert [self.space.int_w(i) for i in output] == [21, 63, 1]

    def test_throw_in_include(self, tmpdir):
        f = tmpdir.join('x.php')
        f.write('''<?php
        throw new Exception("message");
        ?>''')
        output = self.run('''
        try {
            include "%s";
        } catch (Exception $e) {
            echo $e->getMessage();
        }
        ''' % f)
        assert self.space.str_w(output[0]) == 'message'

    def test_extend_included_class(self, tmpdir):
        f = tmpdir.join('x.php')
        f.write('''<?php
        class A {
            function hello() {return 'hello';}
        }
        ?>''')
        output = self.run('''
        include "%s";
        class B extends A {}
        $b = new B;
        echo $b->hello();
        ''' % f)
        assert self.space.str_w(output[0]) == 'hello'


    def test_chgrp_basedir(self):

        with self.warnings([
                'Warning: chgrp(): open_basedir restriction in effect. File(/proc/cpuinfo) is not within the allowed path(s): (.)']):
                output = self.run('''
                ini_set('open_basedir', '.');
                echo chgrp('/proc/cpuinfo', 1);
                ''')

        assert self.space.str_w(output[0]) == ''

    def test_chown_basedir(self):

        with self.warnings([
                'Warning: chown(): open_basedir restriction in effect. File(/proc/cpuinfo) is not within the allowed path(s): (.)']):
                output = self.run('''
                ini_set('open_basedir', '.');
                echo chown('/proc/cpuinfo', 1);
                ''')

        assert self.space.str_w(output[0]) == ''

    def test_dirname_basedir(self):

        output = self.run('''
        ini_set('open_basedir', '.');
        echo dirname('/proc/');
        ''')

        assert self.space.str_w(output[0]) == '/'

    def test_disk_total_space_basedir(self):

        with self.warnings([
                'Warning: disk_total_space(): open_basedir restriction in effect. File(/proc/cpuinfo) is not within the allowed path(s): (.)']):
                output = self.run('''
                ini_set('open_basedir', '.');
                echo disk_total_space('/proc/cpuinfo');
                ''')

        assert self.space.str_w(output[0]) == ''

    def test_mkdir_basedir(self):

        with self.warnings([
                'Warning: mkdir(): open_basedir restriction in effect. File(/proc/cpuinfo/test) is not within the allowed path(s): (.)']):
                output = self.run('''
                ini_set('open_basedir', '.');
                echo mkdir('/proc/cpuinfo/test');
                ''')

        assert self.space.str_w(output[0]) == ''

    def test_pathinfo_basedir(self):

        output = self.run('''
        ini_set('open_basedir', '.');
        echo pathinfo('/proc/cpuinfo/test', 1);
        ''')

        assert self.space.str_w(output[0]) == '/proc/cpuinfo'

    def test_readfile_basedir(self):

        with self.warnings([
                "Warning: readfile(): open_basedir restriction in effect. "
                "File(/proc/cpuinfo) is not within the allowed path(s): (.)",
                "Warning: readfile(/proc/cpuinfo): failed to open "
                "stream: Operation not permitted",]):
                output = self.run('''
                ini_set('open_basedir', '.');
                echo readfile('/proc/cpuinfo');
                ''')

        assert self.space.str_w(output[0]) == ''

    def test_realpath_basedir(self):

        with self.warnings([
                "Warning: realpath(): open_basedir restriction in effect. "
                "File(/proc/cpuinfo) is not within the allowed path(s): (.)",]):
                output = self.run('''
                ini_set('open_basedir', '.');
                echo realpath('/proc/cpuinfo');
                ''')

        assert self.space.str_w(output[0]) == ''

    def test_fresource_basedir(self):
        """ check if you can access fileresource created before
        basedir,  and than narrowed
        we can write flush gets and so on, but restrictions have impact"""
        # First, make sure that the cwd is where we think it is
        os.chdir(os.path.dirname(__file__))

        with self.warnings([
                "Warning: unlink(): open_basedir restriction in effect. "
                "File(to_be_deleted) is not within the allowed path(s): (/tmp)", ]):
            output = self.run('''
            $fname = 'to_be_deleted';
            $h = fopen($fname, 'w');
            ini_set('open_basedir', '/tmp');
            echo fwrite($h, "test");
            echo fflush($h);
            echo fgets($h);
            echo fclose($h);
            echo unlink($fname);
            ''')

        assert self.space.str_w(output[0]) == '4'
        assert self.space.str_w(output[1]) == '1'
        assert self.space.str_w(output[2]) == ''
        assert self.space.str_w(output[3]) == '1'
        os.remove('to_be_deleted')

    def test_basedir(self):
        "we can set open_basedir only once"
        output = self.run('''
        ini_set('open_basedir', '/tmp');
        ini_set('open_basedir', '/home');
        echo ini_get('open_basedir');

        ''')

        assert self.space.str_w(output[0]) == '/tmp'

    def test_phpmemory(self):
        "we can set open_basedir only once"
        output = self.run('''
        $path = 'php://memory';
        $h = fopen($path, "rw+");
        fwrite($h, "bugabuga");
        echo ftell($h);
        fseek($h, 0);
        echo fread($h, 1024);
        fclose($h);

        $h = fopen('php://memory', "rw+");
        fseek($h, 0);
        echo fread($h, 1024);
        ''')

        assert self.space.str_w(output[0]) == '8'
        assert self.space.str_w(output[1]) == 'bugabuga'
        assert self.space.str_w(output[2]) == ''

    def test_file_filter_rot13(self, tmpdir):
        output = self.run('''
        $fp = fopen('%s/test.txt', 'w+');
        stream_filter_append($fp, "string.rot13", STREAM_FILTER_WRITE);
        fwrite($fp, "This is a test\n");
        rewind($fp);
        echo fread($fp, 1024);
        fclose($fp);
        ''' % tmpdir)
        assert self.space.str_w(output[0]) == 'Guvf vf n grfg\n'

    def test_file_filter_rot13_err(self):
        with self.warnings([
                "Warning: stream_filter_append(): unable to locate filter \"wrong_filter\""
        ]):
            output = self.run('''
            $fp = fopen('test.txt', 'w+');
            stream_filter_append($fp, "wrong_filter", STREAM_FILTER_WRITE);
            fwrite($fp, "This is a test\n");
            rewind($fp);
            echo fread($fp, 1024);
            fclose($fp);
            ''')

        assert self.space.str_w(output[0]) == 'This is a test\n'

    def test_file_filter_base64(self, tmpdir):
        # with tmpdir.as_cwd():
        self.run('''
        $param = array('line-length' => 8, 'line-break-chars' => "\r\n");
        $fp = fopen('%s/test.txt', 'w');
        stream_filter_append($fp, 'convert.base64-encode', STREAM_FILTER_WRITE, $param);
        fwrite($fp, "This is a test.\n");
        fclose($fp);
        ''' % tmpdir)
        with open('%s/test.txt' % tmpdir) as fh:
            content = fh.readlines()
            assert content[0] == 'VGhpcyBp\r\n'
            assert content[1] == 'cyBhIHRl\r\n'
            assert content[2] == 'c3QuCg=='

    def test_file_fd_1_open_close_write(self):
        output = self.run('''
        $fp = fopen('php://fd/1', 'r');
        fclose($fp);
        echo "php";
        ''')
        assert self.space.str_w(output[0]) == 'php'
