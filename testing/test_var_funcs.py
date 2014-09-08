import re
import py.test
from hippy.objects.floatobject import W_FloatObject
from testing.test_interpreter import BaseTestInterpreter

class TestVarFuncs(BaseTestInterpreter):
    def test_print_r(self):
        output = self.run('''
        class A {
            private $y = 5;
        }
        $a = new A;
        $a->x = array($a);
        $a->zzz = array($a);
        $result = print_r($a, TRUE);
        echo str_replace("\\n", '\\n', $result);
        ''')
        expected = """\
A Object
(
    [y:A:private] => 5
    [x] => Array
        (
            [0] => A Object
 *RECURSION*
        )

    [zzz] => Array
        (
            [0] => A Object
 *RECURSION*
        )

)
"""
        assert self.space.str_w(output[0]) == '\\n'.join(expected.split('\n'))

    def test_print_r_builtin(self):
        """Check that print_r() works correctly on built-in classes"""
        output = self.run('''
        $result = print_r(dir('/'), TRUE);
        echo str_replace("\\n", '\\n', $result);''')
        expected = """\
Directory Object
(
    [path] => /
    [handle] => Resource id #1
)
"""
        assert re.sub(r'\d+', '1', self.space.str_w(output[0])) == \
            '\\n'.join(expected.split('\n'))

    @py.test.mark.parametrize(['input', 'expected'],
        [["'xxx'", 0.], ["'3.4bcd'", 3.4], ['2e1', 20.],
         ['5', 5.], ['1.3', 1.3], ["array()", 0.]])
    def test_floatval(self, input, expected):
        output, = self.run('echo floatval(%s);' % input)
        assert output == W_FloatObject(expected)

    def test_floatval_object(self):
        with self.warnings(['Notice: Object of class stdClass '
                            'could not be converted to double']):
            output, = self.run('echo floatval(new stdClass);')
        assert output == W_FloatObject(1.)
