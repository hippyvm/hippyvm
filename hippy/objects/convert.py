import sys, math
from rpython.rlib.rarithmetic import intmask, maxint, r_longlong
from rpython.rlib.rfloat import isnan
from hippy.objects.floatobject import W_FloatObject
from hippy.objects.intobject import W_IntObject


def _whitespaces_in_front(s):
    i = 0
    while i < len(s):
        if s[i].isspace():
            i += 1
        else:
            break
    return i


def nextchr(s, i):
    if i < len(s):
        return s[i]
    else:
        return '\0'


_OVERFLOWED = 1 << 20


def _convert_hexadecimal(s, i):
    value_int = 0
    value_float = 0.0
    fully_processed = False
    while True:
        c = nextchr(s, i)
        if '0' <= c <= '9':
            digit = ord(c) - ord('0')
        elif 'A' <= c <= 'F':
            digit = ord(c) - ord('A') + 10
        elif 'a' <= c <= 'f':
            digit = ord(c) - ord('a') + 10
        else:
            break
        value_int = intmask((value_int * 16) + digit)
        value_float = (value_float * 16.0) + digit
        fully_processed = True
        i += 1
    fully_processed = fully_processed and i == len(s)
    if abs(float(value_int) - value_float) < _OVERFLOWED:
        return W_IntObject(value_int), fully_processed
    else:    # overflowed at some point
        return W_FloatObject(value_float), fully_processed


def _convert_octal(s, i):
    value_int = 0
    value_float = 0.0
    while True:
        c = nextchr(s, i)
        if '0' <= c <= '7':
            digit = ord(c) - ord('0')
        else:
            break
        value_int = intmask((value_int * 8) + digit)
        value_float = (value_float * 8.0) + digit
        i += 1
    fully_processed = i == len(s)
    if abs(float(value_int) - value_float) < _OVERFLOWED:
        return W_IntObject(value_int), fully_processed
    else:    # overflowed at some point
        return W_FloatObject(value_float), fully_processed


def convert_string_to_number(s, can_be_octal=False):
    """Returns (wrapped number, flag: number-fully-processed)."""
    i = _whitespaces_in_front(s)
    forced_float = False
    negative_sign = False
    at_least_one_digit = False

    if nextchr(s, i) == '-':
        negative_sign = True
        i += 1
    elif nextchr(s, i) == '+':
        i += 1
    elif nextchr(s, i) == '0':
        if nextchr(s, i + 1) in 'xX':
            return _convert_hexadecimal(s, i + 2)
        if can_be_octal:
            return _convert_octal(s, i + 1)

    value_int = 0
    value_float = 0.0
    while nextchr(s, i).isdigit():
        digit = ord(s[i]) - ord('0')
        value_int = intmask((value_int * 10) + digit)
        value_float = (value_float * 10.0) + digit
        if abs(value_int - value_float) < _OVERFLOWED:
            value_float = float(value_int)   # force equal
        at_least_one_digit = True
        i += 1

    if nextchr(s, i) == '.':
        i += 1
        fraction = 1.0
        while nextchr(s, i).isdigit():
            digit = ord(s[i]) - ord('0')
            fraction *= 0.1
            value_float += fraction * digit
            at_least_one_digit = True
            i += 1
        forced_float |= at_least_one_digit

    if nextchr(s, i) in 'Ee' and at_least_one_digit:
        at_least_one_digit = False
        negative_exponent = False
        i += 1
        if nextchr(s, i) == '-':
            negative_exponent = True
            i += 1
        elif nextchr(s, i) == '+':
            i += 1

        exponent = 0
        while nextchr(s, i).isdigit():
            digit = ord(s[i]) - ord('0')
            exponent = exponent * 10 + digit
            if exponent > 99999:
                exponent = 99999    # exponent is huge enough already
            at_least_one_digit = True
            i += 1

        if negative_exponent:
            exponent = -exponent
        try:
            value_float *= math.pow(10.0, exponent)
        except OverflowError:
            value_float = 0.0

        # value_float *= math.pow(10.0, exponent)
        forced_float |= at_least_one_digit

    if negative_sign:
        value_int = intmask(-value_int)
        value_float = -value_float

    fully_processed = at_least_one_digit and i == len(s)
    if forced_float or abs(float(value_int) - value_float) > _OVERFLOWED:
        return W_FloatObject(value_float), fully_processed
    else:
        return W_IntObject(value_int), fully_processed

MAXINT_PLUS_1 = convert_string_to_number(str(sys.maxint + 1))[0].floatval
assert MAXINT_PLUS_1 == float(sys.maxint + 1)   # and not just approximately only


def force_float_to_int_in_any_way(x):
    """This force a float to be converted to an int.
    Any float is fine.  The result is truncated.
    Like PHP, if the input float is greater than 2**63, then the result
    is 0, even if intmask(int(f)) would return some bits."""
    # magic values coming from pypy.rlib.rarithmetic.ovfcheck_float_to_int
    # on 64-bit.
    if isnan(x):
        return -maxint - 1
    if -9223372036854776832.0 <= x < 9223372036854775296.0:
        x = r_longlong(x)
        return intmask(x)
    return 0


def strtol(s):
    """Returns (int_value_forced_in_bounds, flag_any_digit_processed)"""
    i = _whitespaces_in_front(s)
    negative_sign = False
    at_least_one_digit = False

    if nextchr(s, i) == '-':
        negative_sign = True
        i += 1
    elif nextchr(s, i) == '+':
        i += 1

    value_int = 0
    value_float = 0.0
    while nextchr(s, i).isdigit():
        digit = ord(s[i]) - ord('0')
        value_int = intmask((value_int * 10) + digit)
        value_float = (value_float * 10.0) + digit
        if abs(value_int - value_float) < _OVERFLOWED:
            value_float = float(value_int)   # force equal
        at_least_one_digit = True
        i += 1

    if negative_sign:
        value_int = intmask(-value_int)
        value_float = -value_float

    if abs(float(value_int) - value_float) > _OVERFLOWED:
        if negative_sign:
            value_int = -sys.maxint-1
        else:
            value_int = sys.maxint
    return value_int, at_least_one_digit


if __name__ == '__main__':
    print convert_string_to_number('',  True)
