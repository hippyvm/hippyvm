from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.rlib.rarithmetic import intmask

from hippy import consts
from hippy.error import PHPException
from hippy.builtin import wrap_method, ThisUnwrapper, StringArg
from hippy.builtin_klass import GetterSetterWrapper, k_Exception
from hippy.klass import def_class
from hippy.module.date import timelib
from hippy.objects.instanceobject import W_InstanceObject


class W_DateInterval(W_InstanceObject):
    pass


@wrap_method(['interp', ThisUnwrapper(W_DateInterval), StringArg(None)],
             name='DateInterval::__construct')
def construct(interp, this, spec):

    exc_obj = k_Exception.call_args(
        interp, [interp.space.wrap('Unknown or bad format (%s)' % spec)]
    )

    if not (len(spec) > 1 and spec[0] == 'P'):
        raise PHPException(exc_obj)

    index = 1
    time = False
    formats = {'y': 0, 'm': 0, 'd':0, 'h':0, 'i':0 ,'s': 0}

    while index < len(spec):
        format = None
        times = 0

        if spec[index] == 'T':
            index += 1
            time = True

        while spec[index].isdigit():
            times = times * 10
            times = times + (ord(spec[index]) - ord('0'))
            index += 1

        if times:
            if spec[index] == 'Y':
                format = 'y'
            elif spec[index] == 'M' and not time:
                format = 'm'
            elif spec[index] == 'D':
                format = 'd'
            elif spec[index] == 'W':
                format = 'd'
                times *= 7
            elif spec[index] == 'H':
                format = 'h'
            elif spec[index] == 'M' and time:
                format = 'i'
            elif spec[index] == 'S':
                format = 's'

            if not formats[format]:
                formats[format] = times
            else:
                raise PHPException(exc_obj)

        index += 1

    this.time_diff = timelib.timelib_rel_time_ctor()

    this.time_diff.c_y = rffi.cast(lltype.Signed, formats['y'])
    this.time_diff.c_m = rffi.cast(lltype.Signed, formats['m'])
    this.time_diff.c_d = rffi.cast(lltype.Signed, formats['d'])
    this.time_diff.c_h = rffi.cast(lltype.Signed, formats['h'])
    this.time_diff.c_i = rffi.cast(lltype.Signed, formats['i'])
    this.time_diff.c_s = rffi.cast(lltype.Signed, formats['s'])


@wrap_method(['interp', StringArg(None)],
             name='DateInterval::createFromDateString', flags=consts.ACC_STATIC)
def create_from_date_string(interp, string):
    spec = "P%sY%sM%sDT%sH%sM%sS" % timelib.str_interval_to_time(string)
    return k_DateInterval.call_args(interp, [interp.space.wrap(spec)])


@wrap_method(['interp', ThisUnwrapper(W_DateInterval), StringArg(None)], name='DateInterval::format')
def format(interp, this, format):

    y = this.time_diff.c_y
    m = this.time_diff.c_m
    d = this.time_diff.c_d
    h = this.time_diff.c_h
    i = this.time_diff.c_i
    s = this.time_diff.c_s

    index = 0

    results = []

    while index < len(format):
        c = format[index]
        if c == '%':

            index += 1
            next_c = format[index]

            if next_c == 'Y':
                results.append(timelib.format_to(2, y))
            elif next_c == 'y':
                results.append("%d" % y)
            elif next_c == 'M':
                results.append(timelib.format_to(2, m))
            elif next_c == 'm':
                results.append("%d" % m)
            elif next_c == 'D':
                results.append(timelib.format_to(2, d))
            elif next_c == 'd':
                results.append("%d" % d)
            elif next_c == 'H':
                results.append(timelib.format_to(2, h))
            elif next_c == 'h':
                results.append("%d" % h)
            elif next_c == 'I':
                results.append(timelib.format_to(2, i))
            elif next_c == 'i':
                results.append("%d" % i)
            elif next_c == 'S':
                results.append(timelib.format_to(2, s))
            elif next_c == 's':
                results.append("%d" % s)
            elif next_c == 'a':
                if this.time_diff.c_d != -99999:
                    results.append("%d" % this.time_diff.c_days)
                else:
                    results.append("(unknown)")
            elif next_c == 'r':
                results.append("-" if int(this.time_diff.c_invert) else "")
            elif next_c == 'R':
                results.append("-" if int(this.time_diff.c_invert) else "+")
            elif next_c == '%':
                results.append('%')
            else:
                results.append("%%%s" % next_c)
        else:
             results.append(c)

        index += 1

    return interp.space.wrap("".join(results))


def get_y(interp, this):
    return interp.space.wrap(this.time_diff.c_y)

def set_y(interp, this, w_newvalue):
    this.time_diff.c_y = interp.space.int_w(w_newvalue)

def get_m(interp, this):
    return interp.space.wrap(this.time_diff.c_m)

def set_m(interp, this, w_newvalue):
    this.time_diff.c_m = interp.space.int_w(w_newvalue)

def get_d(interp, this):
    return interp.space.wrap(this.time_diff.c_d)

def set_d(interp, this, w_newvalue):
    this.time_diff.c_d = interp.space.int_w(w_newvalue)

def get_h(interp, this):
    return interp.space.wrap(this.time_diff.c_h)

def set_h(interp, this, w_newvalue):
    this.time_diff.c_h = interp.space.int_w(w_newvalue)

def get_i(interp, this):
    return interp.space.wrap(this.time_diff.c_i)

def set_i(interp, this, w_newvalue):
    this.time_diff.c_i = interp.space.int_w(w_newvalue)

def get_s(interp, this):
    return interp.space.wrap(this.time_diff.c_s)

def set_s(interp, this, w_newvalue):
    this.time_diff.c_s = interp.space.int_w(w_newvalue)

def get_invert(interp, this):
    return interp.space.wrap(intmask(this.time_diff.c_invert))

def set_invert(interp, this, w_newvalue):
    this.time_diff.c_invert = rffi.cast(rffi.INT, interp.space.int_w(w_newvalue))

def get_days(interp, this):
    return interp.space.wrap(this.time_diff.c_days or False)

def set_days(interp, this, w_newvalue):
    this.time_diff.c_days = interp.space.int_w(w_newvalue)

def get_weekday(interp, this):
    return interp.space.wrap(intmask(this.time_diff.c_weekday))

def set_weekday(interp, this, value):
    raise NotImplementedError("bogus cast!")
    this.time_diff.c_weekday = rffi.cast(rffi.INT, value)

def get_weekday_behavior(interp, this):
    return interp.space.wrap(intmask(this.time_diff.c_weekday_behavior))

def set_weekday_behavior(interp, this, value):
    raise NotImplementedError("bogus cast!")
    this.time_diff.c_weekday_behavior = rffi.cast(rffi.INT, value)

def get_first_last_day_of(interp, this):
    return interp.space.wrap(intmask(this.time_diff.c_first_last_day_of))

def set_first_last_day_of(interp, this, value):
    raise NotImplementedError("bogus cast!")
    this.time_diff.c_first_last_day_of = rffi.cast(rffi.INT, value)

def get_special_type(interp, this):
    return interp.space.wrap(intmask(this.time_diff.c_special.c_type))

def set_special_type(interp, this, value):
    raise NotImplementedError("bogus cast!")
    this.time_diff.c_special.c_type = rffi.cast(rffi.UINT, value)

def get_special_amount(interp, this):
    return interp.space.wrap(intmask(this.time_diff.c_special.c_amount))

def set_special_amount(interp, this, value):
    raise NotImplementedError("bogus cast!")
    this.time_diff.c_special.c_amount = rffi.cast(lltype.Signed, value)

def get_have_weekday_relative(interp, this):
    return interp.space.wrap(intmask(this.time_diff.c_have_weekday_relative))

def set_have_weekday_relative(interp, this, value):
    raise NotImplementedError("bogus cast!")
    this.time_diff.c_have_weekday_relative = rffi.cast(rffi.UINT, value)

def get_have_special_relative(interp, this):
    return interp.space.wrap(intmask(this.time_diff.c_have_special_relative))

def set_have_special_relative(interp, this, value):
    raise NotImplementedError("bogus cast!")
    this.time_diff.c_have_special_relative = rffi.cast(rffi.UINT, value)


k_DateInterval = def_class(
    'DateInterval',

    [construct,
     create_from_date_string,
     format],

    [GetterSetterWrapper(get_y, set_y,
                         "y", consts.ACC_PUBLIC),
     GetterSetterWrapper(get_m, set_m,
                         "m", consts.ACC_PUBLIC),
     GetterSetterWrapper(get_d, set_d,
                         "d", consts.ACC_PUBLIC),
     GetterSetterWrapper(get_h, set_h,
                         "h", consts.ACC_PUBLIC),
     GetterSetterWrapper(get_i, set_i,
                         "i", consts.ACC_PUBLIC),
     GetterSetterWrapper(get_s, set_s,
                         "s", consts.ACC_PUBLIC),
     GetterSetterWrapper(get_weekday, set_weekday,
                         "weekday", consts.ACC_PUBLIC),
     GetterSetterWrapper(get_weekday_behavior, set_weekday_behavior,
                         "weekday_behavior", consts.ACC_PUBLIC),
     GetterSetterWrapper(get_first_last_day_of, set_first_last_day_of,
                         "first_last_day_of", consts.ACC_PUBLIC),
     GetterSetterWrapper(get_invert, set_invert,
                         "invert", consts.ACC_PUBLIC),
     GetterSetterWrapper(get_days, set_days,
                         "days", consts.ACC_PUBLIC),
     GetterSetterWrapper(get_special_type, set_special_type,
                         "special_type", consts.ACC_PUBLIC),
     GetterSetterWrapper(get_special_amount, set_special_amount,
                         "special_amount", consts.ACC_PUBLIC),
     GetterSetterWrapper(get_have_weekday_relative, set_have_weekday_relative,
                         "have_weekday_relative", consts.ACC_PUBLIC),
     GetterSetterWrapper(get_have_special_relative, set_have_special_relative,
                         "have_special_relative", consts.ACC_PUBLIC)],

    instance_class=W_DateInterval
)
