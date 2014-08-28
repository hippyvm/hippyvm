# -*- encoding:utf-8 -*-
import pytest

from hippy.objspace import getspace
from .test_interpreter import BaseTestInterpreter
from hippy.localemodule import rsetlocale, strcoll_u
from rpython.rlib.rlocale import LC_CTYPE, LC_COLLATE, LocaleError

def has_locales(*locales):
    """Check if te locales are available on the system"""
    orig_locale = rsetlocale(LC_CTYPE, None)
    try:
        for locale in locales:
            rsetlocale(LC_CTYPE, locale)
            rsetlocale(LC_COLLATE, locale)
    except LocaleError:
        return False
    else:
        return True
    finally:
        rsetlocale(LC_CTYPE, orig_locale)

def requires_locales(*locales):
    locale_string = ', '.join("'%s'" % l for l in locales)
    return pytest.mark.skipif("not has_locales(%s)" % locale_string,
        reason="This test requires locales: %s" % locale_string)

interp = BaseTestInterpreter()
interp.init_space()
space = interp.space

@requires_locales("fr_FR.ISO8859-1")
def test_strcoll_u():
    orig_locale = rsetlocale(LC_COLLATE, None)
    rsetlocale(LC_COLLATE, "fr_FR.ISO8859-1")
    e_acute = u'é'.encode('latin1')
    assert strcoll_u('f', 'e') > 0
    assert strcoll_u('f', e_acute) > 0
    rsetlocale(LC_COLLATE, orig_locale)

@requires_locales("fr_FR")
def test_setlocale():
    output = interp.run('''
    $prev = setlocale(LC_TIME, "0");
    setlocale(LC_TIME, "C");

    $locale = setlocale(LC_TIME, "0");
    echo $locale;
    echo setlocale(LC_TIME, "fr_FR");
    echo setlocale(LC_TIME, $locale);
    echo setlocale(LC_TIME, "not a locale");
    echo setlocale(LC_TIME, "x", "y", "C");
    echo setlocale(LC_TIME, array("x", "y", "C"));
    echo setlocale(LC_TIME, array("x", "y"), "C");

    setlocale(LC_TIME, $prev);
    ''')
    assert map(space.str_w, output[:3]) == ['C', 'fr_FR', 'C']
    assert space.is_w(output[3], space.w_False)
    assert space.str_w(output[4]) == 'C'
    assert space.str_w(output[5]) == 'C'
    assert space.is_w(output[6], space.w_False)

@pytest.mark.skipif('config.option.runappdirect or not has_locales("fr_FR")')
def test_localeconv():
    output = interp.run('''
    setlocale(LC_ALL, "fr_FR");
    var_dump(localeconv());
    ''')
    assert ''.join(output) == """\
array(18) {
  ["decimal_point"]=>
  string(1) ","
  ["thousands_sep"]=>
  string(1) " "
  ["int_curr_symbol"]=>
  string(4) "EUR "
  ["currency_symbol"]=>
  string(3) "EUR"
  ["mon_decimal_point"]=>
  string(1) ","
  ["mon_thousands_sep"]=>
  string(1) " "
  ["positive_sign"]=>
  string(0) ""
  ["negative_sign"]=>
  string(1) "-"
  ["int_frac_digits"]=>
  int(2)
  ["frac_digits"]=>
  int(2)
  ["p_cs_precedes"]=>
  int(0)
  ["p_sep_by_space"]=>
  int(1)
  ["n_cs_precedes"]=>
  int(0)
  ["n_sep_by_space"]=>
  int(1)
  ["p_sign_posn"]=>
  int(1)
  ["n_sign_posn"]=>
  int(1)
  ["grouping"]=>
  array(1) {
    [0]=>
    int(3)
  }
  ["mon_grouping"]=>
  array(1) {
    [0]=>
    int(3)
  }
}
"""

@requires_locales("fr_FR.ISO-8859-1", "en_US.UTF-8")
def test_nl_langinfo():
    output = interp.run('''
    setlocale(LC_TIME, "en_US.UTF-8");
    echo nl_langinfo(ABDAY_3);
    setlocale(LC_TIME, "fr_FR.ISO-8859-1");
    echo nl_langinfo(ABDAY_3);
    setlocale(LC_TIME, "en_US.UTF-8");
    echo nl_langinfo(ABDAY_3);
    ''')
    assert map(space.str_w, output) == ["Tue", "mar.", "Tue"]
    with interp.warnings(["Warning: nl_langinfo(): Item '1234' is not valid"]):
        out, = interp.run('echo nl_langinfo(1234);')
    assert space.is_w(out, space.w_False)

@requires_locales("fr_FR.UTF-8")
def test_strcoll():
    # NB: \xc3\xa9 is 'é' in UTF-8
    output = interp.run('''
    $loc = setlocale(LC_COLLATE, 0);
    setlocale(LC_COLLATE, "C");
    echo strcoll("F", "\\xc3\\xa9");
    echo strcoll("F", "e");
    setlocale(LC_COLLATE, "fr_FR.UTF-8");
    echo strcoll("F", "\\xc3\\xa9");
    echo strcoll("F", "e");
    setlocale(LC_COLLATE, $loc);
    ''')
    for out, sign in zip(output, [-1, -1, 1, 1]):
        assert space.int_w(out) * sign > 0

@requires_locales("fr_FR.ISO-8859-1")
def test_strtolower():
    output = interp.run('''
    $loc = setlocale(LC_CTYPE, 0);
    setlocale(LC_CTYPE, "C");
    echo strtolower("AbC\\xc9");
    setlocale(LC_CTYPE, "fr_FR.ISO-8859-1");
    echo strtolower("AbC\\xc9");
    setlocale(LC_CTYPE, $loc);
    ''')
    assert [space.str_w(s) for s in output] == [u'abcÉ'.encode('latin1'),
            u'abcé'.encode('latin1')]

@requires_locales("fr_FR.ISO-8859-1")
def test_strtoupper():
    output = interp.run('''
    $loc = setlocale(LC_CTYPE, 0);
    setlocale(LC_CTYPE, "C");
    echo strtoupper("AbC\\xe9");
    setlocale(LC_CTYPE, "fr_FR.ISO-8859-1");
    echo strtoupper("AbC\\xe9");
    setlocale(LC_CTYPE, $loc);

    //clear locale
    setlocale(LC_ALL, "en_US.UTF-8");

    ''')
    assert [space.str_w(s) for s in output] == [u'ABCé'.encode('latin1'),
            u'ABCÉ'.encode('latin1')]
