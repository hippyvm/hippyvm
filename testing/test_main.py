
import py, re, tempfile, os
from hippy.main import main
from hippy.constants import E_ALL, E_NOTICE

class TestMain(object):
    def setup_method(self, meth):
        self.tmpname = meth.im_func.func_name

    def run(self, code, capfd, expected_err=False, expected_exitcode=0,
            cgi=False, args=[]):
        tmpdir = py.path.local.make_numbered_dir('hippy')
        phpfile = tmpdir.join(self.tmpname + '.php')
        phpfile.write(code)
        r = main(str(phpfile), args, cgi, None)
        out, err = capfd.readouterr()
        if expected_err:
            assert not expected_exitcode,"can't give both this and expected_err"
            return out, err
        assert r == expected_exitcode
        assert not err
        return out

    def test_running(self, capfd):
        out = self.run("""<?php
        $x = 3;
        echo $x;
        ?>""", capfd)
        assert out == "3"

    def test_running2(self, capfd):
        out = self.run("""<?php
        $x = 3;
        echo $x;
        ?>""", capfd)
        assert out == "3"

    def test_running3(self, capfd):
        out = self.run("""<?
        $x = 3;
        echo $x;
        ?>""", capfd)
        assert out == "3"

    def test_running4(self, capfd):
        out = self.run('''<?php
        $n = 20;
        while ($n-- > 0) {
          echo $n;
        }
        ?>''', capfd)
        assert out == '191817161514131211109876543210'

    def test_exit(self, capfd):
        out = self.run('''<?php echo 5; exit("abc"); echo 6;?>''', capfd)
        assert out == '5abc'
        out = self.run('''<?php echo 5; exit(42); echo 6;?>''', capfd,
                       expected_exitcode=42)
        assert out == '5'

    def test_traceback(self, capfd):
        out, err = self.run('''Hello World
        <?php
        f();
        ?>''', capfd, expected_err=True)
        errlines = err.splitlines()
        assert re.match('In function <main>, file .*test_traceback.php, '
                        'line 3', errlines[0])
        assert re.match(' *f\(\); *', errlines[1])
        assert errlines[2].startswith('Fatal error: '
                                      'Call to undefined function f()')

    def test_multiple_blocks(self, capfd):
        out = self.run(
            'Hello <? echo "little"; ?> <?php echo "world"?>\n!', capfd)
        assert out == 'Hello little world!'

    def test_compilation_warning(self, capfd):
        out, err = self.run('''<?php
        function f($x, $x) { }
        ?>''', capfd, expected_err=True)
        assert err == "Hippy warning: Argument list contains twice '$x'\n"

    def test_buffering(self, capfd):
        out = self.run('''<?
        function f($x) {
           return $x . "a";
        }
        ob_start("f");
        echo "a";
        ?>b<?
        echo "c";
        ?>''', capfd)
        assert out == "abca"
        out = self.run('''<?
        function f($x) {
          return $x . "+";
        }
        echo "a";
        ob_start("f");
        echo "b";
        ob_end_flush();
        echo "c";
        ?>''', capfd)
        assert out == "ab+c"

    def test_exception_handler(self, capfd):
        output = self.run('''<?
        function f($e) {
            echo "exception";
        }
        set_exception_handler("f");
        throw new Exception();
        echo "xyz";
        ?>
        ''', capfd)
        assert output == "exception"

    def test_uncaught_exception(self, capfd):
        out, err = self.run('''<?
        throw new Exception();
        echo "xyz";
        ?>
        ''', capfd, expected_err=True)
        assert out == ""
        assert re.match("""\
Fatal error: Uncaught exception 'Exception' in .*:\d+
Stack trace:
#0 {main}
  thrown in .*""", err)

    def test_headers(self, capfd):
        output = self.run('''<?
        header("xyz")
        ?>''', capfd, cgi=True)
        assert output == "Content-Type: text/html\r\nxyz\r\n\r\n"

    def test_headers_replace(self, capfd):
        output = self.run('''<?
        header("Content-Type: text/css", true);
        ?>''', capfd, cgi=True)
        assert output == "Content-Type: text/css\r\n\r\n"

    def test_hippy_ini_read(self, capfd):
        tmpdir = tempfile.mkdtemp()
        d = os.getcwd()
        f = open(os.path.join(tmpdir, "hippy.ini"), "w")
        f.write("error_reporting = E_ALL & ~E_NOTICE\n")
        f.close()
        os.chdir(tmpdir)
        try:
            output = self.run('''<?
            echo ini_get("error_reporting");
            echo $a;
            ?>''', capfd)
            assert output == str(E_ALL & ~E_NOTICE)
        finally:
            os.chdir(d)
