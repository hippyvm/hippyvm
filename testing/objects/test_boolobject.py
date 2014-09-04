
from testing.test_interpreter import BaseTestInterpreter


class TestBoolObject(BaseTestInterpreter):

    def test_repr(self):
        assert self.echo('fAlSe') == ''
        assert self.echo('tRuE') == '1'
        assert self.echo('gettype(FaLSE)') == 'boolean'
        assert self.echo('gettype(TRue)') == 'boolean'

    def test_false_values(self):
        assert self.echo('FALSE ? 42 : 31') == '31'
        assert self.echo('0 ? 42 : 31') == '31'
        assert self.echo('0.0 ? 42 : 31') == '31'
        assert self.echo('(-0.0) ? 42 : 31') == '31'
        assert self.echo('"" ? 42 : 31') == '31'
        assert self.echo('"0" ? 42 : 31') == '31'
        assert self.echo('array() ? 42 : 31') == '31'
        assert self.echo('NULL ? 42 : 31') == '31'
        assert self.echo('$some_unset_variable ? 42 : 31',
                         ['Notice: Undefined variable: some_unset_variable']
                         ) == '31'

    def test_true_values(self):
        assert self.echo('TRUE ? 42 : 31') == '42'
        assert self.echo('1 ? 42 : 31') == '42'
        assert self.echo('(-1) ? 42 : 31') == '42'
        assert self.echo('(-2147483648) ? 42 : 31') == '42'
        assert self.echo('(-9223372036854775808) ? 42 : 31') == '42'
        assert self.echo('-1.0 ? 42 : 31') == '42'
        assert self.echo('1E-50 ? 42 : 31') == '42'
        assert self.echo('1E50 ? 42 : 31') == '42'
        assert self.echo('-1E-50 ? 42 : 31') == '42'
        assert self.echo('-1E50 ? 42 : 31') == '42'
        assert self.echo('(1E200*1E200) ? 42 : 31') == '42'        # INF
        assert self.echo('(-1E200*1E200) ? 42 : 31') == '42'       # -INF
        assert self.echo('((1E200*1E200)*0.0) ? 42 : 31') == '42'  # NAN
        assert self.echo('"00" ? 42 : 31') == '42'
        assert self.echo('"." ? 42 : 31') == '42'
        assert self.echo('array(FALSE) ? 42 : 31') == '42'

    def test_cast_to_bool(self):
        assert self.echo('(bool)5') == '1'
        assert self.echo('(bool)0.0') == ''
        assert self.echo('(bool)"foo"') == '1'

    def test_cast_to_boolean(self):
        assert self.echo('(boolean)5') == '1'
        assert self.echo('(boolean)0.0') == ''
        assert self.echo('(boolean)"foo"') == '1'

    def test_plusplus(self):
        output = self.run('''$i = true; $i++; echo $i;''')
        assert output[0] == self.space.wrap(True)

        output = self.run('''$i = false; $i++; echo $i;''')
        assert output[0] == self.space.wrap(False)
