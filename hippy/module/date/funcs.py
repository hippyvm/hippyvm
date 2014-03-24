import sys
import time as pytime

from rpython.rtyper.lltypesystem import lltype, rffi
from rpython.rlib.rarithmetic import intmask

from hippy.builtin import (
    wrap, StringArg, Optional, LongArg, InstanceUnwrapper, handle_as_void)
from hippy.module.date import (
    timelib, datetimezone_klass, W_DateTime, W_DateTimeZone)
from hippy.module.date.datetime_klass import k_DateTime
from hippy.module.date.dateinterval_klass import W_DateInterval
from hippy.module.date.datetimezone_klass import k_DateTimeZone

from hippy.module.date import common


@wrap(['interp', str], error=False)
def date_default_timezone_set(interp, timezone_name):
    timelib_timezone = timelib.timelib_timezone(timezone_name)

    if timelib_timezone:
        w_datetimezone = W_DateTimeZone(k_DateTimeZone, [])
        w_datetimezone.timelib_timezone = timelib_timezone

        interp.timezone = w_datetimezone
        interp.timezone_set = True
        return interp.space.w_True
    else:
        interp.notice(
            "date_default_timezone_set(): Timezone ID '%s' is invalid"
            % timezone_name)
        return interp.space.w_False


@wrap(['interp'], error=False)
def date_default_timezone_get(interp):
    w_datetimezone = interp.get_default_timezone("date_default_timezone_get")
    return interp.space.wrap(timelib.timezone_name(w_datetimezone.timelib_timezone))


@wrap(['interp', str, Optional(int)], error=False)
def date(interp, date_format, timestamp=int(pytime.time())):

    timelib_timezone = interp.get_default_timezone("date").timelib_timezone
    timelib_time = timelib.timelib_time_from_timestamp(timestamp, timelib_timezone)

    return interp.space.wrap(timelib.date_format(date_format, timelib_time))


@wrap(['interp', str, Optional(int)], error=False)
def idate(interp, date_format, timestamp=int(pytime.time())):
    space = interp.space

    if len(date_format) != 1:
        interp.space.ec.warn("idate(): idate format is one char")
        return interp.space.w_False

    timelib_timezone = interp.get_default_timezone("idate").timelib_timezone
    timelib_time = timelib.timelib_time_from_timestamp(timestamp, timelib_timezone)

    if date_format == 'B':
        retval = (
            ((timelib_time.c_sse)-(
                (timelib_time.c_sse) - (((timelib_time.c_sse) % 86400) + 3600))) * 10
        ) / 864


        while retval < 0:
            retval += 1000

        return space.wrap(retval % 1000)

    elif date_format == 'd':
        return space.wrap(timelib_time.c_d)

    elif date_format == 'h':
        if timelib_time.c_h % 12:
            return space.wrap(timelib_time.c_h % 12)
        else:
            return space.wrap(12)

    elif date_format == 'H':
        return space.wrap(timelib_time.c_h)

    elif date_format == 'i':
        return space.wrap(timelib_time.c_i)

    elif date_format == 'I':
        raise NotImplementedError()

    elif date_format == 'L':
        return space.wrap(int(timelib.is_leap(timelib_time.c_y)))

    elif date_format == 'm':
        return space.wrap(timelib_time.c_m)

    elif date_format == 's':
        return space.wrap(timelib_time.c_s)

    elif date_format == 't':
        return space.wrap(
            timelib.timelib_days_in_month(timelib_time.c_y, timelib_time.c_m)
        )

    elif date_format == 'U':
        return space.wrap(timelib_time.c_sse)

    elif date_format == 'w':
        return space.wrap(
            timelib.timelib_day_of_week(
                timelib_time.c_y, timelib_time.c_m, timelib_time.c_d
            ))

    elif date_format == 'W':
        return space.wrap(
            timelib.isoweek_from_date(
                timelib_time.c_y, timelib_time.c_m, timelib_time.c_d)
        )

    elif date_format == 'y':
        return space.wrap(timelib_time.c_y)

    elif date_format == 'Y':
        return space.wrap(timelib_time.c_y)

    elif date_format == 'z':
        return space.wrap(
            timelib.timelib_day_of_year(
                timelib_time.c_y, timelib_time.c_m, timelib_time.c_d
            ))

    elif date_format == 'Z':
        raise NotImplementedError()

    else:
        interp.space.ec.warn("idate(): Unrecognized date format token.")
        return interp.space.w_False


@wrap(['space', str, Optional(int)], error=False)
def gmdate(space, date_format, timestamp=int(pytime.time())):

    timelib_timezone = timelib.timelib_timezone('GMT')
    timelib_time = timelib.timelib_time_from_timestamp(timestamp, timelib_timezone)

    return space.wrap(timelib.date_format(date_format, timelib_time))


@wrap(['space'])
def time(space):
    return space.wrap(int(pytime.time()))


@wrap(['interp', str, Optional(LongArg(None))], error=False)
def strtotime(interp, str_time, now=-1):
    timelib_timezone = interp.get_default_timezone("strtotime").timelib_timezone

    res = timelib.strtotime(str_time, now, timelib_timezone)

    if res == -1:
        return interp.space.w_False
    return interp.space.wrap(res)


def _mktime(interp, is_gmt, hour, minute, second,
            month, day, year, dst=-1):

    now = timelib.timelib_time_ctor()
    adjust_seconds = 0

    if is_gmt:
        timelib.timelib_unixtime2gmt(now, int(pytime.time()))
    else:
        now.c_tz_info = interp.get_default_timezone("mktime").timelib_timezone
        now.c_zone_type = timelib.TIMELIB_ZONETYPE_ID
        timelib.timelib_unixtime2local(now, int(pytime.time()))

    if year >= 0 and year < 70:
        year += 2000
    elif year >= 70 and year <= 100:
        year += 1900

    now.c_y = rffi.cast(lltype.Signed, year)
    now.c_d = rffi.cast(lltype.Signed, day)
    now.c_m = rffi.cast(lltype.Signed, month)
    now.c_s = rffi.cast(lltype.Signed, second)
    now.c_i = rffi.cast(lltype.Signed, minute)
    now.c_h = rffi.cast(lltype.Signed, hour)

    if is_gmt:
        timelib.timelib_update_ts(
            now,
            lltype.nullptr(timelib.timelib_tzinfo.TO))
    else:
        timelib.timelib_update_ts(
            now,
            interp.get_default_timezone("mktime").timelib_timezone)

    if dst != -1:
        interp.space.ec.deprecated(
            "mktime(): The is_dst parameter is deprecated"
        )
        if is_gmt:
            if dst == 1:
                adjust_seconds -= 3600
        else:
            tmp_offset = timelib.timelib_get_time_zone_info(
                now.c_sse, interp.get_default_timezone("mktime").timelib_timezone
            )
            if dst == 1 and intmask(tmp_offset.c_is_dst) == 0:
                adjust_seconds -= 3600
            if dst == 0 and intmask(tmp_offset.c_is_dst) == 1:
                adjust_seconds += 3600
            timelib.timelib_time_offset_dtor(tmp_offset)

    error = lltype.malloc(
        rffi.CArrayPtr(lltype.Signed).TO, 1, flavor='raw', zero=True
    )

    timestamp = timelib.timelib_date_to_int(now, error)
    timestamp += adjust_seconds

    timelib.timelib_time_dtor(now)
    lltype.free(error, flavor='raw')

    return timestamp


@wrap(['interp', 'num_args', Optional(int), Optional(int), Optional(int),
       Optional(int), Optional(int), Optional(int), Optional(int)],
      error=False)
def mktime(interp, num_args, hour=0, minute=0, second=0,
           month=0, day=0, year=0, dst=-1):

    if not num_args:
        interp.space.ec.strict(
            "mktime(): You should be using the time() function instead")
        return interp.space.wrap(0)

    return interp.space.wrap(
        _mktime(interp, False, hour, minute, second, month, day, year, dst)
    )


@wrap(['interp', 'num_args', Optional(int), Optional(int), Optional(int),
       Optional(int), Optional(int), Optional(int), Optional(int)],
      error=False)
def gmmktime(interp, num_args, hour=0, minute=0, second=0,
           month=0, day=0, year=0, dst=-1):

    if not num_args:
        interp.space.ec.strict(
            "mktime(): You should be using the time() function instead")
        return interp.space.wrap(0)

    return interp.space.wrap(
        _mktime(interp, True, hour, minute, second, month, day, year, dst)
    )


@wrap(['interp', int, int, int], error=False)
def checkdate(interp, month, day, year):
    if year < 1 or year > 32767 or \
       timelib.timelib_valid_date(year, month, day) == 0:
        return interp.space.w_False
    return interp.space.w_True


@wrap(['interp', Optional(int), Optional(bool)], error=False)
def localtime(interp, timestamp=int(pytime.time()), is_associative=False):
    space = interp.space

    timelib_timezone = interp.get_default_timezone("mktime").timelib_timezone

    timelib_time = timelib.timelib_time_ctor()
    timelib_time.c_tz_info = timelib_timezone
    timelib_time.c_zone_type = timelib.TIMELIB_ZONETYPE_ID

    timelib.timelib_unixtime2local(timelib_time, timestamp)

    if is_associative:
        return_value = space.new_array_from_pairs([
            (space.wrap("tm_sec"),   space.wrap(timelib_time.c_s)),
            (space.wrap("tm_min"),   space.wrap(timelib_time.c_i)),
            (space.wrap("tm_hour"),  space.wrap(timelib_time.c_h)),
            (space.wrap("tm_mday"),  space.wrap(timelib_time.c_d)),
            (space.wrap("tm_mon"),   space.wrap(timelib_time.c_m - 1)),
            (space.wrap("tm_year"),  space.wrap(timelib_time.c_y - 1900)),
            (space.wrap("tm_wday"),  space.wrap(timelib.timelib_day_of_week(
                timelib_time.c_y,
                timelib_time.c_m,
                timelib_time.c_d))),
            (space.wrap("tm_yday"),  space.wrap(timelib.timelib_day_of_year(
                timelib_time.c_y,
                timelib_time.c_m,
                timelib_time.c_d))),
            (space.wrap("tm_isdst"), space.wrap(int(timelib_time.c_dst))),
        ])
    else:
        return_value = interp.space.new_array_from_list([
            space.wrap(timelib_time.c_s),
            space.wrap(timelib_time.c_i),
            space.wrap(timelib_time.c_h),
            space.wrap(timelib_time.c_d),
            space.wrap(timelib_time.c_m - 1),
            space.wrap(timelib_time.c_y - 1900),
            space.wrap(timelib.timelib_day_of_week(
                timelib_time.c_y,
                timelib_time.c_m,
                timelib_time.c_d)),
            space.wrap(timelib.timelib_day_of_year(
                timelib_time.c_y,
                timelib_time.c_m,
                timelib_time.c_d)),
            space.wrap(int(timelib_time.c_dst)),
        ])

    timelib.timelib_time_dtor(timelib_time)

    return return_value


@wrap(['interp', Optional(int)], error=False)
def getdate(interp, timestamp=int(pytime.time())):

    space = interp.space

    timelib_timezone = interp.get_default_timezone("getdate").timelib_timezone

    timelib_time = timelib.timelib_time_ctor()
    timelib_time.c_tz_info = timelib_timezone
    timelib_time.c_zone_type = timelib.TIMELIB_ZONETYPE_ID

    timelib.timelib_unixtime2local(timelib_time, timestamp)

    return_value = space.new_array_from_pairs([
        (space.wrap("seconds"),   space.wrap(timelib_time.c_s)),
        (space.wrap("minutes"),   space.wrap(timelib_time.c_i)),
        (space.wrap("hours"),  space.wrap(timelib_time.c_h)),
        (space.wrap("mday"),  space.wrap(timelib_time.c_d)),
        (space.wrap("wday"),  space.wrap(timelib.timelib_day_of_week(
            timelib_time.c_y, timelib_time.c_m, timelib_time.c_d))),
        (space.wrap("mon"),   space.wrap(timelib_time.c_m)),
        (space.wrap("year"),  space.wrap(timelib_time.c_y)),
        (space.wrap("yday"),  space.wrap(timelib.timelib_day_of_year(
            timelib_time.c_y, timelib_time.c_m, timelib_time.c_d))),
        (space.wrap("weekday"),  space.wrap(
            timelib.full_day_name(timelib_time.c_y, timelib_time.c_m, timelib_time.c_d))),
        (space.wrap("month"),  space.wrap(timelib.full_month_names[timelib_time.c_m - 1])),

        (space.wrap("0"), space.wrap(timestamp)),
    ])

    timelib.timelib_time_dtor(timelib_time)

    return return_value

def _strftime(interp, is_gmt, format_string, timestamp):
    offset = lltype.nullptr(timelib.timelib_time_offset.TO)
    ta = lltype.malloc(timelib.tm, flavor='raw', zero=True)

    timelib_time = timelib.timelib_time_ctor()
    if is_gmt:
        timelib_timezone = lltype.nullptr(timelib.timelib_tzinfo.TO)
        timelib.timelib_unixtime2gmt(timelib_time, timestamp)
    else:
        timelib_timezone = interp.get_default_timezone("getdate").timelib_timezone
        timelib_time.c_tz_info = timelib_timezone
        timelib_time.c_zone_type = timelib.TIMELIB_ZONETYPE_ID
        timelib.timelib_unixtime2local(timelib_time, timestamp)

    ta.c_tm_sec   = rffi.cast(rffi.INT, timelib_time.c_s)
    ta.c_tm_min   = rffi.cast(rffi.INT, timelib_time.c_i)
    ta.c_tm_hour  = rffi.cast(rffi.INT, timelib_time.c_h)
    ta.c_tm_mday  = rffi.cast(rffi.INT, timelib_time.c_d)
    ta.c_tm_mon   = rffi.cast(rffi.INT, timelib_time.c_m - 1)
    ta.c_tm_year  = rffi.cast(rffi.INT, timelib_time.c_y - 1900)
    ta.c_tm_wday  = rffi.cast(rffi.INT, timelib.timelib_day_of_week(
        timelib_time.c_y,
        timelib_time.c_m,
        timelib_time.c_d
    ))
    ta.c_tm_yday  = rffi.cast(rffi.INT, timelib.timelib_day_of_year(
        timelib_time.c_y,
        timelib_time.c_m,
        timelib_time.c_d
    ))

    if is_gmt:
        ta.c_tm_isdst = rffi.cast(rffi.INT, 0)
        ta.c_tm_gmtoff = rffi.cast(lltype.Signed, 0)
        ta.c_tm_zone = rffi.str2charp("GMT")
    else:
        offset = timelib.timelib_get_time_zone_info(timestamp, timelib_timezone)
        ta.c_tm_isdst = rffi.cast(rffi.INT, offset.c_is_dst)
        ta.c_tm_gmtoff = rffi.cast(lltype.Signed, offset.c_offset)
        ta.c_tm_zone = offset.c_abbr

    # stolen from PyPy
    i = 1024
    while True:
        outbuf = lltype.malloc(rffi.CCHARP.TO, i, flavor='raw')
        try:
            buflen = timelib.c_strftime(outbuf, i, format_string, ta)
            if buflen > 0 or i >= 256 * len(format_string):
                return rffi.charp2strn(outbuf, intmask(buflen))
        finally:
            timelib.timelib_time_dtor(timelib_time)
            lltype.free(outbuf, flavor='raw')
            if offset:
                timelib.timelib_time_offset_dtor(offset)
        i += i


@wrap(['interp', str, Optional(int)], error=False)
def strftime(interp, format_string, timestamp=int(pytime.time())):
    result = _strftime(interp, False, format_string, timestamp)

    if len(result) > 0:
        return interp.space.wrap(result)
    return interp.space.w_False


@wrap(['interp', str, Optional(int)], error=False)
def gmstrftime(interp, format_string, timestamp=int(pytime.time())):
    result = _strftime(interp, True, format_string, timestamp)

    if len(result) > 0:
        return interp.space.wrap(result)
    return interp.space.w_False



@wrap(['interp', Optional(str),
       Optional(InstanceUnwrapper(W_DateTimeZone, 'DateTimeZone'))], error=False)
def date_create(interp, format_string=None, w_datetimezone=None):
    date = W_DateTime(k_DateTime, [])
    error = common.initialize_date(interp, 'date_create', date, format_string, w_datetimezone)
    if error:
        return interp.space.w_False
    else:
        return date

@wrap(['interp', InstanceUnwrapper(W_DateTime, 'DateTime', null=False),
       int, int, int], error=False)
def date_date_set(interp, date, year, month, day):

    date.timelib_time.c_y = year
    date.timelib_time.c_m = month
    date.timelib_time.c_d = day

    timelib.timelib_update_ts(
        date.timelib_time,
        lltype.nullptr(timelib.timelib_tzinfo.TO)
    )

    return date


@wrap(['interp', InstanceUnwrapper(W_DateTime, 'DateTime', null=False),
       int, int, Optional(int)], error=False)
def date_time_set(interp, date, hour, minute, second=0):
    date.timelib_time.c_h = hour
    date.timelib_time.c_i = minute
    date.timelib_time.c_s = second

    timelib.timelib_update_ts(
        date.timelib_time,
        lltype.nullptr(timelib.timelib_tzinfo.TO)
    )

    return date


@wrap(['space', InstanceUnwrapper(W_DateTime, 'DateTime', null=False), str], error=False)
def date_format(space, date, str_time):
    return space.wrap(timelib.date_format(str_time, date.timelib_time))


@wrap(['space'])
def timezone_abbreviations_list(space):
    return datetimezone_klass._abbreviations_list(space)


@wrap(['space', InstanceUnwrapper(W_DateTime, 'DateTime', null=False)], error=False)
def date_timezone_get(space, date):
    return date.timezone


@wrap(['space', str, Optional(int), Optional(int)], error=False)
def timezone_name_from_abbr(space, abbr, offset=-1, isdst=-1):
    res = timelib.timezone_id_from_abbr(abbr, offset, isdst)
    if res:
        return space.wrap(res)
    return space.w_False


@wrap(['interp', str], error=False)
def timezone_open(interp, timezone_name):
    w_datetimezone = W_DateTimeZone(k_DateTimeZone, [])
    success = common.initialize_timezone(
        interp, "timezone_open", w_datetimezone, timezone_name, True)

    if success:
        return w_datetimezone
    return interp.space.w_False


@wrap(['interp', InstanceUnwrapper(W_DateTime, 'DateTime', null=False),
       InstanceUnwrapper(W_DateInterval, 'DateInterval')],
      error_handler=handle_as_void, error=False)
def date_add(interp, date, w_datetime_interval):
    common.date_addsub(interp, date, w_datetime_interval, 1)
    return date


@wrap(['interp', InstanceUnwrapper(W_DateTime, 'DateTime', null=False),
       InstanceUnwrapper(W_DateInterval, 'DateInterval')],
      error_handler=handle_as_void, error=False)
def date_sub(interp, date, w_datetime_interval):
    common.date_addsub(interp, date, w_datetime_interval, -1)
    return date


@wrap(['interp', Optional(bool)])
def gettimeofday(interp, as_float=False):

    space = interp.space

    void = lltype.nullptr(rffi.VOIDP.TO)
    timeval = lltype.malloc(timelib.timeval, flavor='raw')

    timelib.c_gettimeofday(timeval, void)

    if as_float:
        return space.wrap(intmask(timeval.c_tv_sec) + intmask(timeval.c_tv_usec) / 1000000.00)

    timelib_timezone = interp.get_default_timezone("gettimeofday").timelib_timezone
    offset = timelib.timelib_get_time_zone_info(timeval.c_tv_sec, timelib_timezone)

    return space.new_array_from_pairs([
            (space.wrap('sec'), space.wrap(intmask(timeval.c_tv_sec))),
            (space.wrap('usec'), space.wrap(intmask(timeval.c_tv_usec))),
            (space.wrap('minuteswest'), space.wrap(-intmask(offset.c_offset) / 60)),
            (space.wrap('dsttime'), space.wrap(intmask(offset.c_is_dst))),
        ])


def date_parse_element(space, return_val, element, name):
    if intmask(element) == -99999:
        return_val.append(
            (space.wrap(name), space.w_False))
    else:
        return_val.append(
            (space.wrap(name), space.wrap(element)))


@wrap(['interp', str], error=False)
def date_parse(interp, date_string):

    return_val = []
    space = interp.space

    with rffi.scoped_str2charp(date_string) as ll_date_string:
        error_c = lltype.malloc(timelib.timelib_error_containerP.TO, 1, flavor='raw')
        timelib_time = timelib.timelib_strtotime(
            ll_date_string,
            len(date_string), error_c, timelib.timelib_builtin_db(),
            timelib.tzinfo_callback
        )

        lltype.free(error_c, flavor='raw')

        date_parse_element(space, return_val, timelib_time.c_y, "year")
        date_parse_element(space, return_val, timelib_time.c_m, "month")
        date_parse_element(space, return_val, timelib_time.c_d, "day")
        date_parse_element(space, return_val, timelib_time.c_h, "hour")
        date_parse_element(space, return_val, timelib_time.c_i, "minute")
        date_parse_element(space, return_val, timelib_time.c_s, "second")
        date_parse_element(space, return_val, timelib_time.c_s, "fraction")

        return_val.append((space.wrap("warning_count"), space.wrap(0)))
        return_val.append((space.wrap("warnings"), space.new_array_from_list([])))
        return_val.append((space.wrap("error_count"), space.wrap(0)))
        return_val.append((space.wrap("errors"), space.new_array_from_list([])))

        return_val.append((
            space.wrap("is_localtime"),
            space.wrap(intmask(timelib_time.c_is_localtime) == 1))
        )

        if intmask(timelib_time.c_is_localtime):
            zone_type = rffi.cast(lltype.Signed, timelib_time.c_zone_type)

            return_val.append((
                space.wrap("zone_type"),
                space.wrap(zone_type)
            ))

            if zone_type == timelib.ZONETYPE_OFFSET:
                return_val.append((
                    space.wrap("zone"),
                    space.wrap(intmask(timelib_time.c_z))
                ))
                return_val.append((
                    space.wrap("is_dst"),
                    space.wrap(intmask(timelib_time.c_dst))
                ))

            if zone_type == timelib.ZONETYPE_ID:
                if timelib_time.c_tz_abbr:
                    return_val.append((
                        space.wrap("tz_abbr"),
                        space.wrap(rffi.charp2str(timelib_time.c_tz_abbr)))
                    )

                if timelib_time.c_tz_info:
                    return_val.append((
                        space.wrap("tz_id"),
                        space.wrap(rffi.charp2str(timelib_time.c_tz_info.c_name)))
                    )

            if zone_type == timelib.ZONETYPE_ABBR:
                return_val.append((
                    space.wrap("zone"),
                    space.wrap(intmask(timelib_time.c_z))
                ))
                return_val.append((
                    space.wrap("is_dst"),
                    space.wrap(intmask(timelib_time.c_dst) == 1))
                )
                return_val.append((
                    space.wrap("tz_abbr"),
                    space.wrap(rffi.charp2str(timelib_time.c_tz_abbr)))
                )

        if intmask(timelib_time.c_have_relative):
            raise NotImplementedError() # check bug51096.php

            relative_elements = [
                (space.wrap("year"), space.wrap(intmask(timelib_time.c_relative.c_y))),
                (space.wrap("month"), space.wrap(intmask(timelib_time.c_relative.c_m))),
                (space.wrap("day"), space.wrap(intmask(timelib_time.c_relative.c_d))),
                (space.wrap("hour"), space.wrap(intmask(timelib_time.c_relative.c_h))),
                (space.wrap("minute"), space.wrap(intmask(timelib_time.c_relative.c_i))),
                (space.wrap("second"), space.wrap(intmask(timelib_time.c_relative.c_s)))
            ]

            if intmask(timelib_time.c_relative.c_have_weekday_relative):
                relative_elements.append((
                    space.wrap("weekday"),
                    space.wrap(intmask(timelib_time.c_relative.c_relative.weekday))
                ))

            if intmask(timelib_time.c_relative.c_have_special_relative):
                raise NotImplementedError()

            if intmask(timelib_time.c_relative.c_first_last_day_of):
                if intmask(timelib_time.c_relative.c_first_last_day_of) == 1:
                    relative_elements.append((
                        space.wrap("first_day_of_month"), space.w_True
                    ))
                else:
                    relative_elements.append((
                        space.wrap("last_day_of_month"), space.w_True
                    ))

            return_val.append((
                space.wrap("relative"), space.new_array_from_pairs(relative_elements)
            ))

    return space.new_array_from_pairs(return_val)


@wrap(['interp', InstanceUnwrapper(W_DateTime, 'DateTime', null=False),
       int, int, Optional(int)], error=False)
def date_isodate_set(interp, date, year, week, day=1):

    date.timelib_time.c_y = year
    date.timelib_time.c_m = 1
    date.timelib_time.c_d = 1

    date.timelib_time.c_relative.c_d = timelib.timelib_daynr_from_weeknr(year, week, day)
    date.timelib_time.c_have_relative = rffi.cast(
        timelib.timelib_time.TO.c_have_relative, 1
    )

    timelib.timelib_update_ts(
        date.timelib_time,
        lltype.nullptr(timelib.timelib_tzinfo.TO)
    )

    return date

@wrap(['interp',
       InstanceUnwrapper(W_DateTime, 'DateTime', null=False), StringArg()],
      error=False)
def date_modify(interp, date, string_modifier):
    date.timelib_time = timelib.timelib_time_modify(
        date.timelib_time, string_modifier, date.timezone.timelib_timezone
    )

    return date

@wrap(['space', InstanceUnwrapper(W_DateTimeZone, 'DateTimeZone', null=False)],
      error=False)
def timezone_name_get(space, w_datetimezone):
    return space.wrap(rffi.charp2str(w_datetimezone.timelib_timezone.c_name))


@wrap(['interp',
       InstanceUnwrapper(W_DateTime, 'DateTime', null=False),
       InstanceUnwrapper(W_DateTimeZone, 'DateTimeZone', null=False)],
      error=False)
def date_timezone_set(interp, w_date, w_datetimezone):
    w_date.timezone = w_datetimezone

    timelib.timelib_set_timezone(
        w_date.timelib_time, w_date.timezone.timelib_timezone)
    timelib.timelib_unixtime2local(
        w_date.timelib_time, w_date.timelib_time.c_sse)

    return w_date


@wrap(['interp',
       InstanceUnwrapper(W_DateTime, 'DateTime'),
       InstanceUnwrapper(W_DateTime, 'DateTime'),
       Optional(bool)])
def date_diff(interp, w_datetime_1, w_datetime_2, absolute=False):
    return common.date_diff(interp, w_datetime_1, w_datetime_2, absolute)


@wrap(['interp', int, float, float], error=False)
def date_sun_info(interp, time, latitude, longitude):

    space = interp.space

    timelib_time = timelib.timelib_time_ctor()
    timelib_timezone = interp.get_default_timezone("date").timelib_timezone

    timelib_time.c_tz_info = timelib_timezone
    timelib_time.c_zone_type = timelib.TIMELIB_ZONETYPE_ID

    timelib.timelib_unixtime2local(timelib_time, time)

    timelib_time_2 = timelib.timelib_time_ctor()

    dummy = lltype.malloc(rffi.CArrayPtr(rffi.LONGLONG).TO, 1, flavor='raw')
    ddummy = lltype.malloc(rffi.CArrayPtr(lltype.Float).TO, 1, flavor='raw')
    c_rise = lltype.malloc(rffi.CArrayPtr(rffi.LONGLONG).TO, 1, flavor='raw')
    c_set = lltype.malloc(rffi.CArrayPtr(rffi.LONGLONG).TO, 1, flavor='raw')
    c_transit = lltype.malloc(rffi.CArrayPtr(rffi.LONGLONG).TO, 1, flavor='raw')

    ret_val = []

    # Get sun up/down and transit
    rs = timelib.timelib_astro_rise_set_altitude(
        timelib_time,
        longitude, latitude,
        -35.0/60, 1,
        ddummy, ddummy, c_rise, c_set, c_transit
    )

    if rs == -1:
        ret_val.append((space.wrap("sunrise"), space.w_False))
        ret_val.append((space.wrap("sunset"), space.w_False))
    elif rs == 1:
        ret_val.append((space.wrap("sunrise"), space.w_True))
        ret_val.append((space.wrap("sunset"), space.w_True))
    else:
        timelib_time_2.c_sse = c_rise[0]
        ret_val.append((
            space.wrap("sunrise"),
            space.wrap(timelib.timelib_date_to_int(timelib_time_2, dummy))
        ))
        timelib_time_2.c_sse = c_set[0]
        ret_val.append((
            space.wrap("sunset"),
            space.wrap(timelib.timelib_date_to_int(timelib_time_2, dummy))
        ))

    timelib_time_2.c_sse = c_transit[0]
    ret_val.append((
            space.wrap("transit"),
            space.wrap(timelib.timelib_date_to_int(timelib_time_2, dummy))
        ))

    # Get civil twilight
    rs = timelib.timelib_astro_rise_set_altitude(
        timelib_time,
        longitude, latitude,
        -6.0, 0,
        ddummy, ddummy, c_rise, c_set, c_transit
    )

    if rs == -1:
        ret_val.append((space.wrap("civil_twilight_begin"), space.w_False))
        ret_val.append((space.wrap("civil_twilight_end"), space.w_False))
    elif rs == 1:
        ret_val.append((space.wrap("civil_twilight_begin"), space.w_True))
        ret_val.append((space.wrap("civil_twilight_end"), space.w_True))
    else:
        timelib_time_2.c_sse = c_rise[0]
        ret_val.append((
            space.wrap("civil_twilight_begin"),
            space.wrap(timelib.timelib_date_to_int(timelib_time_2, dummy))
        ))
        timelib_time_2.c_sse = c_set[0]
        ret_val.append((
            space.wrap("civil_twilight_end"),
            space.wrap(timelib.timelib_date_to_int(timelib_time_2, dummy))
        ))


    # Get nautical twilight
    rs = timelib.timelib_astro_rise_set_altitude(
        timelib_time,
        longitude, latitude,
        -12.0, 0,
        ddummy, ddummy, c_rise, c_set, c_transit
    )

    if rs == -1:
        ret_val.append((space.wrap("nautical_twilight_begin"), space.w_False))
        ret_val.append((space.wrap("nautical_twilight_end"), space.w_False))
    elif rs == 1:
        ret_val.append((space.wrap("nautical_twilight_begin"), space.w_True))
        ret_val.append((space.wrap("nautical_twilight_end"), space.w_True))
    else:
        timelib_time_2.c_sse = c_rise[0]
        ret_val.append((
            space.wrap("nautical_twilight_begin"),
            space.wrap(timelib.timelib_date_to_int(timelib_time_2, dummy))
        ))
        timelib_time_2.c_sse = c_set[0]
        ret_val.append((
            space.wrap("nautical_twilight_end"),
            space.wrap(timelib.timelib_date_to_int(timelib_time_2, dummy))
        ))

    # Get astronomical twilight
    rs = timelib.timelib_astro_rise_set_altitude(
        timelib_time,
        longitude, latitude,
        -18.0, 0,
        ddummy, ddummy, c_rise, c_set, c_transit
    )

    if rs == -1:
        ret_val.append((space.wrap("astronomical_twilight_begin"), space.w_False))
        ret_val.append((space.wrap("astronomical_twilight_end"), space.w_False))
    elif rs == 1:
        ret_val.append((space.wrap("astronomical_twilight_begin"), space.w_True))
        ret_val.append((space.wrap("astronomical_twilight_end"), space.w_True))
    else:
        timelib_time_2.c_sse = c_rise[0]
        ret_val.append((
            space.wrap("astronomical_twilight_begin"),
            space.wrap(timelib.timelib_date_to_int(timelib_time_2, dummy))
        ))
        timelib_time_2.c_sse = c_set[0]
        ret_val.append((
            space.wrap("astronomical_twilight_end"),
            space.wrap(timelib.timelib_date_to_int(timelib_time_2, dummy))
        ))

    timelib.timelib_time_dtor(timelib_time)
    timelib.timelib_time_dtor(timelib_time_2)

    return space.new_array_from_pairs(ret_val)


@wrap(['interp', 'num_args', int, Optional(int),
       Optional(float), Optional(float),
       Optional(float), Optional(float)], error=False)
def date_sunrise(interp, num_args, timestamp,
                 return_format=common.SUNFUNCS_RET_STRING,
                 latitude=31.7667, longitude=35.2333,
                 zenith=0, gmt_offset=0):

    return common.date_sunrise_sunset(
        "date_sunrise", interp, num_args, timestamp, return_format,
        latitude, longitude, zenith, gmt_offset
    )


@wrap(['interp', 'num_args', int, Optional(int),
       Optional(float), Optional(float),
       Optional(float), Optional(float)], error=False)
def date_sunset(interp, num_args, timestamp,
                 return_format=common.SUNFUNCS_RET_STRING,
                 latitude=31.7667, longitude=35.2333,
                 zenith=0, gmt_offset=0):

    return common.date_sunrise_sunset(
        "date_sunset", interp, num_args, timestamp, return_format,
        latitude, longitude, zenith, gmt_offset
    )

@wrap(['space', Optional(LongArg()), Optional(StringArg())])
def timezone_identifiers_list(space, what=2047, country=None):
    return common.timezone_identifiers_list(space, what, country)


@wrap(['interp', InstanceUnwrapper(W_DateTimeZone, 'DateTimeZone'),
       Optional(int), Optional(int)])
def timezone_transitions_get(interp, w_datetimezone,
                             timestamp_begin=-sys.maxint - 1,
                             timestamp_end=sys.maxint):

    return common.timezone_transitions_get(
        interp, w_datetimezone, timestamp_begin, timestamp_end)


@wrap(['interp', InstanceUnwrapper(W_DateTime, 'DateTime')], error=False)
def date_timestamp_get(interp, w_datetime):
    return common.date_timestamp_get(interp, w_datetime)
