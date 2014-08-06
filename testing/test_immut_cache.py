from testing.test_interpreter import BaseTestInterpreter


class TestFunctionCache(BaseTestInterpreter):

    def test_declare_function_call(self):
        output = self.run('''
        function myf2197123($a, $b) { return $a + $b; }
        echo myf2197123(10, 20);
        ''')
        assert self.space.int_w(output[0]) == 30
        cell = self.space.global_function_cache.get_cell('myf2197123', object())
        assert cell.constant_value_is_currently_declared
        assert cell.constant_value is cell.currently_declared
        #
        output2 = self.run('''
        function myf2197123($a, $b) { return $a - $b; }
        echo myf2197123(100, 20);
        ''')
        assert self.space.int_w(output2[0]) == 80
        cell2 = self.space.global_function_cache.get_cell('myf2197123', object())
        assert cell2 is cell
        assert not cell2.constant_value_is_currently_declared
        assert cell2.constant_value is not cell2.currently_declared

    def test_has_definition(self):
        output = self.run('''
        define('fooBAR', 42);
        ''')
        assert self.space.global_constant_cache.has_definition('fooBAR')
        assert not self.space.global_constant_cache.has_definition('foobar')
