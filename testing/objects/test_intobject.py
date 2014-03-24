import sys
from testing.test_interpreter import BaseTestInterpreter

if sys.maxint == 2**31-1:
    R1 = sys.maxint + 1
    R2 = 2 * sys.maxint
else:
    R1 = 9.2233720368548e+18      # approximately sys.maxint + 1
    R2 = 1.844674407371e+19      # approximately 2 * sys.maxint


class TestIntObject(BaseTestInterpreter):

    def test_cast_to_int(self):
        assert self.echo('(int)42') == '42'
        assert self.echo('(int)FaLsE') == '0'
        assert self.echo('(int)TrUe') == '1'
        assert self.echo('(int)12.34') == '12'
        assert self.echo('(int)-12.34') == '-12'
        assert self.echo('(int)"  42  "') == '42'

    def test_cast_to_integer(self):
        assert self.echo('(integer)-42') == '-42'
        assert self.echo('(integer)FaLsE') == '0'
        assert self.echo('(integer)TrUe') == '1'
        assert self.echo('(integer)-1E3') == '-1000'
        assert self.echo('(integer)"  12.34  "') == '12'
        assert self.echo('(integer)NULL') == '0'

    def test_addition(self):
        assert eval(self.echo('%d + %d' % (sys.maxint, sys.maxint))) == R2
        assert self.echo('gettype(%d + %d)' % (sys.maxint,
                                               sys.maxint)) == 'double'

    def test_subtraction(self):
        assert eval(self.echo('%d - (%d)' % (sys.maxint, -sys.maxint))) == R2
        assert self.echo('gettype(%d - (%d))' % (sys.maxint,
                                                 -sys.maxint)) == 'double'

    def test_multiplication(self):
        assert eval(self.echo('2 * %d' % (sys.maxint,))) == R2

        assert self.echo('gettype(2 * %d)' % (sys.maxint,)) == 'double'

    def test_division(self):
        assert self.echo('5 / 2') == '2.5'
        assert self.echo('6 / 2') == '3'
        assert self.echo('gettype(5 / 2)') == 'double'
        assert self.echo('gettype(6 / 2)') == 'integer'
        assert eval(self.echo('(%d) / (-1)' % (-sys.maxint-1,))) == R1
        assert self.echo('gettype((%d) / (-1))' % (-sys.maxint-1,)) == 'double'

    def test_modulo(self):
        assert self.echo('50 % 20') == '10'
        assert self.echo('50 % -20') == '10'
        assert self.echo('(-50) % 20') == '-10'
        assert self.echo('(-50) % -20') == '-10'

    def test_lshift(self):
        bits = 32 if sys.maxint == 2**31-1 else 64
        assert self.echo('1 << 30') == str(1 << 30)
        assert self.echo('1 << %d' % (bits-1)) == str(-(1 << (bits-1)))
        assert self.echo('1.9 << %d.8' % (bits-1)) == str(-(1 << (bits-1)))
        assert self.echo('123 << %d' % bits) == str(123)
        assert self.echo('123 << %d' % (bits+1)) == str(123 << 1)
        assert self.echo('123 << %d' % (-bits+1)) == str(123 << 1)

    def test_rshift(self):
        bits = 32 if sys.maxint == 2**31-1 else 64
        assert self.echo('123 >> 1') == str(123 >> 1)
        assert self.echo('123 >> %d' % bits) == str(123)
        assert self.echo('123 >> %d' % (bits+1)) == str(123 >> 1)
        assert self.echo('123 >> %d' % (-bits+1)) == str(123 >> 1)
        assert self.echo('(-123) >> 1') == str((-123) >> 1)
        assert self.echo('(-123) >> %d' % bits) == str(-123)
        assert self.echo('(-123) >> %d' % (bits+1)) == str((-123) >> 1)
        assert self.echo('(-123) >> %d' % (-bits+1)) == str((-123) >> 1)

    def test_uplusplus(self):
        output = self.run('$a = -189;\necho ++$a;')
        assert self.space.is_w(output[0], self.space.newint(-188))
        output = self.run('$a = %d;\necho ++$a;' % sys.maxint)
        assert output[0] == self.space.newfloat(float(sys.maxint + 1))
        output = self.run('$a = NULL;\necho ++$a;')
        assert self.space.is_w(output[0], self.space.newint(1))
