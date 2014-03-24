import sys
from hippy.objects.strobject import W_ConstStringObject

from testing.test_interpreter import BaseTestInterpreter

def test_is_numeric():
    assert W_ConstStringObject('  \n+123').is_numeric() is True
    assert W_ConstStringObject(' +').is_numeric() is False
    assert W_ConstStringObject('abc').is_numeric() is False

class TestStrObject(BaseTestInterpreter):

    def test_uplusplus(self):
        w = ["Hippy warning: '++' on a string <digits><character><digits> "
             "is dangerous: if <character> would be E, it "
             "would be interpreted as a float"]

        output = self.run('$a = "189";\necho ++$a;')
        assert self.space.is_w(output[0], self.space.newint(190))

        output = self.run('$a = "  -01";\necho ++$a;')
        assert self.space.is_w(output[0], self.space.newint(0))

        output = self.run('$a = " 0x10";\necho ++$a;')
        assert self.space.is_w(output[0], self.space.newint(0x11))

        output = self.run('$a = " 0x 10";\necho ++$a;')
        assert self.space.is_w(output[0], self.space.newstr(" 0x 11"))

        output = self.run('$a = "017";\necho ++$a;')
        assert self.space.is_w(output[0], self.space.newint(18))

        output = self.run('$a = "1z8";\necho ++$a;', w)
        assert self.space.is_w(output[0], self.space.newstr("1z9"))

        output = self.run('$a = "1y9";\necho ++$a;', w)
        assert self.space.is_w(output[0], self.space.newstr("1z0"))

        output = self.run('$a = "1y39";\necho ++$a;', w)
        assert self.space.is_w(output[0], self.space.newstr("1y40"))

        output = self.run('$a = "a";\necho ++$a;')
        assert self.space.is_w(output[0], self.space.newstr("b"))

        output = self.run('$a = "?";\necho ++$a;')
        assert self.space.is_w(output[0], self.space.newstr("?"))

        output = self.run('$a = "y99";\necho ++$a;')
        assert self.space.is_w(output[0], self.space.newstr("z00"))

        output = self.run('$a = "1z9";\necho ++$a;', w)
        assert self.space.is_w(output[0], self.space.newstr("2a0"))

        output = self.run('$a = "z99";\necho ++$a;')
        assert self.space.is_w(output[0], self.space.newstr("aa00"))

        output = self.run('$a = "Y99";\necho ++$a;')
        assert self.space.is_w(output[0], self.space.newstr("Z00"))

        output = self.run('$a = "1Z9";\necho ++$a;', w)
        assert self.space.is_w(output[0], self.space.newstr("2A0"))

        output = self.run('$a = "9Z";\necho ++$a;')
        assert self.space.is_w(output[0], self.space.newstr("10A"))

        output = self.run('$a = "*9Z";\necho ++$a;')
        assert self.space.is_w(output[0], self.space.newstr("*0A"))

        output = self.run('$a = "Z99";\necho ++$a;')
        assert self.space.is_w(output[0], self.space.newstr("AA00"))

        output = self.run('$a = "Cz9Z99";\necho ++$a;')
        assert self.space.is_w(output[0], self.space.newstr("Da0A00"))

        output = self.run('$a = "  - 99";\necho ++$a;')
        assert self.space.is_w(output[0], self.space.newstr("  - 00"))

        output = self.run('$a = "  - 99 ";\necho ++$a;')
        assert self.space.is_w(output[0], self.space.newstr("  - 99 "))

        output = self.run('$a = "4.5";\necho ++$a;')
        assert self.space.is_w(output[0], self.space.newfloat(5.5))

        output = self.run('$a = "";\necho ++$a;')
        assert self.space.is_w(output[0], self.space.newstr("1"))

        output = self.run('$a = " ";\necho ++$a;')
        assert self.space.is_w(output[0], self.space.newstr(" "))

        output = self.run('$a = "9D9";\necho ++$a;', w)
        assert self.space.is_w(output[0], self.space.newstr("9E0"))
        output = self.run('$a = "9E0";\necho ++$a;')
        assert self.space.is_w(output[0], self.space.newfloat(10.0))   # argh
        output = self.run('$a = "9E2";\necho ++$a;')
        assert self.space.is_w(output[0], self.space.newfloat(901.0))

        output = self.run('$a = "?9D9";\necho ++$a;')   # no warning
        assert self.space.is_w(output[0], self.space.newstr("?9E0"))
        output = self.run('$a = "9D9";\necho ++$a;', w)
        assert self.space.is_w(output[0], self.space.newstr("9E0"))

    def test_uminusminus(self):
        output = self.run('$a = "190";\necho --$a;')
        assert self.space.is_w(output[0], self.space.newint(189))

        output = self.run('$a = "  -01";\necho --$a;')
        assert self.space.is_w(output[0], self.space.newint(-2))

        output = self.run('$a = "1z8";\necho --$a;')
        assert self.space.is_w(output[0], self.space.newstr("1z8"))
        # no change

        output = self.run('$a = "c";\necho --$a;')
        assert self.space.is_w(output[0], self.space.newstr("c"))
        # no change

        output = self.run('$a = "4.5";\necho --$a;')
        assert self.space.is_w(output[0], self.space.newfloat(3.5))

        output = self.run('$a = NULL;\necho --$a;')
        assert self.space.is_w(output[0], self.space.w_Null)

    def test_is_true(self):
        output = self.run('if("") $a="yes"; else $a="no";\necho $a;')
        assert self.space.is_w(output[0], self.space.newstr("no"))

        output = self.run('if("0") $a="yes"; else $a="no";\necho $a;')
        assert self.space.is_w(output[0], self.space.newstr("no"))

        output = self.run('if("1") $a="yes"; else $a="no";\necho $a;')
        assert self.space.is_w(output[0], self.space.newstr("yes"))

        output = self.run('if("00") $a="yes"; else $a="no";\necho $a;')
        assert self.space.is_w(output[0], self.space.newstr("yes"))

    def test_cast_to_string(self):
        output = self.run('echo (string)1.5;')
        assert self.space.is_w(output[0], self.space.newstr("1.5"))

    def test_set_char_at(self):
        output = self.run('$x = "abc"; echo $x[1] = "de"; echo $x;')
        assert self.space.str_w(output[0]) == "d"
        assert self.space.str_w(output[1]) == "adc"

    def test_set_char_at_neg(self):
        output = self.run('$x = "abc"; echo $x[-1] = "de"; echo $x;',
                          ["Warning: Illegal string offset:  -1"])
        assert self.space.is_w(output[0], self.space.w_Null)
        assert self.space.str_w(output[1]) == "abc"

    def test_set_char_at_too_large(self):
        output = self.run('$x = "abc"; echo $x[6] = "de"; echo $x;')
        assert self.space.str_w(output[0]) == "d"
        assert self.space.str_w(output[1]) == "abc   d"

    def test_getitem_out_of_bound(self):
        for n in [-1, 3]:
            output = self.run('$x = "abc"; echo $x[%d];' % n,
                              ['Notice: Uninitialized string offset: %d' % n])
            assert self.space.is_w(output[0], self.space.newstr(""))
        for x, y in [('3.0', 3),
                     ('false', 0),
                     ('true', 1),
                     ('null', 0)]:
            output = self.run('$a = ""; echo $a[%s];' % x, [
                'Notice: String offset cast occurred',
                'Notice: Uninitialized string offset: %d' % y])
            assert self.space.is_w(output[0], self.space.newstr(""))
        output = self.run('$a = ""; echo $a[array()];', [
            'Warning: Illegal offset type',
            'Notice: Uninitialized string offset: 0'])
        assert self.space.is_w(output[0], self.space.newstr(""))
        output = self.run('$a = ""; echo $a["3E100"];', [
            "Warning: Illegal string offset '3E100'",
            'Notice: Uninitialized string offset: 3'])
        assert self.space.is_w(output[0], self.space.newstr(""))
        output = self.run(
            '$a = ""; echo $a["10000000000000000000000000000000000000000"];', [
            "Warning: Illegal string offset '10000000000000000000000000000000000000000'",
            'Notice: Uninitialized string offset: %d' % (sys.maxint,)])
        assert self.space.is_w(output[0], self.space.newstr(""))
        output = self.run(
            '$a = ""; echo $a["-1000000000000000000000000000000000000000"];', [
            "Warning: Illegal string offset '-1000000000000000000000000000000000000000'",
            'Notice: Uninitialized string offset: %d' % (-sys.maxint-1,)])
        assert self.space.is_w(output[0], self.space.newstr(""))

    def test_even_more_nonsense(self):
        self.run('$a = ""; echo $a["0y2"];', [
            'Notice: A non well formed numeric value encountered',
            'Notice: Uninitialized string offset: 0'])
        self.run('$a = ""; echo $a["0x2"];', [        # no notice/warning!
            'Notice: Uninitialized string offset: 0'])
        self.run('$a = ""; echo $a["0e2"];', [
            "Warning: Illegal string offset '0e2'",
            'Notice: Uninitialized string offset: 0'])

        self.run('$a = ""; echo $a["1y2"];', [
            'Notice: A non well formed numeric value encountered',
            'Notice: Uninitialized string offset: 1'])
        self.run('$a = ""; echo $a["1x2"];', [
            'Notice: A non well formed numeric value encountered',
            'Notice: Uninitialized string offset: 1'])
        self.run('$a = ""; echo $a["1e2"];', [
            "Warning: Illegal string offset '1e2'",
            'Notice: Uninitialized string offset: 1'])

        self.run('$a = "xx"; echo $a["20.2t"];', [
            "Notice: A non well formed numeric value encountered",
            "Warning: Illegal string offset '20.2t'",
            'Notice: Uninitialized string offset: 20'])

        self.run('$a = ""; echo $a[""];', [
            "Warning: Illegal string offset ''",
            "Notice: Uninitialized string offset: 0"])

        self.run('$a = ""; echo $a[" +0"];', [
            "Notice: Uninitialized string offset: 0"])

        self.run('$a = ""; echo $a[" t"];', [
            "Warning: Illegal string offset ' t'",
            "Notice: Uninitialized string offset: 0"])

        self.run('$a = ""; echo $a[" 5t"];', [
            "Notice: A non well formed numeric value encountered",
            "Notice: Uninitialized string offset: 5"])

        self.run('$a = ""; echo $a[NAN];', [
            "Notice: String offset cast occurred",
            "Hippy warning: cast float to integer: NaN is returned as -9223372036854775808",
            "Notice: Uninitialized string offset: %d" % (-sys.maxint-1,)])

    def test_empty_string_turns_into_guess_what_array(self):
        output = self.run('$a = ""; echo $a[0]=427; echo $a;', [
            'Hippy warning: Creating array from empty value'])
        assert self.space.int_w(output[0]) == 427
        d = output[1].as_dict()
        assert d.keys() == ['0']
        assert self.space.int_w(d.values()[0]) == 427

    def test_even_more_nonsense_setitem(self):
        output = self.run('$a = "x"; $a["3y2"]="!"; echo $a;', [
            'Notice: A non well formed numeric value encountered'])
        assert self.space.str_w(output[0]) == "x  !"

        output = self.run('$a = "x"; $a["0x2"]="?"; echo $a;')
        assert self.space.str_w(output[0]) == "?"

        output = self.run('$a = "x"; $a["3e2"]=":"; echo $a;', [
            "Warning: Illegal string offset '3e2'"])
        assert self.space.str_w(output[0]) == "x  :"

        output = self.run('$a = "x"; $a["3x2"]="/"; echo $a;', [
            'Notice: A non well formed numeric value encountered'])
        assert self.space.str_w(output[0]) == "x  /"

        output = self.run('$a = "x"; $a["3.2t"]="%"; echo $a;', [
            "Notice: A non well formed numeric value encountered",
            "Warning: Illegal string offset '3.2t'"])
        assert self.space.str_w(output[0]) == "x  %"

        output = self.run('$a = "x"; $a[""]="X"; echo $a;', [
            "Warning: Illegal string offset ''"])
        assert self.space.str_w(output[0]) == "X"

        output = self.run('$a = "x"; $a[" +3"]="Y"; echo $a;')
        assert self.space.str_w(output[0]) == "x  Y"

        output = self.run('$a = "x"; $a[" t"]="Z"; echo $a;', [
            "Warning: Illegal string offset ' t'"])
        assert self.space.str_w(output[0]) == "Z"

        output = self.run('$a = "x"; $a[" 3t"]="_"; echo $a;', [
            "Notice: A non well formed numeric value encountered"])
        assert self.space.str_w(output[0]) == "x  _"

        # ignored an highly obscure case:
##        output = self.run('$a = "x"; echo $a[NAN]="M"; echo $a;', [
##            "Notice: String offset cast occurred"])
##        assert self.space.str_w(output[0]) == "M"
##        assert self.space.str_w(output[1]) == "M"

        output = self.run('$a = "x"; echo $a[-2]="M"; echo $a;', [
            "Warning: Illegal string offset:  -2"])
        assert self.space.is_w(output[0], self.space.w_Null)
        assert self.space.str_w(output[1]) == "x"

    def test_isset_out_of_bound(self):
        output = self.run('$x = "abc"; echo isset($x[-1]); echo isset($x[3]);')
        assert self.space.is_w(output[0], self.space.w_False)
        assert self.space.is_w(output[1], self.space.w_False)

    def test_isset_invalid(self):
        output = self.run('$x = "abc"; echo isset($x["x"]);')
        assert self.space.is_w(output[0], self.space.w_False)
        output = self.run('$x = ""; echo isset($x["x"]);')
        assert self.space.is_w(output[0], self.space.w_False)
        output = self.run('$x = "abc"; echo isset($x[array()]);')
        assert self.space.is_w(output[0], self.space.w_False)
        output = self.run('$x = ""; echo isset($x[array()]);')
        assert self.space.is_w(output[0], self.space.w_False)

    def test_isset_bool(self):
        for x in ['false', 'true']:
            output = self.run('$x = ""; echo isset($x[%s]);' % x)
            assert self.space.is_w(output[0], self.space.w_False)
            output = self.run('$x = "a"; echo isset($x[%s]);' % x)
            assert self.space.is_w(output[0], self.space.wrap(x == 'false'))
            output = self.run('$x = "ab"; echo isset($x[%s]);' % x)
            assert self.space.is_w(output[0], self.space.w_True)

    def test_more_isset_strangeness(self):
        output = self.run('$x = "ab"; echo isset($x["2t"]);')
        assert self.space.is_w(output[0], self.space.w_False)
        output = self.run('$x = "abc"; echo isset($x["2t"]);')
        assert self.space.is_w(output[0], self.space.w_False)    # !?
        output = self.run('$x = "abc"; echo isset($x["1E100"]);')
        assert self.space.is_w(output[0], self.space.w_False)    # !?
        output = self.run('$x = "abc"; echo isset($x[2.9]);')
        assert self.space.is_w(output[0], self.space.w_True)
        output = self.run('$x = "abc"; echo isset($x[3.0]);')
        assert self.space.is_w(output[0], self.space.w_False)
