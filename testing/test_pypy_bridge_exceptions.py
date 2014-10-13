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

    def test_php_exn_str_in_py(self):
        php_space = self.space
        output = self.run('''
            $src = <<<EOD
            def catch_php_exn():
                try:
                    raise_php_exn();
                    return "bad"
                except PHPException as e:
                    return str(e)
            EOD;

            $catch_php_exn = embed_py_func($src);

            function raise_php_exn() {
                throw new RuntimeException("oh no!");
            }

            $r = $catch_php_exn();
            echo $r;

        ''')
        assert php_space.str_w(output[0]) == "oh no!"

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

    def test_python_lookup_missing_php_attr(self):
        pytest.skip("BROKEN")
        php_space = self.space
        output = self.run("""
            $src = <<<EOD
            def ref():
                return C().x
            EOD;
            $ref = embed_py_func($src);

            class C {}
            $ref();
        """)
        assert php_space.int_w(output[0]) == 2
