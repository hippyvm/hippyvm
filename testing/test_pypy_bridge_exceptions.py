from testing.test_interpreter import BaseTestInterpreter
import pytest

class TestPyPyBridgeExceptions(BaseTestInterpreter):
    def test_py_exn_is_passed_up_to_phpc(self):
        php_space = self.space
        output = self.run('''
            $src = "def raise_ex(): raise ValueError('my error')";
            $raise_ex = embed_py_func($src);
            try {
                $raise_ex();
                echo "no";
            } catch (PyException $e) {
                echo "yes";
            }
        ''')
        assert php_space.str_w(output[0]) == "yes"

    def test_wrapped_py_exn_message(self):
        php_space = self.space
        output = self.run('''
            $src = "def raise_ex(): raise ValueError('my error')";
            $raise_ex = embed_py_func($src);
            try {
                $raise_ex();
                echo "no";
            } catch (PyException $e) {
                echo $e->getMessage();
            }
        ''')
        assert php_space.str_w(output[0]) == "my error"

    def test_php_exn_is_passed_up_to_py(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def catch_php_exn():
                #x = PHPException # forces PHPException to exist
                try:
                    raise_php_exn();
                    return "bad"
                except PHPException:
                    return "ok"
            EOD;

            $catch_php_exn = embed_py_func($src);

            function raise_php_exn() {
                throw new RuntimeException("oh no!");
            }

            $r = $catch_php_exn();
            echo $r;

        ''')
        assert php_space.str_w(output[0]) == "ok"

    def test_php_exn_message_in_py(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def catch_php_exn():
                #x = PHPException # forces PHPException to exist
                try:
                    raise_php_exn();
                    return "bad"
                except PHPException as e:
                    return e.args[0]
                    return e.message
            EOD;

            $catch_php_exn = embed_py_func($src);

            function raise_php_exn() {
                throw new RuntimeException("oh no!");
            }

            $r = $catch_php_exn();
            echo $r;

        ''')
        assert php_space.str_w(output[0]) == "oh no!"

        # XXX more tests that check line number, trace, filename etc.

    def test_exns_can_pass_pass_thru_multiple_langs(self):
        php_space = self.space
        output = self.run('''
            $src = "def py_f1(): php_f()";
            $py_f1 = embed_py_func($src);

            $src2 = "def py_f2(): raise ValueError('explosion')";
            $py_f2 = embed_py_func($src2);

            function php_f() {
                global $py_f2;
                $py_f2();
            }

            try {
                $py_f1();
                echo "fail";
            } catch (PyException $e) {
                echo $e->getMessage();
            }
        ''')
        assert php_space.str_w(output[0]) == "explosion"

