import tempfile
import pytest
from testing.test_interpreter import BaseTestInterpreter


class TestComparisons(BaseTestInterpreter):
    # Test PHP's "recursive" comparison scheme.
    # Implemented hippy iteratively to avoid exhausting the stack

    # XXX move into Base
    @pytest.fixture
    def php_space(self):
        return self.space

    def test_compare_int_eq_int(self, php_space):
        output = self.run("""
        $a = 1;
        $b = 1;
        echo $a == $b;
        """)
        assert php_space.is_true(output[0])

    def test_compare_int_arry_eq_int_arry(self, php_space):
        output = self.run("""
        $a = array(1, 6, 8);
        $b = array(1, 6, 8);
        echo $a == $b;
        """)
        assert php_space.is_true(output[0])

    def test_compare_nested_int_arry_eq_int_arry(self, php_space):
        output = self.run("""
        $a = array(1, array(8));
        $b = array(1, array(8));
        echo $a == $b;
        """)
        assert php_space.is_true(output[0])

    def test_compare_nested_int_arry_not_eq_int_arry(self, php_space):
        output = self.run("""
        $a = array(1, array(9));
        $b = array(0, array(9));
        echo $a == $b;
        """)
        assert not php_space.is_true(output[0])
