
import os
from StringIO import StringIO
from testing.test_interpreter import BaseTestInterpreter

class TestCGI(BaseTestInterpreter):
    def setup_method(self, meth):
        self.env_copy = os.environ.copy()

    def teardown_method(self, meth):
        os.environ = self.env_copy

    def test_get(self):
        os.environ['QUERY_STRING'] = 'xyz=3'
        output = self.run('''
        echo $_GET["xyz"];
        ''', cgi=True)
        assert self.space.str_w(output[0]) == "3"

    def test_php_self(self):
        os.environ['SCRIPT_NAME'] = '/index.php'
        output = self.run('''
        echo $_SERVER["PHP_SELF"];
        ''', cgi=True)
        assert self.space.str_w(output[0]) == "/index.php"

    def test_cookie(self):
        os.environ['HTTP_COOKIE'] = 'mw_installer_session=0374ecdda30e6d06ebeaddfb223dc352'
        output = self.run('''
        function f() {
        echo $_COOKIE["mw_installer_session"];
        }
        f();
        ''', cgi=True)
        assert self.space.str_w(output[0]) == "0374ecdda30e6d06ebeaddfb223dc352"

    def test_post(self):
        data = "x%40=z"
        os.environ['CONTENT_TYPE'] = 'x-www-form-urlencoded; xxasdsa'
        os.environ['CONTENT_LENGTH'] = '6'
        output = self.run('''
        echo $_POST["x@"];
        ''', inp_stream=StringIO(data), cgi=True)
        assert self.space.str_w(output[0]) == "z"

    def test_session(self):
        # no cookie set
        self.run('''
        header("Content-type: text/css");
        session_name("xyz");
        session_id("abcd");
        session_start();
        $_SESSION["a"] = 13;
        ''')
        assert self.interp.sent_headers == ['Content-type: text/css',
                                            'Set-Cookie: xyz=abcd; path=/']

        # now the cookie is set
        os.environ['HTTP_COOKIE'] = 'xyz=abcd;'
        with open("/tmp/xyz-abcd") as f:
            assert f.read() == "a|i:13;"

        output = self.run('''
        session_name("xyz");
        session_start();
        echo $_SESSION["a"];
        ''', cgi=True)
        assert self.unwrap(output[0]) == 13
