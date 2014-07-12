import py
from hippy.objects.convert import _whitespaces_in_front
from hippy.objects.convert import convert_string_to_number
from hippy.objects.convert import _convert_string_to_number
from hippy.objects.convert import _convert_char_to_number
from hippy.objects.intobject import W_IntObject as Int
from hippy.objects.floatobject import W_FloatObject as Float


def test_whitespaces_in_front():
    assert _whitespaces_in_front('') == 0
    assert _whitespaces_in_front('\t ') == 2
    assert _whitespaces_in_front('\tX\t') == 1
    assert _whitespaces_in_front('   .-.') == 3

def test_convert_string_to_number_int():
    assert convert_string_to_number('') == (Int(0), False)
    assert convert_string_to_number('    ') == (Int(0), False)
    assert convert_string_to_number('+') == (Int(0), False)
    assert convert_string_to_number('-') == (Int(0), False)
    assert convert_string_to_number('1') == (Int(1), True)
    assert convert_string_to_number('\t-101') == (Int(-101), True)
    assert convert_string_to_number('020') == (Int(20), True)
    assert convert_string_to_number('50b') == (Int(50), False)
    assert convert_string_to_number('50x') == (Int(50), False)
    assert convert_string_to_number('5x0') == (Int(5), False)
    assert convert_string_to_number('x50') == (Int(0), False)
    assert convert_string_to_number('0x50') == (Int(80), True)
    assert convert_string_to_number('0X50') == (Int(80), True)
    assert convert_string_to_number('0X50X') == (Int(80), False)
    assert convert_string_to_number('-0x50') == (Int(0), False)
    assert convert_string_to_number('+0x50') == (Int(0), False)

def test_convert_string_to_number_overflow():
    assert convert_string_to_number('1' * 100) == (
        Float(1.11111111111111111111111111e99), True)
    assert convert_string_to_number('-' + '1' * 100) == (
        Float(-1.111111111111111111111111e99), True)
    assert convert_string_to_number('0x' + '1' * 100) == (
        Float(float(int('1' * 100, 16))), True)
    assert convert_string_to_number('-0x' + '1' * 100) == (
        Int(0), False)

def test_convert_string_to_number_float():
    assert convert_string_to_number(' 5.') == (Float(5.0), True)
    assert convert_string_to_number(' -.5') == (Float(-0.5), True)
    assert convert_string_to_number(' .') == (Int(0), False)
    assert convert_string_to_number(' 10.25') == (Float(10.25), True)
    assert convert_string_to_number(' 10.25X') == (Float(10.25), False)
    #
    assert convert_string_to_number('E5') == (Int(0), False)
    assert convert_string_to_number('.E5') == (Int(0), False)
    assert convert_string_to_number('5E') == (Int(5), False)
    assert convert_string_to_number('5.E') == (Float(5.0), False)
    assert convert_string_to_number('5E-') == (Int(5), False)
    assert convert_string_to_number('5E+') == (Int(5), False)
    assert convert_string_to_number('5E0') == (Float(5.0), True)
    assert convert_string_to_number('5E+0') == (Float(5.0), True)
    assert convert_string_to_number('5E-0') == (Float(5.0), True)
    assert convert_string_to_number('5E2') == (Float(500.0), True)
    assert convert_string_to_number('5E-02') == (Float(0.05), True)
    assert convert_string_to_number('5E-02.9') == (Float(0.05), False)
    assert convert_string_to_number('5E-02E9') == (Float(0.05), False)
    assert convert_string_to_number('5e2') == (Float(500.0), True)

def test_convert_string_to_number_single_char():
    for can_be_octal in [False, True]:
        for i in range(256):
            print i
            s = chr(i)
            res1, full1 = _convert_string_to_number(s, can_be_octal)
            res2, full2 = _convert_char_to_number(s)
            assert full1 == full2
            assert type(res1) == type(res2)
            assert res1.__dict__ == res2.__dict__

@py.test.mark.xfail
def test_precision_issues():
    assert convert_string_to_number('55123.456') == (Float(55123.456), True)
