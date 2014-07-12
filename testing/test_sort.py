import py
from testing.test_interpreter import BaseTestInterpreter
from hippy.sort import (
    _get_key_func, default_cmp, MultiSort,
    identity, to_double, to_string, to_string_lower)

def convert(space, table):
    to_pair = lambda x: (space.wrap(0), space.wrap(x))
    return [map(to_pair, line) for line in table]

def test_get_key_func():
    assert _get_key_func(0) is identity
    assert _get_key_func(8) is identity
    assert _get_key_func(1) is to_double
    assert _get_key_func(9) is to_double
    assert _get_key_func(2) is to_string
    assert _get_key_func(10) is to_string_lower
    with py.test.raises(KeyError):
        _get_key_func(16)

class TestSortDirect(BaseTestInterpreter):
    def test_ArrayMultiSort_direct(self):
        input = [[1, 'a', 1], ['a', 'b', 2], [0., 'b', 3], ['b', 0, 4]]
        keys = [to_double, to_string, identity]
        cmps = [default_cmp, default_cmp, default_cmp]
        signs = [1, -1, -1]
        expected = [[0., 'b', 3], ['a', 'b', 2], ['b', 0, 4], [1, 'a', 1]]
        input_w = convert(self.space, input)
        MultiSort(self.space, input_w, keys, cmps, signs).sort()
        assert input_w == convert(self.space, expected)
