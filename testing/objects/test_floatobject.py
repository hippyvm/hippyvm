import sys
from testing.test_interpreter import BaseTestInterpreter


class TestFloatObject(BaseTestInterpreter):

    def test_repr(self):
        assert self.echo('3.0') == '3'
        assert self.echo('gettype(3.0)') == 'double'

    def test_is(self):
        assert self.echo('5.33 === 5.33') == '1'

    def test_cast_to_float(self):
        assert self.echo('(float)NULL') == '0'
        assert self.echo('(float)TrUe') == '1'
        assert self.echo('(float)5') == '5'
        assert self.echo('(float)5.5') == '5.5'
        assert self.echo('(float)"1E3"') == '1000'

    def test_cast_to_real(self):
        assert self.echo('(real)NULL') == '0'
        assert self.echo('(real)TrUe') == '1'
        assert self.echo('(real)"1.25"') == '1.25'

    def test_cast_to_double(self):
        assert self.echo('(double)nULl') == '0'
        assert self.echo('(double)true') == '1'
        assert self.echo('(double)-5.5') == '-5.5'

    def test_modulo(self):
        # floats are just truncated to ints first
        assert self.echo('5.9 % 2') == '1'
        assert self.echo('5.9 % 2.9') == '1'
        assert self.echo('6.0 % 2.9') == '0'
        assert self.echo('6 % 2.9') == '0'
        assert self.echo('(-5.9) % 2.9') == '-1'
        assert self.echo('5.9 % (-2.9)') == '1'
        assert self.echo('gettype((-5.9) % 2.9)') == 'integer'

    def test_lshift(self):
        # truncated to ints
        assert self.echo('5.9 << 1') == '10'
        assert self.echo('5.9 << 1.9') == '10'
        assert self.echo('gettype(5.9 << 1)') == 'integer'

    def test_rshift(self):
        # truncated to ints
        assert self.echo('32.9 >> 1') == '16'
        assert self.echo('32.9 >> 2.9') == '8'
        assert self.echo('gettype(32.9 >> 1)') == 'integer'

    def test_or(self):
        # truncated to ints
        assert self.echo('6.9 | 1') == '7'
        assert self.echo('6.9 | 1.9') == '7'
        assert self.echo('gettype(6.9 | 1.9)') == 'integer'

    def test_and(self):
        # truncated to ints
        assert self.echo('6.9 & 5.9') == '4'
        assert self.echo('gettype(6.9 & 5.9)') == 'integer'

    def test_xor(self):
        # truncated to ints
        assert self.echo('6.9 ^ 5.9') == '3'
        assert self.echo('gettype(6.9 ^ 5.9)') == 'integer'

    def test_cast_to_int_overflow(self):
        w = ['Hippy warning: cast float to integer: value 1.0E+100 overflows'
             ' and is returned as 0']
        assert self.echo('(int)1E100', w) == '0'

    def test_cast_to_int_overflow_inf(self):
        w = ['Hippy warning: cast float to integer: value INF overflows'
             ' and is returned as 0']
        assert self.echo('(int)INF', w) == '0'

    def test_cast_to_int_overflow_minus_inf(self):
        w = ['Hippy warning: cast float to integer: value -INF overflows'
             ' and is returned as 0']
        assert self.echo('(int)-INF', w) == '0'

    def test_cast_to_int_nan(self):
        f = -sys.maxint - 1
        w = ['Hippy warning: cast float to integer: NaN'
             ' is returned as %d' % f]
        assert self.echo('(int)NAN', w) == str(f)
