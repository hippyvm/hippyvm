import math
import sys
from rpython.rlib import rfloat, jit
from rpython.rlib.rarithmetic import r_uint, intmask, ovfcheck
from rpython.rlib.rstring import StringBuilder
from rpython.rlib.objectmodel import we_are_translated

from hippy.objects.base import W_Root
from hippy.objects.boolobject import W_BoolObject
from hippy.objects.intobject import W_IntObject
from hippy.objects.floatobject import W_FloatObject
from hippy.builtin import wrap, Optional, LongArg

from rpython.rlib.rrandom import Random
_random = Random()

RANDMAX = 0x7fffffff
MAX_BITS = sys.maxint.bit_length()  # == 31 or 63


@wrap(['space', W_Root], name="abs")
def _abs(space, w_obj):
    return w_obj.abs(space)


@wrap(['space', float])
def acos(space, d):
    """ acos - Arc cosine """
    try:
        return space.wrap(math.acos(d))
    except OverflowError:
        return space.wrap(rfloat.INFINITY)
    except ValueError:
        return space.wrap(rfloat.NAN)


@wrap(['space', float])
def acosh(space, d):
    """ acosh - Inverse hyperbolic cosine """
    try:
        return space.wrap(math.acosh(d))
    except OverflowError:
        return space.wrap(rfloat.INFINITY)
    except ValueError:
        return space.wrap(rfloat.NAN)


@wrap(['space', float])
def asin(space, d):
    """ asin - Arc sine """
    try:
        return space.wrap(math.asin(d))
    except OverflowError:
        return space.wrap(rfloat.INFINITY)
    except ValueError:
        return space.wrap(rfloat.NAN)


@wrap(['space', float])
def asinh(space, d):
    """ asinh - Inverse hyperbolic sine """
    try:
        return space.wrap(math.asinh(d))
    except OverflowError:
        return space.wrap(rfloat.INFINITY)
    except ValueError:
        return space.wrap(rfloat.NAN)


@wrap(['space', float, float])
def atan2(space, x, y):
    """ atan2 - Arc tangent of two variables"""
    try:
        return space.wrap(math.atan2(x, y))
    except ValueError:
        return space.wrap(rfloat.NAN)


@wrap(['space', float])
def atan(space, d):
    """ atan - Arc tangent """
    try:
        return space.wrap(math.atan(d))
    except OverflowError:
        return space.wrap(rfloat.INFINITY)
    except ValueError:
        return space.wrap(rfloat.NAN)


@wrap(['space', float])
def atanh(space, d):
    """ atanh - Inverse hyperbolic tangent """
    try:
        return space.wrap(math.atanh(d))
    except OverflowError:
        return space.wrap(rfloat.INFINITY)
    except ValueError:
        return space.wrap(rfloat.NAN)


@wrap(['space', W_Root, LongArg(None), LongArg(None)])
def base_convert(space, w_number, frombase, tobase):
    """ base_convert - Convert a number between arbitrary bases"""
    # problem with big numbers
    # php casts 10000000000000000000 to 1.0E+19
    # py casts to 1e+19 so we are missing '0' ;-)
    if w_number.tp == space.tp_array:
        space.ec.notice("Array to string conversion")
        return space.newstr("0")
    number = space.str_w(w_number)

    if number == "":
        return space.newstr("0")

    if frombase < 2 or frombase > 36:
        space.ec.warn("base_convert(): Invalid `from base' (%d)" % frombase)
        return space.w_False
    if tobase < 2 or tobase > 36:
        space.ec.warn("base_convert(): Invalid `to base' (%d)" % tobase)
        return space.w_False

    digits = "0123456789abcdefghijklmnopqrstuvwxyz"

    fromdigits = digits[:frombase]
    todigits = digits[:tobase]

    number = number.lower()
    if str(number)[0] == '-':
        number = str(number)[1:]

    x = 0
    for digit in str(number):
        idx = fromdigits.find(digit)
        if idx != -1:
            x = x * len(fromdigits) + idx

    if x == 0:
        res = todigits[0]
    else:
        res = ""
        while x > 0:
            digit = x % len(todigits)
            res = todigits[digit] + res
            x = int(x / len(todigits))
    return space.wrap(res)


@wrap(['space', W_Root])
def bindec(space, w_obj):
    """ bindec - Binary to decimal"""
    s = space.str_w(space.as_string(w_obj))
    binstr = StringBuilder(len(s))
    i = 0
    while i < len(s) and s[i] != '1':
        i += 1
    while i < len(s):
        c = s[i]
        if c == '0' or c == '1':
            binstr.append(c)
        i += 1
    binstr = binstr.build()
    if len(binstr) == 0:
        return space.newint(0)
    elif len(binstr) <= MAX_BITS:
        return space.newint(int(binstr, 2))
    else:
        fnum = float(int(binstr[:MAX_BITS], 2))
        for i in range(MAX_BITS, len(binstr)):
            fnum = 2 * fnum + int(binstr[i])
        return space.newfloat(fnum)


@wrap(['space', W_Root])
def ceil(space, d):
    """ ceil - Round fractions up"""
    d = d.as_number(space)
    if isinstance(d, W_IntObject):
        return W_FloatObject(d.float_w(space))
    elif isinstance(d, W_FloatObject):
        try:
            return W_FloatObject(math.ceil(rpy_round(d.floatval, 2)))
        except OverflowError:
            return W_FloatObject(rfloat.INFINITY)
    else:
        return space.w_False


@wrap(['space', float])
def cos(space, d):
    """ cos - Cosine """
    try:
        return space.wrap(math.cos(d))
    except OverflowError:
        return space.wrap(rfloat.INFINITY)


@wrap(['space', float])
def cosh(space, d):
    """ cosh - Hyperbolic cosine"""
    try:
        return space.wrap(math.cosh(d))
    except OverflowError:
        return space.wrap(rfloat.INFINITY)


def _bin(i):
    if i == 0:
        return "0"
    s = StringBuilder()
    c = r_uint(sys.maxint + 1)
    while c > i:
        c >>= r_uint(1)
    while c:
        if i & c:
            s.append("1")
        else:
            s.append("0")
        c >>= r_uint(1)
    return s.build()


@wrap(['space', W_Root])
def decbin(space, w_obj):
    """ decbin - Decimal to binary"""
    i = space.force_int(w_obj)
    ui = r_uint(i)
    return space.wrap(_bin(ui))


@wrap(['space', W_Root])
def dechex(space, w_obj):
    """ dechex - Decimal to hexadecimal"""
    i = space.force_int(w_obj)
    ui = r_uint(i)
    ret = hex(ui)
    if not we_are_translated():
        ret = ret.replace("L", "")
    return space.wrap(ret[2:])


@wrap(['space', W_Root])
def decoct(space, w_obj):
    """ decoct - Decimal to octal"""
    i = space.force_int(w_obj)
    ui = r_uint(i)
    ret = oct(ui)
    if not we_are_translated():
        if ret.endswith('L'):
            ret = ret[:-1]
    if len(ret) == 1:
        return space.wrap(ret)
    if ret.startswith('0'):
        ret = ret[1:]
    return space.wrap(ret)

degToRad = math.pi / 180.0


@wrap(['space', float])
def deg2rad(space, d):
    """ deg2rad - Converts the number in degrees to the radian equivalent"""
    try:
        return space.wrap(d * degToRad)
    except OverflowError:
        return space.wrap(rfloat.INFINITY)


@wrap(['space', float])
def exp(space, d):
    """ Calculates the exponent of e"""
    try:
        return space.wrap(math.exp(d))
    except OverflowError:
        return space.wrap(rfloat.INFINITY)


@wrap(['space', float])
def expm1(space, d):
    """ Returns exp(number) - 1, computed in a way that is
    accurate even when the value of number is close to zero"""
    try:
        return space.wrap(math.expm1(d))
    except OverflowError:
        return space.wrap(rfloat.INFINITY)


@wrap(['space', W_Root], name="floor")
def _floor(space, d):
    """ floor - Round fractions down"""
    d = d.as_number(space)
    if isinstance(d, W_IntObject):
        return W_FloatObject(d.float_w(space))
    elif isinstance(d, W_FloatObject):
        try:
            return W_FloatObject(math.floor(rpy_round(d.floatval, 2)))
        except OverflowError:
            return W_FloatObject(rfloat.INFINITY)
    else:
        return space.w_False


@wrap(['space', float, float], name="fmod")
def _fmod(space, x, y):
    """ fmod - Returns the floating point remainder
    (modulo) of the division of the arguments"""
    try:
        return space.wrap(math.fmod(x, y))
    except ValueError:
        return space.wrap(rfloat.NAN)


@wrap(['space'], aliases=["mt_getrandmax"])
def getrandmax(space):
    """ getrandmax - Show largest possible random value"""
    return space.wrap(RANDMAX)


@wrap(['space', W_Root])
def hexdec(space, w_string):
    """ hexdec - Hexadecimal to decimal"""
    s = w_string.str(space)
    num = 0
    for i in xrange(len(s)):
        c = s[i]
        if '0' <= c <= '9':
            digit = ord(c) - ord('0')
        elif 'A' <= c <= 'F':
            digit = ord(c) - (ord('A') - 10)
        elif 'a' <= c <= 'f':
            digit = ord(c) - (ord('a') - 10)
        else:
            continue
        try:
            num = ovfcheck(num * 16 + digit)
        except OverflowError:
            fnum = float(num)
            break
    else:
        return space.newint(num)
    for j in xrange(i, len(s)):
        c = s[i]
        if '0' <= c <= '9':
            digit = ord(c) - ord('0')
        elif 'A' <= c <= 'F':
            digit = ord(c) - (ord('A') - 10)
        elif 'a' <= c <= 'f':
            digit = ord(c) - (ord('a') - 10)
        else:
            continue
        fnum = fnum * 16. + float(digit)
    return space.newfloat(fnum)


@wrap(['space', float, float])
def hypot(space, x, y):
    """ hypot - Calculate the length of the
    hypotenuse of a right-angle triangle"""
    try:
        return space.wrap(math.sqrt(math.pow(x, 2) + math.pow(y, 2)))
    except ValueError:
        return space.wrap(rfloat.NAN)


@wrap(['space', float])
def is_finite(space, f):
    """ is_finite - Finds whether a value is a legal finite number """
    return space.wrap(not math.isinf(f) and not math.isnan(f))


@wrap(['space', float])
def is_infinite(space, f):
    """ is_infinite - Finds whether a value is infinite """
    return space.wrap(math.isinf(f) and not math.isnan(f))


@wrap(['space', float])
def is_nan(space, f):
    """ is_nan - Finds whether a value is not a number """
    return space.wrap(math.isnan(f))


@wrap(['space', 'args_w'])
def lcg_value(space, args_w):
    """ lcg_value - Combined linear congruential generator """
    # XXX: actually uses a Mersenne twister
    return space.newfloat(_random.random())


@wrap(['space', float])
def log10(space, d):
    """ Base-10 logarithm"""
    if d < 0:
        return space.wrap(rfloat.NAN)
    try:
        return space.wrap(math.log10(d))
    except ValueError:
        return space.wrap(-rfloat.INFINITY)


@wrap(['space', float])
def log1p(space, d):
    """ Base-10 logarithm"""
    if d < 0:
        return space.wrap(rfloat.NAN)
    try:
        return space.wrap(math.log1p(d))
    except ValueError:
        return space.wrap(-rfloat.INFINITY)


@wrap(['space', float, 'num_args', Optional(float)])
def log(space, x, num_args, b=0.0):
    """ Base-10 logarithm"""
    if x < 0:
        return space.wrap(rfloat.NAN)
    try:
        if num_args == 2:
            if b <= 0:
                space.ec.warn("log(): base must be greater than 0")
                return space.w_False
            return space.wrap(math.log(x) / math.log(b))
        return space.wrap(math.log(x))
    except ValueError:
        return space.wrap(-rfloat.INFINITY)
    except ZeroDivisionError:
        return space.wrap(rfloat.NAN)


# XXX unroll_iff probably
@jit.unroll_safe
@wrap(['space', 'args_w'])
def max(space, args_w):
    """  max - Find highest value """
    if len(args_w) == 0:
        space.ec.warn("max() expects at least 1 parameter, 0 given")
        return space.w_Null

    if len(args_w) == 1:
        w_arr = args_w[0]
        if w_arr.tp != space.tp_array:
            space.ec.warn("max(): When only one parameter is given, "
                          "it must be an array")
            return space.w_Null
        if space.arraylen(w_arr) == 0:
            space.ec.warn("max(): Array must contain at least one element")
            return space.w_False
        _max = None
        with space.iter(w_arr) as w_arr_iter:
            while not w_arr_iter.done():
                _, w_val = w_arr_iter.next_item(space)
                if _max is None:
                    _max = w_val
                    continue
                else:
                    if space._compare(_max, w_val) < 0:
                        _max = w_val
        return _max

    _max = args_w[0]
    for w_arg in args_w[1:]:
        if space._compare(_max, w_arg) < 0:
            _max = w_arg
    return _max


@wrap(['space', 'args_w'])
def min(space, args_w):
    """ min - Find lowest value """
    if len(args_w) == 0:
        space.ec.warn("min() expects at least 1 parameter, 0 given")
        return space.w_Null

    if len(args_w) == 1:
        w_arr = args_w[0]
        if w_arr.tp != space.tp_array:
            space.ec.warn("min(): When only one parameter is given, "
                          "it must be an array")
            return space.w_Null
        if space.arraylen(w_arr) == 0:
            space.ec.warn("min(): Array must contain at least one element")
            return space.w_False
        _min = None
        with space.iter(w_arr) as w_arr_iter:
            while not w_arr_iter.done():
                _, w_val = w_arr_iter.next_item(space)
                if _min is None:
                    _min = w_val
                    continue
                else:
                    if space._compare(_min, w_val) > 0:
                        _min = w_val
        return _min

    _min = args_w[0]
    for w_arg in args_w[1:]:
        if space._compare(_min, w_arg) > 0:
            _min = w_arg
    return _min


@wrap(['space', W_Root])
def octdec(space, w_string):
    """ octdec - Octal to decimal"""
    s = w_string.str(space)
    num = 0
    for i in xrange(len(s)):
        c = s[i]
        if '0' <= c <= '7':
            digit = ord(c) - ord('0')
            try:
                num = ovfcheck(num * 8 + digit)
            except OverflowError:
                fnum = float(num)
                break
    else:
        return space.newint(num)
    for j in xrange(i, len(s)):
        c = s[i]
        if '0' <= c <= '7':
            digit = ord(c) - ord('0')
            fnum = fnum * 8. + float(digit)
    return space.newfloat(fnum)


@wrap(['space'])
def pi(space):
    """ pi - Get value of pi"""
    return space.wrap(math.pi)


@wrap(['space', W_Root, W_Root], name="pow")
def _pow(space, x, y):
    """ pow - Exponential expression"""
    x = x.as_number(space)
    y = y.as_number(space)
    exponent_is_odd = False
    try:
        if (isinstance(x, W_IntObject) and
                isinstance(y, W_IntObject) and y.intval >= 0):
            ibase = x.intval
            iexp = y.intval
            exponent_is_odd = (iexp % 2 == 1)
            if iexp == 0:
                return space.newint(1)
            elif ibase == 0:
                return space.newint(0)
            assert iexp > 0
            result = 1
            while True:
                if iexp % 2:
                    result = ovfcheck(result * ibase)
                iexp >>= 1
                if iexp == 0:
                    break
                ibase = ovfcheck(ibase * ibase)
            return space.newint(result)
    except OverflowError:
        pass
    fbase = x.float_w(space)
    fexp = y.float_w(space)
    if fbase == 0.:
        if fexp < 0:
            return space.newfloat(float('inf'))
        elif fexp == 0.:
            return space.newfloat(1.)
        elif math.isnan(fexp):
            return space.newfloat(float('nan'))
        else:
            return space.newfloat(0.)
    try:
        p = math.pow(fbase, fexp)
        return space.newfloat(p)
    except OverflowError:
        # NB: the following treats all integers that cannot fit into a double
        # (i.e. those greater than 2**53) as even, which is wrong, but matches
        # exactly the behavior of PHP 5.4.
        if not exponent_is_odd:
            try:
                exponent_is_odd = (int(fexp) % 2 != 0)
            except OverflowError:
                pass
        if fbase < 0 and exponent_is_odd:
            return space.wrap(-rfloat.INFINITY)
        return space.wrap(rfloat.INFINITY)
    except ValueError:
        return space.wrap(rfloat.NAN)


@wrap(['space', float])
def rad2deg(space, d):
    """ rad2deg - Converts the radian number
    to the equivalent number in degrees"""
    try:
        return space.wrap(d / degToRad)
    except OverflowError:
        return space.wrap(rfloat.INFINITY)


def unbiased_rand(mn, mx):
    # migu way
    _range = mx - mn
    unbiased_range = _range + RANDMAX % _range
    rnd = intmask(_random.genrand32()) % unbiased_range
    while rnd >= _range:
        rnd = intmask(_random.genrand32()) % unbiased_range
    return rnd + mn


def rand_range(a, b):
    # php way a + n(b-a+1)/(M+1)
    n = intmask(_random.genrand32())
    M = RANDMAX
    return int(a + n * (b - a + 1) / (M + 1))


@wrap(['space', 'num_args', Optional(int), Optional(int)],
      check_num_args=False)
def rand(space, num_args, x=0, y=RANDMAX):
    """ rand - Generate a random integer"""
    if num_args == 1 or num_args >= 3:
        space.ec.warn("rand() expects exactly 2 parameters, %d given"
                % num_args)
        return space.w_Null
    # return space.wrap(int(rand_range(x, y)))
    return space.wrap(int(unbiased_rand(x, y)))

NDIGITS_MAX = int((rfloat.DBL_MANT_DIG - rfloat.DBL_MIN_EXP) * 0.30103)
NDIGITS_MIN = -int((rfloat.DBL_MAX_EXP + 1) * 0.30103)


def rpy_round(number, ndigits):
    # Algorithm copied directly from CPython

    if number == 0 or rfloat.isinf(number) or rfloat.isnan(number):
        return number

    # Deal with extreme values for ndigits. For ndigits > NDIGITS_MAX, x
    # always rounds to itself.  For ndigits < NDIGITS_MIN, x always
    # rounds to +-0.0.
    if ndigits > NDIGITS_MAX:
        return number
    elif ndigits < NDIGITS_MIN:
        # return 0.0, but with sign of x
        return 0.0 * number

    # finite x, and ndigits is not unreasonably large
    z = rfloat.round_double(number, ndigits)
    if rfloat.isinf(z):
        raise OverflowError
    return z


@wrap(['space', 'num_args', Optional(int), Optional(int)],
      check_num_args=False)
def mt_rand(space, num_args, x=0, y=RANDMAX):
    """ rand - Generate a random integer"""
    if num_args == 1 or num_args >= 3:
        space.ec.warn("mt_rand() expects exactly 2 parameters, %d given"
                % num_args)
        return space.w_Null
    if x > y:
        space.ec.warn("mt_rand(): max(%s) is smaller than min(%s)" % (y, x))
        return space.w_False

    #return space.wrap(int(unbiased_rand(int(x), int(y))))
    return space.newint(rand_range(x, y))


@wrap(['interp', W_Root, Optional(int), Optional(int)], name="round")
def _round(interp, w_d, precision=0, mode=1):
    """ round - Rounds a float
        'PHP_ROUND_HALF_UP': 1,
        'PHP_ROUND_HALF_DOWN': 2,
        'PHP_ROUND_HALF_EVEN': 3,
        'PHP_ROUND_HALF_ODD': 4,
        """
    space = interp.space
    w_d = w_d.as_number(space)
    if isinstance(w_d, W_BoolObject):
        return w_d
    d = w_d.float_w(space)
    if precision > interp.config.get_precision():
        return space.wrap(d)

    d = rpy_round(d * math.pow(10, precision), 2)
    if d >= 0.0:
        tmp = math.floor(d + 0.5)
        if (mode == 1 and d == (0.5 + tmp)) or\
                (mode == 2 and d == (-0.5 + tmp)) or\
                (mode == 3 and d == (0.5 + 2 * math.floor(tmp / 2))) or\
                (mode == 4 and d == (0.5 + 2 * math.floor(tmp / 2.0) - 1)):
            tmp -= 1
    else:
        tmp = math.ceil(d - 0.5)
        if (mode == 1 and d == (-0.5 + tmp)) or\
                (mode == 2 and d == (0.5 + tmp)) or\
                (mode == 3 and d == (-0.5 + 2 * math.ceil(tmp / 2))) or\
                (mode == 4 and d == (-0.5 + 2 * math.ceil(tmp / 2.0) + 1)):
            tmp += 1
    if tmp == 0.:
        # Return early, in case 10**precision underflows
        return space.newfloat(tmp)
    tmp = tmp / math.pow(10, precision)
    return space.wrap(rpy_round(tmp, precision))


@wrap(['space', float])
def sin(space, d):
    """ sin - Sine """
    try:
        return space.wrap(math.sin(d))
    except OverflowError:
        return space.wrap(rfloat.INFINITY)


@wrap(['space', float])
def sinh(space, d):
    """ sinh - Hyperbolic sine """
    try:
        return space.wrap(math.sinh(d))
    except OverflowError:
        if d > 0:
            return space.wrap(rfloat.INFINITY)
        return space.wrap(-rfloat.INFINITY)


@wrap(['space', Optional(int)], aliases=["mt_srand"])
def srand(space, d=0):
    """ srand - Seed the random number generator"""
    _random.init_genrand(r_uint(d))
    return space.w_Null


@wrap(['space', float])
def sqrt(space, d):
    """ sqrt - Square root """
    try:
        return space.wrap(math.sqrt(d))
    except ValueError:
        return space.wrap(rfloat.NAN)


@wrap(['space', float])
def tan(space, d):
    """ tan - Tangent """
    try:
        return space.wrap(math.tan(d))
    except OverflowError:
        return space.wrap(rfloat.INFINITY)


@wrap(['space', float])
def tanh(space, d):
    """ tanh - Hyperbolic tangent """
    try:
        return space.wrap(math.tanh(d))
    except OverflowError:
        return space.wrap(rfloat.INFINITY)
