from testing.test_interpreter import BaseTestInterpreter
import pytest

class TestPyPyBridgeMeta(BaseTestInterpreter):
    # metaprogramming

    @pytest.fixture
    def php_space(self):
        return self.space

    def test_get_class_py_adapter(self, php_space):
        output = self.run('''
        $src = <<<EOD
        def f():
            class A: pass
            return A
        EOD;
        embed_py_func_global($src);
        $a = f();
        echo get_class($a);
        ''')
        assert php_space.str_w(output[0]) == "A"
