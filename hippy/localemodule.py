"""
Locale-aware builtin functions
"""
from rpython.rlib.rlocale import (setlocale as rsetlocale, LocaleError,
                                  localeconv as rlocaleconv,
                                  nl_langinfo as rnl_langinfo)
from rpython.rlib import rlocale
from rpython.rtyper.lltypesystem.rffi import charp2str
from rpython.rtyper.lltypesystem import rffi
from rpython.rlib.rstring import StringBuilder

from hippy.builtin import wrap
from hippy.objects.base import W_Root


def lower_char(c):
    """Return the lowercase version of the character in the current locale."""
    return chr(_tolower(ord(c)))


def lower(string):
    """Return the lowercase version of the string in the current locale."""
    builder = StringBuilder(len(string))
    for c in string:
        builder.append(lower_char(c))
    return builder.build()


def upper_char(c):
    """Return the uppercase version of the character in the current locale."""
    return chr(_toupper(ord(c)))


def upper(string):
    """Return the uppercase version of the string in the current locale."""
    builder = StringBuilder(len(string))
    for c in string:
        builder.append(upper_char(c))
    return builder.build()


def _setlocale(space, category, locale):
    if locale == '0':
        locale = None
    result = rsetlocale(category, locale)
    return space.newstr(result)


@wrap(['space', int, W_Root, 'args_w'])
def setlocale(space, category, w_locale, extras):
    """Set locale information."""
    if w_locale.tp == space.tp_array:
        locales = []
        it = space.create_iter(w_locale)
        while not it.done():
            _, w_val = it.next_item(space)
            locales.append(space.str_w(w_val))
    else:
        locales = [space.str_w(w_locale)]
        for w_extra in extras:
            locales.append(space.str_w(w_extra))
    for locale in locales:
        try:
            result = _setlocale(space, category, locale)
            return result
        except LocaleError:
            pass
    else:
        return space.w_False


def _w_grouping(space, ptr):
    i = 0
    grouping = []
    while ord(ptr[i]):
        grouping.append(space.newint(ord(ptr[i])))
        i += 1
    return space.new_array_from_list(grouping)


@wrap(['space'])
def localeconv(space):
    """Get numeric formatting information."""
    lp = rlocaleconv()
    return space.new_array_from_pairs([
        (space.newstr('decimal_point'), space.newstr(charp2str(lp.c_decimal_point))),
        (space.newstr('thousands_sep'), space.newstr(charp2str(lp.c_thousands_sep))),
        (space.newstr('int_curr_symbol'), space.newstr(charp2str(lp.c_int_curr_symbol))),
        (space.newstr('currency_symbol'), space.newstr(charp2str(lp.c_currency_symbol))),
        (space.newstr('mon_decimal_point'), space.newstr(charp2str(lp.c_mon_decimal_point))),
        (space.newstr('mon_thousands_sep'), space.newstr(charp2str(lp.c_mon_thousands_sep))),
        (space.newstr('positive_sign'), space.newstr(charp2str(lp.c_positive_sign))),
        (space.newstr('negative_sign'), space.newstr(charp2str(lp.c_negative_sign))),
        (space.newstr('int_frac_digits'), space.newint(int(lp.c_int_frac_digits))),
        (space.newstr('frac_digits'), space.newint(int(lp.c_frac_digits))),
        (space.newstr('p_cs_precedes'), space.newint(int(lp.c_p_cs_precedes))),
        (space.newstr('p_sep_by_space'), space.newint(int(lp.c_p_sep_by_space))),
        (space.newstr('n_cs_precedes'), space.newint(int(lp.c_n_cs_precedes))),
        (space.newstr('n_sep_by_space'), space.newint(int(lp.c_n_sep_by_space))),
        (space.newstr('p_sign_posn'), space.newint(int(lp.c_p_sign_posn))),
        (space.newstr('n_sign_posn'), space.newint(int(lp.c_n_sign_posn))),
        (space.newstr('grouping'), _w_grouping(space, lp.c_grouping)),
        (space.newstr('mon_grouping'), _w_grouping(space, lp.c_mon_grouping)),
    ])


#@wrap(['space', 'args_w'])
#def money_format(space, args_w):
#    """Formats a number as a currency string."""
#    raise NotImplementedError()


@wrap(['space', int])
def nl_langinfo(space, item):
    """Query language and locale information."""
    try:
        return space.newstr(rnl_langinfo(item))
    except ValueError:
        space.ec.warn("nl_langinfo(): Item '%d' is not valid" % item)
        return space.w_False

_strcoll = rlocale.external('strcoll', [rffi.CCHARP, rffi.CCHARP], rffi.INT)

def strcoll_u(str1, str2):
    return _strcoll(rffi.str2charp(str1), rffi.str2charp(str2))


@wrap(['space', str, str])
def strcoll(space, str1, str2):
    """Locale based string comparison."""
    return space.newint(strcoll_u(str1, str2))

_tolower = rlocale.external('tolower', [rffi.INT], rffi.INT)
_toupper = rlocale.external('toupper', [rffi.INT], rffi.INT)


@wrap(['space', str])
def strtolower(space, string):
    """Make a string lowercase."""
    return space.newstr(lower(string))


@wrap(['space', str])
def strtoupper(space, string):
    """Make a string uppercase."""
    return space.newstr(upper(string))
