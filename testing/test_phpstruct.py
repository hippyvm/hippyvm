import sys
import struct
import pytest

from hippy.module import phpstruct
from testing.test_interpreter import BaseTestInterpreter


class TestPackFormat(BaseTestInterpreter):

    def test_1(self):
        fmt = phpstruct.Pack(self.space, "aa",  '').interpret()

        assert fmt.pop(0)[-1] == 1
        assert fmt.pop(0)[-1] == 1

    def test_2(self):
        fmt = phpstruct.Pack(self.space, "a0a1a2",  '').interpret()

        assert fmt.pop(0)[-1] == 0
        assert fmt.pop(0)[-1] == 1
        assert fmt.pop(0)[-1] == 2

    def test_3(self):
        fmt = phpstruct.Pack(self.space, "a*",  '').interpret()

        assert fmt.pop(0)[-1] == sys.maxint


class TestPack(BaseTestInterpreter):

    def test_pack_a_string_nul_padded(self):
        output = self.run("""
            echo pack("a", "string");
            echo pack("a*", "string");
            echo pack("a1", "string");
            echo pack("a0", "string");
            echo pack("a3", "string");
            echo pack("a6", "string");
            echo pack("a7", "string");
            echo pack("a8", "string");

            echo pack("a3a3", "string", "string");
            echo pack("a8a3", "string", "string");
        """)

        assert self.space.str_w(output.pop(0)) == 's'
        assert self.space.str_w(output.pop(0)) == 'string'
        assert self.space.str_w(output.pop(0)) == 's'
        assert self.space.str_w(output.pop(0)) == ''
        assert self.space.str_w(output.pop(0)) == 'str'
        assert self.space.str_w(output.pop(0)) == 'string'
        assert self.space.str_w(output.pop(0)) == 'string\x00'
        assert self.space.str_w(output.pop(0)) == 'string\x00\x00'

        assert self.space.str_w(output.pop(0)) == 'strstr'
        assert self.space.str_w(output.pop(0)) == 'string\x00\x00str'

    def test_pack_A_string_space_padded(self):
        output = self.run("""
            echo pack("A", "string");
            echo pack("A1", "string");
            echo pack("A3", "string");
            echo pack("A6", "string");
            echo pack("A7", "string");
            echo pack("A8", "string");

            echo pack("A3A3", "string", "string");
            echo pack("A8A3", "string", "string");
        """)

        assert self.space.str_w(output.pop(0)) == 's'
        assert self.space.str_w(output.pop(0)) == 's'
        assert self.space.str_w(output.pop(0)) == 'str'
        assert self.space.str_w(output.pop(0)) == 'string'
        assert self.space.str_w(output.pop(0)) == 'string '
        assert self.space.str_w(output.pop(0)) == 'string  '

        assert self.space.str_w(output.pop(0)) == 'strstr'
        assert self.space.str_w(output.pop(0)) == 'string  str'

    def test_pack_Z_nul_padded_string(self):
        output = self.run("""
            echo pack("Z", "string");

            echo pack("Z1", "string");
            echo pack("Z2", "string");
            echo pack("Z3", "string");
            echo pack("Z4", "string");
            echo pack("Z5", "string");
            echo pack("Z6", "string");
            echo pack("Z7", "string");
            echo pack("Z8", "string");
            echo pack("Z9", "string");
        """)

        assert self.space.str_w(output[0]) == '\x00'

        assert self.space.str_w(output[1]) == '\x00'
        assert self.space.str_w(output[2]) == 's\x00'
        assert self.space.str_w(output[3]) == 'st\x00'
        assert self.space.str_w(output[4]) == 'str\x00'
        assert self.space.str_w(output[5]) == 'stri\x00'
        assert self.space.str_w(output[6]) == 'strin\x00'
        assert self.space.str_w(output[7]) == 'string\x00'
        assert self.space.str_w(output[8]) == 'string\x00\x00'
        assert self.space.str_w(output[9]) == 'string\x00\x00\x00'

    def test_pack_string_warnings(self):
        with self.warnings() as w:
            self.run("""
                echo pack("a6a6", "string");
            """)

        assert w[0] == 'Warning: pack(): Type a: not enough arguments'

    def test_pack_h_hex_string_low_nibble_first(self):
        output = self.run("""
            echo pack("h", '8');
            echo pack("h2", '8f');
            echo pack("h3", '8f8');
            echo pack("h4", '8f8f');
            echo pack("h5", '8f8f8');
            echo pack("h2h2", 'FF', 'FF');
        """)

        assert self.space.str_w(output.pop(0)) == '\x08'
        assert self.space.str_w(output.pop(0)) == '\xf8'
        assert self.space.str_w(output.pop(0)) == '\xf8\x08'
        assert self.space.str_w(output.pop(0)) == '\xf8\xf8'
        assert self.space.str_w(output.pop(0)) == '\xf8\xf8\x08'
        assert self.space.str_w(output.pop(0)) == '\xff\xff'

    def test_pack_H_hex_string_high_nibble_first(self):
        output = self.run("""
            echo pack("H", '8');
            echo pack("H2", '8f');
            echo pack("H3", '8f8');
            echo pack("H4", '8f8f');
            echo pack("H5", '8f8f8');
            echo pack("H2H2", 'FF', 'FF');
        """)

        assert self.space.str_w(output.pop(0)) == '\x80'
        assert self.space.str_w(output.pop(0)) == '\x8f'
        assert self.space.str_w(output.pop(0)) == '\x8f\x80'
        assert self.space.str_w(output.pop(0)) == '\x8f\x8f'
        assert self.space.str_w(output.pop(0)) == '\x8f\x8f\x80'
        assert self.space.str_w(output.pop(0)) == '\xff\xff'

    def test_pack_hex_warnings(self):

        with self.warnings() as w:
            self.run("""
                echo pack("hh", "8");
                echo pack("h2", "8");
                echo pack("h", "!");
            """)

        assert w.pop(0) == 'Warning: pack(): Type h: not enough arguments'
        assert w.pop(0) == 'Warning: pack(): Type h: not enough characters in string'
        assert w.pop(0) == 'Warning: pack(): Type h: illegal hex digit !'

    @pytest.mark.parametrize(['fmt', 'py_fmt'], [
        ('c', 'b'),
        ('C', 'b'),
        ('s', 'h'),
        ('S', 'H'),
        ('n', '>H'),
        ('v', '<H'),
        ('i', '=i'),
        ('l', 'i'),
        ('f', 'f'),
        ('d', 'd')])
    def test_pack_numeric(self, fmt, py_fmt):
        assert len(py_fmt) <= 2
        py_fmt2 = py_fmt + py_fmt[-1]
        output = self.run("""
            echo pack("%(fmt)s", 40);
            echo pack("%(fmt)s", '40');
            echo pack("%(fmt)s%(fmt)s", 40, 40);
            echo pack("%(fmt)s2", 40, 40);
            echo pack("%(fmt)s*", 40, 40);
        """ % {'fmt': fmt})

        assert self.space.str_w(output.pop(0)) == struct.pack(py_fmt, 40)
        assert self.space.str_w(output.pop(0)) == struct.pack(py_fmt, 40)
        assert self.space.str_w(output.pop(0)) == struct.pack(py_fmt2, 40, 40)
        assert self.space.str_w(output.pop(0)) == struct.pack(py_fmt2, 40, 40)
        assert self.space.str_w(output.pop(0)) == struct.pack(py_fmt2, 40, 40)

    def test_pack_int_warnings(self):
        with self.warnings() as w:
            self.run("""
                echo pack("c2", 40);
                echo pack("cc", 40);
            """)

        assert w[0] == 'Warning: pack(): Type c: too few arguments'
        assert w[1] == 'Warning: pack(): Type c: too few arguments'

    def test_x_null_byte(self):
        output = self.run("""
            echo pack("x");
            echo pack("x2");
        """)

        assert self.space.str_w(output.pop(0)) == '\x00'
        assert self.space.str_w(output.pop(0)) == '\x00\x00'

    def test_X_back_up_one_byte(self):
        output = self.run("""
            echo pack("a6X", "string");
            echo pack("a1X", "s");
        """)

        assert self.space.str_w(output[0]) == 'strin'
        assert self.space.str_w(output[1]) == ''

    def test_X_back_up_one_byte_warning(self):
        with self.warnings() as w:
            self.run("""
                echo pack("X");
                echo pack("a3XXXX", "str");
            """)

        assert w[0] == 'Warning: pack(): Type X: outside of string'
        assert w[1] == 'Warning: pack(): Type X: outside of string'

    def test_null_fill_to_absolute_position(self):
        output = self.run("""
            echo pack("@2a3a3", "string", "string");
            echo pack("a3a3@7", "alama", "testromek");
        """)

        assert self.space.str_w(output.pop(0)) == '\x00\x00strstr'
        assert self.space.str_w(output.pop(0)) == 'alates\x00'

    def test_star_warnings(self):
        with self.warnings() as w:
            self.run("""
                echo pack("x*");
                echo pack("X*");
                echo pack("@*");
            """)

        assert w[0] == "Warning: pack(): Type x: '*' ignored"
        assert w[1] == "Warning: pack(): Type X: '*' ignored"
        assert w[2] == "Warning: pack(): Type @: '*' ignored"

    def test_arguments_unused_warnings(self):
        with self.warnings() as w:
            self.run("""
                echo pack("", "72");
                echo pack("c", "72", "72");
                echo pack("c", "72", "72", "72");
            """)

        assert w[0] == "Warning: pack(): 1 arguments unused"
        assert w[1] == "Warning: pack(): 1 arguments unused"
        assert w[2] == "Warning: pack(): 2 arguments unused"


class TestUnpackFormat(BaseTestInterpreter):

    def test_1(self):
        fmt = phpstruct.Unpack("a1one/a2two/a*three",  'zyz').interpret()

        assert fmt.pop(0)[1:] == (1, 'one')
        assert fmt.pop(0)[1:] == (2, 'two')
        assert fmt.pop(0)[1:] == (sys.maxint, 'three')

    def test_2(self):
        fmt = phpstruct.Unpack("a0one",  'zyz').interpret()

        assert fmt.pop(0)[1:] == (0, 'one')


class TestUnpack(BaseTestInterpreter):

    def _next(self, o, _type):
        return [
            _type(a[1]) for a in o.pop(0).as_pair_list(self.space)
        ]

    def _next_arr(self, o, _type):
        return [
            [_type(a[0]), _type(a[1])] for a in o.pop(0).as_pair_list(self.space)
        ]

    def test_a_nul_padded_string(self):
        output = self.run("""
            echo unpack("a", "string");
            echo unpack("a*", "string");
            echo unpack("a3", "string");
            echo unpack("a6", "string");
            echo unpack("a7", "string ");
            echo unpack("a7", "string\0");
        """)

        assert self._next(output, self.space.str_w) == ['s']
        assert self._next(output, self.space.str_w) == ['string']
        assert self._next(output, self.space.str_w) == ['str']
        assert self._next(output, self.space.str_w) == ['string']
        assert self._next(output, self.space.str_w) == ['string ']
        assert self._next(output, self.space.str_w) == ['string\x00']

        with self.warnings() as w:
            out = self.run("""
                echo unpack("a8", "string\0");
            """)

            assert out[0] == self.space.w_False
        assert w[0] == 'Warning: unpack(): Type a: not enough input, need 8, have 7'

    def test_Z_nulpadded_string(self):

        output = self.run("""
            echo unpack("Z", "string");
            echo unpack("Z*", "string");
            echo unpack("Z3", "string");
            echo unpack("Z6", "string");
            echo unpack("Z7", "string ");
            echo unpack("Z7", "string\0ala");
        """)

        assert self._next(output, self.space.str_w) == ['s']
        assert self._next(output, self.space.str_w) == ['string']
        assert self._next(output, self.space.str_w) == ['str']
        assert self._next(output, self.space.str_w) == ['string']
        assert self._next(output, self.space.str_w) == ['string ']
        assert self._next(output, self.space.str_w) == ['string']

    def test_A_space_padded_string(self):
        output = self.run("""
            echo unpack("A", "string");
            echo unpack("A*", "string");
            echo unpack("A3", "string");
            echo unpack("A6", "string");
            echo unpack("A8", "string  ");
            echo unpack("A7", "string\0");
            echo unpack("A8", "string  ");
            echo unpack("A*", "string string");
        """)

        assert self._next(output, self.space.str_w) == ['s']
        assert self._next(output, self.space.str_w) == ['string']
        assert self._next(output, self.space.str_w) == ['str']
        assert self._next(output, self.space.str_w) == ['string']
        assert self._next(output, self.space.str_w) == ['string']
        assert self._next(output, self.space.str_w) == ['string']
        assert self._next(output, self.space.str_w) == ['string']
        assert self._next(output, self.space.str_w) == ['string string']

    def test_h_hex_string_low_nibble_first(self):
        output = self.run("""
            echo unpack("h",  '\x08');
            echo unpack("h2", '\xf8');
            echo unpack("h3", '\xf8\x08');
            echo unpack("h4", '\xf8\xf8');
            echo unpack("h5", '\xf8\xf8\x08');
        """)

        assert self._next(output, self.space.str_w) == ['8']
        assert self._next(output, self.space.str_w) == ['8f']
        assert self._next(output, self.space.str_w) == ['8f8']
        assert self._next(output, self.space.str_w) == ['8f8f']
        assert self._next(output, self.space.str_w) == ['8f8f8']

    def test_H_hex_string_high_nibble_first(self):
        output = self.run("""
            echo unpack("H",  '\x80');
            echo unpack("H2", '\x8f');
            echo unpack("H3", '\x8f\x80');
            echo unpack("H4", '\x8f\x8f');
            echo unpack("H5", '\x8f\x8f\x80');
        """)

        assert self._next(output, self.space.str_w) == ['8']
        assert self._next(output, self.space.str_w) == ['8f']
        assert self._next(output, self.space.str_w) == ['8f8']
        assert self._next(output, self.space.str_w) == ['8f8f']
        assert self._next(output, self.space.str_w) == ['8f8f8']

    def test_c_signed_char(self):
        output = self.run("""
            echo unpack("c", "1");
            echo unpack("c2", "12");
            echo unpack("c3", "123");
            echo unpack("c", "\xec");
        """)

        assert self._next(output, self.space.int_w) == [49]
        assert self._next(output, self.space.int_w) == [49, 50]
        assert self._next(output, self.space.int_w) == [49, 50, 51]
        assert self._next(output, self.space.int_w) == [-20]

    def test_C_unsigned_char(self):
        output = self.run("""
            echo unpack("C", "1");
            echo unpack("C2", "12");
            echo unpack("C3", "123");
        """)

        assert self._next(output, self.space.int_w) == [49]
        assert self._next(output, self.space.int_w) == [49, 50]
        assert self._next(output, self.space.int_w) == [49, 50, 51]

    def test_s_signed_short(self):
        output = self.run("""
            echo unpack("s", "AZ");
            echo unpack("s", "\x10\x20");
            echo unpack("s2", "\x10\x20\x10\x20");
            echo unpack("s", "\xec\xff");
        """)

        assert self._next(output, self.space.int_w) == [23105]
        assert self._next(output, self.space.int_w) == [8208]
        assert self._next(output, self.space.int_w) == [8208, 8208]
        assert self._next(output, self.space.int_w) == [-20]

    def test_S_unsigned_short(self):
        output = self.run("""
            echo unpack("S", "AZ");
            echo unpack("S", "\x10\x20");
            echo unpack("S2", "\x10\x20\x10\x20");
            echo unpack("S2", "AZAZ");
        """)

        assert self._next(output, self.space.int_w) == [23105]
        assert self._next(output, self.space.int_w) == [8208]
        assert self._next(output, self.space.int_w) == [8208, 8208]
        assert self._next(output, self.space.int_w) == [23105, 23105]

    def test_n_unsigned_short_big_endian(self):
        output = self.run("""
            echo unpack("n", "AZ");
            echo unpack("n", "\x10\x20");
            echo unpack("n2", "\x10\x20\x10\x20");
            echo unpack("n2", "AZAZ");
        """)

        assert self._next(output, self.space.int_w) == [16730]
        assert self._next(output, self.space.int_w) == [4128]
        assert self._next(output, self.space.int_w) == [4128, 4128]
        assert self._next(output, self.space.int_w) == [16730, 16730]

    def test_v_unsigned_short_little_endian(self):
        output = self.run("""
            echo unpack("v", "AZ");
            echo unpack("v", "\x10\x20");
            echo unpack("v2", "\x10\x20\x10\x20");
            echo unpack("v2", "AZAZ");
        """)

        assert self._next(output, self.space.int_w) == [23105]
        assert self._next(output, self.space.int_w) == [8208]
        assert self._next(output, self.space.int_w) == [8208, 8208]
        assert self._next(output, self.space.int_w) == [23105, 23105]

    def test_i_signed_integer(self):

        output = self.run("""
            echo unpack("i", "AZAZ");
            echo unpack("i2", "AZAZAZAZ");
            echo unpack("i", "\x10\x20\x10\x20");
            echo unpack("i", "\xec\xff\xff\xff");
            echo unpack("i", "\xec\xc1\xe4\xfa");
        """)

        assert self._next(output, self.space.int_w) == [1514232385]
        assert self._next(output, self.space.int_w) == [1514232385, 1514232385]
        assert self._next(output, self.space.int_w) == [537927696]
        assert self._next(output, self.space.int_w) == [-20]
        assert self._next(output, self.space.int_w) == [-85671444]

    def test_I_unsigned_integer(self):
        output = self.run("""
            echo unpack("I", "AZAZ");
            echo unpack("I2", "AZAZAZAZ");
            echo unpack("I", "\x10\x20\x10\x20");
        """)

        assert self._next(output, self.space.int_w) == [1514232385]
        assert self._next(output, self.space.int_w) == [1514232385, 1514232385]
        assert self._next(output, self.space.int_w) == [537927696]

    def test_l_signed_long(self):

        output = self.run("""
            echo unpack("l", "AZAZ");
            echo unpack("l2", "AZAZAZAZ");
            echo unpack("l", "\x10\x20\x10\x20");
            echo unpack("l2", "\x10\x20\x10\x20\x10\x20\x10\x20");
            echo unpack("l", "\xec\xff\xff\xff\xff\xff\xff\xff");
        """)

        assert self._next(output, self.space.int_w) == [1514232385]
        assert self._next(output, self.space.int_w) == [1514232385, 1514232385]
        assert self._next(output, self.space.int_w) == [537927696]
        assert self._next(output, self.space.int_w) == [537927696, 537927696]
        assert self._next(output, self.space.int_w) == [-20]

    def test_L_unsigned_long(self):

        output = self.run("""
            echo unpack("L", "AZAZ");
            echo unpack("L2", "AZAZAZAZ");
            echo unpack("L", "\x10\x20\x10\x20");
            echo unpack("L2", "\x10\x20\x10\x20\x10\x20\x10\x20");
        """)

        assert self._next(output, self.space.int_w) == [1514232385]
        assert self._next(output, self.space.int_w) == [1514232385, 1514232385]
        assert self._next(output, self.space.int_w) == [537927696]
        assert self._next(output, self.space.int_w) == [537927696, 537927696]

    def test_N_unsigned_long(self):
        output = self.run("""
            echo unpack("N", "AZAZ");
            echo unpack("N2", "AZAZAZAZ");
            echo unpack("N", "\x10\x20\x10\x20");
            echo unpack("N2", "\x10\x20\x10\x20\x10\x20\x10\x20");
            echo unpack("N", "\xec\xc1\xe4\xfa");
        """)

        assert self._next(output, self.space.int_w) == [1096434010]
        assert self._next(output, self.space.int_w) == [1096434010, 1096434010]
        assert self._next(output, self.space.int_w) == [270536736]
        assert self._next(output, self.space.int_w) == [270536736, 270536736]
        if sys.maxint <= 2147483647:
            assert self._next(output, self.space.int_w) == [-322837254]
        else:
            assert self._next(output, self.space.int_w) == [3972130042]

    def test_V_unsigned_long(self):
        # unsigned long (always 32 bit, little endian byte order)
        output = self.run("""
            echo unpack("V", "AZAZ");
            echo unpack("V2", "AZAZAZAZ");
            echo unpack("V", "\x10\x20\x10\x20");
            echo unpack("V2", "\x10\x20\x10\x20\x10\x20\x10\x20");
        """)

        assert self._next(output, self.space.int_w) == [1514232385]
        assert self._next(output, self.space.int_w) == [1514232385, 1514232385]
        assert self._next(output, self.space.int_w) == [537927696]
        assert self._next(output, self.space.int_w) == [537927696, 537927696]

    def test_f_float(self):
        output = self.run("""
            echo unpack("f", "\x00\x00\x80?");
            echo unpack("f2",  "\x00\x00\x80?\x00\x00 A");
        """)

        assert self._next(output, self.space.float_w) == [1]
        assert self._next(output, self.space.float_w) == [1, 10]

    def test_d_double(self):
        output = self.run("""
            echo unpack("d", "\x00\x00\x00\x00\x00\x00$@");
            echo unpack("d2", "\x00\x00\x00\x00\x00\x00$@\x00\x00\x00\x00\x00\x00Y@");
        """)

        assert self._next(output, self.space.float_w) == [10.0]
        assert self._next(output, self.space.float_w) == [10.0, 100.0]

    def test_X_back_up_one_byte(self):
        output = self.run("""
            echo unpack("a*one/X6/a*two", "string");
            echo unpack("aone/X/atwo", "string");
            echo unpack("aone/X100/atwo", "string");
        """)

        assert self._next(output, self.space.str_w) == ['string', 'string']
        assert self._next(output, self.space.str_w) == ['s', 's']
        assert self._next(output, self.space.str_w) == ['s', 's']

    def test_nullfill_to_absolute_position(self):

        output = self.run("""
            echo unpack("@/a", "string");
            echo unpack("@2/a", "string");
            echo unpack("@3/a", "string");
            echo unpack("@3/a*", "string");
        """)

        assert self._next(output, self.space.str_w) == ['t']
        assert self._next(output, self.space.str_w) == ['r']
        assert self._next(output, self.space.str_w) == ['i']
        assert self._next(output, self.space.str_w) == ['ing']

    def test_return_array_keys(self):

        output = self.run("""
            echo unpack("c2chars/nint", "\x04\x00\xa0\x00");
            echo unpack("c2/nint", "\x04\x00\xa0\x00");
            echo unpack("c2/n3int", "\x04\x00\xa0\x00\xa0\x00\xa0\x00");
        """)
        assert self._next_arr(output, self.space.str_w) == [
            ['chars1', '4'],
            ['chars2', '0'],
            ['int', '40960']
        ]
        assert self._next_arr(output, self.space.str_w) == [
            ['1', '4'],
            ['2', '0'],
            ['int', '40960']
        ]

        assert self._next_arr(output, self.space.str_w) == [
            ['1', '4'],
            ['2', '0'],
            ['int1', '40960'],
            ['int2', '40960'],
            ['int3', '40960']
        ]

class TestRoundTrips(BaseTestInterpreter):
    def test_double(self):
        output = self.run('''
        $hex = "2d431cebe2362a3f";
        $packed = pack("H*", $hex);
        echo $packed;
        $num = unpack("d", pack("H*", $hex))[1];
        echo $num;
        $serialized = serialize($num);
        echo $serialized;
        $num2 = unserialize(serialize($num));
        echo $num2;
        $packed2 = pack("d", $num2);
        echo $packed2;
        $repr = unpack("H*", $packed2)[1];
        echo $repr;
        ''')
        assert output[0] == self.space.newstr("\x2d\x43\x1c\xeb\xe2\x36\x2a\x3f")
        assert output[1] == self.space.newfloat(0.0002)
        assert output[2] == self.space.newstr('d:0.00020000000000000001;')
        assert output[3] == self.space.newfloat(0.0002)
        assert output[4] == output[0]
        assert output[5] == self.space.newstr("2d431cebe2362a3f")
